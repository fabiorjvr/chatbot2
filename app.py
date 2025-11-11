# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
import requests
import os
from ai_agent import AIAgent


# Manual .env parsing
try:
    with open('.env', 'r', encoding='latin-1') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
except FileNotFoundError:
    print("Warning: .env file not found. Falling back to environment variables.")


app = Flask(__name__)
ai_agent = AIAgent()


# Evolution API configuration
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")
INSTANCE_NAME = "default"


@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("Received webhook:", data)

    # Extract message details from the webhook payload
    if data.get("event") == "messages.upsert" and data.get("data"):
        message_data = data["data"]
        if message_data.get("key", {}).get("fromMe"):
            return jsonify({"status": "ignored_from_me"})

        sender = message_data.get("key", {}).get("remoteJid")
        message_text = message_data.get("message", {}).get("conversation")

        if sender and message_text:
            # Process the message with the AI Agent
            response_text = ai_agent.process_message(message_text)

            # Send the response back to the user
            send_message(sender, response_text)

    return jsonify({"status": "received"})


def send_message(recipient_jid, text):
    """Sends a message using the Evolution API."""
    url = f"{EVOLUTION_API_URL}/message/sendText/{INSTANCE_NAME}"
    headers = {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "number": recipient_jid,
        "options": {
            "delay": 1200,
            "presence": "composing"
        },
        "textMessage": {
            "text": text
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"Sent message to {recipient_jid}: {text}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to {recipient_jid}: {e}")


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)