import sqlite3

# Connect to a database named "test.db"
conn = sqlite3.connect("test.db")
print("Database connected!")

# Create the "Pen" (Cursor)
cursor = conn.cursor()

# This wipes the table clean before you add data
cursor.execute("DROP TABLE IF EXISTS gym_bros")

# 1. Create a Table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS gym_bros (
        name TEXT,
        bench_press_kg INT
    )
""")

# 2. Insert Data (Add a gym bro)
cursor.execute("INSERT INTO gym_bros VALUES ('Azaan', 100)")
cursor.execute("INSERT INTO gym_bros VALUES ('John', 80)")

# 3. Save the changes! (Crucial step)
conn.commit()

print("Data saved!")


# Run a SELECT query
response = cursor.execute("SELECT * FROM gym_bros")
# The waiter has the food, now 'fetchall' puts it on your table
data = response.fetchall()

print("Here is the data from SQL:")
print(data)