"""
LiveTrack Microservice

- Receives astronaut activity data from the Simulator via ZeroMQ
- Tracks events: Flushes, Water Additions, Planet Visits
- Logs all events into WaterLog (SQLite via Flask API)
"""

import zmq
import requests
import json


# ZeroMQ Subscriber Setup
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://localhost:5556")  # Connect to the Simulator
socket.setsockopt_string(zmq.SUBSCRIBE, "")

print("🚀 LiveTrack: Listening for astronaut activity events...")

def send_to_waterlog(event):
    """
    Sends received event data to WaterLog for storage.
    
    Args:
        event (dict): The event data (e.g., flush, refill, planet visit)
    """
    try:
        response = requests.post("http://localhost:5001/log", json=event)
        if response.status_code == 201:
            print(f"✅ Event Logged: {event}")
        else:
            print(f"⚠️ Error logging event: {response.status_code} | Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")

while True:
    # Receive event data from the Simulator
    message = socket.recv_json()
    print(f"📥 Received Event: {json.dumps(message, indent=2)}")

    # Log the received data into WaterLog
    send_to_waterlog(message)
