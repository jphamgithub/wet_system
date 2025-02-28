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
from datetime import datetime, timedelta
from matplotlib.ticker import FuncFormatter

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
        self.full_refill_button = tk.Button(button_frame, text="🌍 Massive Water Refill", command=self.full_refill_and_balance)
        self.full_refill_button.grid(row=4, column=1, padx=5, pady=2, sticky='ew')
        self.full_refill_button.config(**button_style)

        # Add a new button for simulating massive waste flush
        self.massive_flush_button = tk.Button(button_frame, text="🚽 Massive Waste Event", command=self.simulate_massive_flush)
        self.massive_flush_button.grid(row=4, column=0, padx=5, pady=2, sticky='ew')
        self.massive_flush_button.config(**button_style)

        # Add a button to open the astronaut-specific guide file
        self.astronaut_readme_button = tk.Button(button_frame, text="📘 Astronaut Guide", command=self.open_astronaut_readme)
        self.astronaut_readme_button.grid(row=11, column=0, columnspan=2, padx=5, pady=2, sticky='ew')
        self.astronaut_readme_button.config(**button_style)

        # Add a button to open the picture book explanation
        self.picture_book_button = tk.Button(button_frame, text="📖 Picture Book Explanation", command=self.open_picture_book)
        self.picture_book_button.grid(row=12, column=0, columnspan=2, padx=5, pady=2, sticky='ew')
        self.picture_book_button.config(**button_style)

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

        # Automatically send 5 flush events to populate the chart
        for _ in range(5):
            self.send_flush_event()

        # Pack the image label at the top
        self.img_label.pack(side="top", expand=False, fill='both', pady=10)

        # Simulate pressing the left arrow key on the horizontal scrollbar four times
        for _ in range(4):
            self.canvas.xview_scroll(-1, 'units')

    def update_data(self):
        """Fetches and updates event data, charts, and motivational quote."""
        self.fetch_event_history()
        self.fetch_motivational_quote()
        self.fetch_nearby_planet()
        self.fetch_nearby_station()
        self.update_chart()

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
        """Starts the simulator process and schedules dashboard updates."""
        print("✅ Starting Simulator...")
        global simulator_process
        simulator_process = subprocess.Popen(
            ["python3", "./microservices/Simulator/simulator.py"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        self.simulator_status.set("⏸ Pause Simulator")
        print("🚀 Simulator Running.")
        self.schedule_dashboard_updates()  # Start updating the dashboard

    def schedule_dashboard_updates(self):
        """Schedules regular updates for the dashboard when the simulator is running."""
        if simulator_process:
            self.update_data()
            # Schedule the next update in 5 seconds
            self.root.after(5000, self.schedule_dashboard_updates)

    def clear_database(self):
        """Sends a request to WaterLog API to clear all stored events."""
        response = requests.post("http://127.0.0.1:5001/clear")
        
        if response.status_code == 200:
            print("✅ Database successfully cleared.")
            self.update_data()  # Refresh the UI after clearing
        else:
            print("❌ Failed to clear database. Response:", response.text)

    def full_refill_and_balance(self):
        """Simulates a full refill by sending multiple water refill events with recent timestamps."""
        try:
            # Simulate 50 water refill events
            for i in range(50):
                event_data = {
                    "event_type": "water_refill",
                    "water_added": 20,  # Example value
                    "timestamp": time.time() - i * 60  # Each event 1 minute apart
                }
                response = requests.post(LIVE_TRACK_API, json=event_data)
                if response.status_code != 201:
                    print(f"❌ Failed to log water refill event. Response: {response.text}")
                    break
            print("✅ Full refill simulated successfully.")
            self.update_data()  # Refresh the dashboard
        except Exception as e:
            print(f"❌ Error simulating full refill: {e}")

    def update_chart(self):
        """Fetches event data and updates the line chart with trend insights."""
        try:
            response = requests.get(WATERLOG_API)
            events = response.json()

            if not events:
                print("⚠️ No event data available for chart.")
                return  # Avoid processing empty data

            # Filter events to only include those from the last 24 hours
            one_day_ago = datetime.now() - timedelta(days=1)
            recent_events = [event for event in events if datetime.fromtimestamp(event['timestamp']) >= one_day_ago]

            event_counts = {"Flushes": 0, "Water Refills": 0}
            ratios = []
            ratio_times = []
            flush_count = 0
            refill_count = 0

            for event in recent_events:
                timestamp = datetime.fromtimestamp(event['timestamp'])
                
                if event['event_type'] == 'flush':
                    flush_count += 1
                    event_counts["Flushes"] += 1
                elif event['event_type'] == 'water_refill':
                    refill_count += 1
                    event_counts["Water Refills"] += 1

                if refill_count > 0:
                    ratios.append(flush_count / refill_count)
                    ratio_times.append(timestamp)

            # Clear existing chart
            for widget in self.chart_frame.winfo_children():
                widget.destroy()

            if not ratio_times or not ratios:
                print("⚠️ No valid ratio data for chart. Skipping plot.")
                return  # Avoid plotting empty charts

            # Create ratio line chart
            fig, ax = plt.subplots(figsize=(6, 3))
            ax.plot(ratio_times, ratios, 'm-', label='Flush-to-Refill Ratio')
            ax.set_title('Flush-to-Refill Ratio Over Time')
            ax.set_ylabel('Ratio')
            ax.legend()

            # Hide x-axis labels
            ax.xaxis.set_ticklabels([])

            # Embed the chart
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack()

            # Add total counts and ratio below the chart
            flush_total_label = tk.Label(self.chart_frame, text=f'Total Flushes: {event_counts["Flushes"]}', font=("Arial", 10))
            flush_total_label.pack()
            refill_total_label = tk.Label(self.chart_frame, text=f'Total Water Refills: {event_counts["Water Refills"]}', font=("Arial", 10))
            refill_total_label.pack()

            # Calculate and display the flush-to-refill ratio
            if refill_count > 0:
                ratio = flush_count / refill_count
                ratio_label = tk.Label(self.chart_frame, text=f'Flush-to-Refill Ratio: {ratio:.2f}', font=("Arial", 10, "bold"))
                ratio_label.pack()

                # Add warning brackets based on ratio
                if ratio > 2.0:
                    warning_label = tk.Label(self.chart_frame, text='⚠️ High Flush-to-Refill Ratio! Consider refilling.', font=("Arial", 10, "bold"), fg='red')
                    warning_label.pack()
                elif ratio > 0.5 and ratio < 2.0:
                    warning_label = tk.Label(self.chart_frame, text='You flush and fill at a good rate!', font=("Arial", 10, "bold"), fg='green')
                    warning_label.pack()
                elif ratio < 0.5:
                    warning_label = tk.Label(self.chart_frame, text='⚠️ Low Flush-to-Refill Ratio! Consider flushing.', font=("Arial", 10, "bold"), fg='orange')
                    warning_label.pack()

        except Exception as e:
            print(f"❌ Error updating chart: {e}")

    def simulate_massive_flush(self):
        """Simulates a massive waste flush by sending multiple flush events with recent timestamps."""
        try:
            for i in range(50):  # Simulate 50 flush events
                event_data = {
                    "event_type": "flush",
                    "waste_volume": 3,
                    "timestamp": time.time() - i * 60  # Each event 1 minute apart
                }
                response = requests.post(LIVE_TRACK_API, json=event_data)
                if response.status_code != 201:
                    print(f"❌ Failed to log flush event. Response: {response.text}")
                    break
            print("✅ Massive waste flush simulated successfully.")
            self.update_data()  # Refresh the dashboard
        except Exception as e:
            print(f"❌ Error simulating massive waste flush: {e}")

    def open_astronaut_readme(self):
        """Opens the astronaut-specific guide file in a new Tkinter window."""
        readme_path = os.path.join(BASE_DIR, 'microservices', 'ViewPort', 'Astronaut_Guide.txt')
        if os.path.exists(readme_path):
            with open(readme_path, 'r') as file:
                content = file.read()

            # Create a new window
            guide_window = tk.Toplevel(self.root)
            guide_window.title("Astronaut Guide")
            guide_window.geometry("600x400")

            # Add a text widget to display the content
            text_widget = tk.Text(guide_window, wrap='word')
            text_widget.insert('1.0', content)
            text_widget.config(state='disabled')  # Make the text widget read-only
            text_widget.pack(expand=True, fill='both')
        else:
            print("❌ Astronaut Guide file not found.")

    def open_picture_book(self):
        """Opens the manualphoto.png image in a new Tkinter window."""
        image_path = os.path.join(BASE_DIR, 'gui', 'manualphoto.png')
        if os.path.exists(image_path):
            # Create a new window
            image_window = tk.Toplevel(self.root)
            image_window.title("Picture Book Explanation")

            # Load and display the image
            img = Image.open(image_path)
            img = ImageTk.PhotoImage(img)
            img_label = tk.Label(image_window, image=img)
            img_label.image = img  # Keep a reference to avoid garbage collection
            img_label.pack(expand=True, fill='both')
        else:
            print("❌ Manual photo not found.")


if __name__ == "__main__":
    root = tk.Tk()
    app = ViewPortApp(root)
    root.mainloop()


