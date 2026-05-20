
import warnings
warnings.filterwarnings("ignore")  # lightning is verbose

import numpy as np
import pandas as pd
import torch
import lightning.pytorch as pl

from pytorch_forecasting import TemporalFusionTransformer, TimeSeriesDataSet
from pytorch_forecasting.metrics import QuantileLoss

# ── Constants ──────────────────────────────────────────────────────────────────

NUM_SPOTS        = 5
ENCODER_LENGTH   = 32   # 32 × 15 min = 8 hours of history fed to encoder
PREDICTION_LENGTH = 2   # 2  × 15 min = 30 minutes ahead (matches frontend spec)
BATCH_SIZE       = 64
MAX_EPOCHS       = 20
LR               = 0.001

# Quantiles TFT will predict — p50 is the best guess, p10/p90 are the bounds
# These map directly to frontend confidence labels:
#   p90 - p10 < 0.3  → "Pretty reliable"
#   p90 - p10 < 0.6  → "Rough estimate"
#   p90 - p10 >= 0.6 → "Hard to say"
QUANTILES = [0.1, 0.25, 0.5, 0.75, 0.9]


# ── Time Features ──────────────────────────────────────────────────────────────
# Identical to lstm.py — this is the one piece that carries over unchanged.
# sin/cos encoding ensures 11pm and 12am are 1hr apart, not 23hrs apart.

def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    ts = pd.to_datetime(df["timestamp"])
    df["hour_sin"]   = np.sin(2 * np.pi * ts.dt.hour   / 24)
    df["hour_cos"]   = np.cos(2 * np.pi * ts.dt.hour   / 24)
    df["day_sin"]    = np.sin(2 * np.pi * ts.dt.dayofweek / 7)
    df["day_cos"]    = np.cos(2 * np.pi * ts.dt.dayofweek / 7)
    df["minute_sin"] = np.sin(2 * np.pi * ts.dt.minute / 60)
    df["minute_cos"] = np.cos(2 * np.pi * ts.dt.minute / 60)
    return df


# ── Data Preparation ───────────────────────────────────────────────────────────
# Converts wide CSV format → long format with integer time index.
# This is the biggest structural change from lstm.py.

