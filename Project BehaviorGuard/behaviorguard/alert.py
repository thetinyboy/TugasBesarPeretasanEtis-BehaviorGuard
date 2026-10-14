import os
import requests

# Token & chat ID diambil dari environment variable
TELEGRAM_BOT_TOKEN = os.environ.get("BG_TG_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("BG_TG_CHAT_ID")

def send_telegram_alert(event: dict):
    """
    Kirim alert ke Telegram ketika ada anomali.
    Event adalah dict dari collector.
    Kalau token / chat id belum di-set, fungsi ini akan skip (hanya print).
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[alert] BG_TG_TOKEN / BG_TG_CHAT_ID belum di-set, skip Telegram alert.")
        return

    try:
        cpu = float(event.get("cpu") or 0.0)
        mem = float(event.get("mem") or 0.0)
        io_r = float(event.get("io_read_kb") or 0.0)
        io_w = float(event.get("io_write_kb") or 0.0)
    except Exception:
        cpu = mem = io_r = io_w = 0.0

    text = (
        "🚨 *BehaviorGuard Alert* 🚨\n"
        f"Waktu (UTC): `{event.get('ts')}`\n"
        f"User       : `{event.get('username')}`\n"
        f"Process    : `{event.get('pname')}` (PID {event.get('pid')})\n"
        f"Exe        : `{event.get('exe')}`\n"
        f"CPU/Mem    : {cpu:.1f}% / {mem:.1f}%\n"
        f"IO R/W KB  : {io_r:.0f}/{io_w:.0f}\n"
        f"#Conns     : {event.get('num_conns')}\n"
        f"Kategori   : {event.get('exe_category')}\n"
        f"Skor AI    : {event.get('anomaly_score')}\n"
        f"Reason     : {event.get('reason')}\n"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }

    try:
        resp = requests.post(url, json=payload, timeout=5)
        if resp.status_code != 200:
            print("[alert] Gagal kirim Telegram:", resp.text)
    except Exception as e:
        print("[alert] Exception kirim Telegram:", e)
