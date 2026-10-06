import firebase_admin
from firebase_admin import credentials, firestore
import csv
import pandas as pd

cred = credentials.Certificate("C:/Users/aites/Downloads/parking-project-30a86-firebase-adminsdk-fbsvc-1fd81ffcc8.json")
firebase_admin.initialize_app(cred)


# Initialize your client
db = firestore.client()

# 1. Reference the collection
users_ref = db.collection("parkingLots").document("lot1").collection("spots").document("A1").collection("obervations")

oldest_first_query = users_ref.order_by(
    "updatedAt", 
    direction=firestore.Query.ASCENDING
)

# 2. Use .stream() to fetch and loop through documents efficiently
docs = oldest_first_query.stream()
t = 0
i = 0
headers = ['Time', 'Spot_A1']
rows = []
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
    availability_at_ts = doc_data.get("available")
    
    if created_at_ts:
        # Converts native Firestore Timestamp to python datetime
        print(f"Updated At: {created_at_ts.strftime('%Y-%m-%d %H:%M:%S')}")

    else:
        print("Updated At: No timestamp found")
    if str(availability_at_ts):
        # Converts native Firestore Timestamp to python datetime
        print(f"Availbility: {availability_at_ts}")
            
        i+=1
    else:
        print("Availability status couldn't be determined.")
        t+=1
    rows.append({"Time":created_at_ts, "Spot_A1":int(availability_at_ts)})
print(t)
print(i)

with open('availability.csv', 'w', newline='', encoding='utf-8') as csvfile:
    # Create the writer object and pass the column names
    writer = csv.DictWriter(csvfile, fieldnames=headers)
    
    # Write the column names first
    writer.writeheader()
    
    # Write all the data rows
    writer.writerows(rows)

# Load the CSV file into a DataFrame
df = pd.read_csv('availability.csv')

# View the first 5 rows
with pd.option_context('display.max_rows', None, 'display.max_columns', None):
    print(df)
