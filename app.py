import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import datetime

# --- CONFIGURATION ---
DB_NAME = "arm_wrestling.db"

# --- CONFIGURATION ---
DB_NAME = "arm_wrestling.db"

# 🆕 MAP SPECIFIC LIFTS TO BROAD CATEGORIES
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

st.set_page_config(page_title="Arm Wrestling Tracker", page_icon="💪", layout="wide")
st.title("Arm Wrestling Training Log")


# --- SIDEBAR: USER SELECTION ---
with st.sidebar:
    st.header("👤 Who is training?")
    current_user = st.radio("Select User:", ["Kaisar", "Friend"])
    
    st.divider()
    st.header("⚙️ Tools")
    if st.button("↩️ Delete Last Entry"):

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Check if user has data
        cursor.execute("SELECT count(*) FROM training_logs WHERE User = ?", (current_user,))
        
        if cursor.fetchone()[0] > 0:
            # Delete newest row for this user
            cursor.execute("""
                DELETE FROM training_logs 
                WHERE rowid = (SELECT MAX(rowid) FROM training_logs WHERE User = ?)
            """, (current_user,))
            conn.commit()
            st.warning(f"⚠️ Last entry for {current_user} deleted!")
        else:
            st.error("No data to delete.")
        conn.close()
    
    st.divider()
    st.markdown("### 🚫 Danger Zone")
    
    # 1. THE SAFETY LOCK
    # The button is hidden until this box is checked
    confirm_delete = st.checkbox("Unlock Delete All")
    
    if confirm_delete:
        # 2. THE TRIGGER
        if st.button("💥 Delete ALL My Data", type="primary"):
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            
            # 3. THE NUCLEAR OPTION
            # We use 'WHERE User = ?' so you don't delete your Friend's data!
            cursor.execute("DELETE FROM training_logs WHERE User = ?", (current_user,))
            conn.commit()
            conn.close()
            
            st.toast(f"💥 All data for {current_user} has been wiped!")
            st.rerun() # Refresh the app instantly



# --- SECTION 1: INPUT FORM (Fixed) ---
st.header(f"Log a Set for {current_user}")

# --- 1. SPEED PASS (Moved OUTSIDE the form so it's instant) ---
# This filters the dropdown so you find exercises faster
day_filter = st.radio(
    "⚡ Quick Select Day:", 
    ["All Exercises", "Tue (Heavy/Vol)", "Thu (Statics)", "Sat (Table Power)"], 
    horizontal=True
)

