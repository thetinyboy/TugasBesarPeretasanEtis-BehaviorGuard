from behaviorguard.db import init_db
from behaviorguard.model import train_model_from_db

if __name__ == "__main__":
    print("[train_model] Inisialisasi DB (jika belum)...")
    init_db()
    train_model_from_db()
