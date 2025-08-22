import socket
import time
import struct
import json
import sys
import pymem
from pymem import Pymem
from datetime import datetime


# Constants
LIVESPLIT_HOST = '127.0.0.1'
LIVESPLIT_PORT = 16834
ADDRESSES = {
	"time": 0x300E6B0E8,
	"area_id": 0x300EA9908,
	"finish_screen": 0x336F8A4A4
}

BASE = 0x0
offset = None


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
	tutorial_printed = False
	while True:
		try:
			pm = Pymem("rpcs3.exe")
			print("✅ RPCS3 launched!")
			return pm
		except pymem.exception.ProcessNotFound:
			if not tutorial_printed:
				print("\n\n❌ RPCS3 is not started!\n\nWaiting for RPCS3 to be started...\n")
				tutorial_printed = True
			time.sleep(2)

def wait_for_game(pm):
	tutorial_printed = False

	while True:
		try:
			data = pm.read_bytes(ADDRESSES["time"], 4)
			print("✅ Okami launched!")
			time.sleep(3)
			break
		except pymem.exception.MemoryReadError:
			if not tutorial_printed:
				print("\n\n❌ Okami is not started!\n\nWaiting for Okami to be started...\n")
				tutorial_printed = True

def read_zone_changes():
	# Load zone changes
	with open("zone_changes.json", "r") as f:
		zone_changes = json.load(f)
	# Keep only enabled zone changes and initialize already_done
	zone_changes = [z for z in zone_changes if z["enabled"]]
	for z in zone_changes:
		z["already_done"] = False
	return zone_changes


def send_livesplit_command(sock, cmd):
	sock.sendall(f"{cmd}\n".encode())

def read_big_endian_int(pm, address):
	# Read 4 bytes from memory
	try:
		data = pm.read_bytes(address, 4)
	except pymem.exception.MemoryReadError:
		print("\n\n\n❌ THE GAME WAS CLOSED")
		sys.exit()
	# Convert from big-endian bytes to integer
	return struct.unpack(">I", data)[0]

def read_memory_old(pm):
	global ADDRESSES
	data = {}
	for key, address in ADDRESSES.items():
		data[key] = read_big_endian_int(pm, address)
	return data

def read_memory(pm):
	data = {}
	for key, guest_addr in ADDRESSES.items():
		data[key] = read_big_endian_int(pm, guest_addr)
	return data

def should_start(current, old):
	# print(f"{current['area_id']} {current['time']}   {old['time']}")
	return current["area_id"] == 4294967295 and current["time"] < old["time"]

def should_reset(current, old):
	return current["area_id"] == 4294967295 and old["area_id"] != current["area_id"]

def should_split(zone_changes, current, old, run_ended):
	# Zone changes
	if old["area_id"] != current["area_id"]:
		return check_zone_change(zone_changes, current, old)
	# Finish screen
	if current["area_id"] == 62 and not run_ended and current["finish_screen"] == 4294967295:
		run_ended = True
		print(f"🎉 Run ended! {frames_to_time(current['time'])}")
		add_log(f">> Run ended! {frames_to_time(current['time'])}")
		return True
	return False

def check_zone_change(zone_changes, current, old):
	for zone_change in zone_changes:
		if (old["area_id"] == zone_change["old_area"] and current["area_id"] == zone_change["new_area"]):
			if not zone_change["already_done"]:
				zone_change["already_done"] = True
				print(f"🏃‍➡️ Zone changed! {zone_change['description']}")
				add_log(f"Zone changed! {zone_change['old_area']} -> {zone_change['new_area']}")
				return True
			else:
				add_log(f">> Zone change already done! {zone_change['old_area']} -> {zone_change['new_area']}")

	# print(f">> Unknown zone change! {zone_change['old_area']} -> {zone_change['new_area']}")
	add_log(f">> Unknown zone change! {zone_change['old_area']} -> {zone_change['new_area']}")
	return False

def reset_zone_changes(zone_changes):
	for z in zone_changes:
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



# Main loop
def main_loop(sock, pm, zone_changes):
	run_ended = False
	old_values = None

	while True:

		current_values = read_memory(pm)

		if old_values != None:

			if should_start(current_values, old_values):
				send_livesplit_command(sock, "start")
				print("\n\n⏯ New run started!")
				add_log("\n\n>>> New run started!")

			if should_reset(current_values, old_values):
				send_livesplit_command(sock, "reset")
				reset_zone_changes(zone_changes)
				run_ended = False
				print("\n🔁 Run reset!")
				add_log("\n> Run reset!")

			if should_split(zone_changes, current_values, old_values, run_ended):
				send_livesplit_command(sock, "split")
		
		time.sleep(0.033)  # roughly 30fps
		old_values = current_values


def main():
	print("\n╔═══════════════════════════════╗\n║ Auto Splitter for Okami RPCS3 ║\n╚═══════════════════════════════╝\n\n")
	zone_changes = read_zone_changes()
	sock = connect_to_livesplit()
	pm = wait_for_emulator()
	wait_for_game(pm)
	print("\n\n✅✅✅ Everything is good! Auto Splitter is now running...")
	main_loop(sock, pm, zone_changes)


if __name__ == "__main__":
	main()