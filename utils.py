import json
import requests
import logging
from flask import jsonify
import google.generativeai as genai
from config import API_KEY,ACCESS_TOKEN,VERSION,PHONE_NUMBER_ID


genai.configure(api_key=API_KEY)

model = genai.GenerativeModel('gemini-pro')

user_chats={}
instructions = 'Your name is Sanicle AI.You are Menstrual Health Support. answer only queries related to Menstrual Health. '



def generate_response(chat,message_body):
    # Return text in uppercase
    response = chat.send_message(message_body)
    return response


def is_valid_whatsapp_message(body):
    """
    Check if the incoming webhook event has a valid WhatsApp message structure.
    """
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )


def process_whatsapp_message(body):
    global user_chats
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]

    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    message_body = message["text"]["body"]

    if wa_id in user_chats:
        chat = user_chats[wa_id]
    else:
        chat = model.start_chat(history=[])
        user_chats[wa_id] = chat

    # TODO: implement custom function here
    response = chat.send_message(instructions + message_body)   #generate_response(chat, message_body)

    data = get_text_message_input(f'+{wa_id}', response.text)
    send_message(data)
    user_chats[wa_id] = chat




def get_text_message_input(recipient, text):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
    )


def send_message(data):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}",
    }

    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"

    try:
        response = requests.post(
            url, data=data, headers=headers, timeout=10
        )  # 10 seconds timeout as an example
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
    except requests.Timeout:
        logging.error("Timeout occurred while sending message")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except (
        requests.RequestException
    ) as e:  # This will catch any general request exception
        logging.error(f"Request failed due to: {e}")
        return jsonify({"status": "error", "message": "Failed to send message"}), 500
    else:
        # Process the response as normal
        log_http_response(response)
        return response

def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")


