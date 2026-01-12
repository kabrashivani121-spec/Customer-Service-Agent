# src/i18n.py

from langdetect import detect
from openai import OpenAI
from config import OPENAI_MODEL

client = OpenAI()


def detect_language(text: str) -> str:
    try:
        return detect(text)
    except Exception:
        return "en"


def translate(text: str, target_lang: str) -> str:
    """
    Translates text to target_lang using OpenAI.
    If target_lang == 'en', returns text unchanged.
    """
    if target_lang == "en":
        return text

    prompt = (
        f"Translate the following text to {target_lang}. "
        "Return only the translated text.\n\n"
        f"Text: {text}"
    )

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return response.choices[0].message.content.strip()
