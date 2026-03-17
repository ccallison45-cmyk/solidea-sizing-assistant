"""In-memory session store with TTL expiry.

Sessions are ephemeral — no disk persistence (invariant #5).
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from threading import Lock

DEFAULT_TTL_SECONDS = 30 * 60  # 30 minutes


@dataclass
class ConversationSession:
    """State for one sizing conversation."""

    session_id: str
    product_type: str | None = None
    channel: str = "widget"
    measurements: dict[str, float] = field(default_factory=dict)
    current_step: int = 0
    collect_all: bool = False
    skipped: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def touch(self) -> None:
        self.updated_at = time.time()


class SessionStore:
    """Thread-safe in-memory session store with automatic expiry."""

    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        self._sessions: dict[str, ConversationSession] = {}
        self._lock = Lock()
        self._ttl = ttl_seconds

    def create(
        self,
        product_type: str | None = None,
        channel: str = "widget",
        collect_all: bool = False,
    ) -> ConversationSession:
        session_id = uuid.uuid4().hex[:12]
        session = ConversationSession(
            session_id=session_id,
            product_type=product_type,
            channel=channel,
            collect_all=collect_all,
        )
        with self._lock:
            self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> ConversationSession | None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            if time.time() - session.updated_at > self._ttl:
                del self._sessions[session_id]
                return None
            return session

    def delete(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)

    def cleanup_expired(self) -> int:
        """Remove all expired sessions. Returns count of removed sessions."""
        now = time.time()
        removed = 0
        with self._lock:
            expired = [sid for sid, s in self._sessions.items() if now - s.updated_at > self._ttl]
            for sid in expired:
                del self._sessions[sid]
                removed += 1
        return removed

    @property
    def active_count(self) -> int:
        with self._lock:
            return len(self._sessions)
