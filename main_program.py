"""
Main Program for W.E.T. System

Launches and manages the microservices:
- LiveTrack (ZeroMQ)
- WaterLog (SQLite & Flask API)
- ViewPort (Tkinter GUI)
- Simulator (Astronaut Flushes)
"""

import subprocess
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Start Microservices with small delays to prevent race conditions
logging.info("🚀 Starting W.E.T. System Microservices...")

try:
    logging.info("🔹 Starting WaterLog (Flask API & SQLite)")
    water_log = subprocess.Popen(["python3", "./microservices/WaterLog/water_log.py"])
    time.sleep(2)  # Ensure API is ready

    logging.info("🔹 Starting LiveTrack (ZeroMQ Listener)")
    live_track = subprocess.Popen(["python3", "./microservices/LiveTrack/live_track.py"])
    time.sleep(1)

    logging.info("🔹 Starting Simulator (Astronaut Events Generator)")
    simulator = subprocess.Popen(["python3", "./microservices/Simulator/simulator.py"])
    time.sleep(1)

    logging.info("🔹 Starting ViewPort (Tkinter GUI)")
    view_port = subprocess.Popen(["python3", "./microservices/ViewPort/view_port.py"])

    logging.info("✅ W.E.T. System is now running.")

    # Keep the main process running while microservices run
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    logging.info("🔴 Shutting down W.E.T. System...")

    # Terminate each microservice gracefully
    live_track.terminate()
    water_log.terminate()
    view_port.terminate()
    simulator.terminate()

    logging.info("✅ All microservices have been stopped.")
