import os
from datetime import datetime

import joblib
from sklearn.ensemble import IsolationForest

from .config import MODEL_PATH, SYSTEM_DIR_HINTS, USER_RISKY_DIR_HINTS
from .db import get_conn

# ----------------- Feature Engineering ----------------- #

def categorize_exe_path(exe_path: str) -> str:
    """
    Kategorikan lokasi executable:
    - system
    - user_risky (Downloads/Temp/AppData dsb)
    - other
    - unknown
    """
    if not exe_path:
        return "unknown"

    plow = exe_path.lower()

    for hint in SYSTEM_DIR_HINTS:
        if hint.lower() in plow:
            return "system"

    for hint in USER_RISKY_DIR_HINTS:
        if hint.lower() in plow:
            return "user_risky"

    return "other"

def exe_category_to_int(cat: str) -> int:
    mapping = {
        "system": 0,
        "other": 1,
        "user_risky": 2,
        "unknown": 3,
    }
    return mapping.get(cat, 3)

def build_feature_vector(row_dict: dict):
    """
    Ubah event mentah menjadi vektor fitur numerik untuk model AI.
    """
    exe_cat = categorize_exe_path(row_dict.get("exe") or "")
    is_system = 1 if exe_cat == "system" else 0

    cpu = float(row_dict.get("cpu") or 0.0)
    mem = float(row_dict.get("mem") or 0.0)
    io_read = float(row_dict.get("io_read_kb") or 0.0)
    io_write = float(row_dict.get("io_write_kb") or 0.0)
    num_conns = int(row_dict.get("num_conns") or 0)

    ts_str = row_dict.get("ts")
    try:
        dt = datetime.fromisoformat(ts_str)
        hour = dt.hour
    except Exception:
        hour = 0

    return [
        is_system,
        exe_category_to_int(exe_cat),
        cpu,
        mem,
        io_read,
        io_write,
        num_conns,
        hour,
    ]

# ----------------- Model Utilities ----------------- #

def load_model():
    if os.path.exists(MODEL_PATH):
        try:
            return joblib.load(MODEL_PATH)
        except Exception as e:
            print("[model] Gagal load model:", e)
            return None
    return None

def save_model(model):
    joblib.dump(model, MODEL_PATH)

def train_model_from_db():
    """
    Baca semua data dari DB (process_events),
    build fitur, latih IsolationForest, dan simpan model.
    """
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
        SELECT ts, pid, pname, exe, username, cpu, mem,
               io_read_kb, io_write_kb, num_conns, is_system, exe_category
        FROM process_events
        """)
        rows = c.fetchall()

    if not rows:
        print("[train_model] Tidak ada data di DB. Jalankan collector dulu.")
        return

    X = []
    for r in rows:
        row_dict = {
            "ts": r["ts"],
            "pid": r["pid"],
            "pname": r["pname"],
            "exe": r["exe"],
            "username": r["username"],
            "cpu": r["cpu"],
            "mem": r["mem"],
            "io_read_kb": r["io_read_kb"],
            "io_write_kb": r["io_write_kb"],
            "num_conns": r["num_conns"],
            "is_system": r["is_system"],
            "exe_category": r["exe_category"],
        }
        X.append(build_feature_vector(row_dict))

    print(f"[train_model] Melatih model dengan {len(X)} sample...")
    model = IsolationForest(
        n_estimators=100,
        contamination=0.01,   # asumsi -+1% anomali
        random_state=42,
    )
    model.fit(X) #melatih model berdasarkan semua fitur proses
    save_model(model)
    print(f"[train_model] Model disimpan ke {MODEL_PATH}")

def predict_anomaly(model, event_dict: dict):
    """
    Beri prediksi anomali untuk satu event.
    return: (score, is_anom)
      - score: float (semakin kecil biasanya semakin aneh)
      - is_anom: 1 = anomali, 0 = normal
    """
    if model is None:
        # kalau belum ada model, anggap semua normal
        return None, 0

    feat = build_feature_vector(event_dict)
    score = model.decision_function([feat])[0]
    pred = model.predict([feat])[0]  
    is_anom = 1 if pred == -1 else 0
    return float(score), is_anom
