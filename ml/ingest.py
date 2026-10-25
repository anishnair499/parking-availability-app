import os
from datetime import datetime, timedelta, timezone

import pandas as pd

from lstm import DATA_DIR, NUM_SPOTS

csv_path = DATA_DIR / "availabilty.csv"
lot_timezone = "America/Detroit"
spots = [f"spot_{i}" for i in range(1, NUM_SPOTS +1)]

max_stale_time = 20

def get_db():
    import firebase_admin
    from firebase_admin import credentials, firestore

    if not firebase_admin._apps:

        if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            firebase_admin.initialize_app()
        else:
            firebase_admin.initialize_app(credentials.Certificate(DATA_DIR / "serviceAccountKey.json"))
    return firestore.client()

def to_local(df):
    out = df.copy()
    out["timestamp"] = out["timestamp"].dt.tz_convert(lot_timezone).dt.tz_localize(None)
    return out.sort_values("timestamp").reset_index(drop=True)

def load_csv(path):
    df = pd.read_csv(path)
    missing = [c for c in ["timestamp"] + spots if c not in df.columns]
    if missing:
        raise ValueError(f"{path} is missing columns {missing}. mlmodel.py header should be exact")
    if df["timestamp"].astype(str).str.contains(r"[+-]\d\d:\d\d$|Z$").any():
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, format="mixed")
        return to_local(df)
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="mixed")
    return df.sort_values("timestamp").reset_index(drop=True)

def load_history():
    return load_csv(csv_path)


def load_recent_window(hours=4.5):

    df = load_csv(csv_path)
    check_fresh(df)
    cutoff = df["timestamp"].max() - pd.Timedelta(hours=hours)
    return df[df["timestamp"] > cutoff].reset_index(drop=True)

def check_fresh(df):
    if df.empty:
        raise ValueError("no readings in teh file at all. modelpy useless???")
    now = pd.Timestamp.now(tz=lot_timezone).tz_localize(None)
    age = (now-df["timestamp"].max()).total_seconds() / 60
    if age > max_stale_time:
        raise ValueError(f"newest reading is {age:.0f} min old (limit {max_stale_time}). rerun mmmodel")
    