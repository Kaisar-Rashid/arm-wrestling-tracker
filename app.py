import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
from datetime import date, datetime, timedelta
import extra_streamlit_components as stx
import os
import time

# --- PAGE CONFIG ---
st.set_page_config(page_title="Arm Wrestling Tracker", page_icon="💪", layout="wide")

# --- AUTHENTICATION & COOKIE SETUP ---
def get_manager():
    return stx.CookieManager()

cookie_manager = get_manager()

# Initialize Session State
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = None

# --- 1. AUTO-LOGIN (CHECK COOKIE) ---
# We wait a split second for the cookie manager to load
time.sleep(0.1) 
cookie_user = cookie_manager.get(cookie="arm_wrestling_user")

if not st.session_state["logged_in"] and cookie_user:
    # Validate the cookie against our secrets
    if "passwords" in st.secrets and cookie_user in st.secrets["passwords"]:
        st.session_state["logged_in"] = True
        st.session_state["username"] = cookie_user
        st.success(f"Welcome back, {cookie_user}!")
        time.sleep(0.5) # Brief pause to show message
        st.rerun()

# --- 2. MANUAL LOGIN FUNCTION ---
def check_login(username, password):
    if "passwords" not in st.secrets:
        st.error("❌ Error: 'secrets.toml' file is missing or empty!")
        return

    if username in st.secrets["passwords"]:
        if st.secrets["passwords"][username] == password:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            
            # 🍪 SAVE THE COOKIE (Expires in 30 days)
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
    st.title("🔒 Arm Wrestling Tracker")
    
    with st.form("login_form"):
        user_input = st.text_input("Username")
        pass_input = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            check_login(user_input, pass_input)
    
    st.stop() # 🛑 APP STOPS HERE IF NOT LOGGED IN

# =========================================================
#  ✅ MAIN APP STARTS HERE (Only runs if logged in)
# =========================================================

st.title("Arm Wrestling Training Log")

# --- CONFIGURATION ---
GOOGLE_SHEET_NAME = "Arm Wrestling Data"

# MAP SPECIFIC LIFTS TO BROAD CATEGORIES
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

# --- EXERCISE LISTS ---
# 1. Friends
exercises_rahil = ["Squat", "Deadlift", "Leg Press", "Calf Raises"]
exercises_azaan = ["Bicep Curls", "Hammer Curls", "Lat Pulldowns", "Rows"]

# 2. Kaisar's Standard Days
exercises_upper = ["Smith Bench", "Row", "Cable Chest Flies", "Narrow Pulldown", "Lateral Raises", "JM Press", "Reverse Pec Dec", "Tricep Extension", "Shoulder Press", "Incline Dumbbell Press"]
exercises_abs = ["Crunches", "Knee Raises"]

# 3. Kaisar's Arm Wrestling Days
exercises_tue = ["Index Knuckle Pronation", "Heavy Wrist Wrench", "Low Multi-Spinner", "Finger Containment (Static)", "Volume Side Pressure", "Volume Rising", "Volume Pronation"]
exercises_thu = ["Static Back Pressure", "Static Pronation", "Static Cupping"]
exercises_sat = ["Single-Loop Back Pressure", "Heavy Pronation Lift", "Heavy Riser", "High Cable Side Pressure", "Partial Curl", "Volume Cupping"]

# --- GOOGLE SHEETS CONNECTION ---

# --- DATABASE CONNECTION ---
def get_engine():
    try:
        db_url = st.secrets["connections"]["supabase"]["url"]
        return create_engine(db_url)
    except Exception as e:
        st.error(f"❌ Database Connection Error: {e}")
        st.stop()


# --- SIDEBAR: USER INFO ---
with st.sidebar:
    st.header("👤 Who is training?")
    
    # LOCK THE USER to the login name
    current_user = st.session_state["username"]
    st.info(f"Logged in as: **{current_user}**")

    # LOGOUT BUTTON
    if st.button("Log Out"):
        cookie_manager.delete("arm_wrestling_user")
        st.session_state["logged_in"] = False
        st.session_state["username"] = None
        st.rerun()

# --- SECTION 1: INPUT FORM ---
st.header(f"Log a Set for {current_user}")

# ONLY Show Day Filters for Kaisar
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
        
        # LOGIC FOR EXERCISE SELECTION
        if current_user == "Rahil":
            exercise_options = exercises_rahil
        elif current_user == "Azaan":
            exercise_options = exercises_azaan
        elif current_user == "Kaisar":
            if day_filter == "Tue (Heavy/Vol)":
                exercise_options = exercises_tue
            elif day_filter == "Thu (Statics)":
                exercise_options = exercises_thu
            elif day_filter == "Sat (Table Power)":
                exercise_options = exercises_sat
            elif day_filter == "Upper Body":
                exercise_options = exercises_upper
            elif day_filter == "Abs":
                exercise_options = exercises_abs
            else:
                exercise_options = exercises_tue + exercises_thu + exercises_sat + exercises_upper + exercises_abs
        else:
            # Fallback for Friend
            exercise_options = ["Pushups", "Squats"]
                
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
            # 1. Connect to the database
            engine = get_engine()
            
            # 2. The SQL Command (The "Order")
            # We use :parameters to safely pass data (prevents hacking)
            sql_query = text("""
                INSERT INTO workouts (date, exercise, weight, sets, reps, rpe, username, notes, bodyweight)
                VALUES (:date, :exercise, :weight, :sets, :reps, :rpe, :username, :notes, :bodyweight)
            """)
            
            # 3. The Data Packet
            data = {
                "date": d,
                "exercise": exercise,
                "weight": weight,
                "sets": sets,
                "reps": reps,
                "rpe": rpe,
                "username": current_user,  # Note: DB column is 'username', not 'User'
                "notes": notes,
                "bodyweight": Bodyweight
            }

            # 4. Execute
            with engine.connect() as conn:
                conn.execute(sql_query, data)
                conn.commit()
                
            st.success(f"✅ Saved to Cloud SQL: {exercise} ({weight}kg)")
            time.sleep(1)
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Save Failed: {e}")


