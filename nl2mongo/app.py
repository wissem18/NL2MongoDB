import streamlit as st
from main import process_user_input, llm_handler
import pandas as pd

st.set_page_config(page_title="Compliance Regulatory MongoDB Query Assistant", layout="wide")
st.title("MongoDB Chat Assistant")
# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_input" not in st.session_state:
    st.session_state.chat_input = ""


# Function to reset chat
def reset_chat():
    st.session_state.messages = []
    st.session_state.chat_input = ""


# Sidebar for options
st.sidebar.title("Options")
if st.sidebar.button("New Chat"):
    reset_chat()
    llm_handler.conversation_history = []  # Clear LLM context when starting a new chat

# Display chat messages
for msg in st.session_state.messages:
    role = "You" if msg["role"] == "user" else "Assistant"
    with st.chat_message(role):
        st.markdown(msg["content"])
        if msg.get("results"):  # Display query results
            df = pd.DataFrame(msg["results"])
            if "_id" in df.columns:
                df["_id"] = df["_id"].astype(str)  # Convert ObjectId to string
            st.dataframe(df, use_container_width=True)  # Render as a table

# Add the chat input field
if prompt := st.chat_input("Ask your MongoDB Document"):
    # Add the user's input to the chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process the user's input
    response = process_user_input(prompt)

    # Add the assistant's response to the chat history
    if response["type"] == "explanation":
        assistant_message = response["message"]
        with st.chat_message("assistant"):
            st.error(assistant_message)
        st.session_state.messages.append({"role": "assistant", "content": assistant_message})
    elif response["type"] == "results":
        if response["data"]:
            assistant_message = "Here are the results:"
            with st.chat_message("assistant"):
                st.markdown(assistant_message)
                df = pd.DataFrame(response["data"])
                st.dataframe(df, use_container_width=True)
            st.session_state.messages.append({
                "role": "assistant",
                "content": assistant_message,
                "results": response["data"]
            })
        else:
            assistant_message = "No results found."
            with st.chat_message("assistant"):
                st.markdown(assistant_message)
            st.session_state.messages.append({"role": "assistant", "content": assistant_message})
