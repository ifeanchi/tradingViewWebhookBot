import sqlite3
import shutil
import os

DB_NAME = "signals.db"
BACKUP_NAME = "signals_backup_before_cleanup.db"

if not os.path.exists(DB_NAME):
    print(f"ERROR: {DB_NAME} not found.")
    exit()

shutil.copy(DB_NAME, BACKUP_NAME)
print(f"✓ Backup created: {BACKUP_NAME}")

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

cursor.execute("""
SELECT COUNT(*)
FROM signals
WHERE timeframe = '1'
""")

count = cursor.fetchone()[0]
print(f"\nFound {count} signal(s) on the 1-minute timeframe.")

if count == 0:
    print("Nothing to delete.")
    conn.close()
    exit()

cursor.execute("""
DELETE FROM signals
WHERE timeframe = '1'
""")

conn.commit()
print(f"✓ Deleted {count} signal(s).")

print("Optimizing database...")
cursor.execute("VACUUM")

conn.close()

print("\nDatabase cleanup completed.")