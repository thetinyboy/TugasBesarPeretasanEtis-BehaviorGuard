from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BASE_DIR / "behaviorguard.db"
MODEL_PATH = BASE_DIR / "behaviorguard_model.pkl"

# Interval pengambilan data proses (detik)
COLLECT_INTERVAL_SECONDS = 10

# Direktori yang dianggap "system" (sederhana, bisa kamu sesuaikan)
SYSTEM_DIR_HINTS = [
    r"\\Windows\\",
    "/windows/",
    "/usr/",
    "/bin/",
    "/sbin/",
    "/lib/",
]

# Direktori yang dianggap lebih "riskan" (user / downloads / temp)
USER_RISKY_DIR_HINTS = [
    "Downloads",
    "Download",
    "Temp",
    "AppData",
    ".cache",
]
