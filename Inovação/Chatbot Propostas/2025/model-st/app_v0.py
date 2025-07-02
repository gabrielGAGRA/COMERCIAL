# app.py

import streamlit as st
import openai
import time
import json
from pathlib import Path

# --- CONFIGURAÇÃO E INICIALIZAÇÃO ---
# Equivalente ao seu 'config.py'
AVAILABLE_ASSISTANTS = {
    "organizador_atas": {
        "id": "asst_gl4svzGMPxoDMYskRHzK62Fk",
        "name": "Organizador de Atas",
        "description": "Especialista em organizar e estruturar atas de reunião",
        "welcome_message": "Como posso ajudar a organizar sua ata hoje?",
    },
    "criador_propostas": {
        "id": "asst_gqDpEGoOpRvpUai7fdVxgg4d",
        "name": "Criador de Propostas Comerciais",
        "description": "Especialista em criar propostas comerciais persuasivas",
        "welcome_message": "Pronto para criar uma proposta comercial de impacto?",
    },
}
DEFAULT_ASSISTANT = "organizador_atas"

AVAILABLE_MODELS = {
    "gpt-4o": "GPT-4o",
    "gpt-4o-mini": "GPT-4o Mini",
}
DEFAULT_MODEL = "gpt-4o"

# Configuração da página
st.set_page_config(
    page_title="ChatGPT Interface",
    page_icon="assets/img/favicon-32x32.png",
    layout="wide",
)


# --- ESTILOS CUSTOMIZADOS ---
# Injeta o CSS do 'modern-style.css' adaptado para o Streamlit
def load_css():
    css_file = Path(__file__).parent / "assets/css/modern-style.css"
    if css_file.exists():
        with open(css_file) as f:
            # Adaptações de CSS para classes geradas pelo Streamlit
            st.markdown(
                f"""
            <style>
                /* Importa o CSS base */
                {f.read()}

                /* Ajustes específicos para o Streamlit */
                .st-emotion-cache-1c7y2kd {{
                    flex-direction: row-reverse;
                    text-align: right;
                }}
                .st-emotion-cache-1v0mbdj {{
                    padding-top: 2rem;
                }}
                .st-emotion-cache-janbn0 {{
                    padding-top: 2rem;
                }}
                .stChatMessage {{
                    border-radius: var(--border-radius);
                    padding: 0.8rem 1rem;
                    background-color: var(--secondary-color);
                    border: 1px solid var(--border-color);
                }}
                .stChatMessage [data-testid="chatAvatarIcon-user"], .stChatMessage [data-testid="chatAvatarIcon-assistant"] {{
                   background-size: cover;
                   width: 32px;
                   height: 32px;
                }}
                .stChatMessage [data-testid="chatAvatarIcon-user"] {{
                    background-image: url('app/static/assets/img/user.png');
                }}
                .stChatMessage [data-testid="chatAvatarIcon-assistant"] {{
                    background-image: url('app/static/assets/img/gpt.png');
                }}
                .st-emotion-cache-4oy321 {{
                    width: 100%;
                }}
            </style>
            """,
                unsafe_allow_html=True,
            )


load_css()


# --- FUNÇÕES DE LÓGICA (BACKEND) ---

# Inicializa o cliente OpenAI
try:
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error(
        "Chave da API da OpenAI não encontrada. Configure-a em .streamlit/secrets.toml"
    )
    st.stop()


