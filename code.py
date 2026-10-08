
import paho.mqtt.client as mqtt
import sys
import tty
import termios
import time
import json
from pathlib import Path

# ==========================================
# MQTT SETTINGS
# ==========================================

MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "greenhouse/button"

# ==========================================
# COUNT SETTINGS
# ==========================================

COUNT_FILE = Path.home() / "keyboard_count.txt"

try:
    count = int(COUNT_FILE.read_text())
    count = max(0, count)
except (FileNotFoundError, ValueError):
    count = 0

# ==========================================
# MQTT CLIENT
# ==========================================

client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2
)

# ==========================================
# CONNECT TO MQTT BROKER
# ==========================================

try:
    client.connect(
        MQTT_BROKER,
        MQTT_PORT,
        60
    )

    client.loop_start()

    print("MQTT connection started!")

except Exception as e:
    print("MQTT connection failed!")
    print("Error:", e)
    sys.exit(1)

# ==========================================
# GET KEYBOARD INPUT
# ==========================================

def get_key():

    fd = sys.stdin.fileno()

    old_settings = termios.tcgetattr(fd)

    try:
        tty.setraw(fd)
        key = sys.stdin.read(1)

    finally:
        termios.tcsetattr(
            fd,
            termios.TCSADRAIN,
            old_settings
        )

    return key

# ==========================================
# SEND MQTT MESSAGE
# ==========================================

def publish_count(button, status):

    payload = {
        "button": button,
        "status": status,
        "count": count,
        "timestamp": time.time()
    }

    message = json.dumps(payload)

    try:
        result = client.publish(
            MQTT_TOPIC,
            message,
            qos=1
        )

        result.wait_for_publish(timeout=3)

        print("\n--------------------------")
        print("Button:", button)
        print("Status:", status)
        print("TOTAL COUNT:", count)

        if result.is_published():
            print("MQTT SENT:", message)
        else:
            print("MQTT delivery not confirmed")

        print("--------------------------")

    except Exception as e:
        print("MQTT publish error:", e)

# ==========================================
# SAVE COUNT
# ==========================================

def save_count():

    COUNT_FILE.write_text(str(count))

# ==========================================
# PROGRAM INFORMATION
# ==========================================

print("==============================")
print(" Raspberry Pi 5 MQTT Counter")
print("==============================")
print("SPACE = COUNT UP (+1)")
print("ENTER = COUNT DOWN (-1)")
print("ESC   = Quit")
print("==============================")
print("Current Count:", count)
print("==============================")

# ==========================================
# MAIN PROGRAM
# ==========================================

try:

    while True:

        key = get_key()

        # ----------------------------------
        # SPACE = COUNT UP
        # ----------------------------------

        if key == " ":

            count += 1

            save_count()

            publish_count(
                "SPACE",
                "ON"
            )

        # ----------------------------------
        # ENTER = COUNT DOWN
        # ----------------------------------

        elif key == "\r" or key == "\n":

            if count > 0:
                count -= 1

            save_count()

            publish_count(
                "ENTER",
                "OFF"
            )

        # ----------------------------------
        # ESC = QUIT
        # ----------------------------------

        elif key == "\x1b":

            print("\nStopping...")
            break

# ==========================================
# CLEAN UP
# ==========================================

except KeyboardInterrupt:

    print("\nProgram interrupted.")

finally:

    client.loop_stop()
    client.disconnect()

    print("MQTT disconnected.")
    print("Final Count:", count)
