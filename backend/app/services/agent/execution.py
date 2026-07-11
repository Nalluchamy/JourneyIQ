import datetime
from typing import Any
from app.services.agent.memory import agent_memory

class ExecutionModule:
    """Executes actions approved by store managers and logs outcomes."""

    def execute_action(self, action: dict[str, Any], user: str = "Admin Owner") -> dict[str, Any]:
        """
        Runs the specified task.
        """
        title = action["title"]
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Simulate execution response
        result = f"Successfully executed: {title}."
        impact = action.get("impact", "Campaign launched successfully.")
        
        # Write to history memory
        agent_memory.log_decision(action_desc=title, status="completed", impact=impact)
        
        return {
            "action_id": action["id"],
            "title": title,
            "executor": user,
            "timestamp": timestamp,
            "result": result,
            "status": "success"
        }

agent_executor = ExecutionModule()
