from __future__ import annotations

from contextlib import asynccontextmanager
import logging
import os
import re
from typing import Any, AsyncIterator
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from openai import APIError
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv

from .database import BACKEND_DIR, initialize_database

load_dotenv(BACKEND_DIR / ".env")
from .repository import get_analysis_result, get_borough, get_indicators, list_boroughs
from .ai.agent import (
    AgentConfigurationError,
    configured_live_provider,
    configured_mode,
    configured_model,
    configured_provider,
    generate_basic_insights,
    generate_basic_text,
    generate_chat,
    generate_comparison,
    generate_insights,
    generate_live_insights,
    generate_live_chat,
    generate_live_comparison,
    generate_live_text,
    generate_text,
    is_configured,
)
from .ai.providers import ProviderResponseError
from .ai.context import AnalysisContextError, build_analysis_context
from .ai.output_formatter import (
    sanitize_ai_text,
    sanitize_analysis_insights,
    sanitize_chat_answer,
    sanitize_compare_answer,
)
from .ai.prompt_builder import analysis_prompt, chat_prompt, comparison_prompt, report_prompt
from .ai.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    ChatRequest,
    ChatResponse,
    CompareResponse,
    CompareRequest,
    ConversationPDFRequest,
    PDFReportRequest,
    ReportRequest,
    TextResponse,
)
from .ai.report_builder import normalize_report_title
from .reports import build_conversation_pdf, build_markdown_report, build_pdf_report

logger = logging.getLogger("uvicorn.error")

LOCAL_CORS_ORIGINS = (
    "http://127.0.0.1:5173",
    "http://localhost:5173",
)


def configured_cors_origins() -> list[str]:
    origins = list(LOCAL_CORS_ORIGINS)
    configured = os.getenv("BACKEND_CORS_ORIGINS", "")
    for value in configured.split(","):
        origin = value.strip().rstrip("/")
        if not origin:
            continue
        if origin == "*":
            raise ValueError("BACKEND_CORS_ORIGINS must not contain '*'")
        parsed = urlparse(origin)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or parsed.path
            or parsed.params
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError(
                "BACKEND_CORS_ORIGINS entries must be HTTP(S) origins without paths"
            )
        if origin not in origins:
            origins.append(origin)
    return origins


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    database_path = initialize_database()
    logger.info("SQLite database path: %s", database_path)
    yield


