"""
Main Program for W.E.T. System

Launches and manages the microservices:
- LiveTrack (ZeroMQ)
- WaterLog (SQLite & Flask API)
- ViewPort (Tkinter GUI)
"""

import subprocess
import time
import logging
import signal
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Store process references
processes = {}

def start_process(name, command, delay=0):
    """Starts a subprocess and stores it in the processes dictionary."""
    logging.info(f"🔹 Starting {name}...")
    try:
        proc = subprocess.Popen(command)
        processes[name] = proc
        time.sleep(delay)  # Give time for startup if needed
    except Exception as e:
        logging.error(f"❌ Failed to start {name}: {e}")
        shutdown()
        sys.exit(1)

def shutdown(signum=None, frame=None):
    """Gracefully shuts down all running microservices."""
    logging.info("🔴 Shutting down W.E.T. System...")

    for name, proc in processes.items():
        logging.info(f"🛑 Stopping {name}...")
        proc.terminate()
        proc.wait()  # Ensure the process is fully stopped

    logging.info("✅ All microservices have been stopped.")
    sys.exit(0)

# Handle manual interrupts (Ctrl+C)
signal.signal(signal.SIGINT, shutdown)

# Start Microservices (EXCLUDING SIMULATOR)
logging.info("🚀 Starting W.E.T. System Microservices...")

start_process("WaterLog (Flask API & SQLite)", ["python3", "./microservices/WaterLog/water_log.py"], delay=2)
start_process("LiveTrack (ZeroMQ Listener)", ["python3", "./microservices/LiveTrack/live_track.py"], delay=1)
start_process("ViewPort (Tkinter GUI)", ["python3", "./microservices/ViewPort/view_port.py"])

logging.info("✅ W.E.T. System is now running (Simulator NOT Started).")

# Keep running until interrupted
while True:
    time.sleep(1)