def initialize_session_state():
    """Inicializa o estado da sessão se não existir."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = None
    if "current_assistant_key" not in st.session_state:
        st.session_state.current_assistant_key = DEFAULT_ASSISTANT
    if "current_model" not in st.session_state:
        st.session_state.current_model = DEFAULT_MODEL


def start_new_chat():
    """Reseta o estado da sessão para iniciar uma nova conversa."""
    st.session_state.messages = []

    # Cria uma nova thread na API da OpenAI
    try:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
    except Exception as e:
        st.error(f"Não foi possível criar uma nova thread na OpenAI: {e}")
        st.session_state.thread_id = None

    st.rerun()


def stream_assistant_response(thread_id, run_id):
    """Monitora o 'run' da OpenAI e transmite a resposta."""
    max_polling_time = 300  # 5 minutos
    polling_start = time.time()

    # Espera o 'run' ser completado
    while time.time() - polling_start < max_polling_time:
        try:
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            if run.status == "completed":
                break
            elif run.status in ["failed", "cancelled", "expired"]:
                error_message = (
                    f"O 'run' do assistente falhou com o status: {run.status}"
                )
                if run.last_error:
                    error_message += f" - {run.last_error.message}"
                st.error(error_message)
                return
            time.sleep(1)  # Aguarda antes de verificar novamente
        except Exception as e:
            st.error(f"Erro ao verificar o status do 'run': {e}")
            return

    if run.status != "completed":
        st.warning("O assistente demorou muito para responder. Tente novamente.")
        return

    # Recupera as mensagens da thread
    try:
        messages = client.beta.threads.messages.list(
            thread_id=thread_id, order="desc", limit=1
        )
        if messages.data and messages.data[0].role == "assistant":
            message_content = messages.data[0].content[0].text.value

            # Simula o streaming palavra por palavra
            response_words = message_content.split(" ")
            full_response = ""
            placeholder = st.empty()
            for word in response_words:
                full_response += word + " "
                placeholder.markdown(full_response + "▌")
                time.sleep(0.03)
            placeholder.markdown(full_response)

            # Adiciona a resposta completa ao histórico
            st.session_state.messages.append(
                {"role": "assistant", "content": message_content}
            )

    except Exception as e:
        st.error(f"Erro ao recuperar a resposta do assistente: {e}")


# --- INTERFACE (SIDEBAR) ---
with st.sidebar:
    st.markdown(
        """
    <header class="sidebar-header">
        <button class="new-chat-btn" id="new-chat-btn">
            <span class="icon">+</span>
            <span class="text">New Chat</span>
        </button>
    </header>
    """,
        unsafe_allow_html=True,
    )

    if st.button("New Chat", use_container_width=True):
        start_new_chat()

    st.markdown(
        '<div class="conversations-list" id="conversations-list"></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<footer class="sidebar-footer">', unsafe_allow_html=True)
    st.markdown('<div class="settings-panel">', unsafe_allow_html=True)

    # Seletor de Assistente
    st.markdown('<div class="setting-group">', unsafe_allow_html=True)
    assistant_names = {key: data["name"] for key, data in AVAILABLE_ASSISTANTS.items()}
    selected_assistant_name = st.selectbox(
        label="Assistente:",
        options=assistant_names.values(),
        index=list(assistant_names.keys()).index(
            st.session_state.get("current_assistant_key", DEFAULT_ASSISTANT)
        ),
        key="selected_assistant_name",
    )
    # Mapeia o nome de volta para a chave
    current_assistant_key = next(
        key for key, name in assistant_names.items() if name == selected_assistant_name
    )

    if st.session_state.get("current_assistant_key") != current_assistant_key:
        st.session_state.current_assistant_key = current_assistant_key
        start_new_chat()  # Inicia novo chat ao trocar de assistente

    assistant_description = AVAILABLE_ASSISTANTS[current_assistant_key]["description"]
    st.markdown(
        f'<small class="assistant-description">{assistant_description}</small>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # Seletor de Modelo
    st.markdown('<div class="setting-group">', unsafe_allow_html=True)
    st.selectbox(
        label="Modelo:",
        options=AVAILABLE_MODELS.keys(),
        format_func=lambda key: AVAILABLE_MODELS[key],
        key="current_model",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # Informações do App
    st.markdown(
        '<div class="app-info"><small>ChatGPT Interface v2.0 (Streamlit)</small></div>',
        unsafe_allow_html=True,
    )
    st.markdown("</div></footer>", unsafe_allow_html=True)


# --- INTERFACE PRINCIPAL (CHAT) ---

# Inicializa a sessão
initialize_session_state()

# Cabeçalho do Chat
st.markdown(
    f"""
<div class="chat-header">
    <div class="chat-title">
        <h1>ChatGPT</h1>
        <span class="current-assistant">{AVAILABLE_ASSISTANTS[st.session_state.current_assistant_key]['name']}</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# Mensagem de boas-vindas
if not st.session_state.messages:
    welcome_message = AVAILABLE_ASSISTANTS[st.session_state.current_assistant_key][
        "welcome_message"
    ]
    st.markdown(
        f"""
    <div class="welcome-message">
        <h2>Bem-vindo à Interface ChatGPT</h2>
        <p>{welcome_message}</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

# Exibição do Histórico de Mensagens
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=f"assets/img/{message['role']}.png"):
        st.markdown(message["content"])

# Input do Usuário
if prompt := st.chat_input("Digite sua mensagem aqui..."):
    # Garante que temos uma thread
    if not st.session_state.thread_id:
        try:
            thread = client.beta.threads.create()
            st.session_state.thread_id = thread.id
        except Exception as e:
            st.error(f"Falha ao criar thread da OpenAI: {e}")
            st.stop()

    # Adiciona a mensagem do usuário ao histórico e exibe
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="assets/img/user.png"):
        st.markdown(prompt)

    # Envia a mensagem para a API da OpenAI
    try:
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id, role="user", content=prompt
        )

        # Cria e executa o 'run' do assistente
        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=AVAILABLE_ASSISTANTS[st.session_state.current_assistant_key][
                "id"
            ],
            # O modelo é definido no próprio assistente na plataforma da OpenAI
        )

        # Exibe a resposta com streaming
        with st.chat_message("assistant", avatar="assets/img/gpt.png"):
            with st.spinner("Pensando..."):
                stream_assistant_response(st.session_state.thread_id, run.id)

    except Exception as e:
        st.error(f"Ocorreu um erro ao se comunicar com a OpenAI: {e}")
