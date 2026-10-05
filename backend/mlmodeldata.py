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
ESP32_IP = "192.168.1.42" # NOT the actual IP
URL = f"http://{ESP32_IP}/distance"

def main():
    print("Reading distances... Ctrl+C to stop.")
    try:
        while True:
            try:
                resp = requests.get(URL, timeout=2)
                text = resp.text.strip()
                print(f"Distance: {float(text):.2f} cm")
                dist = f"{float(text):.2f}"
                availability = False
                if dist <= 100:
                    availability = True
                else:
                    pass
                db.collection("parkingLots").document("lot1").collection("spots").document("A1").collection("current").document("status").update({
    "available": availability,
    "updatedAt": SERVER_TIMESTAMP
})
            except requests.exceptions.RequestException as e:
                print(f"Connection error: {e}")
                db.collection("parkingLots").document("lot1").collection("spots").document("A1").collection("obervations").add({
                                    "available": availability,
                                    "updatedAt": SERVER_TIMESTAMP })
            time.sleep(60)  # ~1 readings/min, adjust as needed
    except KeyboardInterrupt:
        print("\nStopped.")




if __name__ == "__main__":
    main()