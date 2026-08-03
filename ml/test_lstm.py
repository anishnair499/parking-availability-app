import torch 
import torch.nn as nn
import pandas as pd
from pathlib import Path

from lstm import (
    add_time_features,
    resample_occupancy,
    FEATURE_COLS,
    TARGET_COLS,
    OccupancyDataset,
    ParkingLSTM,
    train,
    DATA_DIR,
)

def run_pipeline():
    print("Load csv")
    csv_path = DATA_DIR / "occupancy_data.csv"
    df = pd.read_csv(csv_path)

    print("shape original: ", df.shape)
    print("columns", list(df.columns))
    # test processing
    print("testing processing ")
    df_sampled = resample_occupancy(df)
    df_features = add_time_features(df_sampled)

    print("checking match")
    for col in FEATURE_COLS:
        if col not in df_features.columns:
            raise KeyError(f"missing feature: {col}")
    print("good")
    features = df_features[FEATURE_COLS].values
    targets = df_features[TARGET_COLS].values

    print("testing dataset index")
    dataset = OccupancyDataset(features, targets)
    print(f"initialized. sequences avail: {len(dataset)}")
    if len(dataset) == 0:
        print("empty dataset")
        return

    x,y = dataset[0]
    print(f"input shape: {x.shape}")
    print(f"target shape: {y.shape}")

    print("test: forward pass")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = ParkingLSTM(input_dim=11, hidden_dim=64, num_layers=2, num_spots=5).to(device)
    sample_batch = x.unsqueeze(0).to(device)
    with torch.no_grad():
        out = model(sample_batch)
    print("success")

    print("overall success")

if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception as e:
        print(f"fail: {str(e)}")
