import numpy as np
import pandas as pd
import pytest
import torch

from lstm import (
    INPUT_DIM, HIDDEN_DIM, NUM_LAYERS, NUM_SPOTS, SEQ_LEN,
    RESAMPLE_FREQ_MIN, FEATURE_COLS, TARGET_COLS, OccupancyDataset, ParkingLSTM, 
    add_time_features, resample_occupancy, contiguous_blocks, window_starts, check_window,
)

def fake_df(minutes=600, start="2026-09-06 00:00"):
    ts = pd.date_range(start, periods=minutes, freq="1min")
    rng = np.random.default_rng(0)
    d = {"timestamp": ts}
    for i in range(1, NUM_SPOTS +1):
        d[f"spot_{i}"] = rng.integers(0,2, minutes)
    return pd.DataFrame(d)

def test_feature_cols_match_input_dim():
    assert len(FEATURE_COLS) == INPUT_DIM
    assert len(TARGET_COLS) == NUM_SPOTS

def test_resample_keeps_gaps_as_gaps():
    a = fake_df(60, "2026-09-06 00:00")
    b= fake_df(60, "2026-09-06 07:00")
    out = resample_occupancy(pd.concat([a,b], ignore_index=True))
    gaps = out["timestamp"].diff().dt.total_seconds().div(60).dropna()
    assert gaps.max() == RESAMPLE_FREQ_MIN, "grid should be even"
    assert out[TARGET_COLS].isna().any().any(), "the outage should still be nan"

def test_windows_dont_straddle_a_gap():
    a = fake_df(SEQ_LEN * 10, "2026-09-06 00:00")
    b = fake_df(SEQ_LEN * 10, "2026-09-07 00:00")
    out = add_time_features(resample_occupancy(pd.concat([a,b], ignore_index=True)))
    blocks = contiguous_blocks(out)
    assert len(blocks) >= 2, "should see 2 separate blocks"
    for i in window_starts(blocks):
        seg = out[TARGET_COLS].iloc[i : i + SEQ_LEN + 1]
        assert not seg.isna().any().any(), f"window at {i} runs through a gap"


def test_short_window_raises_instead_guess():
    # nn.lstm takes a 3 step window without complaining and returns a confident answer.
    #this has to be caught 

    with pytest.raises(ValueError):
        check_window(resample_occupancy(fake_df(30)))


def test_forward_pass_shape():
    out = add_time_features(resample_occupancy(fake_df(SEQ_LEN * 10)))
    ds = OccupancyDataset(out[FEATURE_COLS].values, out[TARGET_COLS].values)
    x, y = ds[0]
    assert x.shape == (SEQ_LEN, INPUT_DIM)
    assert y.shape == (NUM_SPOTS,)

    model = ParkingLSTM(INPUT_DIM, HIDDEN_DIM, NUM_LAYERS, NUM_SPOTS)
    with torch.no_grad():
        assert model(x.unsqueeze(0)).shape == (1, NUM_SPOTS)