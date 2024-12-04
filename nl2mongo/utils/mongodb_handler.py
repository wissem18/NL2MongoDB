import os

from pymongo import MongoClient
from typing import Dict, Any, List
import logging


class MongoDBHandler:
    def __init__(self, database_name: str, collection_name: str):
        """
        Initialize the MongoDB connection.

        :param database_name: The name of the database to connect to.
        :param collection_name: The name of the collection to operate on.
        """
        try:
            self.client = MongoClient(os.getenv("MONGO_URI"))
            self.database = self.client[database_name]
            self.collection = self.database[collection_name]
            logging.info("MongoDB connection established successfully.")
        except Exception as e:
            logging.error(f"Error initializing MongoDB connection: {e}")
            raise

    def execute_query(self, query: Dict[str, Any], sort: Dict[str, int] = None) -> List[Dict[str, Any]]:
        """
        Execute a MongoDB query with optional sorting and return the results.

        :param query: MongoDB query to execute.
        :param sort: Sorting criteria as a dictionary (e.g., {"field_name": 1} for ascending).
        :return: List of query results.
        """
        try:
            logging.info(f"Executing query: {query}, with sort: {sort}")
            if sort:
                results = list(self.collection.find(query).sort(list(sort.items())))
            else:
                results = list(self.collection.find(query))
            logging.info(f"Query executed successfully. Found {len(results)} results.")
            return results
        except Exception as e:
            logging.error(f"Error executing MongoDB query: {e}")
            raise

    def format_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format query results into a consistent, user-friendly structure.

        :param results: List of raw query results.
        :return: Formatted list of results.
        """
        try:
            formatted_results = []
            for result in results:
                # Convert ObjectId to string or exclude it
                result.pop("_id", None)  # Remove the '_id' field
                formatted_results.append(result)
            logging.info("Results formatted successfully.")
            return formatted_results
        except Exception as e:
            logging.error(f"Error formatting results: {e}")
            raise

    def close_connection(self):
        """Close the MongoDB connection."""
        try:
            self.client.close()
            logging.info("MongoDB connection closed successfully.")
        except Exception as e:
            logging.error(f"Error closing MongoDB connection: {e}")
            raise
