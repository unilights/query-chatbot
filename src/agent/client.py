"""
client.py — Anthropic Claude agent: session management and multi-turn tool loop.
"""
import os
import sys
import json
import re
from typing import Any

import anthropic
from dotenv import load_dotenv

from ..config import LLM_MODEL, MAX_TOKENS
from .declarations import TOOL_DECLARATIONS, TOOL_REGISTRY

load_dotenv()

SYSTEM_INSTRUCTION = """
You are an intelligent business assistant for Unilights, a lighting manufacturing company.
You have access to tools for two domains:
1. ORDER DATA: Query orders, production status, dispatch, hold orders, customer order history.
2. BOM DATA: Query Bill of Materials to get component details, manufacturing costs, batch planning, product comparisons, and material sourcing.
Always use a tool to get data. Never guess or make up values.
Present results as a clean, professional summary. Use tables or bullet points.
For BOM cost queries, clearly show per-unit cost and highlight the most expensive components.
If a tool returns no result, say the information was not found.
"""


def _tprint(msg: str) -> None:
    """Force-print to stderr so Streamlit always shows it in the terminal."""
    print(msg, file=sys.stderr, flush=True)


def create_agent() -> anthropic.Anthropic:
    """Initialise and return an Anthropic client."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        _tprint("[Warning] ANTHROPIC_API_KEY is missing from environment.")
    client = anthropic.Anthropic(api_key=api_key)
    _tprint("[Agent] Anthropic Claude agent initialized.")
    return client


def _execute_tool(tool_use) -> Any:
    fn_name = tool_use.name
    fn_args = tool_use.input
    if fn_name not in TOOL_REGISTRY:
        return f"Error: Tool '{fn_name}' not found."
    return TOOL_REGISTRY[fn_name](**fn_args)


def query_agent(client: anthropic.Anthropic, user_input: str) -> tuple[str, str]:
    """
    Send *user_input* to Claude and handle multi-turn tool calling.
    Returns (final_answer, reasoning_log).
    """
    log: list[str] = []
    messages: list[Any] = [{"role": "user", "content": user_input}]

    def _log(msg: str) -> None:
        clean = re.sub(r"\x1b\[[0-9;]*m", "", str(msg))
        _tprint(clean)
        log.append(clean)

    try:
        _log(f"\n[User] {user_input}")

        while True:
            if not client.api_key:
                return (
                    "❌ Anthropic API Key is missing. Please add ANTHROPIC_API_KEY to your .env file.",
                    "\n".join(log),
                )

            _log("[LLM] Sending to Claude...")
            response = client.messages.create(
                model=LLM_MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_INSTRUCTION,
                tools=TOOL_DECLARATIONS,
                messages=messages,
            )

            assistant_content: list[dict] = []
            tool_uses = []

            for part in response.content:
                if part.type == "text":
                    assistant_content.append({"type": "text", "text": part.text})
                elif part.type == "tool_use":
                    tool_uses.append(part)
                    assistant_content.append({
                        "type":  "tool_use",
                        "id":    part.id,
                        "name":  part.name,
                        "input": part.input,
                    })

            messages.append({"role": "assistant", "content": assistant_content})

            # No tool calls → final answer
            if not tool_uses:
                final_answer = "".join(p["text"] for p in assistant_content if p["type"] == "text")
                _log(f"[Answer] {final_answer[:300]}...")
                return final_answer, "\n".join(log)

            # Execute tool calls and feed results back
            tool_results = []
            for tu in tool_uses:
                _log(f"[Tool Selected] {tu.name}({tu.input})")
                result = _execute_tool(tu)
                _log(f"[Tool Result] {json.dumps(result, indent=2, default=str)[:800]}")
                tool_results.append({
                    "type":        "tool_result",
                    "tool_use_id": tu.id,
                    "content":     json.dumps(result, default=str),
                })

            messages.append({"role": "user", "content": tool_results})

    except Exception as e:
        msg = f"❌ An error occurred: {e}"
        _log(f"[Exception] {e}")
        return msg, "\n".join(log)
