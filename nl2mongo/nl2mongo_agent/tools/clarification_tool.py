from typing import Dict, ClassVar

from langchain_core.tools import BaseTool


class ClarificationTool(BaseTool):
    name: ClassVar[str]
    description: ClassVar[str]
    name = "clarification_tool"
    description = "Requests clarification from the user when the query is ambiguous."

    def _run(self, question: str) -> Dict[str, str]:
        """
        Interacts with the user for query clarification.
        Args:
            question: User's original question.
        Returns:
            Clarification request.
        """
        clarification_prompt = f"I didn't quite understand your request: '{question}'.\n Could you please clarify or provide more details?"
        return {"clarification": clarification_prompt}
