from typing import Any, ClassVar

from langchain_core.tools import BaseTool
from nl2mongo.utils.mongodb_handler import MongoDBHandler
from nl2mongo.utils.llm_handler import LLMHandler


class ExecuteQueryTool(BaseTool):
    name: ClassVar[str]
    description: ClassVar[str]
    name = "execute_query_tool"
    description = (
        "Executes MongoDB queries and determines whether to represent the results as a table or plain text."
    )

    def __init__(self, database_name: str, collection_name: str, llm_handler: LLMHandler, **kwargs: Any):
        super().__init__(**kwargs)
        self.db_handler = MongoDBHandler(database_name, collection_name)
        self.llm_handler = llm_handler  # For determining result presentation format

    def _run(self, query: dict, sort: dict) -> dict:
        """
        Executes a query on the MongoDB collection and sorts it if necessary.
        Args:
            query: MongoDB query as a dictionary.
            sort: sorting criteria as a dictionary
        Returns:
            dict: Results formatted based on LLM's decision.
        """
        try:
            # Execute query
            results = self.db_handler.execute_query(query, sort=sort)
            if not results:
                return {"message": "No results found for the given query."}

            # Format the results using the LLM's decision (table or plain text)
            explanation_prompt = (
                "Should the following query results be represented in a table or plain text? "
                "Provide your reasoning and decide: {results}"
            )
            prompt = explanation_prompt.format(results=results)
            response = self.llm_handler.generate_response(prompt)

            # Parse LLM's decision and prepare the final output
            formatted_results = self.db_handler.format_results(results)
            if "table" in response.lower():
                keys = formatted_results[0].keys()
                table = f"{' | '.join(keys)}\n" + "-" * (len(keys) * 8) + "\n"
                table += "\n".join([" | ".join(str(result[key]) for key in keys) for result in formatted_results])
                return {"presentation": "table", "content": table}
            else:
                return {"presentation": "plain text", "content": str(formatted_results)}
        except Exception as e:
            return {"error": str(e)}
