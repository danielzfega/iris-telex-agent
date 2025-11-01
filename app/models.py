from pydantic import BaseModel
from typing import Any, Optional, List

# Minimal JSON-RPC model for A2A requests
class JSONRPCRequest(BaseModel):
    jsonrpc: str
    id: Optional[str]
    method: str
    params: Optional[dict] = {}

class JSONRPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[str]
    result: Optional[Any] = None
    error: Optional[dict] = None

# Telex webhook event (simplified)
class TelexMessageEvent(BaseModel):
    event_type: str
    message_id: str
    channel_id: str
    channel_name: Optional[str]
    author_id: str
    author_name: Optional[str]
    content: str
    timestamp: str

class TaskSummary(BaseModel):
    title: str
    deliverables: List[str]
    deadline: Optional[str]
    plain_summary: str
