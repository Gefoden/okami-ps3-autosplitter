# Okami Auto Splitter

An **auto splitter** for *Okami*, using **LiveSplit** for timing.  
Supports both the **PC/Steam** version and the **PS3 (via RPCS3)** version.

---

## Features

- Automatically detects **zone changes**, **fights**, and more in *Okami*.  
- Sends **split commands** to LiveSplit — no manual key presses required.  
- Works for both PC/Steam and PS3/RPCS3 versions.  

---

## Requirements

Before running, ensure you have:

- **LiveSplit** installed and your splits set up  
  > Example LiveSplit files (`.lss`) are included in the **livesplit/** folder.
- A configured **settings.json** (see [Configuration](#configuration)).  
- The **LiveSplit TCP Server** running  
  > Right-click LiveSplit → *Control* → *Start TCP Server*  
- **Okami** launched (PC/Steam or PS3/RPCS3)

---

## Configuration

Splits are defined in JSON files inside the **splits/** folder (e.g. `splits/your_split_file.json`).  
You can maintain multiple files for different categories or routes. Have a look at *splits_example.json* to see what is possible.

To configure:

1. In `settings.json`, set the `splits_file` property to your chosen file, e.g.:
```json
   "splits_file": "any_percent.json"   
```
2. Set the `game_version` property to either:
-   `"pc"` for the Steam version
-   `"ps3"` for the RPCS3 version
3. If you want to record the values to help you create a splits file, set the `mode` property to `"record"`.
  > It will create a record file for each run in a *records/* folder

---

## Usage

1.  Start **LiveSplit** and enable the TCP server
    > Right-click LiveSplit → _Control_ → _Start TCP Server_
2.  Launch _Okami_.
3.  Download the latest release from the [Releases page](../../releases).
4.  Extract the release files into an empty folder.
5.  Place your `settings.json` in the same folder as `okami_autosplitter.exe` and configure it properly. 
6.  Run `okami_autosplitter.exe`.
8.  Play — splits will happen automatically. 🎉

---

## Support

If you run into issues or have suggestions:
-   Open an **Issue** here on GitHub
-   Or contact me directly