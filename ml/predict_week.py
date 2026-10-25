#input: lstm path + recent window data from ayaan 
#output: a list of readings for the week for each sensor
import torch 
import numpy as np
import torch.nn as nn
import pandas as pd
from pathlib import Path
from lstm import (
    ParkingLSTM, resample_occupancy,load_checkpoint, check_window, check_no_gaps ,add_time_features, FEATURE_COLS,
    SEQ_LEN, INPUT_DIM, NUM_LAYERS, NUM_SPOTS, HIDDEN_DIM, RESAMPLE_FREQ_MIN, DATA_DIR
)
import json
from datetime import timedelta
from ingest import load_csv, csv_path, get_db, local_now, fmt_ts, warn_stale

def forecast_week(model, df, device):
    df = resample_occupancy(df)
    check_window(df)
    check_no_gaps(df)
    df = add_time_features(df)

    window_data = df[FEATURE_COLS].values[-SEQ_LEN:]
    current_window = torch.tensor(window_data, dtype=torch.float32).unsqueeze(0).to(device)
    last_ts = pd.to_datetime(df["timestamp"].iloc[-1])
    steps = 7 * 24 * 60 // RESAMPLE_FREQ_MIN
    forecast = []

    for step in range(steps):
        with torch.no_grad():
            pred = model(current_window)
            probs = torch.sigmoid(pred).squeeze(0).cpu().numpy()
        pred_T = last_ts + timedelta(minutes=(step+1) * RESAMPLE_FREQ_MIN)

        row_dict = {"timestamp": str(pred_T)}
        for i,p in enumerate(probs):
            row_dict[f"spot_{i+1}"] = round(float(p), 3)

        forecast.append(row_dict)
        #appended predictions for the next 5 min step

        #TODO: remove the first 5 minutes of data. 
        # first need to create the time features for the new data
        # then need to convert the converting the probs to the parking spot prediction
        # finally add the row to the window and move the window forward 5 mins
        hr = pred_T.hour
        day = pred_T.dayofweek
        min = pred_T.minute
        time_feats = [
            np.sin(2* np.pi * hr / 24), 
            np.cos(2* np.pi * hr / 24), 
            np.sin(2* np.pi * day / 7), 
            np.cos(2* np.pi * day / 7), 
            np.sin(2* np.pi * min / 60), 
            np.cos(2* np.pi * min / 60), 
        ]
        bin_spots = [1.0 if p > 0.5 else 0.0 for p in probs]
        next_step_feats = bin_spots + time_feats
        next_tensor = torch.tensor(next_step_feats, dtype=torch.float32).view(1,1,-1).to(device)
        current_window = torch.cat([current_window[:,1:,:], next_tensor], dim=1)


    return forecast


def publish_forecast(forecast):
    from datetime import datetime, timezone

    db = get_db()
    ran_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    payload = {"generatedAt": ran_at, "model": "lstm", "points": forecast}

    # latest is what the app reads, forecastRuns keeps every run so we can score old forecasts later
    db.collection("forecasts").document("latest").set(payload)
    db.collection("forecastRuns").document(ran_at).set(payload)
    # shows up as "last forecast" on the model tab. merge so the scores training wrote stay put
    db.collection("models").document("status").set({"lastForecastRun": fmt_ts(local_now())}, merge=True)

    print(f"published {len(forecast)} points, archived as forecastRuns/{ran_at}")


if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="forecast the next week and publish it to firestore")
    parser.add_argument("--csv", default=str(csv_path), help="readings file (default ml/availability.csv)")
    parser.add_argument("--dry-run", action="store_true", help="print a summary and skip the firestore write")
    args = parser.parse_args()

    ckpt = DATA_DIR / "parking_lstm.pth"
    if not ckpt.exists():
        sys.exit("no parking_lstm.pth yet. run `python lstm.py` first")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Running on: {device}")
    model, ck = load_checkpoint(ckpt, device)
    print(f"loaded model trained {ck['trained_at']} for {ck['num_spots']} spots")

    window = load_csv(args.csv)
    warn_stale(window)

    try:
        forecast = forecast_week(model, window, device)
    except ValueError as e:
        # not enough unbroken readings is expected on thin data. say so and stop instead of publishing garbage
        print(f"skipping forecast: {e}")
        sys.exit(1)

    if args.dry_run:
        print(f"dry run: built {len(forecast)} points from {forecast[0]['timestamp']} to {forecast[-1]['timestamp']}")
    else:
        publish_forecast(forecast)