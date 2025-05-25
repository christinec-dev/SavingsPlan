# streamlit_savings_app.py
# A Streamlit app to track savings progress against a goal, with a monthly happiness meter and private per-user session caching.

import streamlit as st
import pandas as pd
import datetime

# --- Initialize session state for history ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=[
        'timestamp', 'goal', 'monthly_target', 'current_saved',
        'remaining', 'progress_fraction', 'happiness_fraction'
    ])

# App title
st.title("📊 Savings Progress Tracker (Private Session)")

# --- Upload past history (optional) ---
st.markdown("---")
st.subheader("Upload Past History (Optional)")
uploaded_file = st.file_uploader(
    "Upload a CSV of your past history to merge into this session", type=['csv']
)
if uploaded_file is not None:
    try:
        df_upload = pd.read_csv(uploaded_file, parse_dates=['timestamp'])
        # Merge and drop duplicates to avoid overlap
        df = pd.concat([st.session_state.history, df_upload], ignore_index=True)
        df = df.drop_duplicates(subset=['timestamp','current_saved'], keep='last')
        st.session_state.history = df.sort_values('timestamp').reset_index(drop=True)
        st.success("History merged into your session!")
    except Exception as e:
        st.error(f"Failed to merge uploaded history: {e}")

# --- Input section for this month ---
st.markdown("---")
goal_default = (st.session_state.history['goal'].iloc[-1]
                if not st.session_state.history.empty else 6000)
monthly_default = (st.session_state.history['monthly_target'].iloc[-1]
                   if not st.session_state.history.empty else 3000)
goal = st.number_input(
    "Set your total savings goal (ZAR)",
    min_value=0,
    value=int(goal_default),
    step=500
)
monthly_target = st.number_input(
    "Expected monthly savings (ZAR)",
    min_value=0,
    value=int(monthly_default),
    step=500
)
current_saved = st.number_input(
    "Amount saved so far this month (ZAR)",
    min_value=0,
    value=0,
    step=500
)

# --- Calculations ---
progress = current_saved / goal if goal > 0 else 0
progress = max(0, min(progress, 1))
remaining = max(goal - current_saved, 0)
happiness = current_saved / monthly_target if monthly_target > 0 else 0
happiness = max(0, min(happiness, 1))

# --- Display metrics ---
st.subheader("Overall Progress")
st.progress(progress)
st.write(f"**Progress:** {progress*100:.1f}%")
st.write(f"**Remaining to goal:** ZAR {remaining:,.2f}")

st.subheader("Monthly Happiness Meter")
st.progress(happiness)
if current_saved >= monthly_target:
    st.success("🎉 You hit or exceeded this month's savings target!")
elif current_saved >= 0.5 * monthly_target:
    st.info("🙂 You’re halfway to your monthly target.")
else:
    st.warning("😕 Behind this month's target—keep going!")

# --- Save this entry to session history ---
st.markdown("---")
st.subheader("Save This Entry")
if st.button("Save Entry to Session"):
    new_record = {
        'timestamp': datetime.datetime.now(),
        'goal': goal,
        'monthly_target': monthly_target,
        'current_saved': current_saved,
        'remaining': remaining,
        'progress_fraction': progress,
        'happiness_fraction': happiness
    }
    st.session_state.history = pd.concat(
        [st.session_state.history, pd.DataFrame([new_record])],
        ignore_index=True
    )
    st.success("Entry saved in your private session! 🙌")

# --- Display and edit history in this session ---
st.markdown("---")
st.subheader("Your Session History")
if not st.session_state.history.empty:
    # Display editable table
    try:
        edited = st.experimental_data_editor(
            st.session_state.history,
            num_rows="dynamic",
            use_container_width=True
        )
        if st.button("Update History"):  # save edits back into session
            edited['timestamp'] = pd.to_datetime(edited['timestamp'])
            st.session_state.history = edited
            st.success("Session history updated.")
    except Exception:
        st.dataframe(st.session_state.history)
        st.info("Editing not supported in this Streamlit version.")

    # Show progress over time
    chart_data = st.session_state.history.set_index('timestamp')['current_saved']
    st.line_chart(chart_data, height=300)
else:
    st.write("No entries yet. Save a new entry or upload one.")

# --- Footer ---
st.markdown("---")
st.write("*All data is stored privately in your browser session and not shared.*")
