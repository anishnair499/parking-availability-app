import pandas as pd
import numpy as np
from datetime import datetime, timedelta

weekday_probs = [
    0.02, 0.01, 0.01, 0.01, 0.01, 0.02, # 12 - 5 am
    0.05, 0.10, 0.30, 0.40, 0.45, 0.50, # 6 - 11 am
    0.45, 0.40, 0.35, 0.38, 0.40, 0.50, # 12 - 5 PPPPPMMMMM
    0.70, 0.80, 0.85, 0.80, 0.65, 0.40, # 6 pm to 11 pm peek hours
]

weekend_probs = [
    0.05, 0.03, 0.02, 0.02, 0.02, 0.03,
    0.05, 0.10, 0.20, 0.35, 0.50, 0.55,
    0.60, 0.58, 0.55, 0.60, 0.65, 0.70,
    0.80, 0.85, 0.88, 0.82, 0.70, 0.50,
]

spot_bias = [0.05, -0.05, 0.1, -0.1, 0.0] # 5 spots some spots might be more popular than others

def gen_occup():
    np.random.seed(42)
    timestamps = pd.date_range(start="2026-07-15", end="2026-09-09", freq=f"{1}min")
    num_spots = 5
    prev = [0] * num_spots
    record = []

    for ts in timestamps:
        is_weekend = ts.weekday() >= 5
        base_probs = weekend_probs if is_weekend else weekday_probs
        row: dict[str, object] = {"timestamp": ts}

        for i in range(num_spots):
            p = base_probs[ts.hour] + spot_bias[i]
            p += 0.15 if prev[i] == 1 else -0.05
            p += np.random.normal(0,0.04)
            p = float(np.clip(p, 0.0, 1.0))
            occupied = int(np.random.random() < p)
            row[f"spot_{i+1}"] = occupied
            prev[i] = occupied
        
        record.append(row)

    df = pd.DataFrame(record)
    df.to_csv("occupancy_data.csv", index=False)
    print(f"Saved {len(df):,} rows -> occupancy_data.csv")
    return df

if __name__ == "__main__":
    gen_occup()
    