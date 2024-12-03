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


# Start the chat-based application
def main():
    print("Welcome to the MongoDB Query Assistant!")
    print("Ask your questions, and I'll generate MongoDB queries for you.")
    print("Type 'exit' or 'quit' to end the session.\n")
    while True:
        try:
            user_input = input("\nYour Question: ")
            if user_input.lower() in ["exit", "quit"]:
                mongodb_handler.close_connection()
                print("Goodbye!")
                break

            # Pass the user input to the LLM handler
            response = llm_handler.chat_with_llm(user_input)

            # Get the query and sort from the response
            query = response.get("query", {})
            sort = response.get("sort", {})
            logging.info(f"Generated Query: {query}, Sort: {sort}")

            # Execute the query and fetch results
            try:
                results = mongodb_handler.execute_query(query, sort)
                formatted_results = mongodb_handler.format_results(results)

                print("\nQuery Results:")
                if formatted_results:
                    for result in formatted_results:
                        print(result)
                else:
                    print("No results found.")

                logging.info(f"Query Results: {formatted_results}")

            except Exception as e:
                print("Error executing the query. Please check your database connection or query syntax.")
                logging.error(f"Error executing query: {e}")

        except Exception as e:
            print("An error occurred. Please try again.")
            logging.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
