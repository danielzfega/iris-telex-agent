from app.models import TaskSummary
from typing import List, Optional
from loguru import logger
import asyncio
import os

# Default summarizer: uses OpenAI if available, otherwise a fallback simple summarizer
try:
    import openai
except Exception:
    openai = None

from app.config import settings

async def summarize_task_openai(title: str, content: str) -> TaskSummary:
    if not settings.openai_api_key or openai is None:
        raise RuntimeError("OpenAI not configured")
    openai.api_key = settings.openai_api_key
    prompt = (
        "You are Iris, an assistant that summarizes tasks posted in a team channel.\n"
        "Return a JSON object with fields: title, deliverables (list), deadline (string or null), plain_summary (short text).\n\n"
        f"Task title: {title}\n\n"
        f"Task content: {content}\n\n"
        "Produce only JSON."
    )
    # Use Chat Completions (change per your OpenAI SDK version)
    resp = await asyncio.to_thread(lambda: openai.ChatCompletion.create(
        model="gpt-4o-mini" if hasattr(openai, "ChatCompletion") else "gpt-4o",
        messages=[{"role":"user","content":prompt}],
        temperature=0.0,
        max_tokens=400
    ))
    text = resp["choices"][0]["message"]["content"]
    import json
    try:
        obj = json.loads(text)
        return TaskSummary(**obj)
    except Exception:
        # best effort fallback parse
        return TaskSummary(
            title=title,
            deliverables=[line.strip("-* ").strip() for line in content.splitlines() if line.strip().startswith("-")][:5],
            deadline=None,
            plain_summary=(content[:400] + "...") if len(content) > 400 else content
        )

async def summarize_fallback(title: str, content: str) -> TaskSummary:
    # super simple summarizer
    lines = [l.strip() for l in content.splitlines() if l.strip()]
    summary = (lines[0] if lines else content[:200])
    deliverables = [l.strip("-* ").strip() for l in lines if l.startswith("-")][:5]
    from app.handlers.task_detector import extract_deadline
    deadline = extract_deadline(content)
    return TaskSummary(title=title, deliverables=deliverables or [], deadline=deadline, plain_summary=summary)
