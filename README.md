# Okami PS3 Auto Splitter  
An **auto splitter** for *Okami* on RPCS3, using **LiveSplit** for timing.

---

## What it does
This tool automatically detects **zone changes** in Okami (PS3 version running in RPCS3) and sends **split commands** to LiveSplit.  
No manual key presses needed — the autosplitter takes care of it for you.

---

## Requirements
Before running the program, make sure you have:

- **LiveSplit** installed with your splits set up  
- **LiveSplit TCP Server enabled**  
  > Right-click LiveSplit → *Control* → *Start TCP Server*  
- **RPCS3** running  
- **Okami (PS3 version)** launched inside RPCS3  

---

## Configuration
Splits are triggered by **zone changes** defined in `zone_changes.json`.  
You can edit this file to customize which zones should create a split.  

---

## Usage
1. Start **LiveSplit** and enable the TCP server  
2. Launch **RPCS3** and run Okami  
3. Run this autosplitter (`okami_autosplit.py`)  
4. Play the game — splits will happen automatically

---

## Support
If you encounter issues, feel free to open an **Issue** on GitHub or contact me directly. 