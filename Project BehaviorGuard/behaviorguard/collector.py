import time
from datetime import datetime

import psutil

from .config import COLLECT_INTERVAL_SECONDS
from .db import init_db, insert_event
from .model import load_model, predict_anomaly, categorize_exe_path
from .alert import send_telegram_alert

def build_reason_for_anomaly(event):
    """
    Bikin teks penjelasan sederhana: kenapa event ini mungkin dianggap anomali.
    Berdasarkan fitur yang kita punya.
    """
    reasons = []

    exe_cat = event.get("exe_category")
    cpu = float(event.get("cpu") or 0.0)
    mem = float(event.get("mem") or 0.0)
    io_r = float(event.get("io_read_kb") or 0.0)
    io_w = float(event.get("io_write_kb") or 0.0)
    num_conns = int(event.get("num_conns") or 0)

    # coba parse jam dari ts
    hour = 0
    ts_str = event.get("ts")
    try:
        dt = datetime.fromisoformat(ts_str)
        hour = dt.hour
    except Exception:
        pass

    # 1) Lokasi exe
    if exe_cat == "user_risky":
        reasons.append("Proses berjalan dari folder yang berisiko (Downloads/AppData/Temp).")
    elif exe_cat == "unknown":
        reasons.append("Lokasi executable tidak dikenal / tidak standar.")

    # 2) CPU / Mem tinggi
    if cpu > 50.0:
        reasons.append(f"Penggunaan CPU tinggi ({cpu:.1f}%).")
    if mem > 30.0:
        reasons.append(f"Penggunaan memori cukup besar ({mem:.1f}%).")

    # 3) IO write tinggi (indikasi banyak menulis file)
    if io_w > 10_000:  # > 10 MB tulisan kumulatif
        reasons.append(f"Menulis data ke disk dalam jumlah besar (~{io_w/1024:.1f} MB).")

    # 4) Banyak koneksi jaringan
    if num_conns >= 5:
        reasons.append(f"Memiliki banyak koneksi jaringan aktif ({num_conns} koneksi).")

    # 5) Jam aneh (misal 0-5 pagi)
    if 0 <= hour <= 5:
        reasons.append(f"Aktif pada jam dini hari ({hour}:00) yang jarang digunakan.")

    # Kalau list alasan kosong, kasih satu alasan generik
    if not reasons:
        reasons.append("Pola fitur proses berbeda dari aktivitas normal menurut model AI.")

    return " ".join(reasons)

def snapshot_processes(model=None):
    """
    Ambil snapshot semua proses yang sedang jalan dan simpan ke DB.
    Kalau ada model, setiap event akan diberi skor anomaly & alasan.
    """
    for proc in psutil.process_iter(
        attrs=["pid", "name", "exe", "username", "cpu_percent", "memory_percent"]
    ):
        try:
            info = proc.info
            pid = info.get("pid")
            pname = info.get("name") or ""
            exe = info.get("exe") or ""
            username = info.get("username") or ""

            cpu = float(info.get("cpu_percent") or 0.0)
            mem = float(info.get("memory_percent") or 0.0)

            io_read_kb = 0.0
            io_write_kb = 0.0
            num_conns = 0

            # IO counters
            try:
                io_counters = proc.io_counters()
                io_read_kb = (io_counters.read_bytes or 0) / 1024.0
                io_write_kb = (io_counters.write_bytes or 0) / 1024.0
            except Exception:
                pass

            # Network connections
            try:
                conns = proc.connections(kind="inet")
                num_conns = len(conns)
            except Exception:
                pass

            exe_cat = categorize_exe_path(exe)
            is_system = 1 if exe_cat == "system" else 0

            event = {
                "ts": datetime.utcnow().isoformat(),
                "pid": pid,
                "pname": pname,
                "exe": exe,
                "username": username,
                "cpu": cpu,
                "mem": mem,
                "io_read_kb": io_read_kb,
                "io_write_kb": io_write_kb,
                "num_conns": num_conns,
                "is_system": is_system,
                "exe_category": exe_cat,
            }

            score, is_anom = predict_anomaly(model, event)
            event["anomaly_score"] = score
            event["is_anomaly"] = is_anom

            # kalau anomali, bikin reason
            if is_anom == 1:
                reason = build_reason_for_anomaly(event)
                event["reason"] = reason
            else:
                event["reason"] = None

            insert_event(event)

            # ------ ALERT ------
            if is_anom == 1:
                print(f"[ALERT] Anomali: {event['pname']} (PID {event['pid']}), skor={score}")
                print("         Reason:", event["reason"])
                send_telegram_alert(event)

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

def run_collector():
    print("[collector] Inisialisasi DB...")
    init_db()

    print("[collector] Load model (jika ada)...")
    model = load_model()
    if model is None:
        print("[collector] Belum ada model. Semua event dianggap normal untuk sekarang.")
    else:
        print("[collector] Model berhasil di-load.")

    print(f"[collector] Mulai mengumpulkan data tiap {COLLECT_INTERVAL_SECONDS} detik...")
    while True:
        snapshot_processes(model)
        time.sleep(COLLECT_INTERVAL_SECONDS)

if __name__ == "__main__":
    run_collector()
