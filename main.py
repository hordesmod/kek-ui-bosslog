import os
import sqlite3
import zipfile
import time
import json
import requests
import hashlib

# --- Configuration ---
CACHE_DIR = "cache"
DATA_DIR = "data"
DB_PATH = os.path.join(CACHE_DIR, "data.sqlite")
SEED_ZIP = os.path.join(CACHE_DIR, "data.zip")
README_PATH = "README.md"
API_URL = "https://hordes.io/api/pve/getbosskillplayerlogs"
DATA_LIMIT = 200
RATE_LIMIT = 0.2

# Global tracker for incremental updates
updated_players = set()

def log_to_readme(message, limit=15, quiet=False):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    full_line = f"[{timestamp} UTC] {message}"
    print(full_line)

    if not os.path.exists(README_PATH): return
    with open(README_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    start_m, end_m = "<!-- LOGS_START -->", "<!-- LOGS_END -->"
    if start_m in content and end_m in content:
        parts = content.split(start_m)
        suffix_parts = parts[1].split(end_m)
        inner, suffix = suffix_parts[0], suffix_parts[1]
        
        lines = [l for l in inner.strip().split('\n') if '```' not in l and l.strip()]
        if quiet and lines:
            lines[0] = lines[0] + "."
        else:
            lines = [full_line] + lines
            
        final_logs = "\n".join(lines[:limit])
        new_content = f"{parts[0]}{start_m}\n```text\n{final_logs}\n```\n{end_m}{suffix}"
        with open(README_PATH, 'w', encoding='utf-8') as f: f.write(new_content)

class DatabaseManager:
    def __init__(self):
        self.conn = self.init_db()
        self.cursor = self.conn.cursor()

    def init_db(self):
        if not os.path.exists(CACHE_DIR): os.makedirs(CACHE_DIR)
        if not os.path.exists(DB_PATH) and os.path.exists(SEED_ZIP):
            log_to_readme("Extracting seed database...")
            with zipfile.ZipFile(SEED_ZIP, 'r') as z: z.extractall(CACHE_DIR)

        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("CREATE TABLE IF NOT EXISTS player (playerid INTEGER PRIMARY KEY, name TEXT, faction INTEGER, class INTEGER)")
        conn.execute('''CREATE TABLE IF NOT EXISTS log (
            playerid INTEGER, killid INTEGER, dps REAL, hps REAL, mps REAL, gs INTEGER, 
            duration INTEGER, active INTEGER, deaths INTEGER, mind INTEGER, maxd INTEGER, 
            crit REAL, haste REAL, hp INTEGER, mp INTEGER, block REAL, defense REAL, time TEXT,
            UNIQUE(playerid, killid))''')
        conn.execute("CREATE INDEX IF NOT EXISTS full_coverage ON log (playerid, killid, dps, hps, mps, gs, duration, active, deaths, mind, maxd, crit, haste, hp, mp, block, defense, time)")
        conn.commit()
        return conn

    def insert_logs(self, logs):
        for item in logs:
            self.cursor.execute("INSERT OR REPLACE INTO player (playerid, name, faction, class) VALUES (?, ?, ?, ?)",
                (item['playerid'], item['name'], item['faction'], item['class']))
            
            s = item.get('stats', [])
            if not isinstance(s, list): s = []
            s += [0] * (8 - len(s))
            
            self.cursor.execute("""INSERT OR IGNORE INTO log 
                (playerid, killid, dps, hps, mps, gs, duration, active, deaths, mind, maxd, crit, haste, hp, mp, block, defense, time)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (item['playerid'], item['killid'], item['dps'], item['hps'], item['mps'], item['gs'], 
                 item['duration'], item['active'], item['deaths'], s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7], item['time']))
            updated_players.add(item['playerid'])
        self.conn.commit()

    def get_last_killid(self):
        res = self.cursor.execute("SELECT MAX(killid) FROM log").fetchone()
        return res[0] if res and res[0] else 0

def fetch_updates(db):
    session = requests.Session()
    current_id = db.get_last_killid() or 1
    log_to_readme(f"Resuming from ID: {current_id}")
    
    empty_streak = 0
    while empty_streak < 2:
        try:
            start_time = time.time()
            resp = session.post(API_URL, json={"killid": current_id, "sort": "dps"}, timeout=15)
            if resp.status_code == 404:
                empty_streak += 1; current_id += 1; continue
            if resp.status_code != 200: break

            try: data = resp.json()
            except: current_id += 1; continue

            if data and isinstance(data, list):
                db.insert_logs(data)
                log_to_readme(f"ID: {current_id}", quiet=(current_id % 5 != 0))
                if len(data) == 100:
                    for cid in [0, 1, 2, 3]:
                        time.sleep(RATE_LIMIT)
                        c_data = session.post(API_URL, json={"killid": current_id, "classid": cid}).json()
                        if c_data: db.insert_logs(c_data)
                empty_streak = 0
            else: empty_streak += 1
            current_id += 1
            time.sleep(max(0, RATE_LIMIT - (time.time() - start_time)))
        except Exception as e:
            log_to_readme(f"Error at {current_id}: {e}"); break

def save_json(data, filename):
    full_path = os.path.join(DATA_DIR, f"{filename}.json")
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, separators=(',', ':'))

def get_top(cursor, param, is_true=False):
    where = "WHERE duration > 60" if is_true else ""
    tox = "CASE WHEN MAX(time) >= date('now', '-14 days') THEN 1 ELSE 0 END AS tox"
    if param in ("kills", "deaths"):
        cols = "p.faction, p.class, p.name, t.v, t.d, t.a, t.tox"
        agg = "COUNT(*)" if param == "kills" else "SUM(deaths)"
        stats_sql = f"{agg} AS v, SUM(duration) AS d, SUM(active) AS a, {tox}"
    elif param == "damage":
        cols, stats_sql = "p.faction, p.class, p.name, t.v, t.a, t.b, t.killid, t.tox", f"MAX((mind + maxd) / 2) AS v, mind AS a, maxd AS b, killid, {tox}"
    else:
        cols, stats_sql = "p.faction, p.class, p.name, t.v, t.killid, t.tox", f"MAX({param}) AS v, killid, {tox}"
    query = f"SELECT {cols} FROM (SELECT playerid, {stats_sql} FROM log {where} GROUP BY playerid ORDER BY v DESC LIMIT {DATA_LIMIT}) AS t JOIN player p ON p.playerid = t.playerid ORDER BY t.v DESC"
    return cursor.execute(query).fetchall()

def get_population(cursor):
    query = '''SELECT strftime('%Y%m%d', l.time) AS day,
               COUNT(DISTINCT CASE WHEN p.faction = 0 THEN l.playerid END) AS f0,
               COUNT(DISTINCT CASE WHEN p.faction = 1 THEN l.playerid END) AS f1
               FROM log l JOIN player p ON l.playerid = p.playerid GROUP BY day ORDER BY day ASC'''
    return cursor.execute(query).fetchall()

def save_global(db):
    params = ["dps", "hps", "mps", "kills", "deaths", "gs", "damage", "crit", "haste", "hp", "mp", "block", "defense"]
    l_c, p_c, lid = db.cursor.execute("SELECT (SELECT COUNT(*) FROM log), (SELECT COUNT(*) FROM player), (SELECT MAX(killid) FROM log)").fetchone()
    data = {"updated": int(time.time()), "stats": {"logs": l_c, "players": p_c, "last_id": lid}, "data": {p: get_top(db.cursor, p) for p in params}}
    data["data"]["r_dps"] = get_top(db.cursor, "dps", True)
    data["data"]["r_hps"] = get_top(db.cursor, "hps", True)
    data["data"]["population"] = get_population(db.cursor)
    save_json(data, "global")
    log_to_readme("Update globals.")

def save_personal_incremental(db):
    if not updated_players: return
    log_to_readme(f"Saving {len(updated_players)} modified players...")
    for pid in updated_players:
        p_info = db.cursor.execute("SELECT name, faction, class FROM player WHERE playerid = ?", (pid,)).fetchone()
        if not p_info: continue
        name, faction, pclass = p_info
        res = db.cursor.execute("SELECT CAST(strftime('%Y%m%d', time) AS INTEGER) as d, max(dps), max(hps), max(mps), max(gs), sum(duration), sum(deaths), max(mind), max(maxd), max(crit), max(haste), max(hp), max(mp), max(block), max(defense), COUNT(*) FROM log WHERE playerid = ? GROUP BY d ORDER BY d ASC", (pid,)).fetchall()
        h = hashlib.sha256(name.lower().encode('utf-8')).hexdigest()
        save_json({"p": [faction, pclass, name], "_": res}, os.path.join(h[0], h[1], h))

if __name__ == "__main__":
    db_m = DatabaseManager()
    fetch_updates(db_m)
    save_global(db_m)
    save_personal_incremental(db_m)
    log_to_readme("Sync finished.")
    db_m.conn.execute("PRAGMA wal_checkpoint(FULL)")
    db_m.conn.close()
