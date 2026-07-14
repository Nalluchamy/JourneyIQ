from typing import Any


class ConversationMemory:
    """Manages session-only conversation memory for the Business Copilot."""

    def __init__(self) -> None:
        # In-memory dictionary map: session_id -> context dict
        self._sessions: dict[str, dict[str, Any]] = {}

    def get_session_context(self, session_id: str) -> dict[str, Any]:
        """Retrieve the memory context for a given session ID, initializing if empty."""
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "previous_questions": [],
                "selected_products": [],
                "preferred_report_type": "weekly",
                "business_focus": "conversion",
                "recent_insights": []
            }
        return self._sessions[session_id]

    def update_session_context(self, session_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        """Update context parameters for a session."""
        context = self.get_session_context(session_id)
        for key, val in updates.items():
            if key in context:
                if isinstance(context[key], list) and isinstance(val, list):
                    # Append unique items for list fields
                    for item in val:
                        if item not in context[key]:
                            context[key].append(item)
                else:
                    context[key] = val
        return context

    def record_question(self, session_id: str, question: str) -> None:
        """Log a question in the session memory history (capped at 10 items)."""
        context = self.get_session_context(session_id)
        history = context["previous_questions"]
        history.append(question)
        if len(history) > 10:
            history.pop(0)

    def clear_session(self, session_id: str) -> None:
        """Reset session memory."""
        if session_id in self._sessions:
            del self._sessions[session_id]


# Singleton instance for application-wide session management
copilot_memory = ConversationMemory()
