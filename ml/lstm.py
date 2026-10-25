"""
lstm.py
LSTM predicts based on past so it literally checks the data from the span of 4 hours of timestamps to
predict what is occupied now. it will remmember patterns that occur freq and forget what hapend 3 hours ago at a diff
time of day (evening rush, morning calm). i chose 2 layers cuz the first would learn the low level patterns and the high level 
will be detected by 2nd layer. (low level = 'last 3 spots were occupied', high leve = 'looks like a rush on monday evening')

test set 20 % training 80 %

"""
#TODO: SET UP CRONJOB WEEKLY HERE NOT NOW BUT AFTER GIVEN THE WEEKS WORTH OF DATA
from datetime import datetime
import numpy as np #type: ignore
import pandas as pd #type: ignore
import torch #type: ignore
import torch.nn as nn #type: ignore
from torch.utils.data import Dataset, DataLoader #type: ignore
from pathlib import Path
DATA_DIR = Path(__file__).parent
RESAMPLE_FREQ_MIN = 5
SEQ_LEN = 48  
NUM_EPOCHS = 20
HIDDEN_DIM = 64
NUM_LAYERS = 2   
LR         = 0.001
NUM_SPOTS  = 2
INPUT_DIM  = NUM_SPOTS + 6   # 2 occupancy + hour_sin/cos + day_sin/cos + min_sin_cos



def add_time_features(df):
    df = df.copy()
    # sin/cos  makes sure that 0 and 23 arent 23 hours apart but 1 hr apart
    ts = pd.to_datetime(df["timestamp"])
    for col, max_val in [('hour',24), ('dayofweek', 7), ('minute', 60)]:
        vals = ts.dt.__getattribute__(col) if col != 'dayofweek' else ts.dt.dayofweek
        df[f"{col}_sin"] = np.sin(2 * np.pi * vals / max_val)
        df[f"{col}_cos"] = np.cos(2 * np.pi * vals / max_val)
    return df
def load_checkpoint(path, device):
    ck = torch.load(path, map_location=device)
    if not isinstance(ck, dict) or "state_dict" not in ck:
        raise ValueError("old checkpoint with no metadata in it. retrain with new lstm.py")
    if ck["num_spots"] != NUM_SPOTS:
        raise ValueError(
            f"checkpoint was trained for {ck["num_spots"]} spots but were set to {NUM_SPOTS}. retrain"
        )
    if ck["seq_len"] != SEQ_LEN:
        raise ValueError(f"checkpoint seq_len {ck["seq_len"]} != {SEQ_LEN}. retrain")
    model = ParkingLSTM(ck["num_spots"] + 6, ck["hidden_dim"], ck["num_layers"], ck["num_spots"])
    model.load_state_dict(ck["state_dict"])
    return model.to(device).eval(), ck

max_fill = 3 # 15 mins at 5 min buckets; handles the gaps
def resample_occupancy(df, freq = f"{RESAMPLE_FREQ_MIN}min"):
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    spot_cols = [c for c in df.columns if c.startswith("spot_")]
    # reindex onto the full time grid. dropna fails
    g = df.set_index("timestamp").resample(freq).mean()
    # short holes get filled and long ones stay as nan so no traingin happens
    g[spot_cols] = g[spot_cols].ffill(limit=max_fill)
    binned = (g[spot_cols] > 0.5).astype(float)
    g[spot_cols] = binned.where(g[spot_cols].notna())
    return g.reset_index()
def check_window(df):
    if len(df) < SEQ_LEN:
        hours = SEQ_LEN * RESAMPLE_FREQ_MIN / 60
        raise ValueError(
            f'need {SEQ_LEN} resampled rows (~{hours:.1f}h of readings) but only got {len(df)}. ' "sensors prolly havent been running long enough yet"
        )

def contiguous_blocks(df):
    """runs of rows with nothing missing. windows must never straddle a gap"""

    spot_cols = [c for c in df.columns if c.startswith("spot_")]
    ok = df[spot_cols].notna().all(axis=1).to_numpy()
    blocks, start = [], None
    for i, good in enumerate(ok):
        if good and start is None:
            start = i
        elif not good and start is not None:
            blocks.append((start, i))
            start = None
    if start is not None:
        blocks.append((start, len(ok)))
    return blocks

def window_starts(blocks, seq_len = SEQ_LEN):
    out = []
    for a, b in blocks:
        out.extend(range(a,b-seq_len))
    return out
FEATURE_COLS = [f"spot_{i}" for i in range(1, NUM_SPOTS + 1)] + \
               ["hour_sin", "hour_cos", "dayofweek_sin", "dayofweek_cos", "minute_sin", "minute_cos"]


TARGET_COLS  = [f"spot_{i}" for i in range(1, NUM_SPOTS + 1)]

class OccupancyDataset(Dataset):
    def __init__(self, features, targets, seq_len=SEQ_LEN, starts = None):
        self.X = torch.tensor(features, dtype=torch.float32)
        self.y = torch.tensor(targets, dtype=torch.float32)
        self.seq_len = seq_len
        # starts = which indexes are allowed to start a window. if. you dont apass it you get the old behavior, 
        #
        if starts is None:
            starts = list(range(max(0, len(self.X) - seq_len)))
        self.starts = starts

    def __len__(self):
        return len(self.starts)
    def __getitem__(self, idx):
        i = self.starts[idx]
        return self.X[i : i + self.seq_len], self.y[i + self.seq_len]

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
    check_window(recent_df)
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
    df = pd.read_csv(DATA_DIR / "occupancy_data.csv") # TODO: once ayaan makes script for creation of csv replace path
    df = resample_occupancy(df)
    df = add_time_features(df)

    blocks = contiguous_blocks(df)
    print(f"{len(blocks)} contiguous blocks, {len(df)} rows total")
    features = df[FEATURE_COLS].values
    targets  = df[TARGET_COLS].values

    # train/val split 
    split = int(len(features) * 0.8)
    starts = window_starts(blocks)
    train_starts = [i for i in starts if i + SEQ_LEN < split]
    val_starts = [i for i in starts if i >= split - SEQ_LEN]


    train_ds = OccupancyDataset(features, targets, SEQ_LEN, train_starts)
    val_ds   = OccupancyDataset(features, targets, SEQ_LEN, val_starts)
    print(f"{len(train_ds)} train windows, {len(val_ds)} val windows")
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
    torch.save({
        "state_dict": model.state_dict(),
        "num_spots": NUM_SPOTS,
        "seq_len": SEQ_LEN,
        "resample_freq_min": RESAMPLE_FREQ_MIN,
        "hidden_dim" : HIDDEN_DIM,
        "num_layers": NUM_LAYERS,
        "feature_cols": FEATURE_COLS,
        "trained_at": datetime.now().isoformat(timespec="seconds"),
    }, DATA_DIR / "parking_lstm.pth")
print("\nModel saved")