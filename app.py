import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
from datetime import date, datetime, timedelta
import extra_streamlit_components as stx
import numpy as np
import time

# --- PAGE CONFIG ---
st.set_page_config(page_title="Workout Buddy", page_icon="💪", layout="wide")

# --- AUTHENTICATION & COOKIE SETUP ---
def get_manager():
    return stx.CookieManager()

cookie_manager = get_manager()

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = None

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

# --- HELPER 1: FETCH EXERCISES ---
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

# --- HELPER 2: FETCH LAST LOG ---
def get_last_log(user, exercise_name):
    engine = get_engine()
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT date, weight, sets, reps, notes, rpe
                FROM workouts
                WHERE username = :user AND exercise = :ex
                ORDER BY date DESC LIMIT 1
            """)
            result = conn.execute(query, {"user": user, "ex": exercise_name}).fetchone()
            return result
    except Exception:
        return None

# --- 1. AUTO-LOGIN ---
time.sleep(0.1) 
cookie_user = cookie_manager.get(cookie="arm_wrestling_user")

if not st.session_state["logged_in"] and cookie_user and not st.session_state["logout_clicked"]:
    if "passwords" in st.secrets and cookie_user in st.secrets["passwords"]:
        st.session_state["logged_in"] = True
        st.session_state["username"] = cookie_user
        st.success(f"Welcome back, {cookie_user}!")
        time.sleep(0.5)
        st.rerun()

# --- 2. MANUAL LOGIN ---
def check_login(username, password):
    if "passwords" not in st.secrets:
        st.error("❌ Error: 'secrets.toml' is missing!")
        return
    if username in st.secrets["passwords"]:
        if st.secrets["passwords"][username] == password:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.session_state["logout_clicked"] = False
            expires = datetime.now() + timedelta(days=30)
            cookie_manager.set("arm_wrestling_user", username, expires_at=expires)
            st.success("Logged in!")
            time.sleep(0.5)
            st.rerun()
        else:
            st.error("❌ Incorrect Password")
    else:
        st.error("❌ User not found")

# --- 3. LOGIN SCREEN ---
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
    "Index Knuckle Pronation": "Pronation", "Heavy Pronation Lift": "Pronation",
    "Static Back Pressure": "Back Pressure", "Single-Loop Back Pressure":"Back Pressure",
    "Cupping (Pulley)": "Cupping", "Low Multi-Spinner":"Cupping",
    "Volume Cupping":"Cupping", "Static Cupping":"Cupping",
    "Finger Containment (Static)": "Fingers", "Heavy Wrist Wrench": "Wrist",
    "Rising (Belt)": "Rising", "Volume Side Pressure": "Side Pressure",
    "Volume Rising": "Rising", "Static Pronation" :"Pronation",
    "Heavy Riser":"Rising", "High Cable Side Pressure":"Side Pressure",
    "Partial Curl":"Bicep" 
}

# --- SIDEBAR ---
with st.sidebar:
    st.header("👤 Who is training?")
    current_user = st.session_state["username"]
    st.info(f"Logged in as: **{current_user}**")

    if st.button("Log Out"):
        cookie_manager.set("arm_wrestling_user", "logged_out")
        st.session_state["logged_in"] = False
        st.session_state["username"] = None
        st.session_state["logout_clicked"] = True
        st.success("Logging out...")
        time.sleep(1)
        st.rerun()

# --- SECTION 1: INPUT FORM ---
st.header(f"Log a Set for {current_user}")

# 1. FILTERS & EXERCISE SELECTION (OUTSIDE THE FORM NOW!) 🔓
# This allows the app to refresh and show stats immediately when you change exercise.

if current_user == "Kaisar":
    day_filter = st.radio("⚡ Quick Select Day:", ["All Exercises", "Tue (Heavy/Vol)", "Thu (Statics)", "Sat (Table Power)", "Upper Body", "Abs"], horizontal=True)
elif current_user == "Rahil":
    day_filter = st.radio("⚡ Quick Select Day:", ["All Exercises", "Monday", "Wednesday", "Friday", "Saturday"], horizontal=True)
else:
    day_filter = "All Exercises"

# Logic to get the list of exercises
db_category_map = {
    "Tue (Heavy/Vol)": "Tuesday", "Thu (Statics)": "Thursday", "Sat (Table Power)": "Saturday",
    "Upper Body": "Upper Body", "Abs": "Abs", "Monday": "Monday", "Wednesday": "Wednesday", "Friday": "Friday"
}
selected_db_category = db_category_map.get(day_filter, None)
exercise_options = get_exercises_from_db(current_user, selected_db_category)

if not exercise_options:
    exercise_options = ["⚠️ No exercises found! Add some in 'Manage Data'."]

# THE EXERCISE DROPDOWN (Now active & instant)
exercise = st.selectbox("Select Exercise to Log:", exercise_options)

# 🔥 PROGRESSIVE OVERLOAD DISPLAY (Updates Instantly) 🔥
last_log = get_last_log(current_user, exercise)
if last_log:
    last_date, last_weight, last_sets, last_reps, last_note, last_rpe = last_log      
    # Date formatting
    if isinstance(last_date, str):
        d_str = datetime.strptime(last_date, '%Y-%m-%d').strftime("%b %d")
    else:
        d_str = last_date.strftime("%b %d")
        
    # Display the stats clearly with the Exercise Name
    st.info(f"🔙 **Last time you did {exercise} ({d_str}):**\n\n {last_weight}kg × {last_reps} reps ({last_sets} sets)")
else:
    st.info(f"🆕 No history found for **{exercise}**. Go crush it!")

# --- 🧠 PRESCRIPTIVE ANALYTICS: RECOMMENDATION ENGINE ----
if last_log:
    last_date, last_weight, last_sets, last_reps, last_note, last_rpe = last_log
    
    recommendation = ""    
    if last_rpe >= 9:
        recommendation = "🛑 **High Intensity detected:** Keep weight the same. Focus on recovery."
    elif last_rpe <= 7:
        recommendation = "🚀 **Room for growth:** Try increasing weight by 2.5kg."
    else:
        recommendation = "✅ **Sweet Spot:** Maintain current weight and try to add 1 rep."
        
    st.info(f"🤖 **AI Coach says:** {recommendation}")


# 2. THE LOGGING FORM (Inputs Only) 📝
with st.form("workout_form", clear_on_submit=False): 
    col1, col2 = st.columns(2)
    with col1:
        d = st.date_input("Date", date.today())
        Bodyweight = st.number_input("Bodyweight (kg)", min_value=0.0, step=0.5, value=70.0)
        
    with col2:
        weight = st.number_input("Weight (kg)", min_value=0.0, step=0.5)
        sets = st.number_input("Sets", min_value=1, step=1, value=3)
        reps = st.text_input("Reps", value="10", help="e.g. 10 or 5,4,3")
        
    rpe = st.slider("RPE (Intensity)", 1, 10, 8)
    notes = st.text_input("📝 Notes (Optional)", placeholder="Form cue, pain check, etc.")
    
    # Save Button
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
            st.success(f"✅ Saved {exercise}!")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"❌ Save Failed: {e}")


# --- SECTION 2: DASHBOARD ---
st.divider()

try:
    engine = get_engine()
    df = pd.read_sql("SELECT * FROM workouts", engine)
    df = df.rename(columns={"date": "Date", "exercise": "Exercise", "weight": "Weight_kg", "sets": "Sets", "reps": "Reps", "rpe": "RPE", "username": "User", "notes": "Notes", "bodyweight": "Bodyweight"})
except Exception as e:
    st.error(f"❌ Error loading data: {e}")
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
    # NOTE: We do NOT force Reps to numeric anymore, so "5,4,3" is allowed.
    df["Bodyweight"] = pd.to_numeric(df["Bodyweight"],errors='coerce').fillna(0)
    
    st.subheader(f"🏆 {current_user}'s Workspace")
    best_lifts = df.groupby("Exercise")["Weight_kg"].max().reset_index().sort_values(by="Weight_kg", ascending=False)
    st.dataframe(best_lifts, hide_index=True, use_container_width=True)
else:
    st.info(f"👋 Welcome, {current_user}! You haven't logged any workouts yet.")

# --- TABS ---
tabs_list = ["📈 Progress", "📅 History", "📚 Logbook", "⚖️ Bodyweight", "🛠️ Manage Data"]
all_tabs = st.tabs(tabs_list)
tab1, tab2, tab3, tab4, tab5 = all_tabs[0], all_tabs[1], all_tabs[2], all_tabs[3], all_tabs[4]

with tab1: # 📈 Progress & Analytics
    if not df.empty:
        # --- 1. PRE-CALCULATE ANALYTICS ---
        target_exercise = st.selectbox("Select Exercise for Analysis:", df["Exercise"].unique())
        ex_data = df[df["Exercise"] == target_exercise].sort_values("Date")
        
        if len(ex_data) > 1:
            # A. Prepare Data
            ex_data['date_ordinal'] = ex_data['Date'].map(datetime.toordinal)
            
            # B. ML Prediction
            slope, intercept = np.polyfit(ex_data['date_ordinal'], ex_data['Weight_kg'], 1)
            monthly_gain = slope * 30 
            
            # C. Calculate e1RM
            ex_data["Clean_Reps"] = ex_data["Reps"].astype(str).str.split(',').str[0]
            ex_data["Clean_Reps"] = pd.to_numeric(ex_data["Clean_Reps"], errors='coerce').fillna(1)
            ex_data["e1RM"] = ex_data["Weight_kg"] * (1 + (ex_data["Clean_Reps"] / 30))
            current_e1rm = ex_data["e1RM"].iloc[-1] 

            # --- 2. THE DASHBOARD ---
            col_main, col_metrics = st.columns([3, 1])
            
            with col_main:
                # Forecast
                future_date = datetime.now() + timedelta(days=30)
                future_val = (slope * future_date.toordinal()) + intercept
                st.caption(f"🤖 **Forecast:** hitting **{future_val:.1f} kg** in 30 days.")
                
                # --- 📊 MAIN GRAPH (The "Sick" Scatter) ---
                fig = px.scatter(
                    ex_data, 
                    x="Date", 
                    y="Weight_kg", 
                    size=ex_data["RPE"].replace(0, 1), 
                    color="RPE", 
                    color_continuous_scale="RdYlGn_r", 
                    hover_data=["Sets", "Reps", "e1RM"], 
                    title=f"Progress: {target_exercise}",
                    trendline="ols" 
                )
                st.plotly_chart(fig, use_container_width=True)

            with col_metrics:
                st.write("### ⚡ Stats")
                
                # Metric 1: Velocity
                if monthly_gain > 0.5:
                    st.metric("Growth Speed", f"+{monthly_gain:.1f} kg/mo", delta="Fast")
                elif monthly_gain > 0:
                    st.metric("Growth Speed", f"+{monthly_gain:.1f} kg/mo", delta="Steady")
                else:
                    st.metric("Growth Speed", f"{monthly_gain:.1f} kg/mo", delta="Stalled", delta_color="inverse")
                
                # Metric 2: Current Max
                st.metric("Est. 1-Rep Max", f"{current_e1rm:.1f} kg")
                
                # --- 📉 NEW: MINI e1RM GRAPH ---
                st.write("Theoretical Limit Trend:")
                # We use a simple line chart here because it fits small spaces better
                st.line_chart(ex_data.set_index("Date")["e1RM"], height=150, color="#FF4B4B")
                
        else:
            st.warning("Log at least 2 workouts to unlock Analytics.")
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
with tab4: # ⚖️ Bodyweight
    if not df.empty:
        # --- 1. DATA TRANSFORMATION ---
        # Create a dedicated dataframe for bodyweight to keep things clean
        bw_df = df[["Date", "Bodyweight"]].sort_values("Date").dropna()
        
        # Create the derived column (The Math)
        bw_df["Bodyweight_lbs"] = bw_df["Bodyweight"] * 2.20462
        
        # --- 2. USER CONTROL ---
        col_controls, col_graph = st.columns([1, 4])
        
        with col_controls:
            st.write("##") # Spacer
            # The Toggle Switch
            unit_choice = st.radio("Select Unit:", ["KG", "LBS"])
        
        # --- 3. THE VISUALIZATION ---
        with col_graph:
            # Logic: Choose which column to plot based on the radio button
            y_col = "Bodyweight" if unit_choice == "KG" else "Bodyweight_lbs"
            color_hex = "#1f77b4" if unit_choice == "KG" else "#ff7f0e" # Blue for KG, Orange for LBS
            
            fig_bw = px.line(
                bw_df, 
                x="Date", 
                y=y_col, 
                markers=True,
                title=f"Bodyweight History ({unit_choice})",
                height=350
            )
            
            # Make it look "Sexy" (Minimalist style)
            fig_bw.update_traces(line_color=color_hex, line_width=3)
            fig_bw.update_layout(yaxis_title=unit_choice)
            
            st.plotly_chart(fig_bw, use_container_width=True)
            
        # Optional: Show the latest stat text
        latest_bw = bw_df.iloc[-1]
        st.metric(
            label="Current Bodyweight", 
            value=f"{latest_bw[y_col]:.1f} {unit_choice}"
        )
            
    else:
        st.write("Track your bodyweight to see it here.")

with tab5: # Manage Data
    st.subheader("🛠️ Manage Exercises")
    
    with st.expander("➕ Add New Exercise to Library"):
        with st.form("add_ex_form"):
            new_ex_name = st.text_input("Name (e.g. King's Move)")
            cat_options = ["Tuesday", "Thursday", "Saturday", "Upper Body", "Abs", "General", "Monday", "Wednesday", "Friday"]
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