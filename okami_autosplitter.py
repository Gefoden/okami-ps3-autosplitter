import socket
import time
import struct
import json
import sys
import os
import pymem
from pymem import Pymem
from datetime import datetime


# Constants
GAME_VERSION = ""
ADDRESSES = {}
BASE_ADDRESS = 0x0
PY_MEMORY = None
LIVESPLIT_HOST = ""
LIVESPLIT_PORT = 16834
MAX_VALUE = 4294967295
START_ZONE = 4294967295
SPLITTER_MODE = ""
SPLITS_FILE = ""
AREA_IDS = {}
RECORD_FILE = "record_unkown_date.txt"


# Functions
def connect_to_livesplit():
	tutorial_printed = False
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	while True:
		try:
			sock.connect((LIVESPLIT_HOST, LIVESPLIT_PORT))
			print("✅ Connected to LiveSplit!")
			return sock
		except ConnectionRefusedError:
			if not tutorial_printed:
				print("\n\n❌ The LiveSplit TCP server is not started!\nTo start it, launch LiveSplit, Right click > Control > Start TCP Server\n\nWaiting for LiveSplit TCP server to be started...\n")
				tutorial_printed = True
			time.sleep(2)

def wait_for_emulator():
	global PY_MEMORY, BASE_ADDRESS
	tutorial_printed = False
	while True:
		try:
			PY_MEMORY = Pymem("rpcs3.exe")
			BASE_ADDRESS = hex_string_to_int(ADDRESSES["base"])
			print("✅ RPCS3 launched!")
			break
		except pymem.exception.ProcessNotFound:
			if not tutorial_printed:
				print("\n\n❌ RPCS3 is not started!\n\nWaiting for RPCS3 to be started...\n")
				tutorial_printed = True
			time.sleep(2)

def wait_for_emulated_game():
	tutorial_printed = False

	while True:
		try:
			data = PY_MEMORY.read_bytes(BASE_ADDRESS + hex_string_to_int(ADDRESSES["time"]), 4)
			print("✅ Okami launched!")
			time.sleep(5)
			break
		except pymem.exception.MemoryReadError:
			if not tutorial_printed:
				print("\n\n❌ Okami is not started!\n\nWaiting for Okami to be started...\n")
				tutorial_printed = True
			time.sleep(2)

def wait_for_pc_game():
	global PY_MEMORY, BASE_ADDRESS
	tutorial_printed = False
	while True:
		try:
			PY_MEMORY = Pymem("okami.exe")
			time.sleep(1)
			BASE_ADDRESS = pymem.process.module_from_name(PY_MEMORY.process_handle, "main.dll").lpBaseOfDll
			print("✅ Okami launched!")
			time.sleep(5)
			break
		except pymem.exception.ProcessNotFound:
			if not tutorial_printed:
				print("\n\n❌ Okami is not started!\n\nWaiting for Okami to be started...\n")
				tutorial_printed = True
			time.sleep(2)


def get_setting(key, filename="settings.json", default=None):
	if not os.path.exists(filename):
		return default
	try:
		with open(filename, "r") as f:
			settings = json.load(f)
	except (json.JSONDecodeError, OSError):
		return default
	return settings.get(key, default)


def read_settings():
	global GAME_VERSION, LIVESPLIT_HOST, LIVESPLIT_PORT, ADDRESSES, MAX_VALUE, START_ZONE, AREA_IDS, SPLITTER_MODE, SPLITS_FILE
	try:
		with open("settings.json", "r") as f:
			settings = json.load(f)
		with open("area_ids.json", "r") as f:
			area_ids = json.load(f)

		GAME_VERSION = settings.get("game_version").lower()
		LIVESPLIT_HOST = settings.get("livesplit_host")
		LIVESPLIT_PORT = settings.get("livesplit_port")
		ADDRESSES = settings.get("addresses")[GAME_VERSION]
		AREA_IDS = area_ids
		SPLITTER_MODE = settings.get("mode")
		SPLITS_FILE = settings.get("splits_file")
		print(f"Game version: {GAME_VERSION}")

		if GAME_VERSION == "pc":
			MAX_VALUE = 65535
			START_ZONE = 29
		elif GAME_VERSION == "ps3":
			MAX_VALUE = 4294967295
			START_ZONE = 4294967295
		AREA_IDS[f"{MAX_VALUE}"] = "Main Menu"

	except (json.JSONDecodeError, OSError):
		print("❌ Wrong settings.json!")


