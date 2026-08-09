# Firebase/Firestore setup for the parking sensor pipeline

Temporary doc for Ayaan — safe to delete once he's through it, doesn't need to stay in the repo long-term.

## 0. What Firestore actually is, in one paragraph

Firestore is a hosted database. You don't run a server for it — you write "documents" (basically JSON objects) into "collections" (basically folders of documents), either from your device code or from a script, and Google hosts it. For this project it's just going to hold parking sensor readings until a Python script pulls them out and turns them into a CSV.

---

## 1. Create the Firebase project

1. Go to https://console.firebase.google.com
2. Click **Add project**, name it something like `parking-availability` (any name is fine, it doesn't have to match the repo).
3. You can decline Google Analytics — not needed for this.
4. Once it's created, you land on the project dashboard. That's it, project exists.

## 2. Turn on Firestore

1. In the left sidebar: **Build → Firestore Database**.
2. Click **Create database**.
3. Choose **Start in production mode** (not test mode — test mode leaves it wide open with a 30-day expiry, and we're going to set proper rules in a minute anyway).
4. Pick a location close to you (e.g. `us-east1`). This can't be changed later, but it doesn't matter much for this project's scale.
5. Click **Enable**. You now have an empty database — you'll see a table-ish UI with no collections yet.

## 3. Decide the data shape (do this before writing any code)

One board is polling 5 parking spot sensors. The simplest and most reliable thing to write is **one document per poll cycle, containing all 5 spots at once** — not 5 separate documents. This matters: the ML side resamples data into 5-minute buckets, and if the 5 spots ever land in different documents at slightly different times, buckets can end up missing a spot's value and get silently dropped.

So: every time your firmware reads all 5 sensors (say, once a minute), it writes **one** document like this into a collection called `occupancySnapshots`:

```
occupancySnapshots (collection)
  └── <auto-id> (document)
        timestamp: <server timestamp>
        spot_1: true
        spot_2: false
        spot_3: false
        spot_4: true
        spot_5: false
```

`true` = occupied, `false` = open. Use the *server* timestamp (Firestore can generate this for you on write) rather than the device's own clock, so you don't have to worry about the device's clock being wrong or drifting.

You don't need to create this collection manually in the console — it gets created automatically the first time your device writes a document into it.

## 4. Get credentials for the device to write with

You need two different kinds of credentials for two different things. Don't mix these up:

- **The device** (firmware, writing sensor readings) needs a way to authenticate *writes only*, ideally scoped down.
- **The export script** (Python, running on a laptop/server, reading everything out to build the CSV) needs full admin read access.

### 4a. Device write access

Easiest path if the firmware can make HTTPS requests (ESP32/Arduino with WiFi definitely can): use the **Firestore REST API** with a Web API key.

1. In Firebase console: gear icon → **Project settings** → **General** tab.
2. Under "Your apps", click the `</>` (web) icon to register a web app (you don't need to actually build a web app, this just gets you an API key).
3. Copy the `apiKey` value from the config snippet it shows you.
4. The device can then POST a new document with a plain HTTPS request:

```
POST https://firestore.googleapis.com/v1/projects/<YOUR_PROJECT_ID>/databases/(default)/documents/occupancySnapshots?key=<YOUR_API_KEY>
Content-Type: application/json

{
  "fields": {
    "timestamp": { "timestampValue": "2026-08-09T14:32:00Z" },
    "spot_1": { "booleanValue": true },
    "spot_2": { "booleanValue": false },
    "spot_3": { "booleanValue": false },
    "spot_4": { "booleanValue": true },
    "spot_5": { "booleanValue": false }
  }
}
```

If the device's own clock is reasonably accurate (NTP-synced, which ESP32 WiFi boards usually are), it's fine to send the timestamp itself like above instead of relying on a server timestamp — server timestamps are mainly useful when writing from a trusted backend, not from a public API-key request.

### 4b. Security rules — lock the collection down

By default, "production mode" denies everything. You need a rule that lets writes into `occupancySnapshots` happen (since the device is writing with just an API key, not a logged-in user) but doesn't let randoms read your data or write into other collections.

Go to **Firestore Database → Rules** and use:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /occupancySnapshots/{docId} {
      allow create: if true;   // device can add new readings
      allow read, update, delete: if false;  // nobody can read/edit/delete via the public API key
    }
  }
}
```

This means: the API key can only ever *add new* documents to that one collection — it can't read anything back, edit old readings, or touch any other collection. That's the right amount of exposure for a device that's just reporting sensor data. Click **Publish** after pasting this in.

### 4c. Export script (admin) access

This is separate from the API key above, and much more powerful — never put this one on the device or in any public code.

1. **Project settings → Service accounts** tab.
2. Click **Generate new private key**. It downloads a `.json` file (something like `parking-availability-firebase-adminsdk-xxxxx.json`).
3. Move that file into the `ml/` folder in the repo and rename it to `serviceAccountKey.json`.
4. **Immediately add it to `.gitignore`** so it never gets committed — this key gives full read/write access to the whole database, unlike the device's API key.

```
# add this line to .gitignore
ml/serviceAccountKey.json
```

## 5. Install what the export script needs

```bash
pip install firebase-admin
```

Add `firebase-admin` to `ml/requirements.txt` too.

## 6. The export script

This is the piece that turns Firestore into the CSV that `lstm.py` and `predict_week.py` already expect. Save as `ml/firestore_export.py`:

```python
# ml/firestore_export.py
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta, timezone

DATA_DIR = Path(__file__).parent
NUM_SPOTS = 5
HIST_CSV = DATA_DIR / "occupancy_data.csv"

cred = credentials.Certificate(DATA_DIR / "serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()


def _doc_to_row(doc):
    d = doc.to_dict()
    row = {"timestamp": d["timestamp"]}
    for i in range(1, NUM_SPOTS + 1):
        row[f"spot_{i}"] = int(d[f"spot_{i}"])
    return row


def export_historical():
    """Pull every new reading since the last run and append to the growing
    training CSV. Meant to run weekly, before lstm.py retrains."""
    query = db.collection("occupancySnapshots").order_by("timestamp")
    if HIST_CSV.exists():
        existing = pd.read_csv(HIST_CSV, parse_dates=["timestamp"])
        query = query.where("timestamp", ">", existing["timestamp"].max())
    else:
        existing = pd.DataFrame()

    rows = [_doc_to_row(doc) for doc in query.stream()]
    if not rows:
        print("no new rows")
        return

    full = pd.concat([existing, pd.DataFrame(rows)], ignore_index=True)
    full.to_csv(HIST_CSV, index=False)
    print(f"appended {len(rows)} rows, {len(full)} total in {HIST_CSV.name}")


def export_recent_window(hours=4.5):
    """Just the last few hours, for predict_week.py's sliding window.
    Meant to run hourly. 4.5 hours (not exactly 4) leaves buffer room so
    5-minute resampling doesn't come up short at the edges."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    query = (
        db.collection("occupancySnapshots")
        .where("timestamp", ">=", cutoff)
        .order_by("timestamp")
    )
    rows = [_doc_to_row(doc) for doc in query.stream()]
    return pd.DataFrame(rows)


if __name__ == "__main__":
    export_historical()
```

What each function is for:

- **`export_historical()`** — this is what keeps the "full history" alive. It only asks Firestore for documents newer than whatever's already in `occupancy_data.csv`, so it doesn't re-download the whole database every time. That CSV is what `lstm.py` trains on. Run this on a weekly cron, right before training.
- **`export_recent_window()`** — this does *not* touch the historical CSV at all. It's a fresh, small query straight to Firestore for just the last ~4.5 hours of readings, returned directly as a DataFrame. This is the "4 hours" piece for `predict_week.py`'s sliding window: `SEQ_LEN = 48` rows at a 5-minute resample = exactly 4 hours, and the extra 0.5 hour is slack so a bucket at the very edge of the window doesn't get dropped for missing data.

## 7. Hook it into the existing prediction script

In `ml/predict_week.py`, the line that currently does:

```python
inputFile = DATA_DIR / "occupancy_data.csv"
df = pd.read_csv(inputFile)
```

should become:

```python
from firestore_export import export_recent_window
df = export_recent_window()
```

That's the whole change — `forecast_week()` already just slices off the last `SEQ_LEN` rows after resampling, so feeding it a small recent-only DataFrame instead of the entire historical CSV is strictly better (faster, and doesn't grow slower over months of data).

## 8. Checklist to know it's actually working

- [ ] Firebase project created, Firestore enabled
- [ ] Security rules published (device can only `create` in `occupancySnapshots`)
- [ ] Device successfully writes a test document — check it shows up in **Firestore Database → Data** tab in the console
- [ ] `serviceAccountKey.json` downloaded, placed in `ml/`, added to `.gitignore`
- [ ] `pip install firebase-admin` done, added to `requirements.txt`
- [ ] `python ml/firestore_export.py` runs and creates/updates `ml/occupancy_data.csv`
- [ ] `export_recent_window()` returns a non-empty DataFrame once at least ~4.5 hours of readings exist
- [ ] `predict_week.py` runs end to end using the live Firestore data instead of the fake CSV from `gen_fake_data.py`
