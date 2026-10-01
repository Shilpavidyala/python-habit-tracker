import json
import os
from datetime import date, datetime, timedelta
import pandas as pd
import streamlit as st

# --- CONSTANTS & CONFIG ---
# Always save habits.json in the exact same directory as this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "habits.json")

st.set_page_config(
    page_title="Habit & Goal Tracker", page_icon="🎯", layout="wide"
)


# --- DATA PERSISTENCE ---
def load_data():
    """Loads habit data from a JSON file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {"habits": []}
    return {"habits": []}


def save_data(data):
    """Saves habit data to a JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


# --- LOGIC & METRICS ---
def calculate_streak(completed_dates):
    """Calculates the current consecutive daily streak."""
    if not completed_dates:
        return 0

    # Sort dates in descending order
    dates = sorted(
        [datetime.strptime(d, "%Y-%m-%d").date() for d in completed_dates],
        reverse=True,
    )
    today = date.today()
    yesterday = today - timedelta(days=1)

    # Check if the habit was done today or yesterday to keep streak active
    if dates[0] not in (today, yesterday):
        return 0

    streak = 1
    current = dates[0]

    for d in dates[1:]:
        if current - d == timedelta(days=1):
            streak += 1
            current = d
        elif current == d:
            continue  # duplicate date guard
        else:
            break

    return streak


def calculate_completion_rate(completed_dates, days=7):
    """Calculates completion percentage over the last N days."""
    today = date.today()
    period_start = today - timedelta(days=days - 1)

    valid_dates = [
        datetime.strptime(d, "%Y-%m-%d").date()
        for d in completed_dates
        if period_start <= datetime.strptime(d, "%Y-%m-%d").date() <= today
    ]

    return (len(set(valid_dates)) / days) * 100


# --- INITIALIZE STATE ---
data = load_data()
today_str = date.today().strftime("%Y-%m-%d")

# --- UI HEADER ---
st.title("🎯 Multi-Metric Habit & Goal Tracker")
st.caption(f"Track consistency, manage streaks, and view progress • **Today:** {date.today().strftime('%A, %b %d, %Y')}")

st.divider()

# --- SIDEBAR: ADD NEW HABIT ---
with st.sidebar:
    st.header("➕ Create New Habit")
    new_habit_name = st.text_input(
        "Habit Name", placeholder="e.g., Read 20 mins, Code Python"
    )
    new_habit_cat = st.selectbox(
        "Category", ["Health", "Learning", "Productivity", "Mindfulness", "Other"]
    )

    if st.button("Add Habit", use_container_width=True):
        if new_habit_name.strip():
            # Prevent duplicate names
            existing_names = [h["name"].lower() for h in data["habits"]]
            if new_habit_name.strip().lower() in existing_names:
                st.error("A habit with this name already exists!")
            else:
                data["habits"].append(
                    {
                        "id": len(data["habits"]) + 1,
                        "name": new_habit_name.strip(),
                        "category": new_habit_cat,
                        "history": [],
                    }
                )
                save_data(data)
                st.success(f"Added '{new_habit_name}'!")
                st.rerun()
        else:
            st.warning("Please enter a valid habit name.")

    st.divider()
    st.markdown("### 📊 Dataset Overview")
    st.metric("Total Habits Tracked", len(data["habits"]))

# --- MAIN DASHBOARD ---
if not data["habits"]:
    st.info("👋 No habits added yet! Use the sidebar on the left to add your first habit.")
else:
    # --- TOP METRICS CARDS ---
    col1, col2, col3 = st.columns(3)

    total_streaks = sum(
        calculate_streak(h["history"]) for h in data["habits"]
    )
    avg_7day_completion = (
        sum(calculate_completion_rate(h["history"], days=7) for h in data["habits"])
        / len(data["habits"])
    )
    completed_today_count = sum(
        1 for h in data["habits"] if today_str in h["history"]
    )

    with col1:
        st.metric("Completed Today", f"{completed_today_count} / {len(data['habits'])}")
    with col2:
        st.metric("Combined Active Streak", f"{total_streaks} Days")
    with col3:
        st.metric("7-Day Avg Completion", f"{avg_7day_completion:.1f}%")

    st.divider()

    # --- TODAY'S CHECK-IN SECTION ---
    st.subheader("📅 Today's Progress Check-In")

    for idx, habit in enumerate(data["habits"]):
        c1, c2, c3, c4 = st.columns([3, 1.5, 1.5, 1])

        # Checkbox for today
        is_completed_today = today_str in habit["history"]

        with c1:
            st.markdown(f"**{habit['name']}** `[{habit['category']}]`")

        with c2:
            streak = calculate_streak(habit["history"])
            st.markdown(f"🔥 **{streak} Day Streak**")

        with c3:
            completed = st.checkbox(
                "Completed",
                value=is_completed_today,
                key=f"check_{habit['name']}_{idx}",
            )

            # Update habit history on toggle
            if completed != is_completed_today:
                if completed and today_str not in habit["history"]:
                    habit["history"].append(today_str)
                elif not completed and today_str in habit["history"]:
                    habit["history"].remove(today_str)
                save_data(data)
                st.rerun()

        with c4:
            if st.button("🗑️", key=f"del_{idx}", help="Delete habit"):
                data["habits"].pop(idx)
                save_data(data)
                st.rerun()

    st.divider()

    # --- ANALYTICS & VISUALIZATIONS ---
    st.subheader("📈 Consistency & Performance Analysis")

    habit_names = [h["name"] for h in data["habits"]]
    selected_habit_name = st.selectbox("Select Habit to Analyze:", habit_names)

    selected_habit = next(
        h for h in data["habits"] if h["name"] == selected_habit_name
    )

    # Calculate rates
    rate_7d = calculate_completion_rate(selected_habit["history"], days=7)
    rate_30d = calculate_completion_rate(selected_habit["history"], days=30)

    col_a, col_b = st.columns(2)
    with col_a:
        st.write(f"**7-Day Completion Rate:** {rate_7d:.1f}%")
        st.progress(rate_7d / 100)

    with col_b:
        st.write(f"**30-Day Completion Rate:** {rate_30d:.1f}%")
        st.progress(rate_30d / 100)

    # Activity Grid (Last 14 Days)
    st.write("**Recent Activity (Last 14 Days):**")
    last_14_days = [date.today() - timedelta(days=i) for i in range(13, -1, -1)]

    activity_data = []
    for d in last_14_days:
        d_str = d.strftime("%Y-%m-%d")
        activity_data.append(
            {
                "Date": d.strftime("%b %d"),
                "Status": "✅ Completed" if d_str in selected_habit["history"] else "❌ Missed",
            }
        )

    df_activity = pd.DataFrame(activity_data)
    st.dataframe(df_activity.T, use_container_width=True)