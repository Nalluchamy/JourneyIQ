import logging
from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.response import APIResponse

from app.services.copilot.query_engine import CopilotQueryEngine
from app.services.copilot.insight_engine import CopilotInsightEngine
from app.services.copilot.report_generator import CopilotReportGenerator
from app.services.copilot.business_context import CopilotBusinessContext
from app.services.copilot.response_builder import CopilotResponseBuilder
from app.services.copilot.conversation_memory import copilot_memory
from app.services.copilot.executive_summary import CopilotExecutiveSummary
from app.services.assistant.providers.nvidia import NvidiaAIProvider
from app.services.assistant.providers.gemini import GeminiAIProvider
from app.services.assistant.providers.openai import OpenAIProvider

router = APIRouter()


class CopilotChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500, description="Business owner query")
    session_id: str = Field(..., description="Persistent session identifier")


def check_owner_access(current_user: User) -> None:
    """Verify requesting user is an administrator/owner."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Admin access required."
        )


@router.post("/chat", response_model=APIResponse[dict[str, Any]])
async def copilot_chat(
    body: CopilotChatRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: User = Depends(get_current_user)
) -> Any:
    """Chat with the Business Copilot to get structured grounded answers from live storefront telemetry."""
    check_owner_access(current_user)
    
    # 1. Retrieve data based on question
    query_engine = CopilotQueryEngine(db)
    query_data = await query_engine.execute_query(body.message)

    # 2. Get and update conversation memory
    memory_context = copilot_memory.get_session_context(body.session_id)
    history = memory_context.get("previous_questions", [])
    
    # Record question in history
    copilot_memory.record_question(body.session_id, body.message)

    # 3. Build Prompt Context
    context_builder = CopilotBusinessContext()
    prompt = context_builder.build_llm_context(body.message, query_data, history)

    # 4. Invoke LLM Chain (NVIDIA -> Gemini -> OpenAI -> Local Fallback)
    nvidia_provider = NvidiaAIProvider()
    gemini_provider = GeminiAIProvider()
    openai_provider = OpenAIProvider()
    
    reply = ""
    source = "local"

    if nvidia_provider.is_configured():
        try:
            reply = await nvidia_provider.generate_response(prompt)
            source = "nvidia"
        except Exception as e:
            logging.error(f"Copilot NVIDIA call failed: {e}")

    if not reply and gemini_provider.is_configured():
        try:
            reply = await gemini_provider.generate_response(prompt)
            source = "gemini"
        except Exception as e:
            logging.error(f"Copilot Gemini call failed: {e}")

    if not reply and openai_provider.is_configured():
        try:
            reply = await openai_provider.generate_response(prompt)
            source = "openai"
        except Exception as e:
            logging.error(f"Copilot OpenAI call failed: {e}")

    # 5. Format Structured Response
    response_builder = CopilotResponseBuilder()
    structured = response_builder.build_structured_response(query_data, raw_llm_reply=reply)
    
    # Update memory context with recent insights
    copilot_memory.update_session_context(body.session_id, {
        "recent_insights": [structured["observation"]],
        "business_focus": "revenue" if "REVENUE" in query_data["intent"] else "conversion"
    })

    return APIResponse(
        success=True,
        message="Copilot response generated successfully.",
        data={
            **structured,
            "source": source
        }
    )


@router.get("/questions", response_model=APIResponse[list[str]])
async def get_suggested_business_questions(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get dynamic preset business exploration questions."""
    check_owner_access(current_user)
    
    questions = [
        "Why did revenue decrease this week?",
        "Which products should I restock?",
        "Which customers are likely to churn?",
        "What products are trending?",
        "Why are recommendations decreasing?",
        "How is customer satisfaction?",
        "Which products are slow moving?",
        "Show today's KPI summary.",
        "Which campaigns performed best?",
        "Generate weekly business report."
    ]
    return APIResponse(success=True, message="Suggested business questions loaded.", data=questions)


@router.get("/summary", response_model=APIResponse[dict[str, Any]])
async def get_executive_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: User = Depends(get_current_user)
) -> Any:
    """Fetch high-level business KPI metrics cards, risks scores, and active threats."""
    check_owner_access(current_user)
    
    summary_service = CopilotExecutiveSummary(db)
    data = await summary_service.get_executive_summary_dashboard()
    return APIResponse(success=True, message="Executive summary metrics compiled.", data=data)


@router.get("/report/{report_type}", response_model=APIResponse[dict[str, Any]])
async def generate_business_report(
    report_type: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    format: str = Query("markdown", description="Format output: markdown, json, pdf"),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Generate daily, weekly, or monthly executive report summaries in multiple formats."""
    check_owner_access(current_user)
    
    if report_type.lower() not in ("daily", "weekly", "monthly"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid report type. Supported: daily, weekly, monthly."
        )

    generator = CopilotReportGenerator(db)
    
    if format.lower() == "json":
        data = await generator.generate_report_data(report_type)
        return APIResponse(success=True, message="Report generated in JSON format.", data={"format": "json", "report": data})
    
    elif format.lower() == "pdf":
        # Return base64 or custom raw HTML formatted report to represent PDF download
        data_md = await generator.generate_markdown_report(report_type)
        html_content = f"<html><body style='font-family:sans-serif;padding:40px;line-height:1.6;'>{data_md.replace('# ', '<h1>').replace('## ', '<h2>').replace('### ', '<h3>').replace('\n', '<br>')}</body></html>"
        return APIResponse(success=True, message="Report generated in print HTML/PDF format.", data={"format": "pdf", "report": html_content})
        
    else:
        # Markdown format default
        data_md = await generator.generate_markdown_report(report_type)
        return APIResponse(success=True, message="Report generated in Markdown format.", data={"format": "markdown", "report": data_md})


@router.get("/insights", response_model=APIResponse[list[dict[str, Any]]])
async def get_copilot_insights(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: User = Depends(get_current_user)
) -> Any:
    """Fetch high-priority anomalies and corrective actions."""
    check_owner_access(current_user)
    
    insight_service = CopilotInsightEngine(db)
    data = await insight_service.generate_business_insights()
    return APIResponse(success=True, message="Insights loaded.", data=data)


@router.get("/risks", response_model=APIResponse[list[dict[str, Any]]])
async def get_copilot_risks(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: User = Depends(get_current_user)
) -> Any:
    """Fetch active operational risks and severity threats."""
    check_owner_access(current_user)
    
    insight_service = CopilotInsightEngine(db)
    data = await insight_service.get_business_risks()
    return APIResponse(success=True, message="Operational risks loaded.", data=data)
