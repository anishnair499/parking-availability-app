import requests
import time

ESP32_IP = "192.168.1.42"  
URL = f"http://{ESP32_IP}/distance"

def main():
    print("Reading distances... Ctrl+C to stop.")
    try:
        while True:
            try:
                resp = requests.get(URL, timeout=2)
                text = resp.text.strip()
                print(f"Distance: {float(text):.2f} cm")
            except requests.exceptions.RequestException as e:
                print(f"Connection error: {e}")
            time.sleep(60)  # ~5 readings/sec, adjust as needed
    except KeyboardInterrupt:
        print("\nStopped.")\



