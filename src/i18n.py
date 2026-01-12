from __future__ import annotations
from langdetect import detect, LangDetectException
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

LANG_NAME = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "hi": "Hindi",
    "pt": "Portuguese",
    "zh-cn": "Chinese (Simplified)",
    "zh-tw": "Chinese (Traditional)",
    "ja": "Japanese",
    "ko": "Korean",
    "ar": "Arabic",
}

def detect_language(text: str) -> str:
    try:
        return detect(text)
    except LangDetectException:
        return "en"

def translate(text: str, target_lang: str, model: str) -> str:
    """Translate with the chat model to keep deps minimal.

    target_lang should be a BCP-47-ish short code like 'en', 'es', etc.
    """
    if not text.strip():
        return text
    if target_lang == "en":
        # If you want always-English internal processing, your caller will send en here.
        pass

    prompt = ChatPromptTemplate.from_template(
        "Translate the text to {target}. Keep meaning, tone, and formatting. "
        "Return only the translation.

Text:
{text}"
    )
    llm = ChatOpenAI(model=model, temperature=0)
    out = (prompt | llm).invoke({"target": LANG_NAME.get(target_lang, target_lang), "text": text}).content
    return out.strip()
