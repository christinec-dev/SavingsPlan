# streamlit_savings_app.py
# A Streamlit app to track savings progress against a goal, with a monthly happiness meter,
# private per-user sessions, and optional collaborative share links.

import streamlit as st
import pandas as pd
import os
import datetime
import uuid

# --- Constants ---
SHARED_DIR = 'shared_histories'
os.makedirs(SHARED_DIR, exist_ok=True)

# --- Initialize session state for history ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=[
        'timestamp', 'goal', 'monthly_target', 'current_saved',
        'remaining', 'progress_fraction', 'happiness_fraction'
    ])
def get_current_url():
    st.markdown(
        """
        <script>
        const streamlitDoc = window.parent.document;
        const url = streamlitDoc.location.href;
        window.parent.postMessage({type: 'STREAMLIT_URL', url: url}, '*');
        </script>
        """,
        unsafe_allow_html=True,
    )
    url = st.experimental_get_query_params().get("streamlit_url", [""])[0]
    return url

# --- Load shared history if share_id provided in URL ---
share_id = st.query_params.get("share_id")
if share_id:
    shared_file = os.path.join(SHARED_DIR, f"history_{share_id}.csv")
    if os.path.exists(shared_file):
        df_shared = pd.read_csv(shared_file, parse_dates=['timestamp'])
        st.session_state.history = df_shared
    else:
        st.warning("Share link not found or expired.")

# App title
st.title("📊 Savings Progress Tracker (Private Session)")

# --- Upload past history (optional) ---
st.markdown("---")
st.subheader("Upload Past History (Optional)")
uploaded_file = st.file_uploader(
    "Upload a CSV of your past history to merge into this session",
    type=['csv']
)
if uploaded_file is not None:
    try:
        df_upload = pd.read_csv(uploaded_file, parse_dates=['timestamp'])
        df = pd.concat([st.session_state.history, df_upload], ignore_index=True)
        df = df.drop_duplicates(
            subset=['timestamp', 'current_saved'], keep='last'
        ).sort_values('timestamp').reset_index(drop=True)
        st.session_state.history = df
        st.success("History merged into your session!")
    except Exception as e:
        st.error(f"Failed to merge uploaded history: {e}")

# --- Input section for this month ---
st.markdown("---")
goal_default = (
    st.session_state.history['goal'].iloc[-1]
    if not st.session_state.history.empty else 6000
)
monthly_default = (
    st.session_state.history['monthly_target'].iloc[-1]
    if not st.session_state.history.empty else 3000
)
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

# --- Save this entry to session or shared history ---
st.markdown("---")
st.subheader("Save This Entry")
if st.button("Save Entry"):
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
    # If we're on a share link, persist to shared file
    if share_id:
        st.session_state.history.to_csv(shared_file, index=False)
    st.success("Entry saved!")

# --- Display and edit history ---
st.markdown("---")
st.subheader("Your Session History")
if not st.session_state.history.empty:
    # Inline editing (requires Streamlit ≥1.19 / ≥1.23)
    editor = getattr(st, 'data_editor', None) or getattr(st, 'experimental_data_editor', None)
    if editor:
        edited = editor(
            st.session_state.history,
            num_rows="dynamic",
            use_container_width=True
        )
        if st.button("Update History"):
            edited['timestamp'] = pd.to_datetime(edited['timestamp'])
            st.session_state.history = edited
            if share_id:
                st.session_state.history.to_csv(shared_file, index=False)
            st.success("History updated.")
    else:
        st.warning(
            "Inline editing requires Streamlit ≥1.19 / ≥1.23.\n"
            "Please upgrade: `pip install --upgrade streamlit`."
        )
        st.dataframe(st.session_state.history)
    
    # Chart cumulative saved over time
    chart_data = st.session_state.history.set_index('timestamp')['current_saved']
    st.line_chart(chart_data, height=300)
else:
    st.write("No entries yet. Save a new entry or upload one.")

# --- Share link section ---
st.markdown("---")
st.subheader("Collaborate via Share Link")
if st.button("Generate Share Link"):
    new_id = uuid.uuid4().hex[:8]
    shared_file = os.path.join(SHARED_DIR, f"history_{new_id}.csv")
    st.session_state.history.to_csv(shared_file, index=False)
    # **Write directly to the URL param**
    st.query_params.share_id = new_id
    st.success(f"Share this link: https://savingsplanner.streamlit.app?share_id={new_id}")

# --- Footer ---
st.markdown("---")
st.write("*All data is stored privately in your browser session or via the share link.*")
