import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
from datetime import date, datetime, timedelta
import extra_streamlit_components as stx
import os
import time

# --- PAGE CONFIG ---
st.set_page_config(page_title="Workout Buddy", page_icon="💪", layout="wide")

# --- AUTHENTICATION & COOKIE SETUP ---
def get_manager():
    return stx.CookieManager()

cookie_manager = get_manager()

# Initialize Session State
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = None

# 🛑 SAFETY FLAG: Prevents "Login Loop"
if "logout_clicked" not in st.session_state:
    st.session_state["logout_clicked"] = False

# --- DATABASE CONNECTION ---
def get_engine():
    try:
        db_url = st.secrets["connections"]["supabase"]["url"]
        return create_engine(db_url)
    except Exception as e:
        st.error(f"❌ Database Connection Error: {e}")
        st.stop()

# --- FETCH EXERCISES FROM SQL (Dynamic List) ---
def get_exercises_from_db(user, category_filter=None):
    engine = get_engine()
    try:
        query_str = "SELECT name FROM exercise_library WHERE username = :user"
        params = {"user": user}
        
        if category_filter and category_filter != "All Exercises":
            query_str += " AND category = :cat"
            params["cat"] = category_filter
            
        with engine.connect() as conn:
            result = conn.execute(text(query_str), params)
            rows = result.fetchall()
            return [row[0] for row in rows]
            
    except Exception:
        return []

# --- 1. AUTO-LOGIN (CHECK COOKIE) ---
time.sleep(0.1) 
cookie_user = cookie_manager.get(cookie="arm_wrestling_user")

# THE FIX: We only auto-login if the user DID NOT just click logout
if not st.session_state["logged_in"] and cookie_user and not st.session_state["logout_clicked"]:
    if "passwords" in st.secrets and cookie_user in st.secrets["passwords"]:
        st.session_state["logged_in"] = True
        st.session_state["username"] = cookie_user
        st.success(f"Welcome back, {cookie_user}!")
        time.sleep(0.5)
        st.rerun()

# --- 2. MANUAL LOGIN FUNCTION ---
def check_login(username, password):
    if "passwords" not in st.secrets:
        st.error("❌ Error: 'secrets.toml' is missing!")
        return

    if username in st.secrets["passwords"]:
        if st.secrets["passwords"][username] == password:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            
            # RESET THE LOGOUT FLAG so they can login again!
            st.session_state["logout_clicked"] = False
            
            # 🍪 SAVE THE COOKIE
            expires = datetime.now() + timedelta(days=30)
            cookie_manager.set("arm_wrestling_user", username, expires_at=expires)
            
            st.success("Logged in!")
            time.sleep(0.5)
            st.rerun()
        else:
            st.error("❌ Incorrect Password")
    else:
        st.error("❌ User not found")

# --- 3. THE GATEKEEPER (LOGIN SCREEN) ---
if not st.session_state["logged_in"]:
    st.title("🔒Workout Buddy")
    with st.form("login_form"):
        user_input = st.text_input("Username")
        pass_input = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            check_login(user_input, pass_input)
    st.stop() 

# =========================================================
#  ✅ MAIN APP STARTS HERE
# =========================================================

st.title("Workout Log")

# CATEGORY MAP
CATEGORY_MAP = {
    "Index Knuckle Pronation": "Pronation",
    "Heavy Pronation Lift": "Pronation",
    "Static Back Pressure": "Back Pressure",
    "Single-Loop Back Pressure":"Back Pressure",
    "Cupping (Pulley)": "Cupping",
    "Low Multi-Spinner":"Cupping",
    "Volume Cupping":"Cupping",
    "Static Cupping":"Cupping",
    "Finger Containment (Static)": "Fingers",
    "Heavy Wrist Wrench": "Wrist",
    "Rising (Belt)": "Rising",
    "Volume Side Pressure": "Side Pressure",
    "Volume Rising": "Rising",
    "Static Pronation" :"Pronation",
    "Heavy Riser":"Rising",
    "High Cable Side Pressure":"Side Pressure",
    "Partial Curl":"Bicep" 
}

