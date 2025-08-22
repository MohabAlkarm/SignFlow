import requests
from agora_token_builder import RtmTokenBuilder
import json


# Set these from your Agora project
AGORA_APP_ID = "5812eca6e34c4aecae565ee3acdc1660"
AGORA_APP_CERTIFICATE = "08a0b81d3c984f45896e8cac9c4d0b0d"
RTM_BASE_URL = "https://api.agora.io/dev/v2/project"
TOKEN = ""
NAME = ""


# Create RTM token
def generate_rtm_token():
    res = requests.get('http://127.0.0.1:8000/getClientInfo')
    response = json.loads(res.text)
    print("RTM token: ")
    print(response['rtmToken'])
    global TOKEN
    global NAME
    TOKEN = response['rtmToken']
    NAME = response['client_name']

# Send a message to a user via Agora RTM REST API
def send_rtm_message(to_user_id, message_text):
    #token = generate_rtm_token(SIGNER_UID)
    url = f"{RTM_BASE_URL}/{AGORA_APP_ID}/rtm/users/listener1/peer_messages?wait_for_ack=false"

    headers = {
        "Content-Type": "application/json",
        "x-agora-token": TOKEN,
        "x-agora-uid": "listener1"
    }

    body = {
        "destination": to_user_id,
        "enable_offline_messaging": False,
        "enable_historical_messaging": False,
        "payload": message_text
    }

    response = requests.post(url, headers=headers, json=body)
    if response.status_code == 200:
        print(f"Sent RTM message: '{message_text}' → {to_user_id}")
    else:
        print(f"Failed to send RTM message: {response.status_code} {response.text}")
