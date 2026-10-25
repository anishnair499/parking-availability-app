import numpy as np
import pandas as pd
import pytest

from ingest import lot_timezone, load_csv
from lstm import (
    SEQ_LEN, check_enough_windows, check_no_gaps, data_summary, resample_occupancy, score, 
)
from model_status import build_recent, build_status

def test_loader_convert(tmp_path):
    f = tmp_path / "availability.csv"
    f.write_text(
        "timestamp,spot_1,spot_2\n"
        "2026-10-20 16:00:00+00:00,1,0\n"
        "2026-10-20 16:01:00.123456+00:00,0,1\n"
    )
    df = load_csv(f)
    want = pd.Timestamp("2026-10-20 16:00", tz ="UTC").tz_convert(lot_timezone).tz_localize(None)
    assert df["timestamp"].iloc[0] == want
    assert df["timestamp"].dt.tz is None
    assert len(df) == 2

def test_loader_names_missing_columns(tmp_path):
    f = tmp_path / "bad.csv"
    f.write_text("timestamp,spot_1\n2026-10-20 16:00:00+00:00,1\n")
    with pytest.raises(ValueError, match="spot_2"):
        load_csv(f)


def test_score_perfect_and_backwards():
    assert score([1, 0], [1, 0])["accuracy"] == 1.0
    assert score([0.9, 0.1], [0, 1])["accuracy"] == 0.0


def test_gap_in_newest_window_is_named():
    ts = pd.date_range("2026-10-20", periods=SEQ_LEN + 10, freq="5min")
    df = pd.DataFrame({"timestamp": ts, "spot_1": 1.0, "spot_2": 0.0})
    check_no_gaps(df)  # clean data passes
    df.loc[len(df) - 5, "spot_1"] = np.nan
    with pytest.raises(ValueError, match="gap"):
        check_no_gaps(df)


def test_data_summary_counts_the_hole():
    ts = pd.date_range("2026-10-20", periods=3 * 24 * 60, freq="1min")
    raw = pd.DataFrame({"timestamp": ts, "spot_1": 1, "spot_2": 0})
    # knock out 200 minutes in the middle so there is exactly one gap
    raw = raw.drop(index=range(1000, 1200)).reset_index(drop=True)
    summary = data_summary(raw, resample_occupancy(raw))
    assert summary["rows"] == 4120
    assert summary["gaps"] == 1
    assert summary["days"] == 3.0
    assert summary["lastReading"] == "2026-10-22 23:59"


def test_thin_data_stops_with_a_clear_message():
    with pytest.raises(ValueError, match="unbroken"):
        check_enough_windows([(0, 30)], 0, 0)
    check_enough_windows([(0, 3000)], 2000, 500)  # plenty of data passes


def test_status_has_no_baseline_and_no_T_in_dates():
    scores = {"accuracy": 0.9, "brier": 0.1, "bce": 0.3}
    data = {"rows": 10, "days": 1.0, "gaps": 0, "lastReading": "2026-10-25 10:00"}
    status = build_status(scores, data, "2026-10-25 10:05")
    assert status["serving"] == "lstm"
    assert "baseline" not in status
    assert status["lstm"]["accuracy"] == 0.9
    assert " " in status["trainedAt"] and "T" not in status["trainedAt"]


def test_recent_is_hourly_and_matches_what_the_tab_reads():
    stamps = list(pd.date_range("2026-10-20", periods=600, freq="5min"))
    probs = np.full((600, 2), 0.25)
    actual = np.zeros((600, 2))
    rec = build_recent(stamps, probs, actual, ["spot_1", "spot_2"], 5)
    pts = rec["points"]
    assert rec["spots"] == ["spot_1", "spot_2"]
    assert len(pts) == 24
    assert pts[0]["pred"] == [0.25, 0.25] and pts[0]["act"] == [0, 0]
    assert pd.to_datetime(pts[1]["t"]) - pd.to_datetime(pts[0]["t"]) == pd.Timedelta(hours=1)
    assert "T" not in pts[0]["t"]

def test_loader_drops_future_rows(tmp_path):
    f = tmp_path / "future.csv"
    now = pd.Timestamp.now(tz="UTC")
    lines = ["timestamp,spot_1,spot_2"]
    for d in (-1, 1):
        lines.append(f"{(now + pd.Timedelta(days=d)).isoformat()},1,0")
    f.write_text("\n".join(lines) + "\n")
    assert len(load_csv(f)) == 1

def test_split_uses_windows_not_rows():
    from lstm import split_windows

    # every usable window is in the last 20% of the rows, like sparse early data then one long stretch
    starts = list(range(9000, 10000))
    train, val = split_windows(starts, 12000)
    assert len(train) == 800 and len(val) == 200
    assert max(train) < min(val)