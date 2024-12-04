import os
import logging
from utils.llm_handler import LLMHandler
from utils.mongodb_handler import MongoDBHandler

LOG_FILE = os.getenv('LOG_FILE')

# Configure logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Initialize LLMHandler
llm_handler = LLMHandler(
    model_name="gpt-4o-mini",
    temperature=0,
)

# Initialize MongoDBHandler
mongodb_handler = MongoDBHandler(
    database_name=os.getenv("DATABASE_NAME"),
    collection_name=os.getenv("COLLECTION_NAME"),
)


def process_user_input(user_input):
    """
    Process user input, generate a query via LLM, execute it on MongoDB, and return results.

    :param user_input: The user's natural language input.
    """

    response = llm_handler.chat_with_llm(user_input)

    # Check if the response is ambiguous
    if response.get("type") == "explanation":
        return {"type": "explanation", "message": response.get("message", "No explanation provided.")}

    # Extract query and sort
    query = response.get("query", {})
    sort = response.get("sort", {})

    # Execute query if valid
    results = mongodb_handler.execute_query(query, sort)
    return {"type": "results", "data": results}
