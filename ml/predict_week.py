#input: lstm path + recent window data from ayaan 
#output: a list of readings for the week for each sensor
import torch 
import torch.nn as nn
import pandas as pd
from pathlib import Path
from lstm import (
    ParkingLSTM, resample_occupancy, add_time_features, FEATURE_COLS,
    SEQ_LEN, INPUT_DIM, NUM_LAYERS, NUM_SPOTS, HIDDEN_DIM, RESAMPLE_FREQ_MIN, DATA_DIR
)
import json
from datetime import timedelta


def forecast_week(model, df, device):
    df = resample_occupancy(df)
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

        pass

    return forecast


if __name__ == '__main__':
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Running on: {device}")
    input_dim = NUM_SPOTS + 6
    
    model = ParkingLSTM(input_dim, HIDDEN_DIM, NUM_LAYERS, NUM_SPOTS)
    model.load_state_dict(torch.load(DATA_DIR / "parking_lstm.pth", map_location=device))
    model.to(device)
    model.eval()
    inputFile = DATA_DIR / "occupancy_data.csv"
    df = pd.read_csv(inputFile) #TODO: get file name from ayaan
    forecast_data = forecast_week(model, df, device)
    #TODO: SET UP A CRONJOB HOURLY HERE NOT NOW BUT LATER UNTIL GIVEN FIRST 4 HOURS OF DATA 
    # AND THEN SLIDING WINDOW CAN BE USED
    output_json_path = DATA_DIR.parent / "frontend" / "assets" / "predictions.json" 
    #make sure folders exist
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_json_path, "w") as file:
        json.dump(forecast_data,file, indent=4)
    