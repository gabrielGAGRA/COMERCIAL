import streamlit as st
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from email.mime.text import MIMEText
import base64
import os
import pickle
import datetime

# --- Configurações via Streamlit secrets ---
SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]
CREDENTIALS_PICKLE = "token.pkl"

# --- OAuth login ---
def login():
    creds = None

    if os.path.exists(CREDENTIALS_PICKLE):
        with open(CREDENTIALS_PICKLE, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Cria o flow diretamente com as configurações do secrets.toml
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": st.secrets["web"]["client_id"],
                        "client_secret": st.secrets["web"]["client_secret"],
                        "auth_uri": st.secrets["web"]["auth_uri"],
                        "token_uri": st.secrets["web"]["token_uri"],
                        "auth_provider_x509_cert_url": st.secrets["web"]["auth_provider_x509_cert_url"],
                        "redirect_uris": st.secrets["web"]["redirect_uris"],
                    }
                },
                scopes=SCOPES,
            )

            # Usa a primeira redirect URI do secrets
            flow.redirect_uri = st.secrets["web"]["redirect_uris"][0]

            auth_url, _ = flow.authorization_url(prompt="consent")
            st.markdown(f"[Clique aqui para se conectar com o Google]({auth_url})")
            query_params = st.query_params

            if "code" in query_params:
                flow.fetch_token(code=query_params["code"][0])
                creds = flow.credentials
                with open(CREDENTIALS_PICKLE, "wb") as token:
                    pickle.dump(creds, token)
                st.experimental_rerun()
            st.stop()

    return creds

# --- Autentica e inicializa serviços ---
creds = login()
cal_service = build("calendar", "v3", credentials=creds)
gmail_service = build("gmail", "v1", credentials=creds)

# --- Fetch events for selected date ---
def fetch_events_for_date(date):
    if isinstance(date, datetime.date):
        date = datetime.datetime.combine(date, datetime.time.min)

    start = date.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
    end = (date + datetime.timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    ).isoformat() + "Z"
    try:
        events_result = (
            cal_service.events()
            .list(
                calendarId="primary",
                timeMin=start,
                timeMax=end,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return events_result.get("items", [])
    except HttpError as error:
        st.error(f"Erro ao buscar eventos: {error}")
        return []

# --- Agrupar eventos e convidados ---
def group_guests(events):
    grouped_events = {}

    for ev in events:
        guests = [
            att
            for att in ev.get("attendees", [])
            if not att["email"].endswith("@polijunior.com.br")
        ]
        if guests:
            event_label = ev['summary']
            if event_label not in grouped_events:
                grouped_events[event_label] = []

            for guest in guests:
                guest_name = guest["email"].split('@')[0]
                grouped_events[event_label].append((guest["email"], guest_name))
    
    return grouped_events

# --- Interface Streamlit ---
st.title("Confirmação de Reuniões")
# Seleção da data
date_option = st.radio("Escolha a data:", ["Hoje", "Amanhã", "Escolher Data"])
if date_option == "Hoje":
    selected_date = datetime.datetime.now()
elif date_option == "Amanhã":
    selected_date = datetime.datetime.now() + datetime.timedelta(days=1)
else:
    selected_date = st.date_input("Escolha a data para enviar os e-mails", datetime.date.today())

events = fetch_events_for_date(selected_date)
grouped_events = group_guests(events)

if not grouped_events:
    st.warning("Não há eventos para a data selecionada.")
else:
    # Mostra os eventos e permite selecionar convidados
    selected_event = st.selectbox("Escolha o evento:", list(grouped_events.keys()))

    # Check if a valid event is selected
    if selected_event:
        guests = grouped_events[selected_event]
        guests_names = [guest[1] for guest in guests]
        chosen_guests = st.multiselect(
            "Escolha os convidados para enviar e-mail:", guests_names
        )

        if chosen_guests:
            selected_guest_emails = [guest[0] for guest in guests if guest[1] in chosen_guests]
            guest_names = [guest[1] for guest in guests if guest[1] in chosen_guests]

            guest_count = len(guest_names)
            if guest_count == 1:
                greeting = f"Bom dia, {guest_names[0]}!"
            elif guest_count == 2:
                greeting = f"Bom dia, {guest_names[0]} e {guest_names[1]}!"
            elif guest_count == 3:
                greeting = f"Bom dia, {guest_names[0]}, {guest_names[1]} e {guest_names[2]}!"
            
            # Now, we correctly get the event object based on the selected event
            event = next(ev for ev in events if ev['summary'] == selected_event)
            
            # Format the time for the desired format
            meeting_time = event["start"].get("dateTime", event["start"].get("date"))
            meeting_time = datetime.datetime.fromisoformat(meeting_time).strftime("%Hh")  # Format: 08h, 12h, etc.

            default_msg = f"""{greeting}\nTudo bem?\n\nGostaria de confirmar, tudo certo para nossa conversa hoje às {meeting_time}?\n\nNos vemos em breve!\nAtt,"""
            msg = st.text_area("Personalize sua mensagem:", default_msg)

            if st.button("Enviar Emails"):
                sent = 0
                for email in selected_guest_emails:
                    personalized = msg.format()
                    mime = MIMEText(personalized)
                    mime["to"] = ", ".join(selected_guest_emails)
                    mime["subject"] = f"Confirmação: {selected_event}"
                    raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()
                    try:
                        gmail_service.users().messages().send(
                            userId="me", body={"raw": raw}
                        ).execute()
                        sent += 1
                    except HttpError as error:
                        st.error(f"Falha ao enviar para {', '.join(selected_guest_emails)}: {error}")
                st.success(f"Foram enviados {sent} emails.")
