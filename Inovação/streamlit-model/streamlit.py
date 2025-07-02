import streamlit as st
import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional
import openai
from openai import OpenAI
import base64
import os

# Page configuration
st.set_page_config(
    page_title="ChatGPT Interface",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS for styling
st.markdown(
    """
<style>
/* Modern ChatGPT Interface Styles */
:root {
    --primary-color: #007acc;
    --primary-hover: #005999;
    --secondary-color: #f5f5f5;
    --background-color: #ffffff;
    --surface-color: #ffffff;
    --text-color: #333333;
    --text-secondary: #666666;
    --border-color: #e0e0e0;
    --shadow-color: rgba(0, 0, 0, 0.1);
    --success-color: #22c55e;
    --error-color: #ef4444;
    --warning-color: #f59e0b;
}

.stApp {
    background-color: var(--background-color);
}

/* Main chat container */
.chat-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 1rem;
}

/* Message styling */
.user-message {
    background-color: #f0f0f0;
    padding: 12px 16px;
    border-radius: 12px;
    margin: 8px 0;
    border-top-right-radius: 4px;
}

.assistant-message {
    background-color: transparent;
    padding: 12px 0;
    margin: 8px 0;
}

/* Avatar styling */
.message-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    margin-right: 12px;
    background-color: var(--secondary-color);
    display: flex;
    align-items: center;
    justify-content: center;
}

/* Welcome message */
.welcome-container {
    text-align: center;
    padding: 2rem;
    color: var(--text-secondary);
}

.welcome-container h2 {
    font-size: 24px;
    font-weight: 600;
    margin-bottom: 0.5rem;
    color: var(--text-color);
}

/* Assistant info */
.assistant-info {
    background-color: #f8f9fa;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 16px;
    border-left: 4px solid var(--primary-color);
}

/* Theme toggle */
.theme-toggle {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 16px;
}

/* Stop button */
.stop-button {
    background-color: var(--error-color);
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    cursor: pointer;
}

/* Loading indicator */
.loading-dots {
    display: inline-block;
    width: 20px;
    height: 20px;
}

.loading-dots::after {
    content: "⏳";
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Code block styling */
pre {
    background-color: #f4f4f4;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 16px;
    overflow-x: auto;
    font-family: 'Monaco', 'Cascadia Code', 'Roboto Mono', monospace;
}

/* Hide Streamlit elements */
.stDeployButton {
    display: none;
}

#MainMenu {
    visibility: hidden;
}

.stFooter {
    display: none;
}

/* Custom button styling */
.stButton > button {
    background-color: var(--primary-color);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 0.5rem 1rem;
    font-weight: 500;
    transition: background-color 0.2s ease;
}

.stButton > button:hover {
    background-color: var(--primary-hover);
}

/* Sidebar styling */
.css-1d391kg {
    padding-top: 1rem;
}
</style>
""",
    unsafe_allow_html=True,
)


# Configuration classes
class ChatModel:
    def __init__(self, id: str, name: str, context_window: int, max_tokens: int):
        self.id = id
        self.name = name
        self.context_window = context_window
        self.max_tokens = max_tokens


class AssistantConfig:
    def __init__(self, id: str, name: str, description: str):
        self.id = id
        self.name = name
        self.description = description


# Available models and assistants
AVAILABLE_MODELS = {
    "gpt-4o": ChatModel("gpt-4o", "GPT-4o", 128000, 4096),
    "gpt-4o-mini": ChatModel("gpt-4o-mini", "GPT-4o Mini", 128000, 16384),
    "o3-mini": ChatModel("o3-mini", "O3 Mini", 128000, 65536),
}

AVAILABLE_ASSISTANTS = {
    "organizador_atas": AssistantConfig(
        "asst_gl4svzGMPxoDMYskRHzK62Fk",
        "Organizador de Atas",
        "Especialista em organizar e estruturar atas de reunião",
    ),
    "criador_propostas": AssistantConfig(
        "asst_gqDpEGoOpRvpUai7fdVxgg4d",
        "Criador de Propostas Comerciais",
        "Especialista em criar propostas comerciais persuasivas",
    ),
}

DEFAULT_MODEL = "gpt-4o"
DEFAULT_ASSISTANT = "organizador_atas"


# Initialize session state
def initialize_session_state():
    if "chat_id" not in st.session_state:
        st.session_state.chat_id = str(uuid.uuid4())

    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []

    if "thread_id" not in st.session_state:
        st.session_state.thread_id = None

    if "current_assistant" not in st.session_state:
        st.session_state.current_assistant = DEFAULT_ASSISTANT

    if "current_model" not in st.session_state:
        st.session_state.current_model = DEFAULT_MODEL

    if "is_generating" not in st.session_state:
        st.session_state.is_generating = False

    if "theme" not in st.session_state:
        st.session_state.theme = "light"

    if "conversations" not in st.session_state:
        st.session_state.conversations = {}


# Initialize OpenAI client
@st.cache_resource
def get_openai_client():
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    if not api_key:
        st.error(
            "OpenAI API key not found in secrets. Please add OPENAI_API_KEY to your Streamlit secrets."
        )
        st.stop()

    return OpenAI(api_key=api_key)


# Utility functions
def generate_conversation_title(messages: List[Dict]) -> str:
    """Generate conversation title from first user message"""
    for msg in messages:
        if msg.get("role") == "user":
            content = msg.get("content", "")
            return content[:50] + ("..." if len(content) > 50 else "")
    return "New Conversation"


def save_conversation():
    """Save current conversation to session state"""
    if st.session_state.conversation_history:
        conversation = {
            "id": st.session_state.chat_id,
            "title": generate_conversation_title(st.session_state.conversation_history),
            "messages": st.session_state.conversation_history.copy(),
            "timestamp": datetime.now().isoformat(),
            "assistant": st.session_state.current_assistant,
        }
        st.session_state.conversations[st.session_state.chat_id] = conversation


def load_conversation(conv_id: str):
    """Load a specific conversation"""
    if conv_id in st.session_state.conversations:
        conversation = st.session_state.conversations[conv_id]
        st.session_state.chat_id = conv_id
        st.session_state.conversation_history = conversation["messages"].copy()
        st.session_state.current_assistant = conversation.get(
            "assistant", DEFAULT_ASSISTANT
        )
        st.session_state.thread_id = None  # Reset thread when loading conversation


def start_new_conversation():
    """Start a new conversation"""
    # Save current conversation if it has messages
    if st.session_state.conversation_history:
        save_conversation()

    # Reset state
    st.session_state.chat_id = str(uuid.uuid4())
    st.session_state.conversation_history = []
    st.session_state.thread_id = None
    st.session_state.is_generating = False


# Assistant API functions
def stream_assistant_response(message: str, client: OpenAI) -> str:
    """Stream response from OpenAI Assistant"""
    try:
        assistant_config = AVAILABLE_ASSISTANTS[st.session_state.current_assistant]

        # Create or use existing thread
        if not st.session_state.thread_id:
            thread = client.beta.threads.create()
            st.session_state.thread_id = thread.id

            # Add conversation history to thread
            for msg in st.session_state.conversation_history[-10:]:  # Last 10 messages
                if msg["role"] in ["user", "assistant"]:
                    client.beta.threads.messages.create(
                        thread_id=st.session_state.thread_id,
                        role=msg["role"],
                        content=msg["content"],
                    )

        # Add current message to thread
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id, role="user", content=message
        )

        # Create and run assistant
        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=assistant_config.id,
        )

        # Poll for completion
        max_polling_time = 300  # 5 minutes
        polling_start = time.time()

        while True:
            if time.time() - polling_start > max_polling_time:
                return "Response timed out. Please try again."

            run = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id, run_id=run.id
            )

            if run.status == "completed":
                # Get the latest assistant message
                messages = client.beta.threads.messages.list(
                    thread_id=st.session_state.thread_id, order="desc", limit=1
                )

                if messages.data and messages.data[0].role == "assistant":
                    message = messages.data[0]
                    if message.content and message.content[0].type == "text":
                        return message.content[0].text.value

                return "No response received."

            elif run.status == "failed":
                error_msg = (
                    run.last_error.message if run.last_error else "Unknown error"
                )
                return f"Assistant run failed: {error_msg}"

            elif run.status in ["cancelled", "expired"]:
                return f"Assistant run {run.status}"

            elif run.status == "requires_action":
                return "Assistant requires action (not supported)"

            # Still running, wait a bit
            time.sleep(1)

    except Exception as e:
        return f"Error: {str(e)}"


