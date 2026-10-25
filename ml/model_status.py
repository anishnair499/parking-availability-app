from ingest import fmt_ts, get_db

def build_status(scores, data, trained_at):
    return {"serving": "lstm", "trainedAt": trained_at, "lstm": scores, "data": data}

def build_recent(stamps, probs, actual, spots, bucket_min, hours=24):
    step = 60 // bucket_min
    start = max(0, len(stamps) - hours * step)
    points = []
    for i in range(start, len(stamps), step):
        points.append({
            "t": fmt_ts(stamps[i]),
            "pred": [round(float(p),3) for p in probs[i]],
            "act": [int(a) for a in actual[i]],
        })
    return {"spots": spots, "points": points}

def publish_training(status, recent, run, run_id):
    from firebase_admin import firestore

    db = get_db()
    db.collection("models").document("status").set({**status, "baseline": firestore.DELETE_FIELD}, merge=True)
    db.collection("models").document("recent").set(recent)
    db.collection("trainingRuns").document(run_id).set(run)
    print(f"published models/status, models/recent and trainingRuns/{run_id}")