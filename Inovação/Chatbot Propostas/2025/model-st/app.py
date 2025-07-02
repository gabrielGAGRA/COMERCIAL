# streamlit_app.py

import streamlit as st
import openai
import time
import os
from typing import Dict, List
from pydantic import BaseModel

# --- Modelos de Configuração (de config.py) ---


class AssistantConfig(BaseModel):
    id: str
    name: str
    description: str


AVAILABLE_ASSISTANTS: Dict[str, AssistantConfig] = {
    "organizador_atas": AssistantConfig(
        id="asst_gl4svzGMPxoDMYskRHzK62Fk",
        name="Organizador de Atas",
        description="Especialista em organizar e estruturar atas de reunião",
    ),
    "criador_propostas": AssistantConfig(
        id="asst_gqDpEGoOpRvpUai7fdVxgg4d",
        name="Criador de Propostas Comerciais",
        description="Especialista em criar propostas comerciais persuasivas",
    ),
}

DEFAULT_ASSISTANT = "organizador_atas"

# --- Configuração da Página e Estilos ---


# Carrega o CSS customizado para um visual mais próximo do original
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# Define a configuração da página
st.set_page_config(
    page_title="ChatGPT Interface",
    page_icon="assets/img/favicon-32x32.png",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Aplica o CSS customizado
load_css("assets/css/style.css")

# --- Lógica de Backend (Integrada do backend.py) ---

try:
    # Inicializa o cliente OpenAI usando as secrets do Streamlit
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error(
        "Chave da API da OpenAI não encontrada. Por favor, configure seus secrets no Streamlit Cloud.",
        icon="🚨",
    )
    st.stop()


# --- Classe para Streaming de Resposta (Melhoria do backend.py) ---
# Usa o EventHandler para um streaming real e eficiente
from openai import AssistantEventHandler


class StreamingEventHandler(AssistantEventHandler):
    def __init__(self, text_placeholder):
        super().__init__()
        self.text_placeholder = text_placeholder
        self.full_response = ""

    def on_text_delta(self, delta, snapshot):
        # Adiciona o novo trecho de texto ao placeholder e atualiza o conteúdo
        self.full_response += delta.value
        self.text_placeholder.markdown(self.full_response + "▌")

    def on_end(self):
        # Exibe a resposta final sem o cursor
        self.text_placeholder.markdown(self.full_response)

    def get_full_response(self):
        return self.full_response


# --- Inicialização do Estado da Sessão ---
# O st.session_state é o equivalente do Streamlit ao localStorage ou variáveis de classe do JS

if "session_id" not in st.session_state:
    st.session_state.session_id = (
        f"session_{int(time.time())}"  # ID único para a sessão
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

if "assistant_key" not in st.session_state:
    st.session_state.assistant_key = DEFAULT_ASSISTANT


# --- Interface da Sidebar (de index.html) ---
with st.sidebar:
    st.title("ChatGPT Interface")

    if st.button("＋ Nova Conversa", use_container_width=True):
        # Reseta o estado da conversa para iniciar um novo chat
        st.session_state.messages = []
        st.session_state.thread_id = None
        st.rerun()

    st.header("Configurações")

    # Seletor de Assistente
    assistant_options = {
        key: assistant.name for key, assistant in AVAILABLE_ASSISTANTS.items()
    }

    selected_assistant_key = st.selectbox(
        label="Assistente:",
        options=assistant_options.keys(),
        format_func=lambda key: assistant_options[key],
        key="selected_assistant",
    )

    # Lógica para confirmar mudança de assistente no meio da conversa
    if selected_assistant_key != st.session_state.assistant_key:
        if st.session_state.messages:  # Se já houver mensagens
            st.warning("Mudar de assistente irá iniciar uma nova conversa.", icon="⚠️")
            if st.button("Confirmar e iniciar nova conversa", use_container_width=True):
                st.session_state.assistant_key = selected_assistant_key
                st.session_state.messages = []
                st.session_state.thread_id = None
                st.rerun()
            else:
                # Reverte a seleção se o usuário não confirmar
                st.session_state.selected_assistant = st.session_state.assistant_key
        else:
            # Se não houver mensagens, apenas muda o assistente
            st.session_state.assistant_key = selected_assistant_key
            st.rerun()

    # Exibe a descrição do assistente selecionado
    assistant_info = AVAILABLE_ASSISTANTS[st.session_state.assistant_key]
    st.markdown(
        f"<small>*{assistant_info.description}*</small>", unsafe_allow_html=True
    )

    st.markdown("---")
    st.info(
        "O tema (Claro/Escuro) pode ser alterado no menu 'Settings' do próprio Streamlit (canto superior direito).",
        icon="🎨",
    )
    st.markdown(
        "<small>ChatGPT Interface v2.0 (Streamlit Edition)</small>",
        unsafe_allow_html=True,
    )


# --- Interface Principal do Chat ---

# Header do Chat
st.markdown(f"### {assistant_info.name}")

# Exibe mensagens do histórico
if not st.session_state.messages:
    st.info(f"Como posso te ajudar hoje como {assistant_info.name}?", icon="👋")

for msg in st.session_state.messages:
    # Usa avatares customizados para replicar o visual
    avatar_img = (
        "assets/img/user.png" if msg["role"] == "user" else "assets/img/gpt.png"
    )
    with st.chat_message(msg["role"], avatar=avatar_img):
        st.markdown(msg["content"])


# Input do usuário (substitui o <textarea> e <button>)
if prompt := st.chat_input("Digite sua mensagem aqui..."):
    # Adiciona e exibe a mensagem do usuário
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="assets/img/user.png"):
        st.markdown(prompt)

    # Prepara para receber a resposta do assistente
    with st.chat_message("assistant", avatar="assets/img/gpt.png"):
        # Se não houver um thread, cria um novo
        if not st.session_state.thread_id:
            try:
                thread = client.beta.threads.create()
                st.session_state.thread_id = thread.id
            except Exception as e:
                st.error(f"Erro ao criar a thread: {e}", icon="🚨")
                st.stop()

        # Adiciona a mensagem do usuário à thread
        try:
            client.beta.threads.messages.create(
                thread_id=st.session_state.thread_id, role="user", content=prompt
            )

            # Cria o placeholder para a resposta em streaming
            response_placeholder = st.empty()

            # Inicializa o handler de streaming
            handler = StreamingEventHandler(response_placeholder)

            # Cria e faz o streaming da run
            with client.beta.threads.runs.stream(
                thread_id=st.session_state.thread_id,
                assistant_id=assistant_info.id,
                event_handler=handler,
            ) as stream:
                # O stream é processado pelo handler em tempo real
                stream.until_done()

            # Adiciona a resposta completa do assistente ao histórico
            assistant_response = handler.get_full_response()
            st.session_state.messages.append(
                {"role": "assistant", "content": assistant_response}
            )

        except Exception as e:
            st.error(
                f"Ocorreu um erro ao se comunicar com a API da OpenAI: {e}", icon="🚨"
            )
            # Remove a última mensagem do usuário para que ele possa tentar novamente
            st.session_state.messages.pop()