# Main interface
def main():
    initialize_session_state()
    client = get_openai_client()

    # Sidebar
    with st.sidebar:
        st.title("🤖 ChatGPT Interface")

        # New Chat Button
        if st.button("➕ New Chat", use_container_width=True):
            start_new_conversation()
            st.rerun()

        st.divider()

        # Conversations List
        st.subheader("Conversations")
        if st.session_state.conversations:
            for conv_id, conversation in reversed(
                list(st.session_state.conversations.items())
            ):
                col1, col2 = st.columns([4, 1])
                with col1:
                    if st.button(
                        conversation["title"],
                        key=f"conv_{conv_id}",
                        use_container_width=True,
                        type=(
                            "secondary"
                            if conv_id != st.session_state.chat_id
                            else "primary"
                        ),
                    ):
                        load_conversation(conv_id)
                        st.rerun()

                with col2:
                    if st.button("🗑️", key=f"del_{conv_id}", help="Delete conversation"):
                        del st.session_state.conversations[conv_id]
                        if conv_id == st.session_state.chat_id:
                            start_new_conversation()
                        st.rerun()
        else:
            st.info("No conversations yet")

        st.divider()

        # Settings
        st.subheader("Settings")

        # Assistant Selection
        assistant_options = {k: v.name for k, v in AVAILABLE_ASSISTANTS.items()}
        selected_assistant = st.selectbox(
            "Assistente:",
            options=list(assistant_options.keys()),
            format_func=lambda x: assistant_options[x],
            index=list(assistant_options.keys()).index(
                st.session_state.current_assistant
            ),
        )

        if selected_assistant != st.session_state.current_assistant:
            if st.session_state.conversation_history:
                if st.button("Confirm Assistant Change", type="primary"):
                    st.session_state.current_assistant = selected_assistant
                    start_new_conversation()
                    st.rerun()
                st.warning("Changing assistant will start a new conversation.")
            else:
                st.session_state.current_assistant = selected_assistant

        # Display assistant info
        assistant_info = AVAILABLE_ASSISTANTS[st.session_state.current_assistant]
        st.info(f"**{assistant_info.name}**\n\n{assistant_info.description}")

        # Model Selection
        model_options = {k: v.name for k, v in AVAILABLE_MODELS.items()}
        st.session_state.current_model = st.selectbox(
            "Modelo:",
            options=list(model_options.keys()),
            format_func=lambda x: model_options[x],
            index=list(model_options.keys()).index(st.session_state.current_model),
        )

        # Theme Selection
        theme = st.radio(
            "Theme:",
            options=["light", "dark"],
            index=0 if st.session_state.theme == "light" else 1,
            horizontal=True,
        )
        st.session_state.theme = theme

        st.divider()

        # App Info
        st.caption("ChatGPT Interface v2.0")
        st.caption(f"Chat ID: {st.session_state.chat_id[:8]}...")

    # Main content area
    st.markdown(
        f"""
    <div class="chat-container">
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1>ChatGPT</h1>
            <p style="color: #666; margin: 0;">
                {AVAILABLE_ASSISTANTS[st.session_state.current_assistant].name}
            </p>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Display conversation or welcome message
    if not st.session_state.conversation_history:
        st.markdown(
            f"""
        <div class="welcome-container">
            <h2>Nova Conversa com {AVAILABLE_ASSISTANTS[st.session_state.current_assistant].name}</h2>
            <p>{AVAILABLE_ASSISTANTS[st.session_state.current_assistant].description}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
    else:
        # Display conversation history
        for i, message in enumerate(st.session_state.conversation_history):
            if message["role"] == "user":
                with st.container():
                    col1, col2 = st.columns([1, 10])
                    with col1:
                        st.markdown("👤", help="User")
                    with col2:
                        st.markdown(
                            f'<div class="user-message">{message["content"]}</div>',
                            unsafe_allow_html=True,
                        )

            elif message["role"] == "assistant":
                with st.container():
                    col1, col2 = st.columns([1, 10])
                    with col1:
                        st.markdown("🤖", help="Assistant")
                    with col2:
                        st.markdown(message["content"])

    # Stop generation button
    if st.session_state.is_generating:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                "⏹ Stop Generation", type="secondary", use_container_width=True
            ):
                st.session_state.is_generating = False
                st.rerun()

    # Input area
    st.markdown("---")

    # Message input
    with st.form(key="message_form", clear_on_submit=True):
        message_input = st.text_area(
            "Type your message here...",
            height=100,
            max_chars=4000,
            disabled=st.session_state.is_generating,
            label_visibility="collapsed",
            placeholder="Type your message here... (Shift+Enter for new line)",
        )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            send_button = st.form_submit_button(
                "Send →" if not st.session_state.is_generating else "Generating...",
                disabled=st.session_state.is_generating or not message_input.strip(),
                use_container_width=True,
                type="primary",
            )

    # Handle message submission
    if send_button and message_input.strip() and not st.session_state.is_generating:
        st.session_state.is_generating = True

        # Add user message to conversation
        user_message = {"role": "user", "content": message_input.strip()}
        st.session_state.conversation_history.append(user_message)

        # Show generating status
        with st.status("Generating response...", expanded=True) as status:
            st.write("Processing your message...")

            # Generate response
            response = stream_assistant_response(message_input.strip(), client)

            # Add assistant response to conversation
            assistant_message = {"role": "assistant", "content": response}
            st.session_state.conversation_history.append(assistant_message)

            status.update(label="Response generated!", state="complete")

        # Save conversation and reset generating state
        save_conversation()
        st.session_state.is_generating = False
        st.rerun()


if __name__ == "__main__":
    main()
