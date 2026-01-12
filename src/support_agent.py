from __future__ import annotations
import time
from typing import Dict, TypedDict, Literal, Optional
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

class State(TypedDict, total=False):
    query: str
    prompt_variant: str
    category: str
    sentiment: str
    response: str

class Classification(BaseModel):
    category: Literal["Technical", "Billing", "General"] = Field(...)
    sentiment: Literal["Positive", "Neutral", "Negative"] = Field(...)

PROMPT_VARIANTS: dict[str, dict[str, str]] = {
    "A": {
        "system": "You are a concise, accurate customer support agent. Ask a single clarifying question if needed.",
        "technical": "Provide a clear technical troubleshooting response with steps, checks, and next actions.",
        "billing": "Provide a billing support response. Be precise, confirm billing identifiers needed, and propose next steps.",
        "general": "Provide a friendly, clear general support response.",
    },
    "B": {
        "system": "You are an empathetic customer support agent. Acknowledge feelings, then solve. Keep it brief.",
        "technical": "Start with a short empathy line, then troubleshooting steps. End with an offer to escalate.",
        "billing": "Start with a short empathy line, then explain policy and next steps. End with escalation option.",
        "general": "Start with empathy, then answer and link to next action.",
    },
}

def _llm(model: str):
    return ChatOpenAI(model=model, temperature=0)

def classify(state: State, model: str) -> State:
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Classify the customer message into category and sentiment. Output JSON only."),
        ("user", "{query}"),
    ])
    llm = _llm(model).with_structured_output(Classification)
    result: Classification = (prompt | llm).invoke({"query": state["query"]})
    return {"category": result.category, "sentiment": result.sentiment}

def _respond(state: State, model: str, kind: str) -> State:
    v = PROMPT_VARIANTS.get(state.get("prompt_variant","A"), PROMPT_VARIANTS["A"])
    prompt = ChatPromptTemplate.from_messages([
        ("system", v["system"]),
        ("user", v[kind] + "\n\nCustomer query: {query}"),
    ])
    response = (prompt | _llm(model)).invoke({"query": state["query"]}).content
    return {"response": response.strip()}

def handle_technical(state: State, model: str) -> State:
    return _respond(state, model, "technical")

def handle_billing(state: State, model: str) -> State:
    return _respond(state, model, "billing")

def handle_general(state: State, model: str) -> State:
    return _respond(state, model, "general")

def escalate(state: State) -> State:
    return {"response": "I’m escalating this to a human agent due to negative sentiment. Please share your account email/order ID and best callback time."}

def route_query(state: State) -> str:
    if state.get("sentiment") == "Negative":
        return "escalate"
    if state.get("category") == "Technical":
        return "handle_technical"
    if state.get("category") == "Billing":
        return "handle_billing"
    return "handle_general"

def build_workflow(model: str):
    workflow = StateGraph(State)
    workflow.add_node("classify", lambda s: classify(s, model))
    workflow.add_node("handle_technical", lambda s: handle_technical(s, model))
    workflow.add_node("handle_billing", lambda s: handle_billing(s, model))
    workflow.add_node("handle_general", lambda s: handle_general(s, model))
    workflow.add_node("escalate", escalate)

    workflow.add_conditional_edges(
        "classify",
        route_query,
        {
            "handle_technical": "handle_technical",
            "handle_billing": "handle_billing",
            "handle_general": "handle_general",
            "escalate": "escalate",
        },
    )
    for node in ["handle_technical","handle_billing","handle_general","escalate"]:
        workflow.add_edge(node, END)

    workflow.set_entry_point("classify")
    return workflow.compile()

def run_support(query: str, prompt_variant: str, model: str) -> Dict[str, str]:
    app = build_workflow(model)
    started = time.time()
    result = app.invoke({"query": query, "prompt_variant": prompt_variant})
    latency_ms = int((time.time() - started) * 1000)
    return {
        "category": result.get("category",""),
        "sentiment": result.get("sentiment",""),
        "response": result.get("response",""),
        "latency_ms": latency_ms,
    }
