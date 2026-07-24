#input: lstm path + recent window data from ayaan 
#output: a list of readings for the week for each sensor
import torch 
import torch.nn as nn
import pandas as pd
from lstm import ParkingLSTM, predict_now, resample_occupancy, add_time_features, FEATURE_COLS, SEQ_LEN

input_size = 11
hidden_size = 64
num_layers = 2
output_size = 5

model = ParkingLSTM(input_size, hidden_size, num_layers, output_size)

model.load_state_dict(torch.load('parking_lstm.pth'))
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def forecast_week(model, df, device):
    df = resample_occupancy(df)
    df = add_time_features(df)

    window = df[FEATURE_COLS].values[-SEQ_LEN:]
    last_ts = pd.to_datetime(df["timestamp"].iloc[-1])
    steps = 7 * 24 * 60 // 5
    forecast = []

    for step in range(steps):
        #TODO: run model on window to get next reading for each sensor
        # then build a new row  and append that to the window and delete the first row. 
        # save the new row into forecast and repeat until 1 week into future is done.
        pass

    return forecast


if __name__ == '__main__':
    df = pd.read_csv("path") #TODO: get file name from ayaan
    forecast = forecast_week(model, df, device)