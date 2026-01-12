# Customer Service Agent (Streamlit Cloud)

A customer service agent hosted on Streamlit Community Cloud with:
- LangGraph workflow (categorize → sentiment → route)
- Multi-language (auto-detect + translate in/out)
- Voice input (mic) + optional TTS playback
- Analytics dashboard (queries, sentiment, categories, latency)
- A/B testing for prompt strategies
- Feedback loop (thumbs up/down) stored in SQLite
- Rate limiting + caching to reduce cost/latency
- Optional REST API (FastAPI) for integrations

## Repo structure

```
.
├─ app.py                         # Streamlit entrypoint (Community Cloud)
├─ src/
│  ├─ support_agent.py            # LangGraph workflow + prompt variants
│  ├─ i18n.py                     # language detect + translate helpers
│  ├─ voice.py                    # STT + TTS helpers (OpenAI Audio API)
│  ├─ storage.py                  # SQLite schema + CRUD
│  ├─ cache.py                    # TTL cache
│  ├─ rate_limit.py               # per-session token bucket
│  ├─ analytics.py                # dashboard helpers
│  └─ integrations/
│     ├─ zendesk.py               # example ticketing integration stubs
│     ├─ freshdesk.py
│     └─ hubspot.py
├─ pages/
│  ├─ 1_📊_Analytics.py           # Streamlit multipage dashboard
│  └─ 2_⚙️_Admin.py                # Admin tools (export DB, prompt notes)
└─ api/
   └─ main.py                     # FastAPI REST endpoint (deploy separately)
```

## Streamlit Cloud setup

1. Push this repo to GitHub.
2. In Streamlit Community Cloud → **Deploy**.
3. Add secrets (App settings → Secrets):

```toml
OPENAI_API_KEY="YOUR_KEY"
```

The app stores a small SQLite DB locally in `data/app.db`.

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## REST API (optional)

Streamlit Community Cloud can’t run a separate FastAPI backend in the same deployment. Deploy the API separately (e.g., Render/Fly/Cloud Run) and point your CRM/ticketing system to it.

Local:
```bash
uvicorn api.main:app --reload --port 8000
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"query":"Where is my invoice?","prompt_variant":"A"}'
```
