import sqlite3

db_name = "arm_wrestling.db"
conn = sqlite3.connect(db_name)
cursor = conn.cursor()

# 1. Add 'User' column (For your friend)
try:
    cursor.execute("ALTER TABLE training_logs ADD COLUMN User TEXT")
    print("✅ User column added.")
except sqlite3.OperationalError:
    print("ℹ️ User column already exists.")

# 2. Add 'Notes' column (For Notion replacement)
try:
    cursor.execute("ALTER TABLE training_logs ADD COLUMN Notes TEXT")
    print("✅ Notes column added.")
except sqlite3.OperationalError:
    print("ℹ️ Notes column already exists.")

# 3. Set default user for existing data
cursor.execute("UPDATE training_logs SET User = 'Azaan' WHERE User IS NULL")
conn.commit()
conn.close()

print("🎉 Database successfully upgraded to Version 2.0!")