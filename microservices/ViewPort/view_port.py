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
from datetime import datetime

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

        # Set a light gray background
        self.root.configure(bg='#f5f5f5')  # Light gray background

        # Set minimum window size
        self.root.minsize(800, 600)

        # ========== IMAGE SETUP ==========
        self.toilet_img_path = os.path.join(BASE_DIR, "gui", "toilet.png")
        self.poop_img_path = os.path.join(BASE_DIR, "gui", "spacepoop.png")

        self.toilet_img = ImageTk.PhotoImage(Image.open(self.toilet_img_path).resize((150, 150)))

        # Create a canvas and scrollbar for the entire window
        self.canvas = tk.Canvas(root, bg='#ffffff')
        self.scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas, style='TFrame')

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Adjust layout settings to prevent stretching
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.scrollbar_horizontal = ttk.Scrollbar(root, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=self.scrollbar_horizontal.set)

        self.scrollbar_horizontal.pack(side="bottom", fill="x")

        # Ensure horizontal scrollbar for the overall window
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        # Update widget parents to scrollable_frame
        self.img_label = tk.Label(self.scrollable_frame, image=self.toilet_img, borderwidth=2, relief="solid")
        self.status_label = tk.Label(self.scrollable_frame, text="System Status: Loading...", font=("Arial", 12, "bold"))
        self.tree = ttk.Treeview(self.scrollable_frame, columns=("Type", "Details", "Time"), show="headings")
        self.chart_frame = tk.Frame(self.scrollable_frame)
        self.chart_insight_label = tk.Label(self.scrollable_frame, text="", font=("Arial", 10, "italic"))
        button_frame = tk.Frame(self.scrollable_frame)

        # ========== STATUS & EVENT DISPLAY ==========
        self.status_label.pack(expand=False, fill='both', pady=2)

        # Update styles for labels
        self.status_label.config(bg='#f5f5f5', fg='#333333')
        self.quote_label = tk.Label(self.scrollable_frame, text="Fetching inspiration...", font=("Arial", 10, "italic"), wraplength=400)
        self.quote_label.pack(pady=2)
        self.quote_label.config(bg='#f5f5f5', fg='#333333')

        self.planet_label = tk.Label(self.scrollable_frame, text="🪐 Nearby Planet Lookup: Loading...", font=("Arial", 10, "bold"))
        self.planet_label.pack(pady=2)
        self.planet_label.config(bg='#f5f5f5', fg='#333333')

        self.station_label = tk.Label(self.scrollable_frame, text="🏠 Nearby Station Lookup: Loading...", font=("Arial", 10, "bold"))
        self.station_label.pack(pady=2)
        self.station_label.config(bg='#f5f5f5', fg='#333333')

        # Event History Table (Logs)
        self.tree.heading("Type", text="Event Type")
        self.tree.heading("Details", text="Details")
        self.tree.heading("Time", text="Timestamp")
        self.tree.pack(expand=True, fill='both', pady=2)

        # Chart Frame & Insights
        self.chart_frame.pack(expand=True, fill='both', pady=2)
        self.chart_insight_label.pack(expand=False, fill='both', pady=2)

        # Update styles for labels
        self.quote_label = tk.Label(self.scrollable_frame, text="Fetching inspiration...", font=("Arial", 10, "italic"), wraplength=400)
        self.quote_label.pack(pady=2)

        self.planet_label = tk.Label(self.scrollable_frame, text="🪐 Nearby Planet Lookup: Loading...", font=("Arial", 10, "bold"))
        self.planet_label.pack(pady=2)

        self.station_label = tk.Label(self.scrollable_frame, text="🏠 Nearby Station Lookup: Loading...", font=("Arial", 10, "bold"))
        self.station_label.pack(pady=2)

        # ========== BUTTON CONTROLS ==========
        button_frame.pack(expand=False, fill='both', pady=5)

        # Configure grid rows and columns to be responsive
        for i in range(9):
            button_frame.grid_rowconfigure(i, weight=1)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        # Update styles for buttons with distinct background color
        button_style = {'bg': '#ffffff', 'fg': '#000000', 'activebackground': '#dddddd', 'activeforeground': '#000000', 'font': ('Arial', 10, 'bold'), 'borderwidth': 1, 'relief': 'flat'}

        # ---- Simulator Controls ----
        tk.Label(button_frame, text="🚀 Simulator Controls", font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=2)
        self.simulator_status = tk.StringVar(value="⏸ Pause Simulator")
        self.sim_button = tk.Button(button_frame, textvariable=self.simulator_status, command=self.toggle_simulator)
        self.sim_button.grid(row=1, column=0, columnspan=2, padx=5, pady=2, sticky='ew')

        # ---- Astronaut Commands ----
        tk.Label(button_frame, text="🧑‍🚀 Astronaut Commands", font=("Arial", 10, "bold")).grid(row=2, column=0, columnspan=2)
        self.flush_button = tk.Button(button_frame, text="🚽 Remote Send Flush", command=self.send_flush_event)
        self.flush_button.grid(row=3, column=0, padx=5, pady=2, sticky='ew')

        self.manual_refill_button = tk.Button(button_frame, text="💧 Manual Refill from Storage", command=self.send_water_refill)
        self.manual_refill_button.grid(row=3, column=1, padx=5, pady=2, sticky='ew')

        # ---- Exploration & Assistance ----
        tk.Label(button_frame, text="🔭 Exploration & Assistance", font=("Arial", 10, "bold")).grid(row=5, column=0, columnspan=2)
        self.quote_button = tk.Button(button_frame, text="🌟 Feeling lonely?", command=self.fetch_motivational_quote)
        self.quote_button.grid(row=6, column=0, padx=5, pady=2, sticky='ew')

        self.planet_button = tk.Button(button_frame, text="🪐 Lookup Planet", command=self.fetch_nearby_planet)
        self.planet_button.grid(row=6, column=1, padx=5, pady=2, sticky='ew')

        self.station_button = tk.Button(button_frame, text="🏠 Find Station", command=self.fetch_nearby_station)
        self.station_button.grid(row=7, column=0, columnspan=2, padx=5, pady=2, sticky='ew')

        # Add a new button for full refill and balance
        self.full_refill_button = tk.Button(button_frame, text="🌍 Full Refill & Balance", command=self.full_refill_and_balance)
        self.full_refill_button.grid(row=4, column=1, padx=5, pady=2, sticky='ew')
        self.full_refill_button.config(**button_style)

        # ---- System Maintenance ----
        tk.Label(button_frame, text="🛠 System Maintenance", font=("Arial", 10, "bold")).grid(row=8, column=0, columnspan=2)
        self.refresh_button = tk.Button(button_frame, text="🔄 Refresh Dashboard", command=self.update_data)
        self.refresh_button.grid(row=9, column=0, padx=5, pady=2, sticky='ew')

        self.clear_button = tk.Button(button_frame, text="🗑 Reset System!", command=self.clear_database)
        self.clear_button.grid(row=9, column=1, padx=5, pady=2, sticky='ew')

        # Apply button styles
        self.sim_button.config(**button_style)
        self.flush_button.config(**button_style)
        self.manual_refill_button.config(**button_style)
        self.quote_button.config(**button_style)
        self.planet_button.config(**button_style)
        self.station_button.config(**button_style)
        self.refresh_button.config(**button_style)
        self.clear_button.config(**button_style)

        # ========== INITIALIZATION ==========
        self.start_simulator()
        self.update_data()

        # Pack the image label at the top
        self.img_label.pack(side="top", expand=False, fill='both', pady=10)

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
                timestamp = datetime.fromtimestamp(event["timestamp"]).strftime('%Y-%m-%d %H:%M:%S')
                self.tree.insert("", "end", values=(event["event_type"], details, timestamp))

            # Update system status based on latest data
            flushes = sum(1 for e in events if e["event_type"] == "flush")
            self.status_label.config(text=f"System Status: Running\nTotal Flushes: {flushes}\nWater Level: OK")

        except Exception as e:
            self.status_label.config(text="❌ Error fetching event data!")

        # Auto-refresh every 5 seconds
        self.root.after(5000, self.fetch_event_history)
    
    def update_chart(self):
        """Fetches event data and updates the bar chart with ratio-based insights."""
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

            # ---- Compute Flush-to-Refill Ratio ----
            flushes = event_counts["Flushes"]
            refills = event_counts["Water Refills"]

            if refills == 0:
                ratio = float("inf")  # Avoid division by zero
            else:
                ratio = flushes / refills

            # ---- Generate Insights Based on Ratio ----
            if ratio > 3:
                insight_text = "🚨 WARNING: The system is running out of water! Refill ASAP."
            elif 2 < ratio <= 3:
                insight_text = "⚠️ Caution: Water levels decreasing. Consider refilling soon."
            elif 0.5 <= ratio <= 2:
                insight_text = "✅ System is running optimally."
            else:  # ratio < 0.5
                insight_text = "🚰 Water refills exceed usage. Check for leaks or inefficiency."

            self.chart_insight_label.config(text=insight_text, font=("Arial", 10, "italic"))
        
        except Exception as e:
            print("❌ Error updating chart:", e)


    def fetch_motivational_quote(self):
        """Fetches a new motivational quote and updates the display."""
        try:
            quote = subprocess.check_output(["python3", NAME_GEN_PATH, "--quote"], text=True).strip()
            self.quote_label.config(text=f"🌟 {quote} 🌟")
        except Exception:
            self.quote_label.config(text="🚀 Keep pushing forward, astronaut! 🌌")
        
        self.root.update_idletasks()  # Force UI update

    def fetch_nearby_planet(self):
        """Fetches a random planet and updates the display immediately."""
        try:
            planet = subprocess.check_output(["python3", NAME_GEN_PATH, "--planet"], text=True).strip()
            self.planet_label.config(text=f"🪐 {planet} has rich water resources! Consider refilling the system there.")
        except Exception:
            self.planet_label.config(text="🪐 Unknown planet detected. Water status uncertain.")
        
        self.root.update_idletasks()  # Force UI refresh

    def fetch_nearby_station(self):
        """Fetches a nearby station and updates the display immediately."""
        try:
            station = subprocess.check_output(["python3", NAME_GEN_PATH, "--station"], text=True).strip()
            self.station_label.config(text=f"🏠 {station} offers expert plumbing repairs for your space toilet!")
        except Exception:
            self.station_label.config(text="🏠 No plumbing stations nearby. Proceed with caution!")
        
        self.root.update_idletasks()  # Force UI refresh

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
            self.update_data()  # Refresh the dashboard
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
            self.update_data()  # Refresh the dashboard
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

    def clear_database(self):
        """Sends a request to WaterLog API to clear all stored events."""
        response = requests.post("http://127.0.0.1:5001/clear")
        
        if response.status_code == 200:
            print("✅ Database successfully cleared.")
            self.update_data()  # Refresh the UI after clearing
        else:
            print("❌ Failed to clear database. Response:", response.text)

    def full_refill_and_balance(self):
        """Performs a full refill and balances the water-to-flush ratio."""
        try:
            flushes = sum(1 for e in requests.get(WATERLOG_API).json() if e["event_type"] == "flush")
            optimal_refills = flushes / 1.5  # Assuming optimal ratio is 1.5
            current_refills = sum(1 for e in requests.get(WATERLOG_API).json() if e["event_type"] == "water_refill")
            additional_refills_needed = max(0, optimal_refills - current_refills)

            for _ in range(int(additional_refills_needed)):
                self.send_water_refill()

            print("✅ Full refill and balance completed.")
        except Exception as e:
            print("❌ Error during full refill and balance:", e)

if __name__ == "__main__":
    root = tk.Tk()
    app = ViewPortApp(root)
    root.mainloop()


