"""
lstm.py
LSTM predicts based on past so it literally checks the data from the span of 4 hours of timestamps to
predict what is occupied now. it will remmember patterns that occur freq and forget what hapend 3 hours ago at a diff
time of day (evening rush, morning calm). i chose 2 layers cuz the first would learn the low level patterns and the high level 
will be detected by 2nd layer. (low level = 'last 3 spots were occupied', high leve = 'looks like a rush on monday evening')

test set 20 % training 80 %

"""
#TODO: SET UP CRONJOB WEEKLY HERE NOT NOW BUT AFTER GIVEN THE WEEKS WORTH OF DATA

import numpy as np #type: ignore
import pandas as pd #type: ignore
import torch #type: ignore
import torch.nn as nn #type: ignore
from torch.utils.data import Dataset, DataLoader #type: ignore
from pathlib import Path
import matplotlib.pyplot as plt
DATA_DIR = Path(__file__).parent
RESAMPLE_FREQ_MIN = 5
SEQ_LEN = 48  
NUM_EPOCHS = 20
HIDDEN_DIM = 64
NUM_LAYERS = 2   
LR         = 0.001
NUM_SPOTS  = 5
INPUT_DIM  = NUM_SPOTS + 6   # 5 occupancy + hour_sin/cos + day_sin/cos + min_sin_cos



def add_time_features(df):
    df = df.copy()
    # sin/cos  makes sure that 0 and 23 arent 23 hours apart but 1 hr apart
    ts = pd.to_datetime(df["timestamp"])
    for col, max_val in [('hour',24), ('dayofweek', 7), ('minute', 60)]:
        vals = ts.dt.__getattribute__(col) if col != 'dayofweek' else ts.dt.dayofweek
        df[f"{col}_sin"] = np.sin(2 * np.pi * vals / max_val)
        df[f"{col}_cos"] = np.cos(2 * np.pi * vals / max_val)
    return df

def resample_occupancy(df, freq = f"{RESAMPLE_FREQ_MIN}min"):
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("timestamp").resample(freq).mean().dropna().reset_index()
    spot_cols = [c for c in df.columns if c.startswith("spot_")]
    df[spot_cols] = (df[spot_cols] > 0.5).astype(int)
    return df

FEATURE_COLS = [f"spot_{i}" for i in range(1, NUM_SPOTS + 1)] + \
               ["hour_sin", "hour_cos", "dayofweek_sin", "dayofweek_cos", "minute_sin", "minute_cos"]


TARGET_COLS  = [f"spot_{i}" for i in range(1, NUM_SPOTS + 1)]

class OccupancyDataset(Dataset):
    def __init__(self, features, targets, seq_len = SEQ_LEN):
        self.X = torch.tensor(features, dtype=torch.float32)
        self.y = torch.tensor(targets,  dtype=torch.float32)
        self.seq_len = seq_len

    def __len__(self):
        return max(0, len(self.X) - self.seq_len)


    def __getitem__(self, idx):
        x = self.X[idx : idx + self.seq_len]           
        y = self.y[idx + self.seq_len]                 
        return x, y

class ParkingLSTM(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_layers, num_spots):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.2 if num_layers > 1 else 0.0,
        )
        self.fc1 = nn.Linear(hidden_dim, 32)
        self.fc2 = nn.Linear(32, num_spots)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = torch.relu(self.fc1(out[:, -1, :]))
        return self.fc2(out)   # use last timestep hidden state


def train(model, loader, optimizer, criterion, device): 
    model.train()
    total_loss = 0
    for X_batch, y_batch in loader:
        X_batch, y_batch = X_batch.to(device), y_batch.to(device)
        optimizer.zero_grad()
        pred = model(X_batch)
        loss = criterion(pred, y_batch)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    return total_loss / len(loader)


def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss = 0
    with torch.no_grad():
        for X_batch, y_batch in loader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            pred = model(X_batch)
            total_loss += criterion(pred, y_batch).item()
    return total_loss / len(loader)


def predict_now(model, recent_df, device):
    """returns seq data kinda like the planet fitness crowdmeter"""
    model.eval()
    recent_df = resample_occupancy(recent_df)
    recent_df = add_time_features(recent_df)
    features = recent_df[FEATURE_COLS].values[-SEQ_LEN:]
    x = torch.tensor(features, dtype=torch.float32).unsqueeze(0).to(device)
    with torch.no_grad():
        probs = torch.sigmoid(model(x)).cpu().numpy()[0]
    preds = {}
    for i, p in enumerate(probs):
        preds[f"spot_{i+1}"] = round(float(p),3)
    
    return preds

if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    

    # load data
    df = pd.read_csv(DATA_DIR / "occupancy_data.csv") # TODO: once ayaan makes script for creationg of csv replace path
    df = resample_occupancy(df)
    df = add_time_features(df)

    features = df[FEATURE_COLS].values
    targets  = df[TARGET_COLS].values

    # train/val split 
    split = int(len(features) * 0.8)
    train_ds = OccupancyDataset(features[:split], targets[:split], SEQ_LEN)
    val_ds   = OccupancyDataset(features[split-SEQ_LEN:],   targets[split-SEQ_LEN:], SEQ_LEN)

    train_loader = DataLoader(train_ds, batch_size=64, shuffle=True)
    val_loader   = DataLoader(val_ds,   batch_size=64)

    # model, optimizer, loss
    model     = ParkingLSTM(INPUT_DIM, HIDDEN_DIM, NUM_LAYERS, NUM_SPOTS).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    criterion = nn.BCEWithLogitsLoss()
    
    # train loop
    print(f"\nTraining for {NUM_EPOCHS} epochs\n")
    for epoch in range(1, NUM_EPOCHS+1):
        train_loss = train(model, train_loader, optimizer, criterion, device)
        val_loss   = evaluate(model, val_loader, criterion, device)
        print(f"Epoch {epoch}/{NUM_EPOCHS} | train_loss={train_loss:.4f}  val_loss={val_loss:.4f}")

    # save model
    torch.save(model.state_dict(), DATA_DIR / "parking_lstm.pth")
    print("\nModel saved")