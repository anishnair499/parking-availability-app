import json

with open(r"C:\Users\aites\Downloads\parking-project-30a86-firebase-adminsdk-fbsvc-1fd81ffcc8.json") as f:
    data = json.load(f)

with open(".env", "w", encoding="utf-8") as f:
    f.write("FIREBASE_KEY_JSON='" + json.dumps(data) + "'\n")