# --- 2. THE FORM ---
with st.form("workout_form"):
    date = st.date_input("Date", datetime.date.today())
    
    col1, col2 = st.columns(2)

    #Column 2
    with col1:
        # Define the lists based on your real split
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

        # Logic to decide which list to show
        if current_user == "Friend":
            exercise_options = ["Bicep Curl", "Bench Press", "Squat", "Deadlift"]
        elif day_filter == "Tue (Heavy/Vol)":
            exercise_options = exercises_tue
        elif day_filter == "Thu (Statics)":
            exercise_options = exercises_thu
        elif day_filter == "Sat (Table Power)":
            exercise_options = exercises_sat
        else:
            # "All Exercises" - Combine them all
            exercise_options = exercises_tue + exercises_thu + exercises_sat
            
        exercise = st.selectbox("Exercise", exercise_options)
        arm = st.selectbox("Arm", ["R", "L", "Both"])
    
    #Column 2
    with col2:
        weight = st.number_input("Weight (kg)", min_value=0.0, step=0.5)
        
        # Smart Reps Input
        reps_input = st.text_input("Reps (e.g. '10' or '4,5,2')", value="10")
        sets_input = st.number_input("Sets (Only used if single rep number)", min_value=1, value=3)

    #Slider + Notes
    rpe = st.slider("RPE (Intensity)", 1, 10, 8)
    soreness = st.slider("Soreness (Next Day Prediction)", 0, 10, 5)
    notes = st.text_area("📝 Session Notes", placeholder="e.g. Wrist felt strong...")
    submitted = st.form_submit_button("Save Workout")


    #After submission
    if submitted:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Smart Logic for "4, 5, 2" inputs
        if "," in reps_input:
            try:
                reps_list = [int(r.strip()) for r in reps_input.split(",")]
                for r in reps_list:
                    cursor.execute("""
                        INSERT INTO training_logs (Date, User, Arm, Exercise, Sets, Reps, Weight_kg, RPE, Soreness, Notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (date, current_user, arm, exercise, 1, r, weight, rpe, soreness, notes))
                st.success(f"✅ Saved {len(reps_list)} individual sets.")
            except ValueError:
                st.error("⚠️ Error: Use commas for multiple sets (e.g., 4,5,2)")
        else:
            # Standard Mode
            try:
                reps = int(reps_input)
                sets = int(sets_input)
                cursor.execute("""
                    INSERT INTO training_logs (Date, User, Arm, Exercise, Sets, Reps, Weight_kg, RPE, Soreness, Notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (date, current_user, arm, exercise, sets, reps, weight, rpe, soreness, notes))
                st.success(f"✅ Saved: {exercise}")
            except ValueError:
                st.error("Invalid Reps number")

        conn.commit()
        conn.close()


# --- SECTION 2: DASHBOARD ---
st.divider()

# Fetch Data for Current User
conn = sqlite3.connect(DB_NAME)
df = pd.read_sql("SELECT * FROM training_logs WHERE User = ? ORDER BY Date ASC", conn, params=(current_user,))
conn.close()

# 🆕 Feature Engineering: Create "Category" Column
# If an exercise isn't in the map, label it "Other"
df["Category"] = df["Exercise"].map(CATEGORY_MAP).fillna("Other")

# 🆕 Feature Engineering: Date Helpers
df["Month"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m")


if not df.empty:
    df["Date"] = pd.to_datetime(df["Date"])
    df["Display_Date"] = df["Date"].dt.strftime('%Y-%m-%d')
    df["Volume_kg"] = df["Sets"] * df["Reps"] * df["Weight_kg"]
    df["e1RM"] = df["Weight_kg"] * (1 + (df["Reps"] / 30))

    # --- FEATURE: TROPHY ROOM (PRs) 🏆 ---
    st.subheader(f"🏆 {current_user}'s Trophy Room (All-Time Best Lifts)")
    
    # Group by Exercise and find MAX Weight
    best_lifts = df.groupby("Exercise")["Weight_kg"].max().reset_index()
    best_lifts = best_lifts.sort_values(by="Weight_kg", ascending=False)
    
    # Show as a clean table
    st.dataframe(
        best_lifts, 
        column_config={
            "Exercise": "Lift",
            "Weight_kg": st.column_config.NumberColumn("Personal Record (kg)", format="%.1f kg")
        },
        hide_index=True,
        use_container_width=True
    )

    # --- TABS FOR DETAILED CHARTS ---
    tab1, tab2, tab3, tab4 = st.tabs(["💪 Strength Trend", "📊 Volume", " 🧠 Training Analytics", "📔 Notebook"])

    with tab1:
        st.caption("Are you getting stronger over time?")
        target_exercise = st.selectbox("Select Exercise:", df["Exercise"].unique(), key="strength_select")
        strength_data = df[df["Exercise"] == target_exercise]
        daily_max = strength_data.groupby("Display_Date")["Weight_kg"].max()
        st.line_chart(daily_max)

    with tab2:
        st.caption("Total tonnage moved per session.")
        daily_vol = df.groupby("Display_Date")["Volume_kg"].sum()
        st.bar_chart(daily_vol)

    with tab3:
        st.header("📊 Training Analytics")
        
        # --- CHART 1: TRAINING BALANCE (PIE CHART) ---
        st.subheader("1. Style Split")
        st.caption("Where are you focusing your efforts?")
        
        # Group by Category and count total sets
        cat_counts = df.groupby("Category")["Sets"].sum().reset_index()
        
        # Create the Pie Chart using Plotly
        fig = px.pie(
            cat_counts, 
            values='Sets', 
            names='Category', 
            title='Distribution of Sets by Style',
            hole=0.4, # Makes it a Donut Chart (looks cooler)
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        
        # Display the Plotly Chart
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # --- CHART 2: CONSISTENCY TRACKER ---
        st.subheader("2. Weekly Consistency")
        st.caption("Visualizing your frequency over time.")
        df["Display_Date"] = df["Date"].dt.strftime('%Y-%m-%d')
        
        daily_activity = df.groupby("Display_Date")["Sets"].sum().reset_index()
        st.bar_chart(daily_activity, x="Display_Date", y="Sets")

    with tab4:
        st.caption("Your training notes.")
        notes_df = df[df["Notes"] != ""][["Display_Date", "Exercise", "Sets", "Reps", "Weight_kg", "Notes"]]
        if not notes_df.empty:
            notes_df["Weight_kg"] = notes_df["Weight_kg"].apply(lambda x: "{:g}".format(x))
            st.dataframe(notes_df.sort_values(by="Display_Date", ascending=False), hide_index=True, use_container_width=True)
        else:
            st.info("No notes found.")

    with st.expander("See Raw History Data"):
        st.dataframe(df.sort_values(by="Date", ascending=False))

else:
    st.info(f"Welcome {current_user}! Your dashboard is empty. Start logging above!")