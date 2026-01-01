import pandas as pd
import sqlite3

# 1. Load the CSV (The Source)
df = pd.read_csv("training_log.csv")

# 2. Connect to the Database (The Destination)
# This creates a NEW file called 'arm_wrestling.db'
conn = sqlite3.connect("arm_wrestling.db")

# 3. The Magic Command
# 'if_exists="replace"' -> This solves your duplicate problem! 
# It deletes the old table and makes a fresh one every time you run this.
df.to_sql("training_logs", conn, if_exists="replace", index=False)

# 4. Check if it worked
print("Migration Complete! Here is the data inside SQL:")
print(pd.read_sql("SELECT * FROM training_logs LIMIT 5", conn))

conn.close()