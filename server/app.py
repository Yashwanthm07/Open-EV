"""
Email Triage Environment — FastAPI Server

Provides REST + WebSocket endpoints following the OpenEnv spec.
Requires: fastapi, uvicorn, pydantic (see requirements.txt)
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from email_triage.environment import EmailTriageEnvironment
from email_triage.models import EmailTriageAction

app = FastAPI(
    title="Email Triage OpenEnv",
    description="Real-world email triage environment for AI agent training and evaluation.",
    version="1.0.0",
    docs_url="/docs",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_environments: Dict[str, EmailTriageEnvironment] = {}


def _serialize(obj: Any) -> Any:
    if hasattr(obj, "model_dump"):
        return _serialize(obj.model_dump())
    if isinstance(obj, list):
        return [_serialize(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    return obj


class ResetRequest(BaseModel):
    task_name: Optional[str] = "email_triage_easy"
    session_id: Optional[str] = "default"
    seed: Optional[int] = None
    episode_id: Optional[str] = None


class StepRequest(BaseModel):
    session_id: Optional[str] = "default"
    action_type: str
    label: Optional[str] = None
    reply_text: Optional[str] = None
    forward_to: Optional[str] = None
    reasoning: Optional[str] = None


@app.get("/health")
async def health():
    return {"status": "ok", "service": "email-triage-openenv", "version": "1.0.0"}


@app.get("/")
async def root():
    return {
        "name": "email-triage-openenv",
        "description": "Real-world corporate email triage environment",
        "tasks": ["email_triage_easy", "email_triage_medium", "email_triage_hard"],
        "endpoints": ["/reset", "/step", "/state", "/summary", "/tasks", "/health", "/docs", "/web"],
    }


@app.post("/reset")
async def reset(req: ResetRequest):
    sid = req.session_id or "default"
    _environments[sid] = EmailTriageEnvironment(task_name=req.task_name or "email_triage_easy")
    obs = _environments[sid].reset(seed=req.seed, episode_id=req.episode_id)
    return {"observation": _serialize(obs), "done": obs.done, "reward": obs.reward,
            "info": {"session_id": sid, "task": req.task_name}}


@app.post("/step")
async def step(req: StepRequest):
    sid = req.session_id or "default"
    if sid not in _environments:
        raise HTTPException(400, f"Session '{sid}' not found. Call /reset first.")
    action = EmailTriageAction(action_type=req.action_type, label=req.label,
                                reply_text=req.reply_text, forward_to=req.forward_to,
                                reasoning=req.reasoning)
    obs, reward, done, info = _environments[sid].step(action)
    return {"observation": _serialize(obs), "reward": reward, "done": done, "info": info}


@app.get("/state")
async def state(session_id: str = "default"):
    if session_id not in _environments:
        raise HTTPException(400, f"Session '{session_id}' not found.")
    return _serialize(_environments[session_id].state())


@app.get("/summary")
async def summary(session_id: str = "default"):
    if session_id not in _environments:
        raise HTTPException(400, f"Session '{session_id}' not found.")
    return _environments[session_id].get_episode_summary()


@app.get("/tasks")
async def list_tasks():
    from email_triage.data import TASKS
    return {n: {"description": c["description"], "difficulty": c["difficulty"],
                "email_count": len(c["emails"]), "max_steps": c["max_steps"]}
            for n, c in TASKS.items()}


@app.get("/web", response_class=HTMLResponse)
async def web_ui():
    return HTMLResponse(content=open(
        os.path.join(os.path.dirname(__file__), "..", "web_ui.html")
    ).read() if os.path.exists(
        os.path.join(os.path.dirname(__file__), "..", "web_ui.html")
    ) else "<html><body><h1>Email Triage OpenEnv</h1><p><a href='/docs'>API Docs</a></p></body></html>")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    sid = f"ws_{id(websocket)}"
    try:
        while True:
            msg = json.loads(await websocket.receive_text())
            cmd = msg.get("command", "")
            if cmd == "reset":
                _environments[sid] = EmailTriageEnvironment(
                    task_name=msg.get("task_name", "email_triage_easy"))
                obs = _environments[sid].reset(seed=msg.get("seed"), episode_id=msg.get("episode_id"))
                await websocket.send_text(json.dumps(
                    {"observation": _serialize(obs), "done": obs.done, "reward": obs.reward}))
            elif cmd == "step":
                if sid not in _environments:
                    await websocket.send_text(json.dumps({"error": "Not initialised"}))
                    continue
                action = EmailTriageAction(action_type=msg.get("action_type", "archive"),
                                          label=msg.get("label"), reply_text=msg.get("reply_text"),
                                          forward_to=msg.get("forward_to"), reasoning=msg.get("reasoning"))
                obs, reward, done, info = _environments[sid].step(action)
                await websocket.send_text(json.dumps(
                    {"observation": _serialize(obs), "reward": reward, "done": done, "info": info}))
            elif cmd == "state":
                await websocket.send_text(json.dumps(
                    _serialize(_environments[sid].state()) if sid in _environments else {"error": "Not initialised"}))
            else:
                await websocket.send_text(json.dumps({"error": f"Unknown command: {cmd}"}))
    except WebSocketDisconnect:
        _environments.pop(sid, None)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=int(os.getenv("PORT", 7860)))
