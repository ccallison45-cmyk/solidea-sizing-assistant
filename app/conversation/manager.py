"""Conversation manager — the core state machine.

Given a session and an answer, determines the next question or final result.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.conversation.flows import ConversationFlow, MeasurementQuestion, get_flow
from app.conversation.parser import parse_measurement
from app.conversation.sessions import ConversationSession
from app.sizing.progressive import ProgressiveResult, evaluate_partial

logger = logging.getLogger(__name__)


@dataclass
class StepResponse:
    """What to return to the client after processing an answer."""

    session_id: str
    message: str
    question: QuestionPayload | None  # None = conversation complete
    progress: ProgressPayload
    result: ResultPayload | None  # None = still in progress
    status: str  # "in_progress" | "complete" | "error"


@dataclass
class QuestionPayload:
    id: str
    text: str
    help_text: str
    input_type: str
    skip_allowed: bool


@dataclass
class ProgressPayload:
    current: int
    estimated_total: int


@dataclass
class ResultPayload:
    recommended_size: str
    confidence: str
    notes: str


class ConversationManager:
    """Drives the step-by-step sizing conversation."""

    def __init__(self, sizing_data: dict[str, list[dict]]) -> None:
        self._sizing_data = sizing_data

    def start(self, session: ConversationSession) -> StepResponse:
        """Begin a conversation — return the greeting + first question."""
        flow = get_flow(session.product_type)
        if flow is None:
            return StepResponse(
                session_id=session.session_id,
                message="Sorry, I don't have sizing information for that product type yet.",
                question=None,
                progress=ProgressPayload(current=0, estimated_total=0),
                result=None,
                status="error",
            )

        session.current_step = 0
        first_q = self._get_next_applicable_question(session, flow)
        if first_q is None:
            return self._build_result(session, flow)

        total = self._estimate_total_questions(flow)
        return StepResponse(
            session_id=session.session_id,
            message=flow.greeting,
            question=self._question_to_payload(first_q),
            progress=ProgressPayload(current=1, estimated_total=total),
            result=None,
            status="in_progress",
        )

    def answer(
        self, session: ConversationSession, raw_value: str | None, skip: bool = False
    ) -> StepResponse:
        """Process an answer and return the next step."""
        flow = get_flow(session.product_type)
        if flow is None:
            return StepResponse(
                session_id=session.session_id,
                message="Session error: unknown product type.",
                question=None,
                progress=ProgressPayload(current=0, estimated_total=0),
                result=None,
                status="error",
            )

        current_q = self._current_question(session, flow)
        if current_q is None:
            return self._build_result(session, flow)

        # Process the answer
        if skip and current_q.skip_allowed:
            session.skipped.append(current_q.id)
            logger.info("Session %s: skipped question %s", session.session_id, current_q.id)
        elif raw_value is not None:
            parsed = parse_measurement(current_q.measurement_key, raw_value)
            if parsed is None:
                return StepResponse(
                    session_id=session.session_id,
                    message=f"I couldn't understand that measurement. {current_q.help_text}",
                    question=self._question_to_payload(current_q),
                    progress=ProgressPayload(
                        current=self._answered_count(session) + 1,
                        estimated_total=self._estimate_total_questions(flow),
                    ),
                    result=None,
                    status="in_progress",
                )
            session.measurements[current_q.measurement_key] = parsed.value_cm_or_kg
            logger.info(
                "Session %s: %s = %.2f (from %r)",
                session.session_id,
                current_q.measurement_key,
                parsed.value_cm_or_kg,
                raw_value,
            )
        else:
            # No value and not a skip — re-ask
            return StepResponse(
                session_id=session.session_id,
                message=current_q.dont_know_response,
                question=self._question_to_payload(current_q),
                progress=ProgressPayload(
                    current=self._answered_count(session) + 1,
                    estimated_total=self._estimate_total_questions(flow),
                ),
                result=None,
                status="in_progress",
            )

        session.current_step += 1
        session.touch()

        # Check if we can give a definitive result early
        if session.measurements:
            progressive = evaluate_partial(
                session.product_type, session.measurements, self._sizing_data
            )
            if progressive.is_definitive and progressive.confidence == "exact":
                return self._build_result_from_progressive(session, flow, progressive)

        # Get next question
        next_q = self._get_next_applicable_question(session, flow)
        if next_q is None:
            return self._build_result(session, flow)

        answered = self._answered_count(session)
        return StepResponse(
            session_id=session.session_id,
            message="Got it!",
            question=self._question_to_payload(next_q),
            progress=ProgressPayload(
                current=answered + 1,
                estimated_total=self._estimate_total_questions(flow),
            ),
            result=None,
            status="in_progress",
        )

    def batch(
        self,
        session: ConversationSession,
        measurements: dict[str, float],
    ) -> StepResponse:
        """Process all measurements at once (for email/n8n channel).

        Returns the result immediately if sufficient, or the next needed question.
        """
        flow = get_flow(session.product_type)
        if flow is None:
            return StepResponse(
                session_id=session.session_id,
                message="Unknown product type.",
                question=None,
                progress=ProgressPayload(current=0, estimated_total=0),
                result=None,
                status="error",
            )

        session.measurements.update(measurements)
        session.touch()

        progressive = evaluate_partial(
            session.product_type, session.measurements, self._sizing_data
        )

        if progressive.is_definitive or progressive.confidence == "exact":
            return self._build_result_from_progressive(session, flow, progressive)

        # Find what's still missing
        next_q = self._find_most_useful_missing_question(session, flow, progressive)
        if next_q is None:
            return self._build_result_from_progressive(session, flow, progressive)

        answered = len(session.measurements)
        total = answered + 1  # at least one more
        return StepResponse(
            session_id=session.session_id,
            message=flow.greeting,
            question=self._question_to_payload(next_q),
            progress=ProgressPayload(current=answered + 1, estimated_total=total),
            result=None,
            status="in_progress",
        )

    # ── internal helpers ─────────────────────────────────────────

    def _get_next_applicable_question(
        self, session: ConversationSession, flow: ConversationFlow
    ) -> MeasurementQuestion | None:
        """Walk from current_step forward, skipping already-answered and conditional questions."""
        questions = flow.questions

        for i in range(session.current_step, len(questions)):
            q = questions[i]

            # Skip if already answered
            if q.measurement_key in session.measurements:
                session.current_step = i + 1
                continue

            # Skip if already explicitly skipped
            if q.id in session.skipped:
                session.current_step = i + 1
                continue

            # Check condition
            if q.condition == "between_sizes":
                if not self._is_between_sizes(session):
                    session.current_step = i + 1
                    continue

            session.current_step = i
            return q

        return None

    def _is_between_sizes(self, session: ConversationSession) -> bool:
        """Check if current measurements put the user between sizes."""
        if not session.measurements:
            return False
        progressive = evaluate_partial(
            session.product_type, session.measurements, self._sizing_data
        )
        return progressive.confidence == "interpolated" or len(progressive.ambiguous_candidates) > 0

    def _current_question(
        self, session: ConversationSession, flow: ConversationFlow
    ) -> MeasurementQuestion | None:
        if session.current_step >= len(flow.questions):
            return None
        return flow.questions[session.current_step]

    def _build_result(self, session: ConversationSession, flow: ConversationFlow) -> StepResponse:
        progressive = evaluate_partial(
            session.product_type, session.measurements, self._sizing_data
        )
        return self._build_result_from_progressive(session, flow, progressive)

    def _build_result_from_progressive(
        self,
        session: ConversationSession,
        flow: ConversationFlow,
        progressive: ProgressiveResult,
    ) -> StepResponse:
        size = progressive.recommended_size
        notes = progressive.notes

        if progressive.confidence == "out_of_range" and not size:
            message = flow.contact_fallback
        elif progressive.confidence == "out_of_range":
            message = flow.out_of_range_template.format(size=size)
        elif progressive.ambiguous_candidates:
            size2 = progressive.ambiguous_candidates[0]
            message = flow.between_sizes_advice.format(size1=size, size2=size2)
            if notes:
                message = f"{notes} {message}"
        else:
            message = flow.result_template.format(size=size)
            if notes:
                message = f"{message} {notes}"

        answered = self._answered_count(session)
        return StepResponse(
            session_id=session.session_id,
            message=message,
            question=None,
            progress=ProgressPayload(current=answered, estimated_total=answered),
            result=ResultPayload(
                recommended_size=size,
                confidence=progressive.confidence,
                notes=notes,
            ),
            status="complete",
        )

    def _find_most_useful_missing_question(
        self,
        session: ConversationSession,
        flow: ConversationFlow,
        progressive: ProgressiveResult,
    ) -> MeasurementQuestion | None:
        """Find the question that would best disambiguate the current result."""
        for q in flow.questions:
            if q.measurement_key not in session.measurements and q.id not in session.skipped:
                return q
        return None

    def _estimate_total_questions(self, flow: ConversationFlow) -> int:
        """Estimate the total number of required questions (excluding conditional ones)."""
        return sum(1 for q in flow.questions if q.condition is None)

    def _answered_count(self, session: ConversationSession) -> int:
        return len(session.measurements) + len(session.skipped)

    @staticmethod
    def _question_to_payload(q: MeasurementQuestion) -> QuestionPayload:
        return QuestionPayload(
            id=q.id,
            text=q.text,
            help_text=q.help_text,
            input_type=q.input_type,
            skip_allowed=q.skip_allowed,
        )
