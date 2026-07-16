"""
lstm.py
LSTM predicts based on past so it literally checks the data from the span of 4 hours of timestamps to
predict what is occupied now. it will remmember patterns that occur freq and forget what hapend 3 hours ago at a diff
time of day (evening rush, morning calm). i chose 2 layers cuz the first would learn the low level patterns and the high level 
will be detected by 2nd layer. (low level = 'last 3 spots were occupied', high leve = 'looks like a rush on monday evening')

test set 20 % training 80 %

"""

import numpy as np #type: ignore
import pandas as pd #type: ignore
import torch #type: ignore
import torch.nn as nn #type: ignore
from torch.utils.data import Dataset, DataLoader #type: ignore

SEQ_LEN = 48     
LR         = 0.001
NUM_SPOTS  = 5
INPUT_DIM  = NUM_SPOTS + 6   # 5 occupancy + hour_sin/cos + day_sin/cos + min_sin_cos



def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # sin/cos  makes sure that 0 and 23 arent 23 hours apart but 1 hr apart
    ts = pd.to_datetime(df["timestamp"])
    df["hour_sin"] = np.sin(2 * np.pi * ts.dt.hour / 24)
    df["hour_cos"] = np.cos(2 * np.pi * ts.dt.hour / 24)
    df["day_sin"]  = np.sin(2 * np.pi * ts.dt.dayofweek / 7)
    df["day_cos"]  = np.cos(2 * np.pi * ts.dt.dayofweek / 7)
    df["minute_sin"] = np.sin(2 * np.pi * ts.dt.minute / 60)
    df["minute_cos"] = np.cos(2 * np.pi * ts.dt.minute / 60)
    return df

def resample_occupancy(df: pd.DataFrame, freq: str = "5min") -> pd.DataFrame:
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("timestamp").resample(freq).last().dropna().reset_index()
    return df

FEATURE_COLS = [f"spot_{i}" for i in range(1, NUM_SPOTS + 1)] + \
               ["hour_sin", "hour_cos", "day_sin", "day_cos", "minute_sin", "minute_cos"]


TARGET_COLS  = [f"spot_{i}" for i in range(1, NUM_SPOTS + 1)]

class OccupancyDataset(Dataset):
    def __init__(self, features: np.ndarray, targets: np.ndarray, seq_len: int = SEQ_LEN):
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
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, num_spots),
            nn.Sigmoid(),   # sigma💀
        )

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])   # use last timestep hidden state


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


def predict_now(model, recent_df: pd.DataFrame, device) -> dict:
    """returns seq data kinda like the planet fitness crowdmeter"""
    model.eval()
    recent_df = resample_occupancy(recent_df)
    recent_df = add_time_features(recent_df)
    features = recent_df[FEATURE_COLS].values[-SEQ_LEN:]
    x = torch.tensor(features, dtype=torch.float32).unsqueeze(0).to(device)
    with torch.no_grad():
        probs = model(x).squeeze().cpu().numpy()
    return {f"spot_{i+1}": float(round(p, 3)) for i, p in enumerate(probs)}

if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    

    # load data
    df = pd.read_csv("occupancy_data.csv")
    df = resample_occupancy(df)
    df = add_time_features(df)

    features = df[FEATURE_COLS].values
    targets  = df[TARGET_COLS].values

    # train/val split 
    split = int(len(features) * 0.8)
    X_train, X_val = features[:split], features[split:]
    y_train, y_val = targets[:split],  targets[split:]

    train_ds = OccupancyDataset(X_train, y_train, SEQ_LEN)
    val_ds   = OccupancyDataset(X_val,   y_val, SEQ_LEN)
    assert len(val_ds) > 0, f"val split too small for seq_len= {SEQ_LEN}"

    train_loader = DataLoader(train_ds, batch_size=64, shuffle=True)
    val_loader   = DataLoader(val_ds,   batch_size=64)

    # model, optimizer, loss
    model     = ParkingLSTM(INPUT_DIM, 64, 2, 5).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    criterion = nn.BCELoss()

    # train loop
    print(f"\nTraining for 20 epochs\n")
    for epoch in range(1, 21):
        train_loss = train(model, train_loader, optimizer, criterion, device)
        val_loss   = evaluate(model, val_loader, criterion, device)
        print(f"Epoch {epoch:02d}/{20}  train_loss={train_loss}  val_loss={val_loss}")

    # save model
    torch.save(model.state_dict(), "parking_lstm.pth")
    print("\nModel saved")
    # crowdmeter prediction on the last 48 rows (4 hours memory)
    recent = df.tail(SEQ_LEN)
    probs  = predict_now(model, recent, device)
    print("\nCrowdmeter:")
    for spot, p in probs.items():
        bar    = "*" * int(p * 20)
        status = "OCCUPIED" if p > 0.5 else "likely free"
        print(f"  {spot}: {bar:20s} {p:.0%}  ({status})")