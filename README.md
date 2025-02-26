# 🚀 W.E.T. System: Space Toilet Water Extraction Tracker 🚽

This project simulates a **space toilet monitoring system**, tracking astronaut waste extraction for water recovery.

## **📌 Features**
1. **Real-Time Monitoring (LiveTrack - ZeroMQ)**
   - Tracks **flushes, waste volume, energy use, filter health**  
   - Sends data to **WaterLog (SQLite & Flask API)**  
   - Publishes updates to **ViewPort GUI**

2. **Data Logging (WaterLog - SQLite & Flask)**
   - Stores **flush events & water extraction efficiency**  
   - Provides **historical data** for visualization  
   - Calls **planet recommendation service** if water is low

3. **Interactive GUI (ViewPort - Tkinter & Matplotlib)**
   - **Animated toilet movement** when flushed  
   - **Live charts** (waste levels, astronaut usage trends)  
   - **Water level alerts & recommendations**  

4. **Astronaut Activity Simulator**
   - Simulates **random astronaut flushes & maintenance water refills**

## **🚀 Installation**
```bash
pip install -r requirements.txt
```

## **🎯 Running the System**
```bash
python main_program.py
```

