"""
Simulator Microservice

- Generates random astronaut activity:
  - Flush events
  - Water refills
  - Planet visits
- Sends data to LiveTrack via ZeroMQ
"""

import zmq
import time
import random

# ZeroMQ Publisher Setup
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:5556")  # LiveTrack subscribes to this

print("🚀 Simulator: Generating astronaut activity...")

def generate_event():
    """
    Randomly generates an astronaut event.
    
    Returns:
        dict: Event containing type, details, and timestamp.
    """
    event_type = random.choice(["flush", "water_refill", "planet_visit"])
    
    if event_type == "flush":
        event = {
            "event_type": "flush",
            "waste_volume": random.randint(1, 5),
            "timestamp": time.time()
        }
    elif event_type == "water_refill":
        event = {
            "event_type": "water_refill",
            "water_added": random.randint(10, 50),  # Liters
            "timestamp": time.time()
        }
    else:  # planet_visit
        event = {
            "event_type": "planet_visit",
            "planet_name": random.choice(["Mars", "Europa", "Titan", "Ganymede"]),
            "timestamp": time.time()
        }

    return event

while True:
    event = generate_event()
    
    # Send event to LiveTrack
    socket.send_json(event)
    print(f"📤 Sent Event: {event}")
    
    time.sleep(random.randint(3, 7))  # Simulating random astronaut activity
