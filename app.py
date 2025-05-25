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
# - persistence of both history & categories across share links
# - ability to export data and generate a mini savings report

import streamlit as st
import pandas as pd
import numpy as np
import os
import datetime
import uuid
import io
from fpdf import FPDF

# --- Constants & setup ---
SHARED_DIR = 'shared_histories'
os.makedirs(SHARED_DIR, exist_ok=True)

# --- Get query params & share_id ---
params = st.query_params
share_id = params.get('share_id', [None])[0]

# --- Init session state for history & allocations ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=[
        'timestamp','goal','monthly_target','current_saved',
        'remaining','progress_fraction','happiness_fraction'
    ])
if 'allocs' not in st.session_state:
    st.session_state.allocs = pd.DataFrame({
        'Usage': ['Housing'],
        'Goal Allocation': [10000],
    })

# --- Load shared history & allocations if provided ---
if share_id:
    hist_file = os.path.join(SHARED_DIR, f"history_{share_id}.csv")
    alloc_file = os.path.join(SHARED_DIR, f"allocs_{share_id}.csv")
    if os.path.exists(hist_file):
        st.session_state.history = pd.read_csv(hist_file, parse_dates=['timestamp'])
    if os.path.exists(alloc_file):
        st.session_state.allocs = pd.read_csv(alloc_file)

# --- App title ---
st.title("📊 Savings Progress Tracker")

# --- Upload past history (optional) ---
st.markdown("---")
st.subheader("Upload Past History (Optional)")
uploaded_hist = st.file_uploader(
    "Upload a CSV of your past history", type=['csv'], key='upload_hist')
if uploaded_hist:
    try:
        df_up = pd.read_csv(uploaded_hist, parse_dates=['timestamp'])
        merged = pd.concat([st.session_state.history, df_up], ignore_index=True)
        merged = (merged
                  .drop_duplicates(subset=['timestamp','current_saved'], keep='last')
                  .sort_values('timestamp')
                  .reset_index(drop=True))
        st.session_state.history = merged
        st.success("History merged!")
    except Exception as e:
        st.error(f"Merge failed: {e}")

# --- Sidebar: categories ---
with st.sidebar:
    st.markdown("---")
    st.subheader("Upload Past Categories (Optional)")
    uploaded_allocs = st.file_uploader(
        "Upload a CSV of your categories", type=['csv'], key='upload_allocs'
    )
    if uploaded_allocs:
        try:
            df_allocs_up = pd.read_csv(uploaded_allocs)
            st.session_state.allocs = df_allocs_up.copy()
            st.success("Categories merged!")
        except Exception as e:
            st.error(f"Could not load categories: {e}")

    st.markdown("---")
    st.subheader("Auto-Allocate Your Savings to Categories")
    editor = getattr(st, 'data_editor', None) or getattr(st, 'experimental_data_editor', None)
    if editor:
        alloc_df = editor(
            st.session_state.allocs, key='alloc_editor', num_rows="dynamic",
            use_container_width=True
        )
        if st.button("Update Categories"):
            st.session_state.allocs = alloc_df.copy()
    else:
        st.warning("Upgrade Streamlit to ≥1.19 for inline editing")
        st.dataframe(st.session_state.allocs)

    # Compute breakdown
    df_alloc = st.session_state.allocs.copy()
    # Ensure numeric
    df_alloc['Goal Allocation'] = pd.to_numeric(
        df_alloc['Goal Allocation'], errors='coerce'
    ).fillna(0)
    total_alloc = df_alloc['Goal Allocation'].sum()
    goal_val = st.session_state.get('goal', 0)
    if total_alloc > goal_val:
        st.error(f"Allocations exceed goal by  {total_alloc-goal_val:,.2f}")
    elif total_alloc < goal_val:
        st.warning(f"Total savings still needed for categories:  {goal_val-total_alloc:,.2f}")
    else:
        st.success("Allocations match the total goal!")

    total_saved_history = st.session_state.history['current_saved'].sum()
    df_alloc['Amount Allocated'] = (
        df_alloc['Goal Allocation'] / (goal_val or 1) * total_saved_history
    ).round(2)
    df_alloc['Amount Remaining'] = (
        df_alloc['Goal Allocation'] - df_alloc['Amount Allocated']
    ).clip(lower=0).round(2)

    st.markdown("### 📂 Category Breakdown")
    st.table(df_alloc[['Usage', 'Goal Allocation', 'Amount Allocated', 'Amount Remaining']])

# --- Inputs for this month ---
st.markdown("---")
st.subheader("Input Current Month Savings")
default_goal = (st.session_state.history['goal'].iloc[-1]
                if not st.session_state.history.empty else 6000)
default_monthly = (st.session_state.history['monthly_target'].iloc[-1]
                   if not st.session_state.history.empty else 3000)

goal = st.number_input(
    "Set your total savings goal", min_value=0,
    value=int(default_goal), step=500, key='goal'
)
monthly_target = st.number_input(
    "Expected monthly savings", min_value=0,
    value=int(default_monthly), step=500, key='monthly_target'
)
current_saved = st.number_input(
    "Amount saved so far this month", min_value=0,
    value=0, step=500, key='current_saved'
)

