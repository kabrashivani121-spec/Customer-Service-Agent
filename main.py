from __future__ import annotations
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from config import validate_config, CHAT_MODEL
from src.support_agent import run_support, PROMPT_VARIANTS
from src.i18n import detect_language, translate

app = FastAPI(title="Customer Service Agent API", version="1.0")

validate_config()

class ChatRequest(BaseModel):
    query: str
    prompt_variant: str = "A"
    translate_in_out: bool = True

class ChatResponse(BaseModel):
    category: str
    sentiment: str
    response: str
    detected_language: str
    latency_ms: int

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if req.prompt_variant not in PROMPT_VARIANTS:
        raise HTTPException(status_code=400, detail=f"prompt_variant must be one of: {list(PROMPT_VARIANTS.keys())}")

    detected = detect_language(req.query) if req.translate_in_out else "en"
    q = req.query
    if req.translate_in_out and detected != "en":
        q = translate(req.query, target_lang="en", model=CHAT_MODEL)

    result = run_support(q, prompt_variant=req.prompt_variant, model=CHAT_MODEL)
    resp = result["response"]
    if req.translate_in_out and detected != "en":
        resp = translate(resp, target_lang=detected, model=CHAT_MODEL)

    return ChatResponse(
        category=result.get("category",""),
        sentiment=result.get("sentiment",""),
        response=resp,
        detected_language=detected,
        latency_ms=result.get("latency_ms",0),
    )