app = FastAPI(
    title="UrbanInsight API",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=configured_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/boroughs")
def boroughs() -> list[dict[str, Any]]:
    return list_boroughs()


@app.get("/boroughs/{borough_id}")
def borough_detail(borough_id: str) -> dict[str, Any]:
    borough = get_borough(borough_id)
    if borough is None:
        raise HTTPException(status_code=404, detail="Borough not found")
    return borough


@app.get("/indicators/{borough_id}")
def borough_indicators(borough_id: str) -> dict[str, Any]:
    indicators = get_indicators(borough_id)
    if indicators is None:
        raise HTTPException(status_code=404, detail="Indicators not found")
    return indicators


@app.get("/analysis/{borough_id}")
def borough_analysis(borough_id: str) -> dict[str, Any]:
    if get_borough(borough_id) is None:
        raise HTTPException(status_code=404, detail="Borough not found")
    return {
        "borough_id": borough_id,
        "result": get_analysis_result(borough_id),
    }


@app.get("/ai/status")
def ai_status() -> dict[str, Any]:
    try:
        mode = configured_mode()
        configured = is_configured()
        return {
            "configured": configured,
            "enabled": configured,
            "mode": mode,
            "provider": configured_provider(),
            "model": configured_model(),
            "default_provider": configured_live_provider(),
            "available_providers": ["deepseek", "qwen"],
        }
    except AgentConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.post("/ai/analyze", response_model=AnalyzeResponse)
def ai_analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    context = _context_or_404(request.borough_id)
    prompt = analysis_prompt(context, request.previous_context, request.locale)
    if not request.include_ai_insights:
        return AnalyzeResponse(
            analysis_mode="basic",
            ai_insights_requested=False,
            ai_insights_applied=False,
            insights=sanitize_analysis_insights(
                generate_basic_insights(prompt), request.locale
            ),
        )

    selected_provider: str | None = request.ai_provider
    selected_model: str | None = None
    try:
        selected_provider = configured_live_provider(request.ai_provider)
        if configured_mode() == "mock":
            return AnalyzeResponse(
                analysis_mode="ai",
                ai_insights_requested=True,
                ai_insights_applied=True,
                ai_provider=selected_provider,
                ai_model=configured_model(),
                insights=sanitize_analysis_insights(
                    generate_insights(prompt), request.locale
                ),
            )
        selected_model = configured_model(selected_provider)
        insights, actual_provider, actual_model = _run_agent(
            lambda: generate_live_insights(prompt, selected_provider),
            selected_provider,
        )
        return AnalyzeResponse(
            analysis_mode="ai",
            ai_insights_requested=True,
            ai_insights_applied=True,
            ai_provider=actual_provider,
            ai_model=actual_model,
            insights=sanitize_analysis_insights(insights, request.locale),
        )
    except HTTPException as error:
        if error.status_code not in (502, 503):
            raise
        return AnalyzeResponse(
            analysis_mode="basic",
            ai_insights_requested=True,
            ai_insights_applied=False,
            ai_provider=selected_provider,
            ai_model=selected_model,
            ai_error="unavailable",
            insights=sanitize_analysis_insights(
                generate_basic_insights(prompt), request.locale
            ),
        )
    except AgentConfigurationError:
        return AnalyzeResponse(
            analysis_mode="basic",
            ai_insights_requested=True,
            ai_insights_applied=False,
            ai_provider=selected_provider,
            ai_model=selected_model,
            ai_error="unavailable",
            insights=sanitize_analysis_insights(
                generate_basic_insights(prompt), request.locale
            ),
        )


@app.post("/ai/chat", response_model=ChatResponse)
def ai_chat(request: ChatRequest) -> ChatResponse:
    context = _context_or_404(request.borough_id)
    comparison = (
        _context_or_404(request.compare_borough_id) if request.compare_borough_id else None
    )
    prompt = chat_prompt(
        context,
        request.question,
        request.previous_context,
        comparison,
        request.locale,
    )
    answer = _generate_structured_request(
        request.ai_provider,
        lambda: generate_chat(prompt),
        lambda provider: generate_live_chat(prompt, provider),
    )
    answer = sanitize_chat_answer(answer, request.locale)
    return ChatResponse(content=answer.summary, answer=answer)


@app.post("/ai/compare", response_model=CompareResponse)
def ai_compare(request: CompareRequest) -> CompareResponse:
    context = _context_or_404(request.borough_id)
    comparison = _context_or_404(request.compare_borough_id)
    prompt = comparison_prompt(
        context, comparison, request.previous_context, request.locale
    )
    answer = _generate_structured_request(
        request.ai_provider,
        lambda: generate_comparison(prompt),
        lambda provider: generate_live_comparison(prompt, provider),
    )
    answer = sanitize_compare_answer(answer, request.locale)
    return CompareResponse(content=answer.summary, answer=answer)


@app.post("/ai/report", response_model=TextResponse)
def ai_report(request: ReportRequest) -> TextResponse:
    context = _context_or_404(request.borough_id)
    if (
        request.insights is not None
        and request.analysis_result is not None
        and request.ai_insights_applied is not None
    ):
        sanitized_request = request.model_copy(
            update={
                "insights": sanitize_analysis_insights(request.insights, request.locale)
            }
        )
        return TextResponse(content=build_markdown_report(context, sanitized_request))

    prompt = report_prompt(context, request.previous_context, request.locale)
    if not request.include_ai_insights:
        return TextResponse(
            content=normalize_report_title(
                sanitize_ai_text(generate_basic_text(prompt), request.locale),
                request.locale,
                False,
            )
        )
    content = _generate_request_text(
        request.ai_provider,
        lambda generator: generator(prompt),
    )
    return TextResponse(
        content=normalize_report_title(
            sanitize_ai_text(content, request.locale), request.locale, True
        )
    )


@app.post("/reports/pdf")
def pdf_report(request: PDFReportRequest) -> Response:
    context = _context_or_404(request.borough_id)
    sanitized_request = request.model_copy(
        update={
            "insights": sanitize_analysis_insights(request.insights, request.locale)
        }
    )
    content = build_pdf_report(context, sanitized_request)
    borough_slug = re.sub(
        r"[^A-Za-z0-9_-]+", "_", context["borough"]["name"]
    ).strip("_")
    mode_slug = "ai" if request.ai_insights_applied else "basic"
    filename = f"UrbanInsight_{borough_slug}_{mode_slug}_report.pdf"
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/conversations/pdf")
def conversation_pdf(request: ConversationPDFRequest) -> Response:
    context = _context_or_404(request.borough_id)
    content = build_conversation_pdf(context, request)
    borough_slug = re.sub(
        r"[^A-Za-z0-9_-]+", "_", context["borough"]["name"]
    ).strip("_")
    filename = f"UrbanInsight_{borough_slug}_Conversation.pdf"
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _context_or_404(borough_id: str) -> dict[str, Any]:
    try:
        return build_analysis_context(borough_id)
    except AnalysisContextError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


def _generate_request_text(provider_name: str | None, operation: Any) -> str:
    if configured_mode() == "mock":
        return _run_agent(lambda: operation(generate_text))
    if provider_name is None:
        return _run_agent(lambda: operation(generate_text))
    return _run_agent(
        lambda: operation(
            lambda prompt: generate_live_text(prompt, provider_name)
        ),
        provider_name,
    )


def _generate_structured_request(
    provider_name: str | None, mock_operation: Any, live_operation: Any
) -> Any:
    if configured_mode() == "mock":
        return _run_agent(mock_operation)
    selected_provider = configured_live_provider(provider_name)
    return _run_agent(lambda: live_operation(selected_provider), selected_provider)


def _run_agent(operation: Any, provider_name: str | None = None) -> Any:
    try:
        return operation()
    except AgentConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except APIError as error:
        logger.error(
            "AI provider error provider=%s type=%s status=%s request_id=%s message=%s",
            provider_name or _provider_name_for_logging(),
            type(error).__name__,
            getattr(error, "status_code", None),
            getattr(error, "request_id", None),
            _format_provider_error(error),
        )
        raise HTTPException(status_code=502, detail="AI provider request failed") from error
    except ProviderResponseError as error:
        logger.error(
            "AI provider response error provider=%s type=%s message=%s",
            error.provider_name,
            type(error).__name__,
            _redact_openai_error(str(error)),
        )
        raise HTTPException(status_code=502, detail="AI provider request failed") from error


def _redact_openai_error(message: str) -> str:
    for variable in ("OPENAI_API_KEY", "DASHSCOPE_API_KEY", "DEEPSEEK_API_KEY"):
        api_key = os.getenv(variable)
        if api_key:
            message = message.replace(api_key, "[REDACTED_API_KEY]")
    return re.sub(r"\bsk-[A-Za-z0-9_-]{8,}\b", "[REDACTED_API_KEY]", message)


def _format_provider_error(error: BaseException) -> str:
    messages = [_redact_openai_error(str(error))]
    cause = error.__cause__
    for _ in range(3):
        if cause is None:
            break
        messages.append(
            f"caused_by={type(cause).__name__}: {_redact_openai_error(str(cause))}"
        )
        cause = cause.__cause__
    return " | ".join(messages)


def _provider_name_for_logging() -> str:
    return os.getenv("AI_PROVIDER", "openai").strip().lower() or "openai"
