import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

for db_path in [r'C:\Projects\adham-agent\agent_memory.db', r'C:\Projects\adham-agent\workspace_data\adham_memory.db']:
    print('=== Checking DB:', db_path)
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        print('Tables:', tables)
        for t in tables:
            cnt = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            print(f"  Table {t}: {cnt} rows")
            if cnt > 0:
                cols = [d[0] for d in cur.execute(f"SELECT * FROM {t} LIMIT 1").description]
                print(f"    Columns: {cols}")
                rows = cur.execute(f"SELECT * FROM {t} ORDER BY rowid DESC LIMIT 15").fetchall()
                for r in rows:
                    print("    ---")
                    for col_name, val in zip(cols, r):
                        val_str = str(val)
                        if len(val_str) > 200:
                            val_str = val_str[:200] + "..."
                        print(f"      {col_name}: {val_str}")
        conn.close()
    except Exception as e:
        print('Error:', e)
