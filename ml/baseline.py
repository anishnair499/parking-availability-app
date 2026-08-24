"""
just averages what happened in each hour and split between
weekday and weekend. no learning. if it beats lstm consistently on real data,
ship this instead + it only needs 1 week of data cmopared to lstm's 3 weeks
"""

import numpy as np
import pandas as pd

from lstm import TARGET_COLS, add_time_features, resample_occupancy

def fit_baseline(df):
    d = df.copy()
    d["timestamp"] = pd.to_datetime(d["timestamp"])
    d["wknd"] = d["timestamp"].dt.dayofweek >= 5
    d["hour"] = d["timestamp"].dt.hour
    table = d.groupby(['wknd', "hour"])[TARGET_COLS].mean()
    prior = d[TARGET_COLS].mean()
    return table, prior

def baseline_predict(table, prior, timestamps):
    out = []
    for ts in pd.to_datetime(pd.Series(list(timestamps))):
        key = (bool(ts.dayofweek >= 5), int(ts.hour))
        row = table.loc[key] if key in table.index else prior
        out.append(np.asarray(row, dtype=float))
    return np.array(out)


def score(pred, actual):
    p = np.clip(np.asarray(pred, dtype=float), 1e-6, 1 - 1e-6)
    a = np.asarray(actual, dtype=float)
    return {
        "accuracy": float(((p>0.5) == a).mean()),
        "brier": float(((p-a) ** 2).mean()),
        "bce": float(-(a* np.log(p) + (1-a)* np.log(1-p)).mean())
        }

if __name__ == "__main__":  
    from pathlib import Path

    DATA_DIR = Path(__file__).parent
    df = add_time_features(resample_occupancy(pd.read_csv(DATA_DIR / "occupancy.csv")))

    split = int(len(df) * 0.8)
    train_df, test_df = df.iloc[:split], df.iloc[split:]
    table, prior = fit_baseline(train_df)
    pred = baseline_predict(table, prior, test_df["timestamp"])
    actual = test_df[TARGET_COLS].values

    print("baseline      ", score(pred,actual))
    flat = np.broadcast_to(train_df[TARGET_COLS].mean().values, actual.shape)
    print("constant     ", score(flat, actual))
