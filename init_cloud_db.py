import streamlit as st
from sqlalchemy import create_engine, text

# 1. Get the connection string from secrets
try:
    db_url = st.secrets["connections"]["supabase"]["url"]
except Exception:
    print("❌ Error: Could not find database URL in secrets.toml")
    exit()

# 2. Connect to Supabase
engine = create_engine(db_url)

# 3. The Blueprint
create_table_sql = """
CREATE TABLE IF NOT EXISTS workouts (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    exercise TEXT NOT NULL,
    weight FLOAT,
    sets INTEGER,
    reps INTEGER,
    rpe INTEGER,
    username TEXT,
    notes TEXT,
    bodyweight FLOAT
);
"""

# 4. Execute
try:
    with engine.connect() as conn:
        conn.execute(text(create_table_sql))
        conn.commit()
    print("✅ SUCCESS! Cloud Table 'workouts' created.")
except Exception as e:
    print(f"❌ FAILED: {e}")