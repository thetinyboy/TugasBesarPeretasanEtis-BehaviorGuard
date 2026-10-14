import sqlite3
from contextlib import contextmanager
from .config import DB_PATH

@contextmanager
def get_conn():
    # row_factory = sqlite3.Row supaya bisa akses dengan index *atau* nama kolom
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS process_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT,
            pid INTEGER,
            pname TEXT,
            exe TEXT,
            username TEXT,
            cpu REAL,
            mem REAL,
            io_read_kb REAL,
            io_write_kb REAL,
            num_conns INTEGER,
            is_system INTEGER,
            exe_category TEXT,
            anomaly_score REAL,
            is_anomaly INTEGER,
            reason TEXT
        )
        """)
        conn.commit()

def insert_event(event: dict):
    """
    Menyimpan satu event proses ke tabel process_events.
    """
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
        INSERT INTO process_events
        (ts, pid, pname, exe, username, cpu, mem,
         io_read_kb, io_write_kb, num_conns,
         is_system, exe_category, anomaly_score, is_anomaly, reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event["ts"],
            event["pid"],
            event["pname"],
            event["exe"],
            event["username"],
            event["cpu"],
            event["mem"],
            event["io_read_kb"],
            event["io_write_kb"],
            event["num_conns"],
            event["is_system"],
            event["exe_category"],
            event.get("anomaly_score"),
            event.get("is_anomaly"),
            event.get("reason"),
        ))
        conn.commit()
