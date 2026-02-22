import markdown
from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from .prompt import SYSTEM_PROMPT
from app.utils.openai import client

template = Jinja2Templates("templates")
stories_router = APIRouter(prefix="/product-discovery")

MODEL = "arcee-ai/trinity-large-preview:free"


class MasterPRD(BaseModel):
    title: str
    problem: str
    audience: str
    features: str
    user_journey: str
    business_model: str
    competitive_landscape: str
    design_language: str
    technical_constraints: str
    success_metrics: str
    risks: str


SECTION_LABELS = {
    "problem": "Problem & Value Proposition",
    "audience": "Target Audience",
    "features": "Core Features (MVP)",
    "user_journey": "User Journey & UX",
    "business_model": "Business Model",
    "competitive_landscape": "Competitive Landscape",
    "design_language": "Design Language",
    "technical_constraints": "Technical Constraints",
    "success_metrics": "Success Metrics",
    "risks": "Risks & Assumptions",
}


@stories_router.get("/")
def get_form(request: Request):
    return template.TemplateResponse("index.html", {"request": request, "prd": None})


@stories_router.post("/")
def generate_prd(request: Request, idea: str = Form(...)):
    completion = client.beta.chat.completions.parse(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": idea.strip()},
        ],
        response_format=MasterPRD,
    )

    prd = completion.choices[0].message.parsed
    if prd is None:
        raise ValueError("Failed to parse PRD response")

    sections = [
        {
            "label": SECTION_LABELS[field],
            "content": markdown.markdown(getattr(prd, field)),
        }
        for field in SECTION_LABELS
    ]

    return template.TemplateResponse("index.html", {
        "request": request,
        "prd": {"title": prd.title, "sections": sections},
        "idea": idea.strip(),
    })


@stories_router.post("/reset")
def reset(request: Request):
    return template.TemplateResponse("index.html", {"request": request, "prd": None})
