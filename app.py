# streamlit_savings_app.py
# A Streamlit app to track savings progress against a goal, with:
# - monthly happiness meter
# - private per-user sessions
# - optional collaborative share links
# - category allocations based on TOTAL saved history
# - a Totals row in the history table
# - inline editing of history
# - per-entry progress bars
# - editable allocations in the sidebar

import streamlit as st
import pandas as pd
import numpy as np
import os
import datetime
import uuid

# --- Constants & setup ---
SHARED_DIR = 'shared_histories'
os.makedirs(SHARED_DIR, exist_ok=True)

# --- Init session state for history ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=[
        'timestamp','goal','monthly_target','current_saved',
        'remaining','progress_fraction','happiness_fraction'
    ])

# --- Load shared history if provided ---
share_id = st.query_params.get("share_id")
if share_id:
    shared_file = os.path.join(SHARED_DIR, f"history_{share_id}.csv")
    if os.path.exists(shared_file):
        df_shared = pd.read_csv(shared_file, parse_dates=['timestamp'])
        st.session_state.history = df_shared
    else:
        st.warning("Share link not found or expired.")

# --- App title ---
st.title("📊 Savings Progress Tracker")

# --- Upload past history (optional) ---
st.markdown("---")
st.subheader("Upload Past History (Optional)")
uploaded_file = st.file_uploader("Upload a CSV of your past history", type=['csv'])
if uploaded_file:
    try:
        df_up = pd.read_csv(uploaded_file, parse_dates=['timestamp'])
        merged = pd.concat([st.session_state.history, df_up], ignore_index=True)
        merged = (merged
                  .drop_duplicates(subset=['timestamp','current_saved'], keep='last')
                  .sort_values('timestamp')
                  .reset_index(drop=True))
        st.session_state.history = merged
        st.success("History merged!")
    except Exception as e:
        st.error(f"Merge failed: {e}")

# --- Inputs for this month ---
st.markdown("---")
st.subheader("Input Current Month Savings")
default_goal = (st.session_state.history['goal'].iloc[-1]
                if not st.session_state.history.empty else 6000)
default_monthly = (st.session_state.history['monthly_target'].iloc[-1]
                   if not st.session_state.history.empty else 3000)

goal = st.number_input("Set your total savings goal (ZAR)",
                       min_value=0, value=int(default_goal), step=500)
monthly_target = st.number_input("Expected monthly savings (ZAR)",
                                 min_value=0, value=int(default_monthly), step=500)
current_saved = st.number_input("Amount saved so far this month (ZAR)",
                                min_value=0, value=0, step=500)

# --- Core calculations & display ---
progress = current_saved/goal if goal>0 else 0
progress = max(0,min(progress,1))
remaining = max(goal-current_saved,0)
happiness = current_saved/monthly_target if monthly_target>0 else 0
happiness = max(0,min(happiness,1))

if st.button("Save Entry"):
    new_rec = {
        'timestamp': datetime.datetime.now(),
        'goal': goal,
        'monthly_target': monthly_target,
        'current_saved': current_saved,
        'remaining': remaining,
        'progress_fraction': progress,
        'happiness_fraction': happiness
    }
    st.session_state.history = pd.concat(
        [st.session_state.history, pd.DataFrame([new_rec])],
        ignore_index=True
    )
    if share_id:
        st.session_state.history.to_csv(shared_file, index=False)
    st.success("Entry saved!")

