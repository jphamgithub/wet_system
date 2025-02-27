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
import signal
import sys

# ZeroMQ Publisher Setup
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:5556")  # LiveTrack subscribes to this

print("🚀 Simulator: Generating astronaut activity...")

# Global flag to stop the simulator properly
running = True

def shutdown_simulator(signum, frame):
    """Handles termination signals (e.g., SIGTERM, SIGINT) to shut down gracefully."""
    global running
    print("🛑 Simulator Shutting Down...")
    running = False  # Set flag to stop the event loop

# Catch termination signals
signal.signal(signal.SIGTERM, shutdown_simulator)
signal.signal(signal.SIGINT, shutdown_simulator)  # Handle Ctrl+C

def generate_event():
    """Randomly generates an astronaut event."""
    event_type = random.choice(["flush", "water_refill", "planet_visit"])
    
    if event_type == "flush":
        return {"event_type": "flush", "waste_volume": random.randint(1, 5), "timestamp": time.time()}
    elif event_type == "water_refill":
        return {"event_type": "water_refill", "water_added": random.randint(10, 50), "timestamp": time.time()}
    else:  # planet_visit
        return {"event_type": "planet_visit", "planet_name": random.choice(["Mars", "Europa", "Titan", "Ganymede"]), "timestamp": time.time()}

# Modified loop that stops when running = False
while running:
    event = generate_event()
    socket.send_json(event)
    print(f"📤 Sent Event: {event}")
    time.sleep(random.randint(3, 7))  # Simulate astronaut activity

print("✅ Simulator Stopped Cleanly.")
