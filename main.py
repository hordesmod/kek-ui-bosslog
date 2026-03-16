import json
import sqlite3
import time
import os
import hashlib

DATA_DIR = "data"
DATA_LIMIT = 200

def load_player(name):
    h = hashlib.md5(name.lower().encode('utf-8')).hexdigest()
    filepath = os.path.join(DATA_DIR, h[0], h[1], f"{h}.json")
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # print(f"No data found for: {name}")
        return None

def save_json(data, filename):
    full_path = os.path.join(DATA_DIR, f"{filename}.json")
    folder = os.path.dirname(full_path)
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)
    with open(full_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, separators=(',', ':'))

def get_top(param, is_true=False):
    start = time.perf_counter()
    where = "WHERE duration > 60" if is_true else ""

    if param in ("kills", "deaths"):
        cols = "p.faction, p.class, p.name, t.v, t.d, t.a"
        agg = "COUNT(*)" if param == "kills" else f"SUM({param})"
        stats_sql = f"{agg} AS v, SUM(duration) AS d, SUM(active) AS a"
        
    elif param == "damage":
        # SQLite: MAX() will pull mind, maxd, and killid from the SAME row
        cols = "p.faction, p.class, p.name, t.v, t.a, t.b, t.killid"
        stats_sql = "MAX((mind + maxd) / 2) AS v, mind AS a, maxd AS b, killid"
    else:
        stats_sql = f"MAX({param}) AS v, killid"
        cols = "p.faction, p.class, p.name, t.v, t.killid"

    query = f'''
        SELECT {cols}
        FROM (
            SELECT playerid, {stats_sql}
            FROM log {where}
            GROUP BY playerid
            ORDER BY v DESC LIMIT {DATA_LIMIT}
        ) AS t
        JOIN player p ON p.playerid = t.playerid
        ORDER BY t.v DESC
    '''
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    print(f"{param:<10} | Filter: {str(is_true):<5} | Time: {time.perf_counter() - start:.4f}s")
    return rows

def get_population():
    start = time.perf_counter()
    query = f'''
        SELECT 
            strftime('%Y%m%d', l.time) AS day,
            COUNT(DISTINCT CASE WHEN p.faction = 0 THEN l.playerid END) AS f0,
            COUNT(DISTINCT CASE WHEN p.faction = 1 THEN l.playerid END) AS f1
        FROM log l
        JOIN player p ON l.playerid = p.playerid
        GROUP BY day
        ORDER BY day ASC;
    '''
    cursor.execute(query)
    rows = cursor.fetchall()
    
    print(f"{"population":<10} | Time: {time.perf_counter() - start:.4f}s")
    return rows

def save_global():
    cursor.execute("SELECT COUNT(*) FROM player")
    p_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*), MAX(killid) FROM log")
    l_count, last_id = cursor.fetchone()
    data = {
        "updated": int(time.time()),
        "stats": {
            "last_id": last_id or 0,
            "logs": l_count,
            "players": p_count
        },
        "data": {
            "dps":  get_top("dps"),
            "hps":  get_top("hps"),
            "mps":  get_top("mps"),
            "kills": get_top("kills"),
            "deaths": get_top("deaths"),
            "r_dps": get_top("dps", True),
            "r_hps": get_top("hps", True),
            "gs":   get_top("gs"),
            "damage":   get_top("damage"),
            "crit":   get_top("crit"),
            "haste":   get_top("haste"),
            "hp":   get_top("hp"),
            "mp":   get_top("mp"),
            "block":   get_top("block"),
            "defense":   get_top("defense"),
            "population": get_population(),
        }
    }
    save_json(data, "global")
    print("Global JSON updated.")

def save_all_personal():
    cursor.execute("SELECT playerid, name, faction, class as pclass FROM player")
    player_rows = cursor.fetchall()
    total = len(player_rows)
    print(f"{'TOTAL':<8} {'CNT':<8} {'PLAYER NAME':<20} {'ROWS':<5}")
    print("-" * 45)
    for cnt, (playerid, name, faction, pclass) in enumerate(player_rows, 1):
        cursor.execute('''
            SELECT 
                CAST(strftime('%Y%m%d', time) AS INTEGER) AS day,
                max(dps), max(hps), max(mps), max(gs),
                sum(duration), sum(deaths), max(mind), max(maxd), max(crit),
                max(haste), max(hp), max(mp), max(block), max(defense),
                COUNT(*)
            FROM log
            WHERE playerid = ?
            GROUP BY day
            ORDER BY day ASC
        ''', (playerid,))
        results = cursor.fetchall()

        data = {
            "p": [faction, pclass, name],
            "_": results
        }
        h = hashlib.sha256(name.lower().encode('utf-8')).hexdigest()
        filename = os.path.join(h[0], h[1], h)
        save_json(data, filename)
        print(f"{total:<8} {cnt:<8} {name[:20]:<20} {len(results):<5}", end="\r" if cnt < total else "\n")
    print(f"\nPersonal JSON updated for {total} players.\n")


####################################################################################
conn = sqlite3.connect('cache/data.db')
cursor = conn.cursor()

# cursor.execute('''SELECT name FROM player''')
# results = cursor.fetchall()
# names = list(next(zip(*results))) if results else []
# save_json(names, "name")
# exit()

save_all_personal()
save_global()

print(f"\nUpdate complete.")
