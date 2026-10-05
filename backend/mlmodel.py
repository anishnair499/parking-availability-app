import firebase_admin
from firebase_admin import credentials, firestore
import csv

cred = credentials.Certificate("C:/Users/aites/Downloads/parking-project-30a86-firebase-adminsdk-fbsvc-1fd81ffcc8.json")
firebase_admin.initialize_app(cred)


# Initialize your client
db = firestore.client()

# 1. Reference the collection
users_ref = db.collection("parkingLots").document("lot1").collection("spots").document("A1").collection("obervations")

# 2. Use .stream() to fetch and loop through documents efficiently
docs = users_ref.stream()

for doc in docs:
    # Get the unique document ID string
    doc_id = doc.id
    
    # Extract the document fields as a standard Python dictionary
    doc_data = doc.to_dict()
    
    print(f"--- Processing Document: {doc_id} ---")
    
    # 3. Accessing fields safely
    name = doc_data.get("updatedAt", "Unknown")
    print(f"Name: {name}")
    
    # 4. Converting a Firestore Timestamp field back to a Python datetime
    created_at_ts = doc_data.get("updatedAt")
    
    if created_at_ts:
        # Converts native Firestore Timestamp to python datetime
        print(f"Created At: {created_at_ts.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("Created At: No timestamp found")
