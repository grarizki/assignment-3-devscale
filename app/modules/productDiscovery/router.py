import uuid
import markdown
from fastapi import APIRouter, Request, Form, Response
from fastapi.templating import Jinja2Templates
from .prompt import SYSTEM_PROMPT
from app.utils.openai import client

template = Jinja2Templates("templates")
stories_router = APIRouter(prefix="/product-discovery")

# In-memory session store: { session_id: [ {role, content}, ... ] }
sessions: dict[str, list[dict]] = {}

COOKIE_NAME = "pd_session"
MODEL = "arcee-ai/trinity-large-preview:free"


def get_or_create_session(session_id: str | None) -> tuple[str, list[dict]]:
    if session_id and session_id in sessions:
        return session_id, sessions[session_id]
    new_id = str(uuid.uuid4())
    sessions[new_id] = []
    return new_id, sessions[new_id]


@stories_router.get("/")
def get_chat(request: Request, response: Response):
    session_id = request.cookies.get(COOKIE_NAME)
    session_id, history = get_or_create_session(session_id)
    resp = template.TemplateResponse("index.html", {
        "request": request,
        "history": history,
        "started": len(history) > 0,
    })
    resp.set_cookie(COOKIE_NAME, session_id, httponly=True, samesite="lax")
    return resp


@stories_router.post("/")
def send_message(request: Request, response: Response, message: str = Form("")):
    session_id = request.cookies.get(COOKIE_NAME)
    session_id, history = get_or_create_session(session_id)

    if not message.strip():
        resp = template.TemplateResponse("index.html", {
            "request": request,
            "history": history,
            "started": len(history) > 0,
        })
        resp.set_cookie(COOKIE_NAME, session_id, httponly=True, samesite="lax")
        return resp

    history.append({"role": "user", "content": message.strip()})

    completion = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history,  # type: ignore[arg-type]
        extra_body={"reasoning": {"enabled": True}},
    )

    ai_text = completion.choices[0].message.content or ""
    history.append({"role": "assistant", "content": ai_text})

    # Convert assistant markdown to HTML for rendering
    rendered = [
        {
            "role": msg["role"],
            "content": markdown.markdown(msg["content"]) if msg["role"] == "assistant" else msg["content"],
            "raw": msg["content"],
        }
        for msg in history
    ]

    resp = template.TemplateResponse("index.html", {
        "request": request,
        "history": rendered,
        "started": True,
    })
    resp.set_cookie(COOKIE_NAME, session_id, httponly=True, samesite="lax")
    return resp


@stories_router.post("/reset")
def reset_session(request: Request, response: Response):
    session_id = request.cookies.get(COOKIE_NAME)
    if session_id and session_id in sessions:
        sessions.pop(session_id)
    resp = template.TemplateResponse("index.html", {
        "request": request,
        "history": [],
        "started": False,
    })
    resp.delete_cookie(COOKIE_NAME)
    return resp
