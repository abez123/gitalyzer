"""FastAPI application powering the Gitalyzer web app."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Dict, Optional

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .ai_agent import call_ai_agent, generate_rule_based_summary
from .config import ANALYSIS_FIELDS
from .github_client import GitHubAPIError, extract_owner_repo, fetch_repository_snapshot
from .pdf_generator import build_pdf


class GlossaryItem(BaseModel):
    term: str
    definition: str


class RepositoryAnalysis(BaseModel):
    project_summary: str
    how_it_helps_people: str
    main_features: list[str] = Field(default_factory=list)
    how_it_works: list[str] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list)
    getting_started: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    glossary: list[GlossaryItem] = Field(default_factory=list)


class RepositoryInfo(BaseModel):
    name: Optional[str]
    full_name: Optional[str]
    description: Optional[str]
    html_url: Optional[str]
    default_branch: Optional[str]
    license: Optional[str]
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    watchers: int = 0
    language: Optional[str]
    topics: list[str] = Field(default_factory=list)
    languages: Dict[str, int] = Field(default_factory=dict)
    recent_commits: list[Dict[str, Optional[str]]] = Field(default_factory=list)
    readme_excerpt: Optional[str]


class AnalyzeRequest(BaseModel):
    repo_url: str
    api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key. When omitted the server falls back to a basic summary.",
    )
    model: Optional[str] = Field(
        default=None,
        description="Optional override for the OpenAI model identifier.",
    )


class AnalyzeResponse(BaseModel):
    repository: RepositoryInfo
    analysis: RepositoryAnalysis
    used_ai: bool
    raw_response: Optional[str]


class PdfRequest(BaseModel):
    repo_name: str
    analysis: RepositoryAnalysis


app = FastAPI(title="Gitalyzer", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api")


def _build_context(repo: RepositoryInfo) -> str:
    languages_line = ", ".join(f"{name} ({score})" for name, score in repo.languages.items())
    commits_lines = "\n".join(
        f"  - {item.get('message', '').strip()} ({item.get('date', 'unknown date')})"
        for item in repo.recent_commits
    )

    return (
        f"Repository: {repo.full_name or repo.name}\n"
        f"Description: {repo.description or 'No description provided.'}\n"
        f"Primary language: {repo.language or 'Unknown'}\n"
        f"Languages: {languages_line or 'Not reported'}\n"
        f"Stars: {repo.stars}, Forks: {repo.forks}, Open issues: {repo.open_issues}\n"
        f"Topics: {', '.join(repo.topics) if repo.topics else 'None'}\n"
        f"Default branch: {repo.default_branch or 'main'}\n"
        "Recent commits:\n"
        f"{commits_lines if commits_lines else '  - No recent commits retrieved.'}\n"
        "README excerpt:\n"
        f"{repo.readme_excerpt or 'No README available.'}"
    )


@api_router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_repository(payload: AnalyzeRequest) -> JSONResponse:
    try:
        owner, repo = extract_owner_repo(payload.repo_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        snapshot = await fetch_repository_snapshot(owner, repo)
    except GitHubAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    repo_info = RepositoryInfo.model_validate(snapshot)
    context = _build_context(repo_info)

    used_ai = False
    raw_response: Optional[str] = None

    if payload.api_key:
        try:
            model = payload.model or "gpt-4o-mini"
            result, raw_response = await asyncio.to_thread(
                call_ai_agent, context, payload.api_key, model
            )
            used_ai = True
        except Exception as exc:  # pragma: no cover - relies on live API behaviour
            # Fall back to a rule-based summary but keep the error message to help debugging.
            result = generate_rule_based_summary(context)
            raw_response = f"AI call failed: {exc}"
            used_ai = False
    else:
        result = generate_rule_based_summary(context)

    try:
        analysis = RepositoryAnalysis.model_validate(result)
    except Exception as exc:  # pragma: no cover - ensures we never crash on malformed AI output
        raise HTTPException(status_code=500, detail=f"Failed to parse analysis: {exc}") from exc

    return JSONResponse(
        AnalyzeResponse(
            repository=repo_info,
            analysis=analysis,
            used_ai=used_ai,
            raw_response=raw_response,
        ).model_dump()
    )


@api_router.post("/generate-pdf")
async def generate_pdf(payload: PdfRequest) -> StreamingResponse:
    pdf_bytes = await asyncio.to_thread(build_pdf, payload.repo_name, payload.analysis.model_dump())
    filename = f"{payload.repo_name or 'repository'}-gitalyzer.pdf"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return StreamingResponse(iter([pdf_bytes]), media_type="application/pdf", headers=headers)


@api_router.get("/analysis-schema")
async def analysis_schema() -> Dict[str, str]:
    """Expose the structured fields used when summarising repositories."""

    return ANALYSIS_FIELDS


app.include_router(api_router)


# Serve the frontend if it exists so the project works out of the box.
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():  # pragma: no cover - filesystem dependent
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


__all__ = ["app", "ANALYSIS_FIELDS"]
