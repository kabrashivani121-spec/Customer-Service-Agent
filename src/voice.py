from __future__ import annotations
import io
from typing import Optional
from openai import OpenAI

def transcribe_wav_bytes(wav_bytes: bytes, api_key: str, model: str) -> str:
    """Speech-to-text using OpenAI Audio transcriptions."""
    client = OpenAI(api_key=api_key)
    file_obj = io.BytesIO(wav_bytes)
    file_obj.name = "audio.wav"  # some libs expect a name
    tx = client.audio.transcriptions.create(
        model=model,
        file=file_obj,
    )
    return (tx.text or "").strip()

def text_to_speech_mp3(text: str, api_key: str, model: str, voice: str = "alloy") -> bytes:
    """Text-to-speech using OpenAI Audio speech endpoint."""
    client = OpenAI(api_key=api_key)
    audio = client.audio.speech.create(
        model=model,
        voice=voice,
        input=text,
        format="mp3",
    )
    return audio.read()
