# quick test to make sure the sliding window is actually sliding lol
# run with pytest from the repo root, or `python test_predictweek.py` from inside ml/ to see the crowdmeter printout

import numpy as np
import pandas as pd
import torch

from lstm import ParkingLSTM, INPUT_DIM, HIDDEN_DIM, NUM_LAYERS, NUM_SPOTS, SEQ_LEN, RESAMPLE_FREQ_MIN
from predict_week import forecast_week


def make_forecast():
    rng = np.random.default_rng(0)
    torch.manual_seed(0)
    # need enough raw 1 min rows so that after resampling to 5 min buckets we still have SEQ_LEN rows
    # +5 is just extra buffer so resample doesnt drop us below SEQ_LEN
    n_raw_rows = (SEQ_LEN + 5) * RESAMPLE_FREQ_MIN
    timestamps = pd.date_range("2026-07-20", periods=n_raw_rows, freq="1min")

    df = pd.DataFrame({"timestamp": timestamps})
    for i in range(1, NUM_SPOTS + 1):
        df[f"spot_{i}"] = rng.integers(0, 2, size=n_raw_rows)

    device = torch.device("cpu")
    model = ParkingLSTM(INPUT_DIM, HIDDEN_DIM, NUM_LAYERS, NUM_SPOTS).to(device)
    model.eval()
    # random untrained weights on purpose. this only checks the window moves forward, not accuracy
    return forecast_week(model, df, device)


def test_window_slides():
    forecast = make_forecast()

    expected_steps = 7 * 24 * 60 // RESAMPLE_FREQ_MIN
    assert len(forecast) == expected_steps, f"expected {expected_steps} rows but got {len(forecast)}"

    # timestamps should be exactly RESAMPLE_FREQ_MIN apart
    ts_out = [pd.to_datetime(row["timestamp"]) for row in forecast]
    for i in range(len(ts_out) - 1):
        gap = (ts_out[i + 1] - ts_out[i]).total_seconds() / 60
        assert gap == RESAMPLE_FREQ_MIN, f"timestamp gap is wrong at step {i}: {gap}"

    # probs go through a sigmoid so they have to stay in [0, 1]
    for row in forecast:
        for i in range(1, NUM_SPOTS + 1):
            key = f"spot_{i}"
            assert key in row, f"where did {key} go??"
            assert 0.0 <= row[key] <= 1.0, f"{key} is out of range: {row[key]}"

    # THE ACTUAL THING IM TRYING TO CATCH: if the window isnt sliding forward, every
    # step gives back the exact same numbers since its the same input every time
    sample = [
        [forecast[i][f"spot_{s}"] for s in range(1, NUM_SPOTS + 1)]
        for i in range(0, len(forecast), 50)
    ]
    unique = {tuple(row) for row in sample}
    assert len(unique) > 1, "window isnt moving"


def show_crowdmeter(forecast):
    # prints it like a crowdmeter instead of 2016 rows of numbers
    df_forecast = pd.DataFrame(forecast)
    df_forecast["timestamp"] = pd.to_datetime(df_forecast["timestamp"])

    print("\n=== RIGHT NOW ===")
    now_row = forecast[0]
    for i in range(1, NUM_SPOTS + 1):
        p = now_row[f"spot_{i}"]
        filled = int(p * 10)
        bar = "#" * filled + "-" * (10 - filled)
        status = "busy" if p > 0.5 else "probably open"
        print(f"spot {i}: [{bar}] {p:.0%}  ({status})")

    # buckets match the 12am/6am/12pm/6pm labels from the crowdmeter pic
    def bucket_label(hour):
        if hour < 6: return "12am"
        if hour < 12: return "6am"
        if hour < 18: return "12pm"
        return "6pm"

    df_forecast["day"] = df_forecast["timestamp"].dt.day_name().str[:2].str.upper()
    df_forecast["bucket"] = df_forecast["timestamp"].dt.hour.apply(bucket_label)

    day_order = ["SU", "MO", "TU", "WE", "TH", "FR", "SA"]
    bucket_order = ["12am", "6am", "12pm", "6pm"]

    print("\n=== THIS WEEK ===")
    for i in range(1, NUM_SPOTS + 1):
        col = f"spot_{i}"
        print(f"\n--- spot {i} ---")
        grid = df_forecast.groupby(["day", "bucket"])[col].mean().unstack()
        grid = grid.reindex(index=day_order, columns=bucket_order)
        for day in day_order:
            row_str = ""
            for bucket in bucket_order:
                val = grid.loc[day, bucket]
                if pd.isna(val):
                    row_str += "  .    "
                else:
                    dots = "*" * int(round(val * 5))  # up to 5 dots, like the app
                    row_str += f"{dots:6s} "
            print(f"{day}: {row_str}")
        print(f"     {'  '.join(f'{b:>6s}' for b in bucket_order)}")


if __name__ == "__main__":
    test_window_slides()
    print("passed - window is actually sliding forward now")
    show_crowdmeter(make_forecast())
