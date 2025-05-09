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
CLIENT_CONFIG = {
    "web": {
        "client_id": st.secrets["oauth"]["client_id"],
        "client_secret": st.secrets["oauth"]["client_secret"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [st.secrets["oauth"]["redirect_uris"]],
    }
}
REDIRECT_URIS = st.secrets["oauth"]["redirect_uris"]


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
    flow.redirect_uris = REDIRECT_URIS

    auth_url, _ = flow.authorization_url(prompt="consent")
    st.markdown(f"[Conecte-se com o Google]({auth_url})")

    # pega o código da URL
    params = st.query_params
    if "code" in params:
        code = params["code"][0]
        flow.fetch_token(code=code)
        creds = flow.credentials
        st.session_state.creds = creds
        # limpa os query params para evitar loop
        st.experimental_set_query_params()
        st.experimental_rerun()

    # pausa a execução até autenticarem
    st.stop()


# --- Serviços autenticados ---
creds = login()
cal_service = build("calendar", "v3", credentials=creds)
gmail_service = build("gmail", "v1", credentials=creds)


# --- Busca eventos num dia ---
def fetch_events_for_date(date):
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
    grouped = {}
    for ev in events:
        guests = [
            att
            for att in ev.get("attendees", [])
            if not att["email"].endswith("@polijunior.com.br")
        ]
        if not guests:
            continue
        label = ev["summary"]
        if label not in grouped:
            grouped[label] = {"event": ev, "guests": []}
        for att in guests:
            name = att["email"].split("@")[0]
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
    st.warning("Não há eventos para a data selecionada.")
    st.stop()

# seleção de evento
event_label = st.selectbox("Evento:", list(grouped.keys()))
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

if len(names_sel) == 1:
    greet = f"Bom dia, {names_sel[0]}!"
elif len(names_sel) == 2:
    greet = f"Bom dia, {names_sel[0]} e {names_sel[1]}!"
else:
    greet = f"Bom dia, {names_sel[0]}, {names_sel[1]} e {names_sel[2]}!"

# formata horário
start_dt = ev["start"].get("dateTime", ev["start"].get("date"))
time_h = datetime.datetime.fromisoformat(start_dt).strftime("%Hh")

# mensagem padrão com preview de {time_h}
default = (
    f"{greet}\nTudo bem?\n\n"
    f"Gostaria de confirmar, tudo certo para nossa conversa hoje às {time_h}?\n\n"
    "Nos vemos em breve!\nAtt,"
)
msg = st.text_area("Mensagem:", default, height=200)

if st.button("Enviar"):
    sent = 0
    mime = MIMEText(msg)
    mime["to"] = ", ".join(emails)
    mime["subject"] = f"Confirmação: {event_label}"
    raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()

    try:
        gmail_service.users().messages().send(userId="me", body={"raw": raw}).execute()
        st.success("E-mail enviado com sucesso!")
    except HttpError as e:
        st.error(f"Erro ao enviar: {e}")