def load_and_prepare(csv_path: str) -> pd.DataFrame:
    """
    Loads your CSV and restructures it for TFT.

    Input (wide, your format):
        timestamp | spot_1 | spot_2 | spot_3 | spot_4 | spot_5

    Output (long, TFT format):
        time_idx | timestamp | spot_id | occupancy | hour_sin | ... | day_cos

    time_idx: required by TFT — just an integer counter per spot (0, 1, 2, ...)
    spot_id:  string identifier for each spot ("spot_1" through "spot_5")
    """
    df = pd.read_csv(csv_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    # Wide → Long: melt all spot columns into rows
    # Before: 17,000 rows × 6 cols
    # After:  85,000 rows × 3 cols (one row per spot per timestamp)
    spot_cols = [f"spot_{i}" for i in range(1, NUM_SPOTS + 1)]
    df_long = df.melt(
        id_vars="timestamp",
        value_vars=spot_cols,
        var_name="spot_id",
        value_name="occupancy",
    )
    df_long["occupancy"] = df_long["occupancy"].astype(float)

    # Add time features (same logic as lstm.py)
    df_long = add_time_features(df_long)

    # Sort so each spot's rows are chronological
    df_long = df_long.sort_values(["spot_id", "timestamp"]).reset_index(drop=True)

    # time_idx: integer index per spot, starting at 0
    # TFT uses this to understand sequence position within each group
    df_long["time_idx"] = (
        df_long.groupby("spot_id").cumcount()
    )

    return df_long


def make_dataset(df: pd.DataFrame, train: bool, training_dataset=None) -> TimeSeriesDataSet:
    """
    Wraps the dataframe in a TFT-compatible TimeSeriesDataSet.

    TFT needs to know the *role* of each feature:
    - time_varying_known_reals:   features known in the future (time encodings —
                                  we always know what hour it will be)
    - time_varying_unknown_reals: features only known up to the present
                                  (occupancy — we can't know future occupancy)
    - group_ids:                  what separates one series from another (spot_id)
    """
    if train:
        return TimeSeriesDataSet(
            df,
            time_idx="time_idx",
            target="occupancy",
            group_ids=["spot_id"],
            max_encoder_length=ENCODER_LENGTH,
            max_prediction_length=PREDICTION_LENGTH,
            time_varying_known_reals=[          # known into the future
                "hour_sin", "hour_cos",
                "day_sin",  "day_cos",
                "minute_sin", "minute_cos",
            ],
            time_varying_unknown_reals=[        # only known up to now
                "occupancy",
            ],
            target_normalizer=None,             # data is already 0/1, no scaling needed
            add_relative_time_idx=True,         # adds position-in-sequence feature
            add_target_scales=False,
            add_encoder_length=True,
        )
    else:
        # Validation dataset must use same parameters as training dataset
        # predict=True allows predicting on the last window of each series
        return TimeSeriesDataSet.from_dataset(
            training_dataset, df, stop_randomization=True
        )


# ── Model ──────────────────────────────────────────────────────────────────────
# In lstm.py you wrote ~30 lines defining ParkingLSTM manually.
# TFT is configured, not implemented — the library builds the full architecture.

def build_model(training_dataset: TimeSeriesDataSet) -> TemporalFusionTransformer:
    """
    Builds the TFT model from the dataset's metadata.
    from_dataset() reads the feature declarations above so you don't
    have to manually set input dimensions.

    hidden_size=64:          same as your hidden_dim in lstm.py
    lstm_layers=2:           same as your num_layers
    attention_head_size=4:   multi-head attention (new — LSTM had none)
    dropout=0.2:             same as lstm.py
    loss=QuantileLoss():     replaces BCELoss, outputs quantile ranges
    """
    return TemporalFusionTransformer.from_dataset(
        training_dataset,
        learning_rate=LR,
        hidden_size=64,
        attention_head_size=4,
        dropout=0.2,
        hidden_continuous_size=32,
        loss=QuantileLoss(quantiles=QUANTILES),
        lstm_layers=2,
        log_interval=10,
        reduce_on_plateau_patience=3,
    )


# ── Training ───────────────────────────────────────────────────────────────────
# In lstm.py you wrote the train/eval loop manually.
# Lightning handles: device placement, gradient zeroing, loss.backward(),
# optimizer.step(), and evaluation — all automatically.

def train_model(model, train_loader, val_loader):
    trainer = pl.Trainer(
        max_epochs=MAX_EPOCHS,
        gradient_clip_val=0.1,   # IMPORTANT: attention layers are unstable without this
        enable_progress_bar=True,
        logger=False,
        enable_checkpointing=False,
        accelerator="gpu",
        devices=1,
    )
    trainer.fit(model, train_dataloaders=train_loader, val_dataloaders=val_loader)
    return trainer


# ── Prediction ─────────────────────────────────────────────────────────────────
# Replaces predict_now() from lstm.py.
# Key difference: returns a range (p10, p50, p90) per spot, not a single float.

def predict_now(model, inference_loader) -> dict:
    # mode="quantiles" returns tensor of shape [num_spots, prediction_steps, num_quantiles]
    predictions = model.predict(inference_loader, mode="quantiles")

    results = {}
    for spot_idx in range(NUM_SPOTS):
        spot_name = f"spot_{spot_idx + 1}"

        # Last prediction step = 30 min ahead
        # Quantile order matches QUANTILES = [0.1, 0.25, 0.5, 0.75, 0.9]
        p10 = float(predictions[spot_idx, -1, 0])
        p50 = float(predictions[spot_idx, -1, 2])  # median
        p90 = float(predictions[spot_idx, -1, 4])

        spread = p90 - p10
        if spread < 0.3:
            confidence = "Pretty reliable"
        elif spread < 0.6:
            confidence = "Rough estimate"
        else:
            confidence = "Hard to say"

        results[spot_name] = {
            "best_guess":  round(p50, 3),
            "lower_bound": round(p10, 3),
            "upper_bound": round(p90, 3),
            "confidence":  confidence,
            "status":      "OCCUPIED" if p50 > 0.5 else "likely free",
        }

    return results
def test_at_hour(model, df_long, train_ds, hour: int, is_weekend: bool = False):
    """
    Simulates prediction at a specific hour so you can test busy vs quiet periods.
    Pulls ENCODER_LENGTH rows from the full dataset where the hour matches.
    
    Examples:
        test_at_hour(model, df_long, train_ds, hour=20, is_weekend=True)  # Saturday 8pm (peak)
        test_at_hour(model, df_long, train_ds, hour=10, is_weekend=False) # Weekday 10am
        test_at_hour(model, df_long, train_ds, hour=2,  is_weekend=False) # 2am (should be empty)
    """
    # Filter to rows matching the target hour and day type
    mask = (
        pd.to_datetime(df_long["timestamp"]).dt.hour == hour
    ) & (
        pd.to_datetime(df_long["timestamp"]).dt.dayofweek >= 5
        if is_weekend else
        pd.to_datetime(df_long["timestamp"]).dt.dayofweek < 5
    )

    matched = df_long[mask]
    if len(matched) == 0:
        print(f"No rows found for hour={hour}, weekend={is_weekend}")
        return

    # Grab a contiguous window ending at a matched timestamp
    # Find a time_idx where the hour matches, then take the preceding ENCODER_LENGTH rows
    target_time_idx = matched["time_idx"].iloc[len(matched) // 2]  # middle of dataset
    window = df_long[
      (df_long["time_idx"] >= target_time_idx - ENCODER_LENGTH) &
      (df_long["time_idx"] <= target_time_idx + PREDICTION_LENGTH)
  ]

    # Build inference dataset from this window
    test_ds = TimeSeriesDataSet.from_dataset(
        train_ds, window, predict=True, stop_randomization=True
    )
    test_loader = test_ds.to_dataloader(train=False, batch_size=NUM_SPOTS, num_workers=0)

    predictions = predict_now(model, test_loader)

    day_label = "Weekend" if is_weekend else "Weekday"
    print(f"\nCrowdmeter — {day_label} {hour:02d}:00\n")
    print(f"  {'Spot':<10} {'Status':<14} {'P10':>6} {'P50':>6} {'P90':>6}  Confidence")
    print("  " + "-" * 60)
    for spot, info in predictions.items():
        bar = "*" * int(info["best_guess"] * 20)
        print(
            f"  {spot:<10} {info['status']:<14} "
            f"{info['lower_bound']:>5.0%} {info['best_guess']:>5.0%} {info['upper_bound']:>5.0%}  "
            f"{info['confidence']}"
        )

# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}\n")

    # ── Load and prepare data
    print("Loading and reshaping data...")
    df = load_and_prepare("occupancy_data.csv")
    print(f"Long-format rows: {len(df):,}  |  Spots: {df['spot_id'].nunique()}")
    print(f"Time range: {df['timestamp'].min()} → {df['timestamp'].max()}\n")

    # ── Train / val split
    # Split on time_idx to avoid leakage — same fix as shuffle=False in lstm.py
    # Use the last 20% of timesteps as validation
    max_time_idx = df["time_idx"].max()
    split_idx    = int(max_time_idx * 0.8)

    train_df = df[df["time_idx"] <= split_idx]
    val_df   = df[df["time_idx"] >  split_idx]

    print(f"Train timesteps: 0 → {split_idx}")
    print(f"Val timesteps:   {split_idx+1} → {max_time_idx}\n")

    # ── Build datasets
    print("Building TimeSeriesDataSets...")
    train_ds = make_dataset(train_df, train=True)
    val_ds   = make_dataset(val_df,   train=False, training_dataset=train_ds)

    train_loader = train_ds.to_dataloader(train=True, batch_size=BATCH_SIZE, num_workers=0)
    val_loader = val_ds.to_dataloader(train=False, batch_size=BATCH_SIZE, num_workers=0)
    print(f"Train batches: {len(train_loader)}  |  Val batches: {len(val_loader)}\n")

    # ── Build model
    print("Building TFT model...")
    model = build_model(train_ds)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"Total parameters: {total_params:,}\n")

    # ── Train
    print(f"Training for {MAX_EPOCHS} epochs...\n")
    trainer = train_model(model, train_loader, val_loader)

    # ── Save
    torch.save(model.state_dict(), "parking_tft.pth")
    print("\nModel saved → parking_tft.pth")

    # ── Predict (crowdmeter equivalent)
    print("\nCrowdmeter (30-min prediction with uncertainty):\n")
    inference_ds = TimeSeriesDataSet.from_dataset(
        train_ds, val_df, predict=True, stop_randomization=True
    )
    inference_loader = inference_ds.to_dataloader(train=False, batch_size=BATCH_SIZE, num_workers=0)
    predictions = predict_now(model, inference_loader)
    for spot, info in predictions.items():
        lo  = info["lower_bound"]
        mid = info["best_guess"]
        hi  = info["upper_bound"]
        bar = "*" * int(mid * 20)
        print(
            f"  {spot}: [{lo:.0%} ←  {mid:.0%}  → {hi:.0%}]  "
            f"{bar:20s}  {info['status']:12s}  ({info['confidence']})"
        )
    test_at_hour(model, df, train_ds, hour=20, is_weekend=True)
    test_at_hour(model, df, train_ds, hour=10, is_weekend=False)
    test_at_hour(model, df, train_ds, hour=3,  is_weekend=False)