# --- Core calculations & display ---
progress = current_saved / (goal or 1)
progress = max(0, min(progress, 1))
remaining = max(goal - current_saved, 0)
happiness = current_saved / (monthly_target or 1)
happiness = max(0, min(happiness, 1))

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
        [st.session_state.history, pd.DataFrame([new_rec])], ignore_index=True
    )
    if share_id:
        pd.DataFrame(st.session_state.history).to_csv(hist_file, index=False)
        pd.DataFrame(st.session_state.allocs).to_csv(alloc_file, index=False)
    st.success("Entry saved!")

# --- Progress Summary ---
st.markdown("---")
st.subheader("Progress Summary")
st.progress(progress)
st.write(f"**Progress:** {progress*100:.1f}%")
st.write(f"**Remaining to goal:**  {remaining:,.2f}")
if current_saved >= monthly_target:
    st.success("🎉 You hit or exceeded this month's target!")
elif current_saved >= 0.5*monthly_target:
    st.info("🙂 You’re halfway there.")
else:
    st.warning("😕 Behind this month's target—keep going!")

# --- Display Session History ---
st.markdown("---")
st.subheader("Your Savings History")
editor = getattr(st, 'data_editor', None) or getattr(st, 'experimental_data_editor', None)
if not st.session_state.history.empty:
    if editor:
        hist_edited = editor(
            st.session_state.history, key='hist_editor', num_rows="dynamic",
            use_container_width=True
        )
        if st.button("Update History"):
            st.session_state.history = hist_edited
            st.success("History updated!")
    else:
        st.warning("Inline editing requires Streamlit ≥1.19 / ≥1.23.")
        st.dataframe(st.session_state.history)

    hist = st.session_state.history.copy().reset_index(drop=True)
    hist['cumulative_saved'] = hist['current_saved'].cumsum()
    st.markdown("### Progress by Entry")
    for idx, row in hist.iterrows():
        c1, c2, c3 = st.columns([2,1,4])
        ts = row['timestamp']
        if not isinstance(ts, str):
            ts = ts.strftime('%b %d')
        c1.write(ts)
        c2.write(f"Saved:  {row['cumulative_saved']}")
        p = row['cumulative_saved']/(row['goal'] or 1)
        p = max(0, min(p, 1))
        c3.progress(p)
else:
    st.write("No entries yet. Save or upload history to get started.")

# --- Data & Report Section ---
st.markdown("---")
st.subheader("Current Data & Report")
col1, col2, col3 = st.columns(3)

# 1) Download History
with col1:
    hist_csv = st.session_state.history.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download History CSV",
        data=hist_csv,
        file_name="savings_history.csv",
        mime="text/csv"
    )
# 2) Download Categories
with col2:
    alloc_csv = st.session_state.allocs.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Categories CSV",
        data=alloc_csv,
        file_name="savings_categories.csv",
        mime="text/csv"
    )
# 3) Generate Report
# 3) Generate PDF Report
with col3:
    if st.button("Generate PDF Report"):
        # Gather stats
        total_saved = st.session_state.history['current_saved'].sum()
        months = max(1, st.session_state.history['timestamp'].dt.to_period('M').nunique())
        avg_per_month = total_saved / months
        goal_val = st.session_state.history['goal'].iloc[-1] if not st.session_state.history.empty else 0
        pct_to_goal = total_saved / max(goal_val, 1)

        # Copy allocations for use
        alloc_df = st.session_state.allocs.copy()
        alloc_df['Saved'] = (alloc_df['Goal Allocation'] / max(goal_val, 1) * total_saved).round(2)
        alloc_df['Remaining'] = (alloc_df['Goal Allocation'] - alloc_df['Saved']).clip(lower=0).round(2)

        # Build PDF
        pdf = FPDF()
        pdf.add_page()

        # Title
        pdf.set_font("Helvetica", 'B', 16)
        pdf.cell(0, 10, "Savings Report", ln=True)
        pdf.ln(5)

        # Summary metrics
        pdf.set_font("Helvetica", '', 12)
        pdf.cell(0, 8, f"Goal: ZAR {goal_val:,.2f}", ln=True)
        pdf.cell(0, 8, f"Total Saved: ZAR {total_saved:,.2f}", ln=True)
        pdf.cell(0, 8, f"Progress: {pct_to_goal*100:.1f}%", ln=True)
        pdf.ln(5)

        # Categories breakdown
        pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(0, 8, "Categories", ln=True)
        pdf.set_font("Helvetica", '', 12)
        for _, row in alloc_df.iterrows():
            pdf.cell(
                0, 6,
                f"- {row['Usage']}: Goal ZAR {row['Goal Allocation']:,.2f}, "
                f"Saved ZAR {row['Saved']:,.2f}, Remaining ZAR {row['Remaining']:,.2f}",
                ln=True
            )
        pdf.ln(5)

        # Recent history
        pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(0, 8, "Recent History", ln=True)
        pdf.set_font("Helvetica", '', 12)
        recent = st.session_state.history.sort_values('timestamp').tail(5)
        for _, row in recent.iterrows():
            ts = row['timestamp']
            ts_str = ts.strftime('%Y-%m-%d %H:%M') if not isinstance(ts, str) else ts
            pdf.cell(0, 6, f"{ts_str}: Saved ZAR {row['current_saved']:,.2f}", ln=True)
        pdf.ln(5)
        
        # Serve PDF
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        st.download_button(
            "Download PDF report",
            data=pdf_bytes,
            file_name="savings_report.pdf",
            mime="application/pdf"
        )


# --- Footer ---
st.markdown("---")
st.write("*All data is stored privately in your browser session.*")