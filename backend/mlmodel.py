import firebase_admin
from firebase_admin import credentials, firestore
import csv
import pandas as pd
import random
import numpy as np
from datetime import datetime, timedelta
import os, json
from dotenv import load_dotenv

load_dotenv()

service_account_info = json.loads(os.environ["FIREBASE_KEY_JSON"])
cred = credentials.Certificate(service_account_info)
firebase_admin.initialize_app(cred)

rng = np.random.default_rng()



db = firestore.client()

users_ref = db.collection("parkingLots").document("lot1").collection("spots").document("A1").collection("obervations")

oldest_first_query = users_ref.order_by(
    "updatedAt", 
    direction=firestore.Query.ASCENDING
)

docs = oldest_first_query.stream()
t = 0
i = 0
headers = ['timestamp', 'spot_1','spot_2']
rows = []
for doc in docs:
    doc_id = doc.id
    
    doc_data = doc.to_dict()
    
    print(f"--- Processing Document: {doc_id} ---")
    
    name = doc_data.get("updatedAt", "Unknown")
    print(f"Name: {name}")
    
    created_at_ts = doc_data.get("updatedAt")
    availability_at_ts = doc_data.get("available")
    
    if created_at_ts:
        print(f"Updated At: {created_at_ts.strftime('%Y-%m-%d %H:%M:%S')}")

    else:
        print("Updated At: No timestamp found")
    if str(availability_at_ts):
        print(f"Availbility: {availability_at_ts}")
            
        i+=1
    else:
        print("Availability status couldn't be determined.")
        t+=1
    rows.append({"timestamp":created_at_ts, "spot_1":int(availability_at_ts), "spot_2":random.randint(0,1)})
print(t)
print(i)
print(type(created_at_ts))

for i in range(30240):
    created_at_ts += timedelta(minutes=1)
    val = rng.normal(loc=0.0, scale=1.0)
    val1 = rng.normal(loc=0.0, scale=1.0)
    zero_or_one = 1 if val > 0 else 0
    zero_or_one1 = 1 if val1 > 0 else 0
    rows.append({"timestamp": created_at_ts, "spot_1":zero_or_one, "spot_2":zero_or_one1})

with open('availability.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=headers)
    
    writer.writeheader()
    
    writer.writerows(rows)

df = pd.read_csv('availability.csv')

with pd.option_context('display.max_rows', None, 'display.max_columns', None):
    print(df)
