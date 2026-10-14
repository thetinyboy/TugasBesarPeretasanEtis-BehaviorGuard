from flask import Flask, render_template_string
from .db import get_conn, init_db

app = Flask(__name__)

INDEX_TEMPLATE = """
<!doctype html>
<title>BehaviorGuard Dashboard</title>
<h1>BehaviorGuard – AI Behavioral Monitor</h1>

<p>
  <a href="/events">Semua Event</a> |
  <a href="/anomalies">Hanya Anomali</a>
</p>

<hr>

<h2>Ringkasan</h2>
<ul>
  <li>Total event: {{ total_events }}</li>
  <li>Total anomali: {{ total_anomalies }}</li>
</ul>
"""

EVENTS_TEMPLATE = """
<!doctype html>
<title>Process Events</title>
<h1>Process Events (terbaru)</h1>
<p><a href="/">Kembali</a></p>

<table border="1" cellpadding="3" cellspacing="0">
  <tr>
    <th>Waktu (UTC)</th>
    <th>PID</th>
    <th>Nama</th>
    <th>Exe</th>
    <th>User</th>
    <th>CPU%</th>
    <th>Mem%</th>
    <th>IO R/W (KB)</th>
    <th>#Conns</th>
    <th>Cat</th>
    <th>Score</th>
    <th>Anom?</th>
    <th>Reason</th>
  </tr>
  {% for r in rows %}
  <tr>
    <td>{{ r["ts"] }}</td>
    <td>{{ r["pid"] }}</td>
    <td>{{ r["pname"] }}</td>
    <td><small>{{ r["exe"] }}</small></td>
    <td>{{ r["username"] }}</td>
    <td>{{ "%.1f"|format(r["cpu"] or 0) }}</td>
    <td>{{ "%.1f"|format(r["mem"] or 0) }}</td>
    <td>{{ "%.0f"|format(r["io_read_kb"] or 0) }}/{{ "%.0f"|format(r["io_write_kb"] or 0) }}</td>
    <td>{{ r["num_conns"] }}</td>
    <td>{{ r["exe_category"] }}</td>
    <td>{{ "%.4f"|format(r["anomaly_score"] or 0) if r["anomaly_score"] is not none else "" }}</td>
    <td style="color: {% if r["is_anomaly"] == 1 %}red{% else %}gray{% endif %};">
      {% if r["is_anomaly"] == 1 %}YES{% else %}no{% endif %}
    </td>
    <td><small>{{ r["reason"] }}</small></td>
  </tr>
  {% endfor %}
</table>
"""

ANOM_TEMPLATE = """
<!doctype html>
<title>Anomalies</title>
<h1>Process Events yang Ditandai Anomali</h1>
<p><a href="/">Kembali</a></p>

<table border="1" cellpadding="3" cellspacing="0">
  <tr>
    <th>Waktu (UTC)</th>
    <th>PID</th>
    <th>Nama</th>
    <th>Exe</th>
    <th>User</th>
    <th>CPU%</th>
    <th>Mem%</th>
    <th>IO R/W (KB)</th>
    <th>#Conns</th>
    <th>Cat</th>
    <th>Score</th>
    <th>Reason</th>
  </tr>
  {% for r in rows %}
  <tr>
    <td>{{ r["ts"] }}</td>
    <td>{{ r["pid"] }}</td>
    <td>{{ r["pname"] }}</td>
    <td><small>{{ r["exe"] }}</small></td>
    <td>{{ r["username"] }}</td>
    <td>{{ "%.1f"|format(r["cpu"] or 0) }}</td>
    <td>{{ "%.1f"|format(r["mem"] or 0) }}</td>
    <td>{{ "%.0f"|format(r["io_read_kb"] or 0) }}/{{ "%.0f"|format(r["io_write_kb"] or 0) }}</td>
    <td>{{ r["num_conns"] }}</td>
    <td>{{ r["exe_category"] }}</td>
    <td>{{ "%.4f"|format(r["anomaly_score"] or 0) if r["anomaly_score"] is not none else "" }}</td>
    <td><small>{{ r["reason"] }}</small></td>
  </tr>
  {% endfor %}
</table>
"""

@app.route("/")
def index():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) AS cnt FROM process_events")
        total_events = c.fetchone()["cnt"]

        c.execute("SELECT COUNT(*) AS cnt FROM process_events WHERE is_anomaly = 1")
        total_anomalies = c.fetchone()["cnt"]

    return render_template_string(
        INDEX_TEMPLATE,
        total_events=total_events,
        total_anomalies=total_anomalies,
    )

@app.route("/events")
def events():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
        SELECT * FROM process_events
        ORDER BY id DESC
        LIMIT 300
        """)
        rows = c.fetchall()
    return render_template_string(EVENTS_TEMPLATE, rows=rows)

@app.route("/anomalies")
def anomalies():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
        SELECT * FROM process_events
        WHERE is_anomaly = 1
        ORDER BY id DESC
        LIMIT 300
        """)
        rows = c.fetchall()
    return render_template_string(ANOM_TEMPLATE, rows=rows)

def run_webapp():
    init_db()
    app.run(host="0.0.0.0", port=5002, debug=False)

if __name__ == "__main__":
    run_webapp()
