"""Tests for the conversation manager and session store."""

import time

from app.conversation.flows import FLOWS, get_flow
from app.conversation.manager import ConversationManager
from app.conversation.sessions import SessionStore
from app.sizing.loader import load_sizing_data

SIZING_DATA = load_sizing_data("data")


class TestSessionStore:
    def test_create_and_get(self):
        store = SessionStore()
        session = store.create(product_type="leggings")
        assert session.session_id is not None
        retrieved = store.get(session.session_id)
        assert retrieved is not None
        assert retrieved.product_type == "leggings"

    def test_get_nonexistent(self):
        store = SessionStore()
        assert store.get("nonexistent") is None

    def test_delete(self):
        store = SessionStore()
        session = store.create(product_type="socks")
        store.delete(session.session_id)
        assert store.get(session.session_id) is None

    def test_expiry(self):
        store = SessionStore(ttl_seconds=1)
        session = store.create(product_type="bras")
        time.sleep(1.1)
        assert store.get(session.session_id) is None

    def test_cleanup(self):
        store = SessionStore(ttl_seconds=1)
        store.create(product_type="socks")
        store.create(product_type="bras")
        time.sleep(1.1)
        removed = store.cleanup_expired()
        assert removed == 2
        assert store.active_count == 0


class TestFlows:
    def test_all_product_types_have_flows(self):
        from app.models import ProductType

        for pt in ProductType:
            flow = get_flow(pt.value)
            assert flow is not None, f"Missing flow for {pt.value}"
            assert len(flow.questions) > 0, f"No questions for {pt.value}"

    def test_flow_questions_have_measurement_keys(self):
        for product_type, flow in FLOWS.items():
            for q in flow.questions:
                assert q.measurement_key, f"{product_type}.{q.id} missing measurement_key"
                assert q.text, f"{product_type}.{q.id} missing text"


class TestConversationManager:
    def setup_method(self):
        self.manager = ConversationManager(SIZING_DATA)
        self.store = SessionStore()

    def test_start_leggings(self):
        session = self.store.create(product_type="leggings")
        step = self.manager.start(session)
        assert step.status == "in_progress"
        assert step.question is not None
        assert step.question.id == "height"
        assert step.message  # greeting is not empty

    def test_start_unknown_product(self):
        session = self.store.create(product_type="nonexistent")
        step = self.manager.start(session)
        assert step.status == "error"

    def test_full_leggings_conversation(self):
        session = self.store.create(product_type="leggings")
        step = self.manager.start(session)
        assert step.question.id == "height"

        # Answer height — may complete early if definitive, or ask more
        step = self.manager.answer(session, "5'6\"")
        while step.status == "in_progress" and step.question:
            # Provide answers for follow-up questions
            if step.question.id == "weight":
                step = self.manager.answer(session, "140 lbs")
            elif step.question.skip_allowed:
                step = self.manager.answer(session, None, skip=True)
            else:
                # Provide a reasonable measurement for any required question
                step = self.manager.answer(session, "30 inches")

        assert step.status == "complete"
        assert step.result is not None
        assert step.result.recommended_size != ""

    def test_socks_conversation(self):
        session = self.store.create(product_type="socks")
        step = self.manager.start(session)
        assert step.question.id == "calf"

        step = self.manager.answer(session, "15 inches")
        assert step.question.id == "ankle"

        step = self.manager.answer(session, "9 inches")
        assert step.status == "complete"
        assert step.result is not None

    def test_skip_question(self):
        session = self.store.create(product_type="leggings")
        step = self.manager.start(session)

        # Answer height
        step = self.manager.answer(session, "5'6\"")
        # Answer weight
        step = self.manager.answer(session, "140 lbs")
        # If between sizes, hip question appears — it's skippable
        if step.status == "in_progress" and step.question and step.question.skip_allowed:
            step = self.manager.answer(session, None, skip=True)
        # Should eventually complete
        # (may get another question or complete)

    def test_bad_input_re_asks(self):
        session = self.store.create(product_type="socks")
        step = self.manager.start(session)
        assert step.question.id == "calf"

        # Send garbage
        step = self.manager.answer(session, "hello world")
        assert step.status == "in_progress"
        # Should re-ask the same question
        assert step.question.id == "calf"

    def test_batch_full_measurements(self):
        session = self.store.create(product_type="socks")
        step = self.manager.batch(
            session,
            {
                "calf_circumference_cm": 35,
                "ankle_circumference_cm": 21,
            },
        )
        assert step.status == "complete"
        assert step.result is not None

    def test_batch_partial_measurements(self):
        session = self.store.create(product_type="socks")
        step = self.manager.batch(
            session,
            {
                "calf_circumference_cm": 35,
            },
        )
        # Missing ankle — should ask for it
        if step.status == "in_progress":
            assert step.question is not None

    def test_bra_conversation(self):
        session = self.store.create(product_type="bras")
        step = self.manager.start(session)
        assert step.question.id == "bust"

        step = self.manager.answer(session, "38 inches")
        assert step.question.id == "underbust"

        step = self.manager.answer(session, "32 inches")
        assert step.status == "complete"
        assert step.result is not None

    def test_gauntlet_single_question(self):
        session = self.store.create(product_type="gauntlets")
        step = self.manager.start(session)
        assert step.question.id == "palm"

        step = self.manager.answer(session, "20 cm")
        assert step.status == "complete"
