"""
ViewPort: GUI for W.E.T. System

- Displays system status, astronaut waste events, and historical logs.
- Pulls event data from WaterLog API.
- Controls the Simulator (Pause & Resume).
- Manually triggers flush & water refill events.
- Fetches random motivational quotes, planets, and stations from Name Generator Microservice.
"""

import psutil 
import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk
import requests
import time
import os
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Get the absolute path to the script's directory
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

# API URLs
WATERLOG_API = "http://127.0.0.1:5001/history"
LIVE_TRACK_API = "http://127.0.0.1:5001/log"

# Path to `name_generator.py`
NAME_GEN_PATH = "../CS361_partner_Microservice/name_generator.py"

# Simulator Process Management
simulator_process = None

class ViewPortApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 W.E.T. System Dashboard")

        # Define image paths
        self.toilet_img_path = os.path.join(BASE_DIR, "gui", "toilet.png")
        self.poop_img_path = os.path.join(BASE_DIR, "gui", "spacepoop.png")

        # Load the toilet image initially
        self.toilet_img = ImageTk.PhotoImage(Image.open(self.toilet_img_path).resize((150, 150)))
        self.img_label = tk.Label(root, image=self.toilet_img)
        self.img_label.pack()

        # Status Label
        self.status_label = tk.Label(root, text="System Status: Loading...", font=("Arial", 12, "bold"))
        self.status_label.pack()

        # Event History Table
        self.tree = ttk.Treeview(root, columns=("Type", "Details", "Time"), show="headings")
        self.tree.heading("Type", text="Event Type")
        self.tree.heading("Details", text="Details")
        self.tree.heading("Time", text="Timestamp")
        self.tree.pack(pady=5)

        # Chart Frame
        self.chart_frame = tk.Frame(root)
        self.chart_frame.pack(pady=5)

        # Motivational Quote
        self.quote_label = tk.Label(root, text="Fetching inspiration...", font=("Arial", 10, "italic"), wraplength=400)
        self.quote_label.pack(pady=5)

        # Nearby Planets & Stations
        self.planet_label = tk.Label(root, text="🪐 Nearby Planet If You've Been Flushing too much: Loading...", font=("Arial", 10, "bold"))
        self.planet_label.pack()

        self.station_label = tk.Label(root, text="🏠 Nearby Station for plumbing services: Loading...", font=("Arial", 10, "bold"))
        self.station_label.pack()

        # Buttons Frame
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)

        # Control Buttons
        self.simulator_status = tk.StringVar(value="⏸ Pause Simulator")
        self.sim_button = tk.Button(button_frame, textvariable=self.simulator_status, command=self.toggle_simulator)
        self.sim_button.grid(row=0, column=0, padx=5)

        self.flush_button = tk.Button(button_frame, text="🚽 Flush", command=self.send_flush_event)
        self.flush_button.grid(row=0, column=1, padx=5)

        self.refill_button = tk.Button(button_frame, text="💧 Refill Water", command=self.send_water_refill)
        self.refill_button.grid(row=0, column=2, padx=5)

        self.quote_button = tk.Button(button_frame, text="🌟 New Quote", command=self.fetch_motivational_quote)
        self.quote_button.grid(row=1, column=0, padx=5)

        self.planet_button = tk.Button(button_frame, text="🪐 Random Planet", command=self.fetch_nearby_planet)
        self.planet_button.grid(row=1, column=1, padx=5)

        self.station_button = tk.Button(button_frame, text="🏠 Random Station", command=self.fetch_nearby_station)
        self.station_button.grid(row=1, column=2, padx=5)

        self.refresh_button = tk.Button(root, text="🔄 Refresh Dashboard", command=self.update_data)
        self.refresh_button.pack(pady=5)

        # Start Simulator Automatically
        self.start_simulator()

        # Initial Data Load
        self.update_data()

    def update_data(self):
        """Fetches and updates event data, charts, and motivational quote."""
        self.fetch_event_history()
        self.update_chart()
        self.fetch_motivational_quote()
        self.fetch_nearby_planet()
        self.fetch_nearby_station()

    def fetch_event_history(self):
        """Fetches event history from WaterLog API and dynamically updates the table."""
        self.tree.delete(*self.tree.get_children())  # Clear previous data

        try:
            response = requests.get(WATERLOG_API)
            events = response.json()

            if not events:
                return  # No data available yet

            # Show all events
            for event in events:
                details = event.get("waste_volume") or event.get("water_added") or event.get("planet_name") or "N/A"
                self.tree.insert("", "end", values=(event["event_type"], details, event["timestamp"]))

            # Update system status based on latest data
            flushes = sum(1 for e in events if e["event_type"] == "flush")
            self.status_label.config(text=f"System Status: Running\nTotal Flushes: {flushes}\nWater Level: OK")

        except Exception as e:
            self.status_label.config(text="❌ Error fetching event data!")

        # Auto-refresh every 5 seconds
        self.root.after(5000, self.fetch_event_history)
    
    def update_chart(self):
        """Fetches event data and updates the bar chart."""
        try:
            response = requests.get(WATERLOG_API)
            events = response.json()

            event_counts = {"Flushes": 0, "Water Refills": 0, "Planet Visits": 0}
            for event in events:
                if event["event_type"] == "flush":
                    event_counts["Flushes"] += 1
                elif event["event_type"] == "water_refill":
                    event_counts["Water Refills"] += 1
                elif event["event_type"] == "planet_visit":
                    event_counts["Planet Visits"] += 1

            # Clear existing chart
            for widget in self.chart_frame.winfo_children():
                widget.destroy()

            # Create new chart
            fig, ax = plt.subplots(figsize=(4, 2))
            ax.bar(event_counts.keys(), event_counts.values(), color=["blue", "green", "red"])
            ax.set_ylabel("Event Count")
            ax.set_title("Astronaut Waste Tracking")

            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack()
        except Exception:
            pass

    def fetch_motivational_quote(self):
        """Calls name_generator.py to fetch a random quote."""
        try:
            quote = subprocess.check_output(["python3", NAME_GEN_PATH, "--quote"], text=True).strip()
            self.quote_label.config(text=f"🌟 {quote} 🌟")
        except Exception:
            self.quote_label.config(text="🚀 Keep pushing forward, astronaut! 🌌")

    def fetch_nearby_planet(self):
        """Calls name_generator.py to fetch a random planet."""
        try:
            planet = subprocess.check_output(["python3", NAME_GEN_PATH, "--planet"], text=True).strip()
            self.planet_label.config(text=f"🪐 Nearby Planet: {planet}")
        except Exception:
            self.planet_label.config(text="🪐 Nearby Planet: Unknown")

    def fetch_nearby_station(self):
        """Calls name_generator.py to fetch a random station."""
        try:
            station = subprocess.check_output(["python3", NAME_GEN_PATH, "--station"], text=True).strip()
            self.station_label.config(text=f"🏠 Nearby Station: {station}")
        except Exception:
            self.station_label.config(text="🏠 Nearby Station: Unknown")

    def send_flush_event(self):
        """Manually logs a flush event and temporarily changes the image."""
        event_data = {
            "event_type": "flush",
            "waste_volume": 3,
            "timestamp": time.time()
        }
        response = requests.post(LIVE_TRACK_API, json=event_data)

        if response.status_code == 201:
            print("✅ Flush event logged successfully.")
            self.toilet_img = ImageTk.PhotoImage(Image.open(self.poop_img_path).resize((150, 150)))
            self.img_label.config(image=self.toilet_img)
            self.root.after(2000, self.reset_toilet_image)  # Reset after 2 seconds
        else:
            print(f"❌ Failed to log flush event. Response: {response.text}")

    def reset_toilet_image(self):
        """Resets the image back to the toilet after showing the poop image."""
        self.toilet_img = ImageTk.PhotoImage(Image.open(self.toilet_img_path).resize((150, 150)))
        self.img_label.config(image=self.toilet_img)

    def send_water_refill(self):
        """Manually logs a water refill event with a proper timestamp."""
        event_data = {
            "event_type": "water_refill",
            "water_added": 20,  # Example value
            "timestamp": time.time()  # ✅ Ensure timestamp is included
        }
        response = requests.post(LIVE_TRACK_API, json=event_data)
        if response.status_code == 201:
            print("✅ Water refill event logged successfully.")
        else:
            print(f"❌ Failed to log water refill event. Response: {response.text}")

    def toggle_simulator(self):
        """Pauses or resumes the simulator process without freezing GUI."""
        global simulator_process

        if simulator_process:
            # Run stopping logic in a separate thread to avoid freezing GUI
            threading.Thread(target=self.stop_simulator, daemon=True).start()
        else:
            self.start_simulator()

    def stop_simulator(self):
        """Kills all simulator instances without blocking the GUI."""
        print("🚫 Stopping Simulator...")

        # Kill all running simulator processes
        subprocess.run(["pkill", "-f", "simulator.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)  # Allow process cleanup

        # Double-check if it's still running
        for proc in psutil.process_iter(attrs=['pid', 'cmdline']):
            if proc.info['cmdline'] and "simulator.py" in " ".join(proc.info['cmdline']):
                print(f"⚠️ Simulator process {proc.info['pid']} is still running! Killing it...")
                proc.terminate()
                proc.wait(timeout=3)

        self.simulator_status.set("▶ Resume Simulator")
        print("✅ Simulator Fully Paused.")
        global simulator_process
        simulator_process = None

    def start_simulator(self):
        """Starts the simulator process."""
        print("✅ Starting Simulator...")
        global simulator_process
        simulator_process = subprocess.Popen(
            ["python3", "./microservices/Simulator/simulator.py"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        self.simulator_status.set("⏸ Pause Simulator")
        print("🚀 Simulator Running.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ViewPortApp(root)
    root.mainloop()