def read_splits():
	with open(f'splits/{SPLITS_FILE}', "r") as f:
		splits = json.load(f)
	print(f"Splits file:  splits/{SPLITS_FILE}")
	splits = [z for z in splits if z["enabled"]]
	for z in splits:
		z["already_done"] = False
	return splits

def send_livesplit_command(sock, cmd):
	sock.sendall(f"{cmd}\n".encode())

def read_4_bytes_big_endian(pm, address, base, close_if_unavailable):
	# Read 4 bytes from memory
	try:
		data = pm.read_bytes(base + address, 4)
	except pymem.exception.MemoryReadError:
		if close_if_unavailable:
			print("\n\n\n❌ THE GAME WAS CLOSED")
		else:
			return None
		sys.exit()
	# Convert from big-endian bytes to integer
	return struct.unpack(">I", data)[0]

def read_2_bytes(pm, address, base):
    try:
        data = pm.read_bytes(base + address, 2)
    except pymem.exception.MemoryReadError:
        print("\n\n\n❌ THE GAME WAS CLOSED")
        sys.exit()
    return struct.unpack("<H", data)[0]


def hex_string_to_int(hex_str):
	return int(hex_str, 16)

def read_memory():
	data = {}
	if GAME_VERSION == "ps3":
		for key, guest_addr in ADDRESSES.items():
			if key != "base":
				data[key] = read_4_bytes_big_endian(PY_MEMORY, hex_string_to_int(guest_addr), BASE_ADDRESS, key in ["time", "area_id"])
	elif GAME_VERSION == "pc":
		for key, guest_addr in ADDRESSES.items():
			if key != "base":
				data[key] = read_2_bytes(PY_MEMORY, hex_string_to_int(guest_addr), BASE_ADDRESS)
	return data

def should_start(current, old):
	# print(f"{current['area_id']} {current['time']}   {old['time']}")
	return (current["area_id"] == START_ZONE or current["area_id"] == MAX_VALUE) and current["time"] < old["time"]

def should_reset(current, old):
	return current["area_id"] == MAX_VALUE and old["area_id"] != current["area_id"]

def should_split(splits, current, old, run_ended):
	# Area changes
	if old["area_id"] != current["area_id"]:
		return check_area_change(splits, current, old)
	# Fight done
	if old["fight_money"] == 0 and current["fight_money"] > 0:
		return check_fights(splits, current, old)
	# Finish screen
	if current["area_id"] == 62 and not run_ended and current["finish_screen"] == MAX_VALUE:
		run_ended = True
		print(f"🎉 Run ended! {frames_to_time(current['time'])}")
		add_log(f">> Run ended! {frames_to_time(current['time'])}")
		return True
	return False

def check_fights(splits, current, old):
	for split in splits:
		if split["split_type"] == "fight":
			if split["area"] == current["area_id"]:
				split["already_done"] = True
				print(f"🏃‍➡️ Fight ended! {split['description']}")
				add_log(f"Fight ended! {split['description']}")
				return True
	return False

