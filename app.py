# streamlit_savings_app.py
# A Streamlit app to track savings progress against a goal, with a monthly happiness meter, persistent history, upload and edit functionality.

import streamlit as st
import pandas as pd
import os
import datetime

# Caching load and save to avoid re-reading unnecessarily
@st.cache_data
def load_history(path):
    if os.path.exists(path):
        return pd.read_csv(path, parse_dates=['timestamp'])
    else:
        return pd.DataFrame(columns=[
            'timestamp', 'goal', 'monthly_target', 'current_saved',
            'remaining', 'progress_fraction', 'happiness_fraction'
        ])

@st.cache_data
def save_history(df, path):
    df.to_csv(path, index=False)
    return df

# Constants
HISTORY_FILE = 'savings_history.csv'

# App title
st.title("📊 Savings Progress Tracker")

# --- Load existing history ---
df_history = load_history(HISTORY_FILE)

# --- Upload history CSV ---
st.markdown("---")
st.subheader("Upload Past History")
uploaded_file = st.file_uploader("Upload a CSV of past history to merge", type=['csv'])
if uploaded_file is not None:
    try:
        df_upload = pd.read_csv(uploaded_file, parse_dates=['timestamp'])
        # Merge and drop duplicates by timestamp & current_saved
        df_history = pd.concat([df_history, df_upload], ignore_index=True)
        df_history = df_history.drop_duplicates(subset=['timestamp','current_saved'], keep='last')
        save_history(df_history, HISTORY_FILE)
        st.success("History merged successfully!")
    except Exception as e:
        st.error(f"Failed to upload and merge: {e}")

# --- Input section ---
st.markdown("---")
goal = st.number_input(
    "Set your total savings goal (ZAR)",
    min_value=0,
    value=int(df_history['goal'].iloc[-1]) if not df_history.empty else 6000,
    step=500,
    help="Enter the total amount you want to save."
)
monthly_target = st.number_input(
    "Expected monthly savings (ZAR)",
    min_value=0,
    value=int(df_history['monthly_target'].iloc[-1]) if not df_history.empty else 3000,
    step=500,
    help="Enter how much you plan to save each month."
)
current_saved = st.number_input(
    "Amount saved so far (ZAR)",
    min_value=0,
    value=0,
    step=500,
    help="Enter the amount you have already saved."
)

# --- Calculations ---
progress_fraction = (current_saved / goal) if goal > 0 else 0
progress_fraction = max(0, min(progress_fraction, 1))
remaining = max(goal - current_saved, 0)

happiness_fraction = (current_saved / monthly_target) if monthly_target > 0 else 0
happiness_fraction = max(0, min(happiness_fraction, 1))

# --- Display metrics ---
st.subheader("Overall Progress")
st.progress(progress_fraction)
st.write(f"**Progress:** {progress_fraction * 100:.1f}%")
st.write(f"**Remaining to reach goal:** ZAR {remaining:,.2f}")

st.subheader("Monthly Happiness Meter")
st.progress(happiness_fraction)
if current_saved >= monthly_target:
    st.success("Great job on saving this month! 😊")
elif current_saved >= monthly_target * 0.5:
    st.info("You're doing okay, but you can do better 🙂")
else:
    st.error("You’re behind this month's savings target. Let's pick up the pace! 😞")

# --- Save current entry ---
st.markdown("---")
st.subheader("Save Current Entry")
if st.button("Save Results"):
    record = {
        'timestamp': datetime.datetime.now(),
        'goal': goal,
        'monthly_target': monthly_target,
        'current_saved': current_saved,
        'remaining': remaining,
        'progress_fraction': progress_fraction,
        'happiness_fraction': happiness_fraction
    }
    df_history = pd.concat([df_history, pd.DataFrame([record])], ignore_index=True)
    save_history(df_history, HISTORY_FILE)
    st.success("Entry saved! ✅")

# --- Display and edit history ---
st.markdown("---")
st.subheader("Monthly History & Edit")
if not df_history.empty:
    df_history = df_history.sort_values('timestamp').reset_index(drop=True)
    # Use available data editor function
    editor = getattr(st, 'data_editor', None) or getattr(st, 'experimental_data_editor', None)
    if editor:
        edited = editor(
            df_history,
            num_rows="dynamic",
            use_container_width=True
        )
        if st.button("Save Edited History"):
            try:
                edited['timestamp'] = pd.to_datetime(edited['timestamp'])
                df_history = edited
                save_history(df_history, HISTORY_FILE)
                st.success("Edited history saved.")
            except Exception as e:
                st.error(f"Error saving edits: {e}")
    else:
        st.warning("Data editor not available in this Streamlit version.")
        st.dataframe(df_history)
    # Chart cumulative saved over time
    chart_df = df_history.set_index('timestamp')['current_saved']
    st.line_chart(chart_df)
else:
    st.write("No history yet. Save an entry or upload data to see it here.")

# --- Footer ---
st.markdown("---")
st.markdown("Built with [Streamlit](https://streamlit.io)")