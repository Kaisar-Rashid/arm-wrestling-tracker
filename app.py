import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime
import gspread
import os


# --- AUTHENTICATION LOGIC ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = None

def check_login(username, password):
    if "passwords" not in st.secrets:
        st.error("❌ Error: 'secrets.toml' file is missing or empty!")
        return

    if username in st.secrets["passwords"]:
        if st.secrets["passwords"][username] == password:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.success("Logged in!")
            st.rerun()
        else:
            st.error("❌ Incorrect Password")
    else:
        st.error("❌ User not found")

# --- THE GATEKEEPER ---
if not st.session_state["logged_in"]:
    st.title("🔒 Arm Wrestling Tracker")
    user_input = st.text_input("Username")
    pass_input = st.text_input("Password", type="password")
    
    if st.button("Login"):
        check_login(user_input, pass_input)
    
    st.stop()

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
    # 1. Find the file on your laptop
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(current_dir, "service_account.json")

    if os.path.exists(json_file_path):
        client = gspread.service_account(filename=json_file_path)
    else:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            client = gspread.service_account_from_dict(creds_dict)
        else:
            st.error("Could not find 'service_account.json' locally, and no Secrets found.")
            st.stop()

    sheet = client.open("Arm Wrestling Data").sheet1 
    return sheet

st.set_page_config(page_title="Arm Wrestling Tracker", page_icon="💪", layout="wide")
st.title("Arm Wrestling Training Log")

# --- SIDEBAR: USER SELECTION ---
# --- SIDEBAR: USER INFO ---
with st.sidebar:
    st.header("👤 Who is training?")
    
    # ✅ 1. LOCK THE USER to the login name
    current_user = st.session_state["username"]
    st.info(f"Logged in as: **{current_user}**")

    # ✅ 2. LOGOUT BUTTON
    if st.button("Log Out"):
        st.session_state["logged_in"] = False
        st.rerun()

# --- SECTION 1: INPUT FORM ---
st.header(f"Log a Set for {current_user}")

day_filter = st.radio(
    "⚡ Quick Select Day:", 
    ["All Exercises", "Tue (Heavy/Vol)", "Thu (Statics)", "Sat (Table Power)"], 
    horizontal=True
)

with st.form("workout_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        d = st.date_input("Date", date.today())
        exercises_tue = ["Index Knuckle Pronation", "Heavy Wrist Wrench", "Low Multi-Spinner", "Finger Containment (Static)", "Volume Side Pressure", "Volume Rising", "Volume Pronation"]
        exercises_thu = ["Static Back Pressure", "Static Pronation", "Static Cupping"]
        exercises_sat = ["Single-Loop Back Pressure", "Heavy Pronation Lift", "Heavy Riser", "High Cable Side Pressure", "Partial Curl", "Volume Cupping"]

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
        Bodyweight =st.number_input("Bodyweight (kg)", min_value=0.0, step=0.5, value=70.0)
        
    with col2:
        weight = st.number_input("Weight (kg)", min_value=0.0, step=0.5)
        sets = st.number_input("Sets", min_value=1, step=1, value=3)
        reps = st.number_input("Reps", min_value=1, step=1, value=10)
        
    rpe = st.slider("RPE (Intensity)", 1, 10, 8)
    notes = st.text_input("📝 Notes (Optional)", placeholder="Form cue, pain check, etc.")
    submitted = st.form_submit_button("Save Workout")

    if submitted:
        date_str = d.strftime("%Y-%m-%d")
        try:
            sheet = connect_to_sheet()
            new_row = [date_str, exercise, weight, sets, reps, rpe, current_user, notes,Bodyweight]
            sheet.append_row(new_row)
            st.success(f"✅ Added: {exercise} ({weight}kg)")
            import time
            time.sleep(1)
            st.rerun() 
        except Exception as e:
            st.error(f"❌ Failed to save to Google Sheets: {e}")

# --- SECTION 2: DASHBOARD ---
st.divider()

try:
    sheet = connect_to_sheet()
    raw_data = sheet.get_all_records()
    df = pd.DataFrame(raw_data)
    if df.empty:
        df = pd.DataFrame(columns=["Date", "Exercise", "Weight_kg", "Sets", "Reps", "RPE", "User", "Notes","Bodyweight"])
except Exception as e:
    st.error(f"❌ Error connecting to Google Sheets: {e}")
    st.stop()

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
    df["e1RM"] = df["Weight_kg"] * (1 + (df["Reps"] / 30))

    st.subheader(f"🏆 {current_user}'s Trophy Room (PRs)")
    best_lifts = df.groupby("Exercise")["Weight_kg"].max().reset_index().sort_values(by="Weight_kg", ascending=False)
    st.dataframe(best_lifts, hide_index=True, use_container_width=True)

    # 1. Define the tabs everyone sees
    tabs_list = ["➕ Log Workout", "📊 Progress", "📅 History", "📉 RPE", "⚖️ Bodyweight"]

    # 2. If it is YOU (Kaisar), add the Admin tab
    if current_user == "Kaisar":
        tabs_list.append("🛠️ Manage Data")

    # 3. Create the tabs
    all_tabs = st.tabs(tabs_list)

    # 4. Unpack them (This is a bit tricky, follow closely)
    tab1, tab2, tab3, tab4, tab6 = all_tabs[0], all_tabs[1], all_tabs[2], all_tabs[3], all_tabs[4]

    # Only define tab5 if it exists
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
                        import time
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
else:
    st.info(f"Welcome {current_user}! Start logging above.")