def check_area_change(splits, current, old):
	for split in splits:
		if split["split_type"] == "area_change":
			if (old["area_id"] == split["old_area"] and current["area_id"] == split["new_area"]) and not split["already_done"]:
				split["already_done"] = True
				print(f"🏞️ Area changed! {split['description']}")
				add_log(f"Area changed! {split['old_area']} -> {split['new_area']}")
				return True

	old_area = old['area_id'] if str(old['area_id']) not in AREA_IDS.keys() else AREA_IDS[str(old['area_id'])]
	current_area = current['area_id'] if str(current['area_id']) not in AREA_IDS.keys() else AREA_IDS[str(current['area_id'])]
	print(f">> Area changed without split! {old_area} -> {current_area}")
	add_log(f">> Area changed without split! {old_area} -> {current_area}")
	return False

def reset_splits(splits):
	for z in splits:
		z["already_done"] = False

def frames_to_time(total_frames, fps=60):
	# Calculate total seconds and remaining frames
	total_seconds = total_frames // fps
	ms_frames = total_frames % fps

	# Extract hours, minutes, and seconds
	hours = total_seconds // 3600
	minutes = (total_seconds % 3600) // 60
	seconds = total_seconds % 60

	# Convert remaining frames to milliseconds
	milliseconds = int((ms_frames / fps) * 1000)

	# Format the time string
	return f"{hours:02d}h {minutes:02d}m {seconds:02d}s {milliseconds:03d}ms"

def add_log(text):
	timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	with open("log.txt", "a", encoding="utf-8") as f:
		f.write(f"[{timestamp}] {text}\n")


def create_record_folder():
	if not os.path.exists("records/"):
		os.makedirs("records")


def record(old_values, current_values):
	for key in current_values.keys():
		if key != "time" and current_values[key] != old_values[key]:
			with open(f"records/{RECORD_FILE}", "a+", encoding="utf-8") as f:
				if key == "area_id":
					old_area = old_values[key]
					current_area = current_values[key]
					old_value = AREA_IDS[str(old_area)] if str(old_area) in AREA_IDS.keys() else old_area
					current_value = AREA_IDS[str(current_area)] if str(current_area) in AREA_IDS.keys() else current_area
					f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {key}: {old_values[key]} -> {current_values[key]} ({old_value} -> {current_value})\n")
				else:
					f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {key}: {old_values[key]} -> {current_values[key]}\n")

# Main loop
def main_loop(sock, splits):
	global RECORD_FILE
	run_ended = False
	old_values = None

	if SPLITTER_MODE == "record":
		create_record_folder()

	while True:

		current_values = read_memory()

		if old_values != None:

			if should_start(current_values, old_values):
				send_livesplit_command(sock, "start")
				print("\n\n⏯  New run started!")
				add_log("\n\n>>> New run started!")
				RECORD_FILE = f'record_{datetime.now().strftime("%Y_%m_%d_%H_%M_%S")}.txt'

			if should_reset(current_values, old_values):
				send_livesplit_command(sock, "reset")
				reset_splits(splits)
				run_ended = False
				print("\n🔁 Run reset!\n")
				add_log("\n> Run reset!\n")

			if should_split(splits, current_values, old_values, run_ended):
				send_livesplit_command(sock, "split")

			if SPLITTER_MODE == "record":
				record(old_values, current_values)
		
		time.sleep(0.033)  # roughly 30fps
		old_values = current_values


def main():
	print("\n╔═════════════════════════╗\n║ Auto Splitter for Okami ║\n╚═════════════════════════╝\n\n")
	read_settings()
	splits = read_splits()
	sock = connect_to_livesplit()

	if(GAME_VERSION == "ps3"):
		wait_for_emulator()
		wait_for_emulated_game()
	elif(GAME_VERSION == "pc"):
		wait_for_pc_game()
	else:
		print("❌ Wrong game_version in settings, please put 'pc' or 'ps3'")
		add_log(f"Wrong game_version in settings, please put 'pc' or 'ps3', not {get_setting('game_version')}")


	print("\n\n✅✅✅ Everything is good! Auto Splitter is now running...\nKeep this window open.\n")
	main_loop(sock, splits)


if __name__ == "__main__":
	main()
