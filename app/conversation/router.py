"""FastAPI router for the v2 conversation endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.conversation.manager import ConversationManager, StepResponse
from app.conversation.sessions import SessionStore
from app.models import (
    ConversationAnswerRequest,
    ConversationBatchRequest,
    ConversationStartRequest,
    ConversationStepResponse,
    DisproportionResponse,
    FieldSizeMappingResponse,
    ProgressResponse,
    QuestionResponse,
    ResultResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/conversation", tags=["conversation"])

# These are initialized by init_conversation() called from main.py lifespan
_session_store: SessionStore | None = None
_manager: ConversationManager | None = None


def init_conversation(sizing_data: dict[str, list[dict]]) -> None:
    """Initialize the conversation subsystem with loaded sizing data."""
    global _session_store, _manager  # noqa: PLW0603
    _session_store = SessionStore()
    _manager = ConversationManager(sizing_data)
    logger.info("Conversation engine initialized")


def _get_store() -> SessionStore:
    if _session_store is None:
        raise RuntimeError("Conversation subsystem not initialized")
    return _session_store


def _get_manager() -> ConversationManager:
    if _manager is None:
        raise RuntimeError("Conversation subsystem not initialized")
    return _manager


def _to_response(step: StepResponse) -> ConversationStepResponse:
    """Convert internal StepResponse to Pydantic response model."""
    question = None
    if step.question is not None:
        question = QuestionResponse(
            id=step.question.id,
            text=step.question.text,
            help_text=step.question.help_text,
            input_type=step.question.input_type,
            skip_allowed=step.question.skip_allowed,
        )

    result = None
    if step.result is not None:
        disproportion = None
        if step.result.disproportion is not None:
            dp = step.result.disproportion
            disproportion = DisproportionResponse(
                is_disproportionate=dp.is_disproportionate,
                size_spread=dp.size_spread,
                field_mappings=[
                    FieldSizeMappingResponse(**fm) for fm in dp.field_mappings
                ],
                notes=dp.notes,
            )
        result = ResultResponse(
            recommended_size=step.result.recommended_size,
            confidence=step.result.confidence,
            notes=step.result.notes,
            disproportion=disproportion,
        )

    return ConversationStepResponse(
        session_id=step.session_id,
        message=step.message,
        question=question,
        progress=ProgressResponse(
            current=step.progress.current,
            estimated_total=step.progress.estimated_total,
        ),
        result=result,
        status=step.status,
    )


@router.post("/start", response_model=ConversationStepResponse)
async def conversation_start(request: ConversationStartRequest):
    store = _get_store()
    manager = _get_manager()

    session = store.create(
        product_type=request.product_type.value,
        channel=request.channel,
        collect_all=request.collect_all,
    )
    step = manager.start(session)
    return _to_response(step)


@router.post("/answer", response_model=ConversationStepResponse)
async def conversation_answer(request: ConversationAnswerRequest):
    store = _get_store()
    manager = _get_manager()

    session = store.get(request.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    step = manager.answer(
        session,
        raw_value=request.answer.value,
        skip=request.answer.skip,
    )
    return _to_response(step)


@router.post("/batch", response_model=ConversationStepResponse)
async def conversation_batch(request: ConversationBatchRequest):
    store = _get_store()
    manager = _get_manager()

    session = store.create(
        product_type=request.product_type.value,
        channel=request.channel,
    )
    step = manager.batch(session, request.measurements)
    return _to_response(step)


@router.get("/{session_id}", response_model=ConversationStepResponse)
async def conversation_status(session_id: str):
    store = _get_store()
    manager = _get_manager()

    session = store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    # Re-evaluate current state
    step = manager.start(session)
    return _to_response(step)
