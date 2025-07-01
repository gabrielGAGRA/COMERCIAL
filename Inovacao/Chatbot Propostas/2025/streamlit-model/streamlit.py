import streamlit as st
import openai
from openai import OpenAI
import os
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import uuid

# Configure page
st.set_page_config(
    page_title="ChatGPT Interface - Assistants",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown(
    """
<style>
    .main {
        padding-top: 2rem;
    }
    
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .assistant-selector {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .chat-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .assistant-info {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 0.5rem 0.5rem 0;
    }
    
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Configuration
AVAILABLE_ASSISTANTS = {
    "organizador_atas": {
        "id": "asst_gl4svzGMPxoDMYskRHzK62Fk",
        "name": "Organizador de Atas",
        "description": "Especialista em organizar e estruturar atas de reunião",
        "emoji": "📋",
    },
    "criador_propostas": {
        "id": "asst_gqDpEGoOpRvpUai7fdVxgg4d",
        "name": "Criador de Propostas Comerciais",
        "description": "Especialista em criar propostas comerciais persuasivas",
        "emoji": "💼",
    },
}

DEFAULT_ASSISTANT = "organizador_atas"


class StreamlitChatInterface:
    def __init__(self):
        self.init_session_state()
        self.setup_openai_client()

    def init_session_state(self):
        """Initialize session state variables"""
        if "messages" not in st.session_state:
            st.session_state.messages = []

        if "current_assistant" not in st.session_state:
            st.session_state.current_assistant = DEFAULT_ASSISTANT

        if "thread_id" not in st.session_state:
            st.session_state.thread_id = None

        if "chat_id" not in st.session_state:
            st.session_state.chat_id = str(uuid.uuid4())

        if "api_key_valid" not in st.session_state:
            st.session_state.api_key_valid = False

    def setup_openai_client(self):
        """Setup OpenAI client with API key"""
        try:
            # Try to get API key from Streamlit secrets first, then environment
            api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))

            if not api_key:
                st.session_state.api_key_valid = False
                return None

            self.client = OpenAI(api_key=api_key)

            # Test the connection
            self.client.beta.assistants.list(limit=1)
            st.session_state.api_key_valid = True

            return self.client

        except Exception as e:
            st.session_state.api_key_valid = False
            st.error(f"Erro ao configurar OpenAI: {str(e)}")
            return None

    def render_header(self):
        """Render the chat header"""
        current_assistant = AVAILABLE_ASSISTANTS[st.session_state.current_assistant]

        st.markdown(
            f"""
        <div class="chat-header">
            <h1>{current_assistant['emoji']} ChatGPT Interface - Assistants</h1>
            <p>Conversando com: <strong>{current_assistant['name']}</strong></p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    def render_sidebar(self):
        """Render the sidebar with controls"""
        with st.sidebar:
            st.title("🛠️ Configurações")

            # Assistant selector
            st.subheader("👤 Assistente")

            assistant_options = {
                key: f"{data['emoji']} {data['name']}"
                for key, data in AVAILABLE_ASSISTANTS.items()
            }

            new_assistant = st.selectbox(
                "Escolha o assistente:",
                options=list(assistant_options.keys()),
                format_func=lambda x: assistant_options[x],
                index=list(assistant_options.keys()).index(
                    st.session_state.current_assistant
                ),
                key="assistant_selector",
            )

            # Check if assistant changed
            if new_assistant != st.session_state.current_assistant:
                if st.session_state.messages:
                    if st.button("🔄 Confirmar Troca de Assistente", type="primary"):
                        self.change_assistant(new_assistant)
                else:
                    self.change_assistant(new_assistant)

            # Show current assistant info
            current_assistant = AVAILABLE_ASSISTANTS[st.session_state.current_assistant]
            st.markdown(
                f"""
            <div class="assistant-info">
                <strong>{current_assistant['emoji']} {current_assistant['name']}</strong><br>
                <small>{current_assistant['description']}</small>
            </div>
            """,
                unsafe_allow_html=True,
            )

            st.divider()

            # Chat controls
            st.subheader("💬 Controles do Chat")

            if st.button("🆕 Nova Conversa", type="secondary"):
                self.start_new_conversation()

            if st.button("🗑️ Limpar Histórico", type="secondary"):
                self.clear_history()

            st.divider()

            # Model info (for display only)
            st.subheader("🧠 Informações do Modelo")
            st.info(
                "Usando OpenAI Assistants API com modelos otimizados para cada tarefa específica."
            )

            st.divider()

            # Session info
            st.subheader("📊 Informações da Sessão")
            st.write(f"**Mensagens:** {len(st.session_state.messages)}")
            st.write(f"**Chat ID:** `{st.session_state.chat_id[:8]}...`")
            if st.session_state.thread_id:
                st.write(f"**Thread ID:** `{st.session_state.thread_id[:8]}...`")

            # API Status
            if st.session_state.api_key_valid:
                st.success("✅ OpenAI API conectada")
            else:
                st.error("❌ OpenAI API não configurada")

    def change_assistant(self, new_assistant: str):
        """Change the current assistant"""
        if st.session_state.messages:
            st.warning("⚠️ Trocar de assistente iniciará uma nova conversa!")

        st.session_state.current_assistant = new_assistant
        st.session_state.thread_id = None  # Reset thread
        st.rerun()

    def start_new_conversation(self):
        """Start a new conversation"""
        st.session_state.messages = []
        st.session_state.thread_id = None
        st.session_state.chat_id = str(uuid.uuid4())
        st.rerun()

    def clear_history(self):
        """Clear conversation history"""
        st.session_state.messages = []
        st.rerun()

    def render_chat_messages(self):
        """Render all chat messages"""
        if not st.session_state.messages:
            current_assistant = AVAILABLE_ASSISTANTS[st.session_state.current_assistant]
            st.markdown(
                f"""
            <div class="assistant-info">
                <h3>👋 Olá! Eu sou o {current_assistant['name']}</h3>
                <p>{current_assistant['description']}</p>
                <p>Como posso ajudá-lo hoje?</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    def generate_assistant_response(self, user_message: str) -> str:
        """Generate response using OpenAI Assistant"""
        try:
            assistant_config = AVAILABLE_ASSISTANTS[st.session_state.current_assistant]

            # Create or use existing thread
            if not st.session_state.thread_id:
                thread = self.client.beta.threads.create()
                st.session_state.thread_id = thread.id

                # Add conversation history to thread if exists
                for msg in st.session_state.messages[-10:]:  # Last 10 messages
                    if msg["role"] in ["user", "assistant"]:
                        self.client.beta.threads.messages.create(
                            thread_id=st.session_state.thread_id,
                            role=msg["role"],
                            content=msg["content"],
                        )

            # Add current user message to thread
            self.client.beta.threads.messages.create(
                thread_id=st.session_state.thread_id, role="user", content=user_message
            )

            # Create and run assistant
            run = self.client.beta.threads.runs.create(
                thread_id=st.session_state.thread_id,
                assistant_id=assistant_config["id"],
            )

            # Poll for completion with progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()

            max_polling_time = 300  # 5 minutes
            polling_start = time.time()
            poll_count = 0

            while True:
                # Check timeout
                elapsed_time = time.time() - polling_start
                if elapsed_time > max_polling_time:
                    st.error("⏰ Timeout: Assistant response took too long")
                    return "Desculpe, a resposta demorou muito para ser gerada. Tente novamente."

                # Update progress
                progress = min(
                    elapsed_time / 30, 1.0
                )  # Show progress for first 30 seconds
                progress_bar.progress(progress)
                status_text.text(f"🤖 Gerando resposta... ({elapsed_time:.1f}s)")

                # Get run status
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=st.session_state.thread_id, run_id=run.id
                )

                if run.status == "completed":
                    # Get the latest assistant message
                    messages = self.client.beta.threads.messages.list(
                        thread_id=st.session_state.thread_id, order="desc", limit=1
                    )

                    if messages.data and messages.data[0].role == "assistant":
                        message = messages.data[0]
                        if message.content and message.content[0].type == "text":
                            progress_bar.empty()
                            status_text.empty()
                            return message.content[0].text.value

                    progress_bar.empty()
                    status_text.empty()
                    return "Desculpe, não consegui gerar uma resposta."

                elif run.status == "failed":
                    error_msg = (
                        run.last_error.message
                        if run.last_error
                        else "Erro desconhecido"
                    )
                    progress_bar.empty()
                    status_text.empty()
                    st.error(f"❌ Erro na execução do assistant: {error_msg}")
                    return f"Erro: {error_msg}"

                elif run.status in ["cancelled", "expired"]:
                    progress_bar.empty()
                    status_text.empty()
                    st.warning(f"⚠️ Execução do assistant foi {run.status}")
                    return f"Execução {run.status}. Tente novamente."

                elif run.status == "requires_action":
                    progress_bar.empty()
                    status_text.empty()
                    st.warning("⚠️ Assistant requer ação (não suportado)")
                    return "Assistant requer ação que não é suportada no momento."

                else:
                    # Still running, wait a bit
                    time.sleep(1)
                    poll_count += 1

        except Exception as e:
            st.error(f"❌ Erro ao gerar resposta: {str(e)}")
            return f"Desculpe, ocorreu um erro: {str(e)}"

    def handle_user_input(self):
        """Handle user input and generate response"""
        if prompt := st.chat_input("Digite sua mensagem aqui..."):
            # Check if API is configured
            if not st.session_state.api_key_valid:
                st.error(
                    "❌ OpenAI API não está configurada. Configure a chave da API."
                )
                return

            # Add user message to chat
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate and display assistant response
            with st.chat_message("assistant"):
                with st.spinner("Pensando..."):
                    response = self.generate_assistant_response(prompt)
                st.markdown(response)

            # Add assistant response to chat
            st.session_state.messages.append({"role": "assistant", "content": response})

    def render_api_key_setup(self):
        """Render API key setup if not configured"""
        if not st.session_state.api_key_valid:
            st.markdown(
                """
            <div class="warning-box">
                <h3>⚠️ Configuração Necessária</h3>
                <p>Para usar esta aplicação, você precisa configurar sua chave da OpenAI API.</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            st.subheader("🔧 Como Configurar")

            with st.expander("📝 Instruções para Deploy no Streamlit Cloud"):
                st.markdown(
                    """
                1. **Obtenha sua chave da OpenAI:**
                   - Acesse [OpenAI Platform](https://platform.openai.com/api-keys)
                   - Crie uma nova chave da API
                
                2. **Configure no Streamlit Cloud:**
                   - Vá para as configurações do seu app no Streamlit Cloud
                   - Na seção "Secrets", adicione:
                   ```toml
                   OPENAI_API_KEY = "sua-chave-aqui"
                   ```
                
                3. **Para desenvolvimento local:**
                   - Crie um arquivo `.streamlit/secrets.toml`
                   - Adicione sua chave:
                   ```toml
                   OPENAI_API_KEY = "sua-chave-aqui"
                   ```
                """
                )

            with st.expander("🤖 Como Obter IDs dos Assistants"):
                st.markdown(
                    """
                1. Acesse [OpenAI Platform - Assistants](https://platform.openai.com/assistants)
                2. Crie ou selecione um assistant
                3. O ID aparece no formato: `asst_xxxxxxxxxxxxxxxxxxxxx`
                4. Atualize os IDs no código se necessário
                """
                )

            # Manual API key input for testing
            st.subheader("🧪 Teste com Chave Temporária")
            temp_key = st.text_input(
                "Cole sua chave da OpenAI aqui (apenas para teste):", type="password"
            )

            if temp_key and st.button("🔄 Testar Conexão"):
                try:
                    test_client = OpenAI(api_key=temp_key)
                    test_client.beta.assistants.list(limit=1)
                    st.success("✅ Chave válida! A aplicação será recarregada.")

                    # Temporarily store in session state
                    os.environ["OPENAI_API_KEY"] = temp_key
                    st.session_state.api_key_valid = True
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Erro na chave: {str(e)}")

    def run(self):
        """Main application runner"""
        self.render_header()
        self.render_sidebar()

        if not st.session_state.api_key_valid:
            self.render_api_key_setup()
        else:
            self.render_chat_messages()
            self.handle_user_input()


# Run the application
if __name__ == "__main__":
    app = StreamlitChatInterface()
    app.run()
