from __future__ import annotations

import uuid
import time
import hashlib
import streamlit as st

from config import (
    validate_config, OPENAI_API_KEY, CHAT_MODEL, STT_MODEL, TTS_MODEL,
    DB_PATH, CACHE_MAXSIZE, CACHE_TTL_SECONDS, RATE_LIMIT_RPM
)
from src.storage import DB
from src.cache import AppCache
from src.rate_limit import TokenBucket
from src.support_agent import run_support, PROMPT_VARIANTS
from src.i18n import detect_language, translate
from src.voice import transcribe_wav_bytes, text_to_speech_mp3

st.set_page_config(page_title="Customer Service Agent", page_icon="💬", layout="wide")

# --- init ---
validate_config()
db = DB(DB_PATH)
cache = AppCache(maxsize=CACHE_MAXSIZE, ttl_seconds=CACHE_TTL_SECONDS)

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "bucket" not in st.session_state:
    st.session_state.bucket = TokenBucket(rpm=RATE_LIMIT_RPM)
if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = None
if "last_conversation_db_id" not in st.session_state:
    st.session_state.last_conversation_db_id = None

st.title("💬 Customer Service Agent")
st.caption("Text chat + voice prompts, with A/B prompt testing, multilingual support, history, and analytics.")

# --- sidebar controls ---
with st.sidebar:
    st.header("Controls")
    input_mode = st.radio(
        "Input methods",
        options=["Both", "Text only", "Voice only"],
        index=0,
        help="Use text chat, voice prompts, or both at the same time."
    )
    prompt_variant = st.selectbox("Prompt strategy (A/B)", list(PROMPT_VARIANTS.keys()), index=0)
    enable_tts = st.toggle("Voice response (TTS)", value=False)
    st.divider()
    st.caption("Deploy on Streamlit Cloud: set OPENAI_API_KEY in **Secrets**.")

# --- helpers ---
def render_messages():
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m.get("audio_mp3_b64"):
                st.audio(m["audio_mp3_b64"], format="audio/mp3")

def handle_user_message(user_query: str, source: str = "text"):
    user_query = (user_query or "").strip()
    if not user_query:
        return

    # Rate limiting (per Streamlit session)
    if not st.session_state.bucket.allow():
        st.warning("Rate limit exceeded. Please wait a bit and try again.")
        return

    t0 = time.time()

    # Show user message
    label = "🎙️" if source == "voice" else "⌨️"
    st.session_state.messages.append({"role": "user", "content": f"{label} {user_query}"})

    # Cache key includes prompt variant + text
    cache_key = f"{prompt_variant}::{user_query}"

    # Multilingual: translate to English for routing, then back to detected language
    detected = detect_language(user_query)
    internal_query = user_query
    final_lang = detected

    if detected != "en":
        internal_query = translate(user_query, target_lang="en", model=CHAT_MODEL)
        final_lang = detected

    def _compute():
        return run_support(internal_query, prompt_variant=prompt_variant, model=CHAT_MODEL)

    result = cache.get_or_set(cache_key, _compute)

    # Translate response back if needed
    response_text = result["response"]
    if final_lang != "en":
        response_text = translate(response_text, target_lang=final_lang, model=CHAT_MODEL)

    latency_ms = int((time.time() - t0) * 1000)

    audio_mp3_b64 = None
    if enable_tts:
        try:
            audio_mp3_b64 = text_to_speech_mp3(response_text, model=TTS_MODEL)
        except Exception as e:
            # Don't break the UX if TTS fails
            st.toast(f"TTS error: {e}", icon="⚠️")

    st.session_state.messages.append(
        {"role": "assistant", "content": response_text, "audio_mp3_b64": audio_mp3_b64}
    )

    # Persist one row per turn (query + response)
    conv_db_id = db.insert_conversation(
        session_id=st.session_state.session_id,
        user_query=user_query,
        detected_language=detected,
        prompt_variant=prompt_variant,
        category=result.get("category"),
        sentiment=result.get("sentiment"),
        response=response_text,
        latency_ms=latency_ms,
    )
    st.session_state.last_conversation_db_id = conv_db_id

# --- UI layout ---
col_left, col_right = st.columns([2, 1], gap="large")

with col_left:
    st.subheader("Chat")
    render_messages()

    # Text chat input (kept alongside voice prompt if input_mode == Both)
    if input_mode in ("Both", "Text only"):
        typed = st.chat_input("Type your question…")
        if typed:
            handle_user_message(typed, source="text")

with col_right:
    st.subheader("Voice prompts")

    if input_mode in ("Both", "Voice only"):
        st.caption("Record a short prompt; it will be transcribed and handled like a chat message.")
        audio = st.audio_input("Record a question (WAV)")
        if audio is not None:
            wav_bytes = audio.getvalue()
            h = hashlib.sha256(wav_bytes).hexdigest()
            st.audio(wav_bytes, format="audio/wav")

            # Prevent re-processing same recording across Streamlit reruns
            if st.session_state.last_audio_hash != h:
                st.session_state.last_audio_hash = h
                with st.spinner("Transcribing…"):
                    try:
                        transcript = transcribe_wav_bytes(wav_bytes, model=STT_MODEL)
                        st.success(f"Transcript: {transcript}")
                        handle_user_message(transcript, source="voice")
                    except Exception as e:
                        st.error(f"Transcription failed: {e}")
            else:
                st.info("Already processed this recording.")

    st.divider()
    st.subheader("Feedback")
    st.caption("This is stored in SQLite and can be exported in the Admin page.")

    fb_cols = st.columns(3)
    with fb_cols[0]:
        up = st.button("👍 Helpful", use_container_width=True)
    with fb_cols[1]:
        down = st.button("👎 Not helpful", use_container_width=True)
    with fb_cols[2]:
        comment = st.text_input("Optional comment", key="fb_comment")

    # Store feedback against the latest assistant turn (best-effort)
    if up or down:
        rating = 1 if up else -1
        if st.session_state.last_conversation_db_id is None:
            st.warning("Send at least one message before leaving feedback.")
        else:
            db.insert_feedback(conversation_id=st.session_state.last_conversation_db_id, rating=rating, comment=comment or None)
        st.toast("Thanks! Saved feedback.", icon="✅")

st.info("Tip: Open **📊 Analytics** to see trends and A/B comparison.")
