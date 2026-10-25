#input: lstm path + recent window data from ayaan 
#output: a list of readings for the week for each sensor
import torch 
import numpy as np
import torch.nn as nn
import pandas as pd
from pathlib import Path
from lstm import (
    ParkingLSTM, resample_occupancy,load_checkpoint, check_window, add_time_features, FEATURE_COLS,
    SEQ_LEN, INPUT_DIM, NUM_LAYERS, NUM_SPOTS, HIDDEN_DIM, RESAMPLE_FREQ_MIN, DATA_DIR
)
import json
from datetime import timedelta


def forecast_week(model, df, device):
    df = resample_occupancy(df)
    check_window(df)
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


if __name__ == '__main__':
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Running on: {device}")
    model, ck = load_checkpoint(DATA_DIR / "parking_lstm.pth", device)
    print(f"loaded model trained {ck['trained_at']} for {ck["num_spots"]} spots")
    from datetime import datetime, timezone
    import firebase_admin
    from firebase_admin import credentials, firestore

    DATA_DIR = Path(__file__).parent

    def _db():
        if not firebase_admin._apps:
            firebase_admin.initialize_app(credentials.Certificate(DATA_DIR / "serviceAccountKey.json")) 
        return firestore.client()
    def publish_forecast(forecast, model_name="lstm"):
        db = _db()
        ran_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        payload = {"generatedAt": ran_at, "model": model_name, "points": forecast}

        db.collection("forecasts").document("latest").set(payload)
        db.collection("forecastRuns").document(ran_at).set(payload)

        print(f"published {len(forecast)} points, archived as forecastRuns/{ran_at}")         
    #TODO: SET UP A CRONJOB HOURLY HERE NOT NOW BUT LATER UNTIL GIVEN FIRST 4 HOURS OF DATA 
    # AND THEN SLIDING WINDOW CAN BE USED
