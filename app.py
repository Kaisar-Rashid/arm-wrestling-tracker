import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime
import gspread
import os  # <--- Make sure this is imported at the very top of your file!


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

# --- GOOGLE SHEETS CONNECTION (Modern Way) ---

def connect_to_sheet():
    # 1. DEFINE THE LOCAL FILE PATH DYNAMICALLY
    # This finds the folder where app.py is currently sitting
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(current_dir, "service_account.json")

    # 2. CHECK: DOES THE LOCAL FILE EXIST?
    if os.path.exists(json_file_path):
        # If the file is found locally, use it!
        client = gspread.service_account(filename=json_file_path)
    else:
        # 3. IF NOT FOUND LOCALLY, TRY SECRETS (For when we go Live)
        # This prevents the "No secrets found" error when working locally
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            client = gspread.service_account_from_dict(creds_dict)
        else:
            st.error("Could not find 'service_account.json' locally, and no Secrets found.")
            st.stop()

    # Open the sheet
    # Make sure this name MATCHES your Google Sheet name exactly
    sheet = client.open("Arm Wrestling Data").sheet1 
    return sheet

st.set_page_config(page_title="Arm Wrestling Tracker", page_icon="💪", layout="wide")
st.title("Arm Wrestling Training Log")

# --- SIDEBAR: USER SELECTION ---
with st.sidebar:
    st.header("👤 Who is training?")
    current_user = st.radio("Select User:", ["Kaisar", "Friend"])    

# --- SECTION 1: INPUT FORM ---
st.header(f"Log a Set for {current_user}")

# 1. SPEED PASS FILTER
day_filter = st.radio(
    "⚡ Quick Select Day:", 
    ["All Exercises", "Tue (Heavy/Vol)", "Thu (Statics)", "Sat (Table Power)"], 
    horizontal=True
)

# 2. THE MAIN FORM
with st.form("workout_form", clear_on_submit=True):
    col1, col2 = st.columns(2)

    # Column 1: Selection Logic
    with col1:
        d = st.date_input("Date", date.today())
        
        exercises_tue = [
            "Index Knuckle Pronation", "Heavy Wrist Wrench", "Low Multi-Spinner", 
            "Finger Containment (Static)", "Volume Side Pressure", "Volume Rising", "Volume Pronation"
        ]
        exercises_thu = [
            "Static Back Pressure", "Static Pronation", "Static Cupping"
        ]
        exercises_sat = [
            "Single-Loop Back Pressure", "Heavy Pronation Lift", "Heavy Riser", 
            "High Cable Side Pressure", "Partial Curl", "Volume Cupping"
        ]

        if current_user == "Friend":
            exercise_options = ["Bicep Curl", "Bench Press", "Squat", "Deadlift"]
        elif day_filter == "Tue (Heavy/Vol)":
            exercise_options = exercises_tue
        elif day_filter == "Thu (Statics)":
            exercise_options = exercises_thu
        elif day_filter == "Sat (Table Power)":
            exercise_options = exercises_sat
        else:
            exercise_options = exercises_tue + exercises_thu + exercises_sat
            
        exercise = st.selectbox("Exercise", exercise_options)
        
    # Column 2: The Numbers
    with col2:
        weight = st.number_input("Weight (kg)", min_value=0.0, step=0.5)
        sets = st.number_input("Sets", min_value=1, step=1, value=3)
        reps = st.number_input("Reps", min_value=1, step=1, value=10)
        
    # Bottom Section
    rpe = st.slider("RPE (Intensity)", 1, 10, 8)
    notes = st.text_input("📝 Notes (Optional)", placeholder="Form cue, pain check, etc.")
    
    # THE SUBMIT BUTTON
    submitted = st.form_submit_button("Save Workout")

    # 3. SAVE LOGIC
    if submitted:
        date_str = d.strftime("%Y-%m-%d")
        
        try:
            sheet = connect_to_sheet()
            # Order: Date, Exercise, Weight, Sets, Reps, RPE, User, Notes
            new_row = [date_str, exercise, weight, sets, reps, rpe, current_user, notes]
            sheet.append_row(new_row)
            
            st.success(f"✅ Added: {exercise} ({weight}kg)")
            import time
            time.sleep(1)
            st.rerun() 
        except Exception as e:
            st.error(f"❌ Failed to save to Google Sheets: {e}")

# --- SECTION 2: DASHBOARD ---
st.divider()

# --- FETCH DATA ---
try:
    sheet = connect_to_sheet()
    raw_data = sheet.get_all_records()
    df = pd.DataFrame(raw_data)
    
    if df.empty:
        df = pd.DataFrame(columns=["Date", "Exercise", "Weight_kg", "Sets", "Reps", "RPE", "User", "Notes"])
except Exception as e:
    st.error(f"❌ Error connecting to Google Sheets: {e}")
    st.stop()

# --- FILTER USER ---
if "User" in df.columns:
    df = df[df["User"] == current_user]
else:
    df = pd.DataFrame()

# --- PRE-PROCESSING ---
if not df.empty:
    # 1. Map Categories
    df["Category"] = df["Exercise"].map(CATEGORY_MAP).fillna("Other")
    
    # 2. Date Conversions
    df["Date"] = pd.to_datetime(df["Date"])
    df["Display_Date"] = df["Date"].dt.strftime('%Y-%m-%d')
    
    # 3. Calculate Stats
    df["Weight_kg"] = pd.to_numeric(df["Weight_kg"], errors='coerce').fillna(0)
    df["Sets"] = pd.to_numeric(df["Sets"], errors='coerce').fillna(0)
    df["Reps"] = pd.to_numeric(df["Reps"], errors='coerce').fillna(0)
    
    df["Volume_kg"] = df["Sets"] * df["Reps"] * df["Weight_kg"]
    df["e1RM"] = df["Weight_kg"] * (1 + (df["Reps"] / 30))

    # --- TAB 1: TROPHY ROOM ---
    st.subheader(f"🏆 {current_user}'s Trophy Room (PRs)")
    best_lifts = df.groupby("Exercise")["Weight_kg"].max().reset_index().sort_values(by="Weight_kg", ascending=False)
    st.dataframe(best_lifts, hide_index=True, use_container_width=True)

    # --- TABS FOR DETAILS ---
    tab1, tab2, tab3, tab4 = st.tabs(["💪 Strength", "📊 Volume", "🧠 Analytics", "📔 Notes"])

    with tab1: # Strength
        target_exercise = st.selectbox("Select Exercise:", df["Exercise"].unique())
        strength_data = df[df["Exercise"] == target_exercise]
        st.line_chart(strength_data.groupby("Display_Date")["Weight_kg"].max())

    with tab2: # Volume
        st.bar_chart(df.groupby("Display_Date")["Volume_kg"].sum())

    with tab3: # Analytics
        st.subheader("Style Split")
        fig = px.pie(df.groupby("Category")["Sets"].sum().reset_index(), values='Sets', names='Category', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

    with tab4: # Notes
        if "Notes" in df.columns:
            notes_df = df[df["Notes"] != ""][["Display_Date", "Exercise", "Weight_kg", "Notes"]]
            st.dataframe(notes_df, hide_index=True, use_container_width=True)
        else:
            st.warning("⚠️ 'Notes' column missing in Google Sheet. Add it to header H1.")

else:
    st.info(f"Welcome {current_user}! Start logging above.")