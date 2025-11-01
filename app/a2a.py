from fastapi import HTTPException
from app.models import JSONRPCRequest, JSONRPCResponse
from typing import Any

async def handle_jsonrpc(req: JSONRPCRequest) -> JSONRPCResponse:
    # minimal handler for "agent.info" or custom methods
    if req.method == "agent.info":
        return JSONRPCResponse(id=req.id, result={"name": "Iris", "capabilities": ["task-summary", "dm"]})
    # add more JSON-RPC methods here per A2A spec
    raise HTTPException(status_code=404, detail=f"Method {req.method} not found")
