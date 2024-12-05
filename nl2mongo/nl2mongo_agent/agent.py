from typing import Annotated, Literal, TypedDict
from langchain_core.messages import AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field
from nl2mongo.utils.llm_handler import LLMHandler
from nl2mongo.utils.mongodb_handler import MongoDBHandler
from tools.get_schema_tool import GetSchemaTool
from tools.execute_query_tool import ExecuteQueryTool
from tools.clarification_tool import ClarificationTool
from langchain_core.runnables import RunnableLambda, RunnableWithFallbacks
from IPython.display import Image, display
from langchain_core.runnables.graph import MermaidDrawMethod
import logging
import os
from dotenv import load_dotenv

load_dotenv()

LOG_FILE = os.getenv('LOG_FILE')

# Configure logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# Load the agent prompt
def load_agent_prompt() -> str:
    """
    Load prompt template from a text file.

    :return: The agent prompt template as a string.
    """
    try:
        with open(os.getenv("AGENT_PROMPT_PATH"), 'r') as file:
            prompt_template = file.read()
        return prompt_template
    except FileNotFoundError:
        logging.error("Prompt file not found. Ensure the PROMPT_PATH is correct.")
        raise
    except Exception as e:
        logging.error(f"Unexpected error while loading prompt: {e}")
        raise


# Define state for the agent
class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


# Error Handling and Fallbacks
def handle_tool_error(state):
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    logging.error(f"Tool Error: {repr(error)}")
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }


def create_tool_node_with_fallback(tool_instance):
    return ToolNode([tool_instance]).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
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

# Tools setup
get_schema_tool = GetSchemaTool(db_handler=mongodb_handler)
execute_query_tool = ExecuteQueryTool(database_name=os.getenv("DATABASE_NAME"),
                                      collection_name=os.getenv("COLLECTION_NAME"), llm_handler=llm_handler)
clarification_tool = ClarificationTool()

# Nodes creation
get_schema_node = create_tool_node_with_fallback(get_schema_tool)
execute_query_node = create_tool_node_with_fallback(execute_query_tool)
clarify_node = create_tool_node_with_fallback(clarification_tool)

# LLM for query generation
query_gen_prompt = load_agent_prompt()
query_gen_llm = ChatOpenAI(model="gpt-4o", temperature=0)
query_gen = query_gen_llm.bind_tools([clarification_tool])

# State Graph
workflow = StateGraph(State)


# First tool call
def first_tool_call(state: State) -> dict[str, list[AIMessage]]:
    return {
        "messages": [
            AIMessage(
                content="Let me retrieve the schema of the collection to assist you.",
                tool_calls=[{"name": "get_schema_tool", "args": {}, "id": "tool_123"}],
            )
        ]
    }


def query_gen_node(state: State):
    # Generate the query using the query_gen model
    message = query_gen.invoke(state)

    return {"messages": [message]}


# Final Answer Submission
class SubmitFinalAnswer(BaseModel):
    final_answer: str = Field(..., description="Final answer to the user's query.")


workflow.add_node("first_tool_call", first_tool_call)
workflow.add_node("get_schema_tool", get_schema_node)
workflow.add_node("query_gen", query_gen_node)
workflow.add_node("clarify_node", clarify_node)
workflow.add_node("execute_query", execute_query_node)
workflow.add_node("submit_final_answer", ToolNode([SubmitFinalAnswer]))


# Conditional Flow: Query Generation
def should_continue(state: State) -> Literal["execute_query", "query_gen", "clarify_node"]:
    last_message = state["messages"][-1]

    # Scenario 1: If there's an error in the query execution
    if last_message.content.startswith("Error:"):
        return "query_gen"  # Retry query generation

    # Scenario 2: If the generated query is ambiguous or empty
    if last_message.content.startswith("I didn't quite understand your request"):
        return "clarify_node"  # Call clarify node for more user input

    # Scenario 3: If the query has been successfully generated
    return "execute_query"


# Conditional Flow: Execute Query
def handle_execute_query(state: State) -> Literal["query_gen", "submit_final_answer"]:
    last_message = state["messages"][-1]

    if "Error:" in last_message.content:  # If there's an error, retry query_gen
        return "query_gen"
    else:
        # If no errors, proceed to submit final answer
        return "submit_final_answer"


# Build the graph by adding edges
workflow.add_edge(START, "first_tool_call")
workflow.add_edge("first_tool_call", "get_schema_tool")
workflow.add_edge("get_schema_tool", "query_gen")
workflow.add_conditional_edges("query_gen", should_continue)
workflow.add_edge("clarify_node", "query_gen")
workflow.add_conditional_edges("execute_query", handle_execute_query)
workflow.add_edge("submit_final_answer", END)

# Compile Workflow
app = workflow.compile()

if __name__ == "__main__":
    display(
        Image(
            app.get_graph().draw_mermaid_png(
                draw_method=MermaidDrawMethod.API,
            )
        )
    )
