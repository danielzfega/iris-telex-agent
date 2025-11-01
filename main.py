import uvicorn
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from app.config import settings
from app.models import JSONRPCRequest, JSONRPCResponse, TelexMessageEvent
from app.a2a import handle_jsonrpc
from app.services.telex_client import TelexClient
from app.services import redis_store
from app.handlers import task_detector, summarizer
from loguru import logger
import json

app = FastAPI(title="Iris - Telex A2A Agent")

telex_client = TelexClient(settings.telex_base_url, settings.telex_api_key)

@app.get("/.well-known/agent.json")
async def agent_card():
    """
    A2A discovery card — Telex will GET this to learn about agent.
    Fill per A2A spec (capabilities, public URL, contact).
    """
    card = {
        "id": settings.agent_id,
        "name": "Iris",
        "description": "Iris: auto-detects tasks and DMs clear summaries to assignees.",
        "url": str(settings.agent_public_url),
        "capabilities": ["task-summary", "notifications"],
        "endpoints": {
            "a2a": f"{settings.agent_public_url}/a2a/jsonrpc",
            "events": f"{settings.agent_public_url}/webhook/events"
        }
    }
    return JSONResponse(card)

@app.post("/a2a/jsonrpc")
async def a2a_jsonrpc(request: Request):
    body = await request.json()
    req = JSONRPCRequest(**body)
    try:
        resp = await handle_jsonrpc(req)
        return JSONResponse(content=resp.model_dump())
    except Exception as e:
        logger.exception("A2A handler error")
        return JSONResponse(status_code=500, content={"jsonrpc": "2.0", "id": req.id, "error": {"message": str(e)}})

@app.post("/webhook/events")
async def webhook_events(event: TelexMessageEvent, background_tasks: BackgroundTasks):
    """
    Entry point for Telex notifications (message.created etc).
    When a new message arrives, determine if it's a task. If yes, summarize and DM.
    """
    # Basic dedupe: skip if we've already processed this message
    seen = await redis_store.has_seen_message(event.message_id)
    if seen:
        return {"status": "ignored-already-seen"}
    await redis_store.save_seen_message(event.message_id)

    # Quick heuristic: only react to message.created events
    if event.event_type not in ("message.created", "message.posted", "message.new"):
        return {"status": "ignored-event-type"}

    # Does this message look like a task?
    if not task_detector.looks_like_task(event.content):
        return {"status": "ignored-no-task-like-pattern"}

    # run summarizer in background
    background_tasks.add_task(process_task_message, event)
    return {"status": "accepted"}

async def process_task_message(event: TelexMessageEvent):
    try:
        title = task_detector.extract_title(event.content)
        # prefer OpenAI summarizer if available
        try:
            if settings.openai_api_key:
                summary = await summarizer.summarize_task_openai(title, event.content)
            else:
                summary = await summarizer.summarize_fallback(title, event.content)
        except Exception:
            summary = await summarizer.summarize_fallback(title, event.content)

        # Build DM content
        dm = build_dm_message(event, summary)
        # send DM
        await telex_client.send_dm(event.author_id, dm)
    except Exception as e:
        logger.exception("failed to process task message: %s", e)

def build_dm_message(event: TelexMessageEvent, summary):
    lines = [
        f"🟣 Iris detected a task in **{event.channel_name or event.channel_id}**",
        f"**Title:** {summary.title}",
        f"**Summary:** {summary.plain_summary}",
    ]
    if summary.deliverables:
        lines.append("**Core deliverables:**")
        for d in summary.deliverables:
            lines.append(f"- {d}")
    if summary.deadline:
        lines.append(f"**Deadline:** {summary.deadline}")
    lines.append(f"_Original message:_\n> " + (event.content[:600] + ("..." if len(event.content) > 600 else "")))
    lines.append("\nIf you'd like, I can create a calendar reminder or add this to your personal todo list. Reply `@Iris remind me`.")
    return "\n\n".join(lines)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=5001, reload=True)
