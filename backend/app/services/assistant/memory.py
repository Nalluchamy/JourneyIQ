from typing import Any

class AssistantMemory:
    """Manages session-level temporary conversation memory in memory."""

    def __init__(self) -> None:
        # Maps session_id -> context dictionary
        self._sessions: dict[str, dict[str, Any]] = {}

    def get_context(self, session_id: str) -> dict[str, Any]:
        """Retrieve context dictionary for a session, initializing if empty."""
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "preferred_categories": set(),
                "budget": None,
                "viewed_products": [],
                "previous_questions": [],
                "wishlist": [],
                "cart": []
            }
        return self._sessions[session_id]

    def update_context(self, session_id: str, updates: dict[str, Any]) -> None:
        """Merge updates into session context."""
        ctx = self.get_context(session_id)
        for k, v in updates.items():
            if k == "preferred_categories" and isinstance(v, (set, list)):
                ctx["preferred_categories"].update(v)
            elif k == "previous_questions" and isinstance(v, str):
                ctx["previous_questions"].append(v)
                if len(ctx["previous_questions"]) > 5:
                    ctx["previous_questions"].pop(0) # Keep last 5 questions
            else:
                ctx[k] = v

    def clear_context(self, session_id: str) -> None:
        """Clear context for a specific session."""
        if session_id in self._sessions:
            del self._sessions[session_id]


# Singleton memory tracker
assistant_memory = AssistantMemory()