# --- Sidebar: Category allocations based on TOTAL saved history ---
with st.sidebar:
    st.markdown("---")
    st.subheader("Auto-Allocate Your Savings to Categories")

    # Initialize allocations if first run
    if 'allocs' not in st.session_state:
        st.session_state.allocs = pd.DataFrame({
            'Usage': ['Housing'],
            'Goal Allocation (ZAR)': [10000],
        })

    # Editable allocations table
    editor = getattr(st, 'data_editor', None) or getattr(st, 'experimental_data_editor', None)
    if editor:
        alloc_df = editor(
            st.session_state.allocs,
            key='alloc_editor',
            num_rows="dynamic",
            use_container_width=True
        )
        if st.button("Update Categories"):
            st.session_state.allocs = alloc_df.copy()
    else:
        st.warning("Upgrade Streamlit to ≥1.19 for inline editing")
        st.dataframe(st.session_state.allocs)

    # Compute allocations
    df_alloc = st.session_state.allocs.copy()
    df_alloc['Goal Allocation (ZAR)'] = pd.to_numeric(
        df_alloc['Goal Allocation (ZAR)'], errors='coerce'
    ).fillna(0)
    total_alloc = df_alloc['Goal Allocation (ZAR)'].sum()

    # Warn if mismatch
    if total_alloc > goal:
        st.error(f"Allocations exceed goal by ZAR {total_alloc-goal:,.2f}")
    elif total_alloc < goal:
        st.warning(f"Total savings still needed for categories: ZAR {goal-total_alloc:,.2f}")
    else:
        st.success("Allocations match the total goal!")

    # Auto-allocate based on sum of history
    total_saved_history = st.session_state.history['current_saved'].sum()
    df_alloc['Saved So Far'] = (
        df_alloc['Goal Allocation (ZAR)'] / goal * total_saved_history
    ).round(2)
    df_alloc['Remaining in Cat'] = (
        df_alloc['Goal Allocation (ZAR)'] - df_alloc['Saved So Far']
    ).clip(lower=0).round(2)

    st.markdown("### 📂 Category Breakdown")
    st.table(df_alloc[['Usage',
                       'Goal Allocation (ZAR)',
                       'Saved So Far',
                       'Remaining in Cat']])

st.markdown("---")
st.subheader("Progress Summary")
st.progress(progress)
st.write(f"**Progress:** {progress*100:.1f}%")
st.write(f"**Remaining to goal:** ZAR {remaining:,.2f}")
if current_saved >= monthly_target:
    st.success("🎉 You hit or exceeded this month's target!")
elif current_saved >= 0.5*monthly_target:
    st.info("🙂 You’re halfway there.")
else:
    st.warning("😕 Behind this month's target—keep going!")

# --- Display Session History with inline editing & per-entry progress bars ---
st.markdown("---")
st.subheader("Your Savings History")

if not st.session_state.history.empty:
    # Inline edit
    if editor:
        hist_edited = editor(
            st.session_state.history,
            key='hist_editor',
            num_rows="dynamic",
            use_container_width=True
        )
        if st.button("Update History"):
            st.session_state.history = hist_edited
            st.success("History updated!")
    else:
        st.warning("Inline editing requires Streamlit ≥1.19 / ≥1.23.")
        st.dataframe(st.session_state.history)

    # Compute cumulative saved
    hist = st.session_state.history.copy().reset_index(drop=True)
    hist['cumulative_saved'] = hist['current_saved'].cumsum()

    # Per-entry progress bars
    st.markdown("### Progress by Entry")
    for idx, row in hist.iterrows():
        c1, c2, c3 = st.columns([2,1,4])
        # Timestamp as Month Day
        ts = row['timestamp']
        if not isinstance(ts, str):
            ts = ts.strftime('%b %d')
        c1.write(ts)
        # Cumulative saved
        c2.write(f"Saved: ZAR {row['cumulative_saved']}")
        # Progress bar
        p = row['cumulative_saved'] / row['goal'] if row['goal']>0 else 0
        p = max(0, min(p,1))
        c3.progress(p)

else:
    st.write("No entries yet. Save or upload history to get started.")

# --- Share link section ---
st.markdown("---")
st.subheader("Collaborate via Share Link")
if not share_id and not st.session_state.history.empty:
    if st.button("Generate Share Link"):
        new_id = uuid.uuid4().hex[:8]
        shared_file = os.path.join(SHARED_DIR, f"history_{new_id}.csv")
        st.session_state.history.to_csv(shared_file, index=False)
        st.query_params.share_id = new_id
        st.success(f"Share this link: ?share_id={new_id}")

# --- Reset Everything ---
st.markdown("---")
st.subheader("Clear All Data")
if st.button("Reset All Data"):
    st.session_state.history = pd.DataFrame(columns=[
        'timestamp','goal','monthly_target','current_saved',
        'remaining','progress_fraction','happiness_fraction'
    ])
    st.query_params.clear()
    st.markdown("""
        <script>
          window.history.replaceState(null,null,window.location.pathname);
          window.location.reload();
        </script>
    """, unsafe_allow_html=True)

# --- Footer ---
st.markdown("---")
st.write("*All data is stored privately in your browser session or via the share link.*")
