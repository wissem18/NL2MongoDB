from typing import Any, ClassVar

from langchain_core.tools import BaseTool
from nl2mongo.utils.mongodb_handler import MongoDBHandler


class GetSchemaTool(BaseTool):
    name: ClassVar[str]
    description: ClassVar[str]
    db_handler: MongoDBHandler
    name = "get_schema_tool"
    description = "Retrieves the schema of the MongoDB collection currently in use."

    def __init__(self, db_handler: MongoDBHandler, **kwargs: Any):
        super().__init__(**kwargs)
        self.db_handler = db_handler

    def _run(self) -> dict:
        """
        Retrieves the schema of the current MongoDB collection.
        Returns:
            dict: The schema with field names and types.
        """
        try:
            sample_doc = self.db_handler.execute_query({}, sort=None)
            if not sample_doc:
                return {"message": "The collection is empty; unable to retrieve schema."}

            # Extract field names and data types from a sample document
            schema = {key: type(value).__name__ for key, value in sample_doc[0].items()}
            return {"schema": schema}
        except Exception as e:
            return {"error": str(e)}
