import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud.firestore_v1 import SERVER_TIMESTAMP
import time
import csv
import requests
import time

cred = credentials.Certificate("C:/Users/aites/Downloads/privkey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()
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
        print("\nStopped.")



db.collection("parkingLots").document("lot1").collection("spots").document("A1").collection("current").document("status").update({
    "available": False,
    "updatedAt": SERVER_TIMESTAMP
})


if __name__ == "__main__":
    main()