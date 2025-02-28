# 🚀 W.E.T. System: Space Toilet Water Extraction Tracker 🚽

A simulated **space toilet monitoring system** that tracks astronaut waste extraction for water recovery.  
This project integrates multiple microservices to monitor, log, and visualize astronaut waste management.

---

## 📌 Features

### 🛰 Real-Time Monitoring (LiveTrack - ZeroMQ)
- Listens for astronaut activity events from the **Simulator**.
- Sends collected data to **WaterLog** for storage.
- Publishes real-time updates to **ViewPort** for visualization.

### 💾 Data Logging (WaterLog - SQLite & Flask)
- Stores astronaut activity (flushes, water refills, planet visits) in an SQLite database.
- Provides historical logs via a REST API for **ViewPort** and other services.
- Ensures data integrity and allows analysis of water recycling efficiency.

### 🖥 Interactive GUI (ViewPort - Tkinter & Matplotlib)
- Displays **real-time astronaut activity logs** in a user-friendly interface.
- Provides **animated toilet visuals** when a flush event occurs.
- Shows **live charts** for waste volume, water levels, and astronaut usage trends.
- Fetches **motivational quotes**, **planet names**, and **station names** for immersive experience.

### 🚀 Astronaut Activity Simulator
- Generates **random astronaut events**: flushes, water refills, and planet visits.
- Uses **ZeroMQ** to publish events to **LiveTrack** for processing.
- Allows **manual event triggering** from the **ViewPort** dashboard.

---

## 📂 Project Structure

```
wet_system/
│── data/                # store water log db as water_log.db but is part of gitignore so your local db will differ
│── gui/                # Images & assets (toilet.png, spacepoop.png)
│── microservices/
│   ├── LiveTrack/      # ZeroMQ Listener
│   ├── Simulator/      # Generates astronaut activity
│   ├── ViewPort/       # GUI dashboard 
│   ├── WaterLog/       # Flask API & SQLite Database
│── main_program.py     # Starts all microservices
│── requirements.txt    # Dependencies
│── README.md           # Documentation
```

---

## 🛠 Installation

To set up and run the system, follow these steps:

1️⃣ Clone the repository:

```
git clone https://github.com/jphamgithub/wet_system.git
cd wet_system
```

2️⃣ Install dependencies:

```
pip install -r requirements.txt
```

3️⃣ Run the system:

```
python3 main_program.py
```

This will launch all microservices, including:
- **WaterLog** (database & API)
- **LiveTrack** (event listener)
- **Simulator** (random astronaut activity)
- **ViewPort** (dashboard & controls)

---

## 🎯 How It Works

1. The **Simulator** generates astronaut events (e.g., a flush event).
2. **LiveTrack** receives the event and logs it into **WaterLog**.
3. The **ViewPort** GUI fetches event history and updates its display.
4. Users can manually **flush** or **refill water** from **ViewPort**.
5. If water levels get low, a **planet recommendation** may be triggered.

---

## 🔄 Microservice Communication Flow

```
[Simulator] ---> (ZeroMQ PUB) ---> [LiveTrack] ---> (HTTP POST) ---> [WaterLog (SQLite)]
                           |
                           v
                     [ViewPort GUI]
```

- **Simulator** publishes events over **ZeroMQ**.
- **LiveTrack** listens for events and forwards them to **WaterLog**.
- **ViewPort** requests event history and updates the user interface.

---

## 🏗 Future Enhancements
- 🌌 **Interplanetary Water Management**: Connect with external services to monitor **off-world** water sources provided by alien microservices.
