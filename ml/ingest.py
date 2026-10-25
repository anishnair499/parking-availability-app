import os
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent
csv_path = DATA_DIR / "availability.csv"

lot_timezone = "America/Detroit"
spots = ["spot_1", "spot_2"]

max_min = 15

def get_db():
    import firebase_admin
    from firebase_admin import credentials, firestore

    if not firebase_admin._apps:
        if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            firebase_admin.initialize_app()
        else:
            firebase_admin.initialize_app(credentials.Certificate(str(DATA_DIR / "serviceAccountKey.json")))
    return firestore.client()

def fmt_ts(ts):
    return pd.Timestamp(ts).strftime("%Y-%m-%d %H:%M")

def local_now():
    return pd.Timestamp.now(tz=lot_timezone).tz_localize(None)

def load_csv(path=csv_path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. get csv from ayaan and put in ml/")
    df = pd.read_csv(path)
    missing = [c for c in ["timestamp"] + spots if c not in df.columns]
    if missing:
        raise ValueError(f"{path} is missing columns {missing}. header should be exact")
    ts = pd.to_datetime(df["timestamp"], utc=True, format="mixed")
    df['timestamp'] = ts.dt.tz_convert(lot_timezone).dt.tz_localize(None)
    df = df[["timestamp"] + spots].dropna(subset=["timestamp"])
    if df.empty:
        raise ValueError(f"{path} has no readings in it")
    return df.sort_values("timestamp").reset_index(drop=True)

def warn_stale(df):
    age = (local_now() - df["timestamp"].max()).total_seconds() / 60
    if age > max_min:
        print(
            f"heads up: newest reading is {age:.0f} min old. the model tab shows its "
            f"sensors-down banner after {max_min}, so make the csv right before publish"
        )
    return age
