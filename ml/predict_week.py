#input: lstm path + recent window data from ayaan 
#output: a list of readings for the week for each sensor
import torch 
import torch.nn as nn
import pandas as pd
from pathlib import Path
from lstm import (
    ParkingLSTM, predict_now, resample_occupancy, add_time_features, FEATURE_COLS,
    SEQ_LEN, INPUT_DIM, NUM_LAYERS, NUM_SPOTS, HIDDEN_DIM, RESAMPLE_FREQ_MIN, DATA_DIR
)
import json
from datetime import timedelta


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = ParkingLSTM(INPUT_DIM, HIDDEN_DIM, NUM_LAYERS, NUM_SPOTS)

model.load_state_dict(torch.load(DATA_DIR / "parking_lstm.pth", map_location=device))
model.to(device)
model.eval()


def forecast_week(model, df, device):
    df = resample_occupancy(df)
    df = add_time_features(df)

    window = df[FEATURE_COLS].values[-SEQ_LEN:]
    last_ts = pd.to_datetime(df["timestamp"].iloc[-1])
    steps = 7 * 24 * 60 // RESAMPLE_FREQ_MIN
    forecast = []

    for step in range(steps):
        #TODO: run model on window to get next reading for each sensor
        # then build a new row  and append that to the window and delete the first row. 
        # save the new row into forecast and repeat until 1 week into future is done.
        pass

    return forecast


if __name__ == '__main__':
    inputFile = "path"
    df = pd.read_csv(inputFile) #TODO: get file name from ayaan
    forecast_data = forecast_week(model, df, device)
    #TODO: SET UP A CRONJOB HOURLY HERE NOT NOW BUT LATER UNTIL GIVEN FIRST 4 HOURS OF DATA 
    # AND THEN SLIDING WINDOW CAN BE USED
    output_json_path = Path("") #ask sarvad about where to send json data

    with open(output_json_path, "w") as file:
        json.dump(forecast_data,file, indent=4)