# --- SIDEBAR: USER INFO & LOGOUT ---
with st.sidebar:
    st.header("👤 Who is training?")
    current_user = st.session_state["username"]
    st.info(f"Logged in as: **{current_user}**")

    # LOGOUT BUTTON (The Fixed Version)
    if st.button("Log Out"):
        # 1. Overwrite cookie (Try to kill it)
        cookie_manager.set("arm_wrestling_user", "logged_out")
        
        # 2. Clear Session
        st.session_state["logged_in"] = False
        st.session_state["username"] = None
        
        # 3. SET THE STOP SIGN: Prevent Auto-Login on next run
        st.session_state["logout_clicked"] = True
        
        st.success("Logging out...")
        time.sleep(1)
        st.rerun()

# --- SECTION 1: INPUT FORM ---
st.header(f"Log a Set for {current_user}")

if current_user == "Kaisar":
    day_filter = st.radio(
        "⚡ Quick Select Day:", 
        ["All Exercises", "Tue (Heavy/Vol)", "Thu (Statics)", "Sat (Table Power)", "Upper Body", "Abs"], 
        horizontal=True
    )
else:
    day_filter = "All Exercises"

with st.form("workout_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        d = st.date_input("Date", date.today())
        
        db_category_map = {
            "Tue (Heavy/Vol)": "Tuesday",
            "Thu (Statics)": "Thursday", 
            "Sat (Table Power)": "Saturday",
            "Upper Body": "Upper Body",
            "Abs": "Abs"
        }
        
        selected_db_category = db_category_map.get(day_filter, None)
        exercise_options = get_exercises_from_db(current_user, selected_db_category)
        
        if not exercise_options:
            exercise_options = ["⚠️ No exercises found! Add some in 'Manage Data'."]

        exercise = st.selectbox("Exercise", exercise_options)
        Bodyweight = st.number_input("Bodyweight (kg)", min_value=0.0, step=0.5, value=70.0)
        
    with col2:
        weight = st.number_input("Weight (kg)", min_value=0.0, step=0.5)
        sets = st.number_input("Sets", min_value=1, step=1, value=3)
        reps = st.number_input("Reps", min_value=1, step=1, value=10)
        
    rpe = st.slider("RPE (Intensity)", 1, 10, 8)
    notes = st.text_input("📝 Notes (Optional)", placeholder="Form cue, pain check, etc.")
    submitted = st.form_submit_button("Save Workout")

    if submitted:
        try:
            engine = get_engine()
            sql_query = text("""
                INSERT INTO workouts (date, exercise, weight, sets, reps, rpe, username, notes, bodyweight)
                VALUES (:date, :exercise, :weight, :sets, :reps, :rpe, :username, :notes, :bodyweight)
            """)
            data = {
                "date": d, "exercise": exercise, "weight": weight, "sets": sets, 
                "reps": reps, "rpe": rpe, "username": current_user, "notes": notes, "bodyweight": Bodyweight
            }
            with engine.connect() as conn:
                conn.execute(sql_query, data)
                conn.commit()
                
            st.success(f"✅ Saved to Cloud SQL: {exercise} ({weight}kg)")
            time.sleep(1)
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Save Failed: {e}")


# --- SECTION 2: DASHBOARD ---
# --- SECTION 2: DASHBOARD ---
st.divider()

# 1. LOAD DATA
try:
    engine = get_engine()
    df = pd.read_sql("SELECT * FROM workouts", engine)
    
    # Standardize Column Names
    df = df.rename(columns={
        "date": "Date", "exercise": "Exercise", "weight": "Weight_kg",
        "sets": "Sets", "reps": "Reps", "rpe": "RPE", "username": "User",
        "notes": "Notes", "bodyweight": "Bodyweight"
    })
except Exception as e:
    st.error(f"❌ Error loading data: {e}")
    st.stop()

# 2. FILTER BY USER
if "User" in df.columns:
    df = df[df["User"] == current_user]
else:
    df = pd.DataFrame()

# 3. PROCESS DATA (Only if it exists)
if not df.empty:
    df["Category"] = df["Exercise"].map(CATEGORY_MAP).fillna("Other")
    df["Date"] = pd.to_datetime(df["Date"])
    df["Display_Date"] = df["Date"].dt.strftime('%Y-%m-%d')
    df["Weight_kg"] = pd.to_numeric(df["Weight_kg"], errors='coerce').fillna(0)
    df["Sets"] = pd.to_numeric(df["Sets"], errors='coerce').fillna(0)
    df["Reps"] = pd.to_numeric(df["Reps"], errors='coerce').fillna(0)
    df["Bodyweight"] = pd.to_numeric(df["Bodyweight"],errors='coerce').fillna(0)
    
    st.subheader(f"🏆 {current_user}'s Workspace")
    best_lifts = df.groupby("Exercise")["Weight_kg"].max().reset_index().sort_values(by="Weight_kg", ascending=False)
    st.dataframe(best_lifts, hide_index=True, use_container_width=True)
else:
    st.info(f"👋 Welcome, {current_user}! You haven't logged any workouts yet. Go to 'Manage Data' to add exercises, then log your first set!")

# 4. CREATE TABS (Always show these, even if data is empty!)
tabs_list = ["📈 Progress", "📅 History", "📚 Logbook", "⚖️ Bodyweight", "🛠️ Manage Data"]
all_tabs = st.tabs(tabs_list)
tab1, tab2, tab3, tab4, tab5 = all_tabs[0], all_tabs[1], all_tabs[2], all_tabs[3], all_tabs[4]

# --- TAB CONTENT ---

with tab1: # Progress
    if not df.empty:
        target_exercise = st.selectbox("Select Exercise:", df["Exercise"].unique())
        strength_data = df[df["Exercise"] == target_exercise]
        st.line_chart(strength_data.groupby("Display_Date")["Weight_kg"].max())
    else:
        st.write("Start training to see your strength curve here!")

with tab2: # History
    if not df.empty:
        st.dataframe(df.sort_values("Date", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.write("No history yet.")

with tab3: # Logbook
    st.subheader("📚 Training Logbook")
    if not df.empty:
        st.caption("Click a day to see your history.")
        df["Day_Name"] = df["Date"].dt.day_name()
        days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for day in days_order:
            day_data = df[df["Day_Name"] == day]
            if not day_data.empty:
                with st.expander(f"🗓️ {day} ({len(day_data)} logs)"):
                    st.dataframe(day_data.sort_values("Date", ascending=False)[["Display_Date", "Exercise", "Weight_kg", "Sets", "Reps", "Notes"]], use_container_width=True, hide_index=True)
    else:
        st.write("Your logs will be grouped by day here.")

with tab4: # Bodyweight
    if not df.empty:
        st.line_chart(df.groupby("Display_Date")["Bodyweight"].mean())
    else:
        st.write("Track your bodyweight to see it here.")

with tab5: # Manage Data (ALWAYS VISIBLE)
    st.subheader("🛠️ Manage Exercises")
    
    # 1. ADD EXERCISE FORM
    with st.expander("➕ Add New Exercise to Library"):
        with st.form("add_ex_form"):
            new_ex_name = st.text_input("Name (e.g. King's Move)")
            cat_options = ["Tuesday", "Thursday", "Saturday", "Upper Body", "Abs", "General"]
            new_ex_cat = st.selectbox("Category", cat_options)
            
            if st.form_submit_button("Add"):
                engine = get_engine()
                with engine.connect() as conn:
                    conn.execute(
                        text("INSERT INTO exercise_library (name, category, username) VALUES (:n, :c, :u)"),
                        {"n": new_ex_name, "c": new_ex_cat, "u": current_user}
                    )
                    conn.commit()
                st.success(f"Added {new_ex_name}!")
                time.sleep(1)
                st.rerun()

    st.divider()
    
    # 2. DELETE FORM (Only if data exists)
    st.subheader(f"🗑️ Delete {current_user}'s Logs")
    if not df.empty:
        manage_df = df.copy().sort_values("id", ascending=False)
        st.dataframe(manage_df[["id", "Date", "Exercise", "Weight_kg", "Notes"]], hide_index=True, use_container_width=True)
        
        col_del_1, col_del_2 = st.columns([1, 2])
        with col_del_1:
            row_to_delete = st.number_input("Enter ID to Delete", min_value=1, step=1)
        with col_del_2:
            st.write("##")
            if st.button("🗑️ Delete Entry"):
                try:
                    engine = get_engine()
                    with engine.connect() as conn:
                        query = text("DELETE FROM workouts WHERE id = :id AND username = :user")
                        result = conn.execute(query, {"id": row_to_delete, "user": current_user})
                        conn.commit()
                        if result.rowcount > 0:
                            st.success(f"✅ Deleted ID {row_to_delete}!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Invalid ID.")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
    else:
        st.write("No logs to delete yet.")