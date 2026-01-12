from __future__ import annotations
import streamlit as st
import pandas as pd
from config import DB_PATH
from src.storage import DB

st.set_page_config(page_title="Admin", page_icon="⚙️", layout="wide")
st.title("⚙️ Admin")

db = DB(DB_PATH)
db.init()

st.subheader("Export database tables")

col1, col2 = st.columns(2)
with col1:
    conv = db.fetch_conversations(limit=5000)
    conv_df = pd.DataFrame(conv)
    st.download_button(
        "Download conversations.csv",
        conv_df.to_csv(index=False).encode("utf-8"),
        file_name="conversations.csv",
        mime="text/csv",
        use_container_width=True,
    )

with col2:
    fb = db.fetch_feedback_joined(limit=5000)
    fb_df = pd.DataFrame(fb)
    st.download_button(
        "Download feedback.csv",
        fb_df.to_csv(index=False).encode("utf-8"),
        file_name="feedback.csv",
        mime="text/csv",
        use_container_width=True,
    )

st.subheader("Latest feedback")
if fb_df.empty:
    st.info("No feedback yet.")
else:
    st.dataframe(fb_df.head(100), use_container_width=True)

st.caption("Note: For a true learning system, periodically retrain prompts or a retrieval layer using this feedback.")