# --- SECTION 2: DASHBOARD ---
st.divider()

try:
    engine = get_engine()
    # Read the entire table
    df = pd.read_sql("SELECT * FROM workouts", engine)
    
    # ✅ FIX: Rename ALL lowercase SQL columns to Capitalized style
    df = df.rename(columns={
        "date": "Date",
        "exercise": "Exercise",  # <--- This was missing!
        "weight": "Weight_kg",
        "sets": "Sets",
        "reps": "Reps",
        "rpe": "RPE",           # <--- This was likely missing too
        "username": "User",
        "notes": "Notes",
        "bodyweight": "Bodyweight"
    })
except Exception as e:
    st.error(f"❌ Error loading data: {e}")
    st.stop()

# Filter Data for Current User
if "User" in df.columns:
    df = df[df["User"] == current_user]
else:
    df = pd.DataFrame()

if not df.empty:
    df["Category"] = df["Exercise"].map(CATEGORY_MAP).fillna("Other")
    df["Date"] = pd.to_datetime(df["Date"])
    df["Display_Date"] = df["Date"].dt.strftime('%Y-%m-%d')
    df["Weight_kg"] = pd.to_numeric(df["Weight_kg"], errors='coerce').fillna(0)
    df["Sets"] = pd.to_numeric(df["Sets"], errors='coerce').fillna(0)
    df["Reps"] = pd.to_numeric(df["Reps"], errors='coerce').fillna(0)
    df["Bodyweight"] = pd.to_numeric(df["Bodyweight"],errors='coerce').fillna(0)
    df["Volume_kg"] = df["Sets"] * df["Reps"] * df["Weight_kg"]
    
    st.subheader(f"🏆 {current_user}'s Trophy Room (PRs)")
    best_lifts = df.groupby("Exercise")["Weight_kg"].max().reset_index().sort_values(by="Weight_kg", ascending=False)
    st.dataframe(best_lifts, hide_index=True, use_container_width=True)

    # Tabs
    tabs_list = ["➕ Log Workout", "📊 Progress", "📅 History", "📉 RPE", "⚖️ Bodyweight"]
    if current_user == "Kaisar":
        tabs_list.append("🛠️ Manage Data")

    all_tabs = st.tabs(tabs_list)
    
    # We unpack safely based on length
    tab1 = all_tabs[0]
    tab2 = all_tabs[1]
    tab3 = all_tabs[2]
    tab4 = all_tabs[3]
    tab6 = all_tabs[4] # Bodyweight
    
    if current_user == "Kaisar":
        tab5 = all_tabs[5]

    with tab1:
        target_exercise = st.selectbox("Select Exercise:", df["Exercise"].unique())
        strength_data = df[df["Exercise"] == target_exercise]
        st.line_chart(strength_data.groupby("Display_Date")["Weight_kg"].max())
    with tab2:
        st.bar_chart(df.groupby("Display_Date")["Volume_kg"].sum())
    with tab3:
        st.subheader("Style Split")
        fig = px.pie(df.groupby("Category")["Sets"].sum().reset_index(), values='Sets', names='Category', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
    with tab4:
        if "Notes" in df.columns:
            notes_df = df[df["Notes"] != ""][["Display_Date", "Exercise", "Weight_kg", "Notes"]]
            st.dataframe(notes_df, hide_index=True, use_container_width=True)
            
    # Bodyweight Tab
    with tab6: 
         st.line_chart(df.groupby("Display_Date")["Bodyweight"].mean())

    if current_user == "Kaisar":
        with tab5:
            st.subheader("🛠️ Manage Data")
            manage_df = df.copy() 
            manage_df["Sheet_Row_Number"] = range(2, 2 + len(manage_df))
            st.dataframe(manage_df[["Sheet_Row_Number", "Display_Date", "Exercise", "Weight_kg","Bodyweight", "Notes"]].sort_values("Sheet_Row_Number", ascending=False), 
            hide_index=True, use_container_width=True)
            st.warning("⚠️ Deleting is permanent!")
            col_del_1, col_del_2 = st.columns([1, 2])
            with col_del_1:
                row_to_delete = st.number_input("Row Number to Delete", min_value=2, step=1)
            with col_del_2:
                st.write("##")
                if st.button("🗑️ Delete Entry"):
                    try:
                        sheet.delete_rows(int(row_to_delete))
                        st.success(f"✅ Deleted Row {row_to_delete}!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
else:
    st.info(f"Welcome {current_user}! Start logging above.")