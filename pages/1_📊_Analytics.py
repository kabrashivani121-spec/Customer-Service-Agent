from __future__ import annotations
import streamlit as st
import plotly.express as px
from config import DB_PATH
from src.storage import DB
from src.analytics import conversations_df

st.set_page_config(page_title="Analytics", page_icon="📊", layout="wide")

st.title("📊 Analytics Dashboard")
st.caption("Query patterns, sentiment trends, prompt A/B comparison, and latency.")

db = DB(DB_PATH)
db.init()

rows = db.fetch_conversations(limit=2000)
df = conversations_df(rows)

if df.empty:
    st.warning("No data yet. Go to the main app and run a few queries.")
    st.stop()

# Filters
with st.sidebar:
    st.header("Filters")
    variants = sorted([v for v in df["prompt_variant"].dropna().unique()])
    chosen_variants = st.multiselect("Prompt variants", variants, default=variants)
    sentiments = sorted([s for s in df["sentiment"].dropna().unique()])
    chosen_sentiments = st.multiselect("Sentiments", sentiments, default=sentiments)

f = df[
    df["prompt_variant"].isin(chosen_variants) &
    df["sentiment"].isin(chosen_sentiments)
].copy()

kpis = st.columns(4)
kpis[0].metric("Total queries", len(f))
kpis[1].metric("Unique sessions", f["session_id"].nunique())
kpis[2].metric("Avg latency (ms)", int(f["latency_ms"].dropna().mean()))
kpis[3].metric("Neg sentiment %", round((f["sentiment"]=="Negative").mean()*100, 1))

c1, c2 = st.columns(2)
with c1:
    st.subheader("Categories")
    fig = px.histogram(f, x="category", color="prompt_variant", barmode="group")
    st.plotly_chart(fig, use_container_width=True)
with c2:
    st.subheader("Sentiment")
    fig = px.histogram(f, x="sentiment", color="prompt_variant", barmode="group")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Latency over time")
fig = px.scatter(f.sort_values("created_at"), x="created_at", y="latency_ms", color="prompt_variant")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Raw data")
st.dataframe(f.sort_values("created_at", ascending=False).head(200), use_container_width=True)
