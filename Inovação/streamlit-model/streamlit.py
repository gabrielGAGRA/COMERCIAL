import streamlit as st
import openai
from openai import OpenAI
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
import base64
import os

# Configuração da página
st.set_page_config(
    page_title="ChatGPT Interface",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS customizado para replicar o visual original
st.markdown(
    """
<style>
/* Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Root variables */
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
    --font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    --font-mono: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
    --border-radius: 8px;
    --border-radius-sm: 4px;
    --border-radius-lg: 12px;
}

/* Dark theme */
[data-theme="dark"] {
    --primary-color: #4a9eff;
    --primary-hover: #3b82f6;
    --secondary-color: #2d2d2d;
    --background-color: #1a1a1a;
    --surface-color: #242424;
    --text-color: #e0e0e0;
    --text-secondary: #a0a0a0;
    --border-color: #404040;
    --shadow-color: rgba(255, 255, 255, 0.1);
}

/* Override Streamlit default styles */
.stApp {
    font-family: var(--font-family) !important;
}

/* Main container */
.main .block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
    max-width: none;
}

/* Sidebar styling */
.css-1d391kg {
    background-color: var(--surface-color);
    border-right: 1px solid var(--border-color);
}

/* Chat messages styling */
.chat-message {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.5rem;
    padding: 0.75rem 0;
}

.chat-avatar {
    flex-shrink: 0;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    overflow: hidden;
    background-color: var(--secondary-color);
    display: flex;
    align-items: center;
    justify-content: center;
}

.chat-avatar img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.chat-content {
    flex: 1;
    min-width: 0;
}

.user-message .chat-content {
    background-color: var(--secondary-color);
    padding: 0.75rem 1rem;
    border-radius: var(--border-radius);
    border-top-left-radius: var(--border-radius-sm);
}

.assistant-message .chat-content {
    padding: 0.75rem 0;
}

/* Button styling */
.stButton > button {
    background-color: var(--primary-color);
    color: white;
    border: none;
    border-radius: var(--border-radius);
    font-weight: 500;
    transition: background-color 0.2s ease;
    font-family: var(--font-family);
}

.stButton > button:hover {
    background-color: var(--primary-hover);
}

/* New chat button */
.new-chat-btn {
    width: 100%;
    background-color: var(--primary-color) !important;
    color: white !important;
    border: none !important;
    border-radius: var(--border-radius) !important;
    font-weight: 500 !important;
    padding: 0.75rem 1rem !important;
    margin-bottom: 1rem !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 0.5rem !important;
}

/* Text input styling */
.stTextArea textarea {
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    font-family: var(--font-family);
    padding: 0.75rem 1rem;
    min-height: 48px;
    max-height: 200px;
}

.stTextArea textarea:focus {
    border-color: var(--primary-color);
    box-shadow: 0 0 0 1px var(--primary-color);
}

/* Select box styling */
.stSelectbox > div > div {
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius-sm);
    background-color: var(--background-color);
}

/* Radio button styling for theme */
.stRadio > div {
    display: flex;
    gap: 0.5rem;
}

/* Custom conversation item */
.conversation-item {
    padding: 0.5rem 1rem;
    margin-bottom: 0.25rem;
    border-radius: var(--border-radius);
    cursor: pointer;
    font-size: 14px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    background: transparent;
    border: 1px solid transparent;
    color: var(--text-color);
}

.conversation-item:hover {
    background-color: var(--secondary-color);
}

.conversation-item.active {
    background-color: var(--primary-color);
    color: white;
}

/* Loading indicator */
.loading-indicator {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem;
    color: var(--text-secondary);
}

/* Welcome message */
.welcome-message {
    text-align: center;
    padding: 2rem 1rem;
    color: var(--text-secondary);
}

.welcome-message h2 {
    font-size: 24px;
    font-weight: 600;
    margin-bottom: 0.5rem;
    color: var(--text-color);
}

/* Theme selector */
.theme-selector {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.5rem;
}

.theme-btn {
    padding: 0.5rem;
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius-sm);
    cursor: pointer;
    background: transparent;
    font-size: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 36px;
    height: 36px;
}

.theme-btn.active {
    background-color: var(--primary-color);
    border-color: var(--primary-color);
    color: white;
}

/* Stop button */
.stop-btn {
    background-color: var(--error-color) !important;
    color: white !important;
    border: none !important;
    padding: 0.5rem 1rem !important;
    border-radius: var(--border-radius-sm) !important;
    font-size: 12px !important;
    display: flex !important;
    align-items: center !important;
    gap: 0.5rem !important;
}

/* Assistant info */
.assistant-description {
    font-size: 11px;
    color: var(--text-secondary);
    font-style: italic;
    margin-top: 0.25rem;
    line-height: 1.3;
}

/* Error message */
.error-message {
    background-color: rgba(239, 68, 68, 0.1);
    border: 1px solid var(--error-color);
    color: var(--error-color);
    padding: 0.75rem 1rem;
    border-radius: var(--border-radius);
    margin: 0.5rem 0;
}

/* Code blocks */
pre {
    background-color: var(--secondary-color) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: var(--border-radius) !important;
    padding: 1rem !important;
    overflow-x: auto !important;
    font-family: var(--font-mono) !important;
    font-size: 14px !important;
    line-height: 1.4 !important;
}

code {
    font-family: var(--font-mono) !important;
    font-size: 0.9em !important;
    background-color: var(--secondary-color) !important;
    padding: 0.2em 0.4em !important;
    border-radius: var(--border-radius-sm) !important;
}

/* Hide streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Custom scrollbar */
::-webkit-scrollbar {
    width: 6px;
}

::-webkit-scrollbar-track {
    background: var(--secondary-color);
}

::-webkit-scrollbar-thumb {
    background: var(--border-color);
    border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--text-secondary);
}
</style>
""",
    unsafe_allow_html=True,
)

# Configurações e modelos disponíveis
AVAILABLE_MODELS = {
    "gpt-4o": {
        "id": "gpt-4o",
        "name": "GPT-4o",
        "context_window": 128000,
        "max_tokens": 4096,
    },
    "gpt-4o-mini": {
        "id": "gpt-4o-mini",
        "name": "GPT-4o Mini",
        "context_window": 128000,
        "max_tokens": 16384,
    },
    "o3-mini": {
        "id": "o3-mini",
        "name": "O3 Mini",
        "context_window": 128000,
        "max_tokens": 65536,
    },
}

AVAILABLE_ASSISTANTS = {
    "organizador_atas": {
        "id": "asst_gl4svzGMPxoDMYskRHzK62Fk",
        "name": "Organizador de Atas",
        "description": "Especialista em organizar e estruturar atas de reunião",
    },
    "criador_propostas": {
        "id": "asst_gqDpEGoOpRvpUai7fdVxgg4d",
        "name": "Criador de Propostas Comerciais",
        "description": "Especialista em criar propostas comerciais persuasivas",
    },
}


# Inicialização do estado da sessão
def init_session_state():
    """Inicializa o estado da sessão"""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "conversations" not in st.session_state:
        st.session_state.conversations = {}

    if "current_conversation_id" not in st.session_state:
        st.session_state.current_conversation_id = str(uuid.uuid4())

    if "current_assistant" not in st.session_state:
        st.session_state.current_assistant = "organizador_atas"

    if "current_model" not in st.session_state:
        st.session_state.current_model = "gpt-4o"

    if "theme" not in st.session_state:
        st.session_state.theme = "light"

    if "thread_id" not in st.session_state:
        st.session_state.thread_id = None

    if "is_generating" not in st.session_state:
        st.session_state.is_generating = False


def get_openai_client():
    """Inicializa o cliente OpenAI"""
    try:
        # Tenta pegar a API key dos secrets do Streamlit
        api_key = st.secrets.get("OPENAI_API_KEY", "")
        if not api_key:
            # Fallback para variável de ambiente
            api_key = os.getenv("OPENAI_API_KEY", "")

        if not api_key:
            st.error(
                "⚠️ API key da OpenAI não encontrada. Configure OPENAI_API_KEY nos secrets do Streamlit."
            )
            st.stop()

        return OpenAI(api_key=api_key)
    except Exception as e:
        st.error(f"❌ Erro ao inicializar cliente OpenAI: {str(e)}")
        st.stop()


def create_avatar_image(role: str) -> str:
    """Cria uma imagem de avatar simples usando base64"""
    if role == "user":
        # SVG simples para usuário
        svg = """
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="16" cy="16" r="16" fill="#007acc"/>
            <circle cx="16" cy="12" r="5" fill="white"/>
            <path d="M6 28c0-5.5 4.5-10 10-10s10 4.5 10 10" fill="white"/>
        </svg>
        """
    else:
        # SVG simples para assistente
        svg = """
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="16" cy="16" r="16" fill="#22c55e"/>
            <path d="M12 12h8v2h-8zm0 4h8v2h-8zm0 4h5v2h-5z" fill="white"/>
            <circle cx="8" cy="8" r="2" fill="white"/>
            <circle cx="24" cy="8" r="2" fill="white"/>
        </svg>
        """

    # Converte SVG para base64
    svg_bytes = svg.encode("utf-8")
    svg_base64 = base64.b64encode(svg_bytes).decode("utf-8")
    return f"data:image/svg+xml;base64,{svg_base64}"


def display_message(role: str, content: str):
    """Exibe uma mensagem no chat"""
    avatar_url = create_avatar_image(role)

    message_class = "user-message" if role == "user" else "assistant-message"

    st.markdown(
        f"""
    <div class="chat-message {message_class}">
        <div class="chat-avatar">
            <img src="{avatar_url}" alt="{role.title()}">
        </div>
        <div class="chat-content">
            {content if role == "user" else ""}
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Para mensagens do assistente, usa st.markdown para renderizar markdown
    if role == "assistant":
        st.markdown(content)


def generate_conversation_title(message: str) -> str:
    """Gera um título para a conversa baseado na primeira mensagem"""
    if len(message) > 50:
        return message[:47] + "..."
    return message


def save_conversation():
    """Salva a conversa atual"""
    if st.session_state.chat_history:
        conversation = {
            "id": st.session_state.current_conversation_id,
            "title": generate_conversation_title(
                st.session_state.chat_history[0]["content"]
            ),
            "messages": st.session_state.chat_history.copy(),
            "timestamp": datetime.now().isoformat(),
            "assistant": st.session_state.current_assistant,
            "model": st.session_state.current_model,
        }
        st.session_state.conversations[st.session_state.current_conversation_id] = (
            conversation
        )


def start_new_conversation():
    """Inicia uma nova conversa"""
    save_conversation()
    st.session_state.current_conversation_id = str(uuid.uuid4())
    st.session_state.chat_history = []
    st.session_state.thread_id = None
    st.rerun()


def load_conversation(conversation_id: str):
    """Carrega uma conversa existente"""
    if conversation_id in st.session_state.conversations:
        conversation = st.session_state.conversations[conversation_id]
        st.session_state.current_conversation_id = conversation_id
        st.session_state.chat_history = conversation["messages"]
        st.session_state.current_assistant = conversation.get(
            "assistant", "organizador_atas"
        )
        st.session_state.current_model = conversation.get("model", "gpt-4o")
        st.session_state.thread_id = None  # Reset thread ID for new conversation
        st.rerun()


def stream_assistant_response(
    client: OpenAI, message: str, assistant_id: str, thread_id: Optional[str] = None
):
    """Processa resposta usando OpenAI Assistants API com streaming simulado"""
    try:
        # Cria ou usa thread existente
        if not thread_id:
            thread = client.beta.threads.create()
            thread_id = thread.id
            st.session_state.thread_id = thread_id

            # Adiciona histórico da conversa ao thread
            for msg in st.session_state.chat_history[-10:]:  # Últimas 10 mensagens
                if msg["role"] in ["user", "assistant"]:
                    client.beta.threads.messages.create(
                        thread_id=thread_id, role=msg["role"], content=msg["content"]
                    )

        # Adiciona mensagem atual do usuário
        client.beta.threads.messages.create(
            thread_id=thread_id, role="user", content=message
        )

        # Cria e executa o assistente
        run = client.beta.threads.runs.create(
            thread_id=thread_id, assistant_id=assistant_id
        )

        # Container para a resposta
        response_container = st.empty()
        full_response = ""

        # Polling para aguardar conclusão
        max_polling_time = 300  # 5 minutos
        polling_start = time.time()

        while True:
            if time.time() - polling_start > max_polling_time:
                st.error(
                    "⏰ Timeout: A resposta do assistente demorou muito para ser processada."
                )
                break

            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

            if run.status == "completed":
                # Busca a última mensagem do assistente
                messages = client.beta.threads.messages.list(
                    thread_id=thread_id, order="desc", limit=1
                )

                if messages.data and messages.data[0].role == "assistant":
                    message_content = messages.data[0]
                    if (
                        message_content.content
                        and message_content.content[0].type == "text"
                    ):
                        content = message_content.content[0].text.value

                        # Simula streaming exibindo palavra por palavra
                        words = content.split(" ")
                        for i, word in enumerate(words):
                            if i > 0:
                                full_response += " "
                            full_response += word
                            response_container.markdown(full_response + "▋")
                            time.sleep(0.03)

                        # Exibe resposta final sem cursor
                        response_container.markdown(full_response)
                        return full_response
                break

            elif run.status == "failed":
                error_msg = (
                    run.last_error.message if run.last_error else "Erro desconhecido"
                )
                st.error(f"❌ Falha na execução do assistente: {error_msg}")
                break

            elif run.status in ["cancelled", "expired"]:
                st.warning(f"⚠️ Execução do assistente {run.status}")
                break

            elif run.status == "requires_action":
                st.warning("⚠️ Assistente requer ação (não suportado nesta interface)")
                break

            # Aguarda um pouco antes de verificar novamente
            time.sleep(1)

    except Exception as e:
        st.error(f"❌ Erro ao processar resposta do assistente: {str(e)}")
        return None


def main():
    """Função principal da aplicação"""
    init_session_state()
    client = get_openai_client()

    # Aplica tema
    if st.session_state.theme == "dark":
        st.markdown('<div data-theme="dark">', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        # Header da sidebar com botão New Chat
        st.markdown('<div class="sidebar-header">', unsafe_allow_html=True)
        if st.button("➕ New Chat", key="new_chat", help="Start a new conversation"):
            start_new_conversation()
        st.markdown("</div>", unsafe_allow_html=True)

        # Lista de conversas
        st.markdown("### 💬 Conversations")

        if st.session_state.conversations:
            for conv_id, conversation in reversed(
                list(st.session_state.conversations.items())
            ):
                is_active = conv_id == st.session_state.current_conversation_id

                # Botão da conversa
                button_style = "active" if is_active else ""
                if st.button(
                    conversation["title"],
                    key=f"conv_{conv_id}",
                    help=f"Loaded on {conversation['timestamp'][:10]}",
                ):
                    load_conversation(conv_id)
        else:
            st.markdown("*No conversations yet*")

        st.divider()

        # Configurações
        st.markdown("### ⚙️ Settings")

        # Seleção do assistente
        st.markdown("**Assistant:**")
        current_assistant = st.selectbox(
            "Choose assistant",
            options=list(AVAILABLE_ASSISTANTS.keys()),
            format_func=lambda x: AVAILABLE_ASSISTANTS[x]["name"],
            index=list(AVAILABLE_ASSISTANTS.keys()).index(
                st.session_state.current_assistant
            ),
            key="assistant_select",
            label_visibility="collapsed",
        )

        if current_assistant != st.session_state.current_assistant:
            if st.session_state.chat_history:
                st.warning("⚠️ Changing assistant will start a new conversation.")
                if st.button("Confirm Change", key="confirm_assistant_change"):
                    st.session_state.current_assistant = current_assistant
                    start_new_conversation()
            else:
                st.session_state.current_assistant = current_assistant

        # Descrição do assistente
        assistant_info = AVAILABLE_ASSISTANTS[st.session_state.current_assistant]
        st.markdown(
            f'<div class="assistant-description">{assistant_info["description"]}</div>',
            unsafe_allow_html=True,
        )

        # Seleção do modelo
        st.markdown("**Model:**")
        current_model = st.selectbox(
            "Choose model",
            options=list(AVAILABLE_MODELS.keys()),
            format_func=lambda x: AVAILABLE_MODELS[x]["name"],
            index=list(AVAILABLE_MODELS.keys()).index(st.session_state.current_model),
            key="model_select",
            label_visibility="collapsed",
        )
        st.session_state.current_model = current_model

        # Seletor de tema
        st.markdown("**Theme:**")
        theme_col1, theme_col2 = st.columns(2)

        with theme_col1:
            if st.button("🌞", key="light_theme", help="Light theme"):
                st.session_state.theme = "light"
                st.rerun()

        with theme_col2:
            if st.button("🌙", key="dark_theme", help="Dark theme"):
                st.session_state.theme = "dark"
                st.rerun()

        st.divider()

        # Info da aplicação
        st.markdown("**ChatGPT Interface v2.0**")
        st.markdown("*Streamlit Version*")

    # Área principal
    st.markdown(
        f"""
    <div class="chat-header">
        <h1>ChatGPT</h1>
        <span class="current-assistant">{AVAILABLE_ASSISTANTS[st.session_state.current_assistant]['name']}</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Container de mensagens
    messages_container = st.container()

    with messages_container:
        if not st.session_state.chat_history:
            # Mensagem de boas-vindas
            st.markdown(
                f"""
            <div class="welcome-message">
                <h2>Welcome to ChatGPT Interface</h2>
                <p>Using <strong>{AVAILABLE_ASSISTANTS[st.session_state.current_assistant]['name']}</strong></p>
                <p>{AVAILABLE_ASSISTANTS[st.session_state.current_assistant]['description']}</p>
            </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            # Exibe histórico de mensagens
            for message in st.session_state.chat_history:
                display_message(message["role"], message["content"])

    # Área de input
    st.markdown("---")

    # Input de mensagem
    col1, col2 = st.columns([6, 1])

    with col1:
        user_input = st.text_area(
            "Message",
            placeholder="Type your message here...",
            height=100,
            max_chars=4000,
            key="message_input",
            label_visibility="collapsed",
        )

    with col2:
        send_button = st.button(
            "➤",
            key="send_button",
            help="Send message",
            disabled=st.session_state.is_generating or not user_input.strip(),
        )

        # Botão de parar (quando gerando)
        if st.session_state.is_generating:
            if st.button("⏹ Stop", key="stop_button", help="Stop generation"):
                st.session_state.is_generating = False
                st.rerun()

    # Processa envio de mensagem
    if send_button and user_input.strip() and not st.session_state.is_generating:
        st.session_state.is_generating = True

        # Adiciona mensagem do usuário
        user_message = {"role": "user", "content": user_input.strip()}
        st.session_state.chat_history.append(user_message)

        # Exibe mensagem do usuário
        display_message("user", user_input.strip())

        # Gera resposta do assistente
        assistant_config = AVAILABLE_ASSISTANTS[st.session_state.current_assistant]

        with st.spinner("🤖 Generating response..."):
            response = stream_assistant_response(
                client,
                user_input.strip(),
                assistant_config["id"],
                st.session_state.thread_id,
            )

        if response:
            # Adiciona resposta do assistente
            assistant_message = {"role": "assistant", "content": response}
            st.session_state.chat_history.append(assistant_message)

            # Salva conversa
            save_conversation()

        st.session_state.is_generating = False

        # Limpa input e rerun
        st.session_state.message_input = ""
        st.rerun()

    # Tecla Enter para enviar (JavaScript)
    st.markdown(
        """
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        const textarea = document.querySelector('textarea[aria-label="Message"]');
        if (textarea) {
            textarea.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    const sendButton = document.querySelector('button[title="Send message"]');
                    if (sendButton) {
                        sendButton.click();
                    }
                }
            });
        }
    });
    </script>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
