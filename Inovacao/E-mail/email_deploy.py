import streamlit as st
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
import base64
import datetime

# --- Escopos Google ---
SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

# --- Carrega config do OAuth via st.secrets ---
# Validação para garantir que os secrets estão carregados e têm a estrutura esperada
if "oauth" not in st.secrets or not all(
    k in st.secrets["oauth"] for k in ["client_id", "client_secret", "redirect_uris"]
):
    st.error("Erro: Configuração OAuth ausente ou incompleta em st.secrets.")
    st.stop()

if (
    not st.secrets["oauth"]["redirect_uris"]
    or not isinstance(st.secrets["oauth"]["redirect_uris"], list)
    or not st.secrets["oauth"]["redirect_uris"][0]
):
    st.error(
        "Erro: 'redirect_uris' ausente, não é uma lista ou está vazia em st.secrets['oauth']."
    )
    st.stop()

CLIENT_CONFIG = {
    "web": {
        "client_id": st.secrets["oauth"]["client_id"],
        "client_secret": st.secrets["oauth"]["client_secret"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": st.secrets["oauth"]["redirect_uris"],  # CORRIGIDO
    }
}
SINGLE_REDIRECT_URI = st.secrets["oauth"]["redirect_uris"][
    0
]  # Usar o primeiro URI da lista


def login():
    # inicializa credenciais na sessão
    creds = st.session_state.get("creds", None)

    # se já temos credenciais e são válidas, retorna
    if creds and creds.valid:
        return creds

    # se expiraram mas têm refresh_token, atualiza
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        st.session_state.creds = creds
        return creds

    # senão, inicia fluxo OAuth
    flow = Flow.from_client_config(CLIENT_CONFIG, scopes=SCOPES)
    flow.redirect_uri = SINGLE_REDIRECT_URI  # CORRIGIDO

    auth_url, _ = flow.authorization_url(prompt="consent")
    # Adiciona um link claro para o usuário clicar
    st.markdown(
        f"### Aviso: \nPara continuar, por favor, [conecte-se com o Google clicando aqui]({auth_url}). \n\nApós autorizar, você será redirecionado de volta para esta página."
    )

    # pega o código da URL
    # Acessando st.query_params diretamente pode ser mais robusto com Streamlit > 1.29
    # Para versões anteriores, st.experimental_get_query_params() pode ser necessário.
    # Vamos usar st.query_params que é a forma mais atual.
    query_params = st.query_params
    if "code" in query_params:
        code = str(query_params["code"])  # Garante que é uma string

        # Limpa os query params para evitar loop ANTES de buscar o token
        # e ANTES do rerun, para que a URL esteja limpa na próxima interação.
        # A forma de limpar pode variar um pouco com a versão do Streamlit
        # st.experimental_set_query_params() # Para versões mais antigas
        # st.query_params.clear() # Pode não ser a forma correta de limpar para redirecionamento
        # A melhor abordagem é redirecionar para a página sem os parâmetros após obter o token.
        # No entanto, para este fluxo, o rerun após salvar as credenciais costuma funcionar.

        try:
            flow.fetch_token(code=code)
            creds = flow.credentials
            st.session_state.creds = creds

            # Limpa os parâmetros da URL após obter o token com sucesso
            # e antes do rerun para evitar que o código seja processado novamente.
            st.query_params.clear()  # Se st.query_params for um objeto mutável tipo dict
            # ou st.experimental_set_query_params() # Se precisar limpar via API específica

            st.rerun()  # Use st.rerun() para versões mais novas do Streamlit

        except Exception as e:
            st.error(f"Erro ao buscar o token: {e}")
            st.stop()

    # Pausa a execução até autenticarem e o código ser recebido
    # Se não houver 'code' nos params, e não houver creds válidas, esta parte é alcançada.
    # O link de autorização já foi mostrado acima.
    if not creds or not creds.valid:  # Adicionado para mais clareza
        st.info("Aguardando autorização do Google...")
        st.stop()

    return creds  # Retorna creds caso tenha passado por aqui com creds já válidas


# --- Serviços autenticados ---
# Coloque esta parte dentro de um if para garantir que creds não é None
creds = login()  # login() agora sempre retorna creds ou para a execução

if creds:
    try:
        cal_service = build("calendar", "v3", credentials=creds)
        gmail_service = build("gmail", "v1", credentials=creds)
        st.success("Conectado aos serviços Google!")  # Feedback opcional
    except Exception as e:
        st.error(f"Erro ao construir serviços Google: {e}")
        st.stop()
else:
    # Esta parte não deveria ser alcançada se login() usa st.stop() corretamente
    st.error("Credenciais não disponíveis após o login.")
    st.stop()


# --- Busca eventos num dia ---
def fetch_events_for_date(date):
    # ... (seu código existente)
    if isinstance(date, datetime.date):
        date = datetime.datetime.combine(date, datetime.time.min)

    start = date.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
    end = (date + datetime.timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    ).isoformat() + "Z"

    try:
        events = (
            cal_service.events()
            .list(
                calendarId="primary",
                timeMin=start,
                timeMax=end,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
            .get("items", [])
        )
        return events
    except HttpError as error:
        st.error(f"Erro ao buscar eventos: {error}")
        return []


# --- Agrupa convidados por evento ---
def group_guests(events):
    # ... (seu código existente)
    grouped = {}
    for ev in events:
        guests = [
            att
            for att in ev.get("attendees", [])
            if not att["email"].endswith("@polijunior.com.br")  # Seu filtro de email
        ]
        if not guests:
            continue
        label = ev["summary"]
        if label not in grouped:
            grouped[label] = {"event": ev, "guests": []}
        for att in guests:
            # Tenta pegar o displayName, se não, o email, e se não, usa o nome do email
            name = att.get("displayName", att.get("email", att["email"].split("@")[0]))
            grouped[label]["guests"].append((att["email"], name))
    return grouped


# --- Interface ---
st.title("🔔 Confirmação de Reuniões")

# escolha da data
mode = st.radio("Data:", ["Hoje", "Amanhã", "Escolher"])
if mode == "Hoje":
    sel_date = datetime.datetime.now()
elif mode == "Amanhã":
    sel_date = datetime.datetime.now() + datetime.timedelta(days=1)
else:
    sel_date = st.date_input("Escolha a data", datetime.date.today())

events = fetch_events_for_date(sel_date)
grouped = group_guests(events)

if not grouped:
    st.warning(
        "Não há eventos para a data selecionada com convidados externos."
    )  # Mensagem mais clara
    st.stop()

# seleção de evento
event_label = st.selectbox("Evento:", list(grouped.keys()))
if not event_label:  # Caso não haja eventos após o filtro
    st.warning("Nenhum evento selecionável.")
    st.stop()

data = grouped[event_label]
ev = data["event"]
guest_list = data["guests"]

# seleção de convidados
names = [g[1] for g in guest_list]
chosen = st.multiselect("Convidados:", names)

if not chosen:
    st.info("Selecione ao menos um convidado.")
    st.stop()

# prepara saudação
selected = [g for g in guest_list if g[1] in chosen]
emails = [g[0] for g in selected]
names_sel = [g[1] for g in selected]

# Lógica de saudação aprimorada
if len(names_sel) == 1:
    first_name = emails[0].split("@")[0].split(".")[0].capitalize()
    greet = f"Bom dia, {first_name}!"
elif len(names_sel) == 2:
    first_names = [email.split("@")[0].split(".")[0].capitalize() for email in emails]
    greet = f"Bom dia, {first_names[0]} e {first_names[1]}!"
elif len(names_sel) > 2:
    first_names = [email.split("@")[0].split(".")[0].capitalize() for email in emails]
    greet = f"Bom dia, {', '.join(first_names[:-1])} e {first_names[-1]}!"
else:  # Caso names_sel esteja vazio por algum motivo (não deveria acontecer se 'chosen' não estiver vazio)
    greet = "Bom dia!"

# formata horário
start_info = ev["start"]
# Verifica se é um evento de dia inteiro ('date') ou com horário específico ('dateTime')
if "dateTime" in start_info:
    start_dt_str = start_info.get("dateTime")
    time_h = datetime.datetime.fromisoformat(
        start_dt_str.replace("Z", "+00:00")
    ).strftime(
        "%Hh%M"
    )  # Adiciona minutos e trata fuso horário
    horario_confirmacao = f"às {time_h}"
elif "date" in start_info:
    start_dt_str = start_info.get("date")
    time_h = datetime.datetime.fromisoformat(start_dt_str).strftime(
        "%d/%m/%Y"
    )  # Formata a data
    horario_confirmacao = f"no dia {time_h}"
else:
    time_h = "(horário não especificado)"  # Fallback
    horario_confirmacao = ""


# mensagem padrão com preview de {time_h}
default = (
    f"{greet}\nTudo bem?\n\n"
    f"Gostaria de confirmar, tudo certo para nossa conversa hoje {horario_confirmacao}?\n\n"
    "Nos vemos em breve!\nAtt,"
)
msg = st.text_area("Mensagem:", default, height=200)

if st.button("Enviar"):
    if not msg.strip():  # Verifica se a mensagem não está vazia
        st.warning("A mensagem não pode estar vazia.")
    else:
        sent = 0  # Esta variável não está sendo usada, pode ser removida se não houver contagem
        mime = MIMEText(msg)
        mime["to"] = ", ".join(emails)
        mime["subject"] = f"Confirmação: {event_label}"
        raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()

        try:
            gmail_service.users().messages().send(
                userId="me", body={"raw": raw}
            ).execute()
            st.success("E-mail enviado com sucesso!")
        except HttpError as e:
            st.error(f"Erro ao enviar: {e}")
        except Exception as e_gen:  # Captura outros erros potenciais
            st.error(f"Um erro inesperado ocorreu ao enviar: {e_gen}")
