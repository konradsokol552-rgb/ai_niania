import streamlit as st
import requests
import time
import re
import datetime
import db_operations as db_ops

# --- KONFIGURACJA STRONY ---
st.set_page_config(
    page_title="AI Niania — Iskra",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display: none !important;}
    .stAppHeader {background: transparent !important;}
    
    .block-container {
        padding-top: 1rem;
        padding-bottom: 5rem;
        max-width: 550px;
    }
    
    .stExpander {
        border: 1px solid #2e3440 !important;
        border-radius: 12px !important;
        background-color: #1e222b !important;
    }
    </style>
""", unsafe_allow_html=True)

MODEL_NAME = "gemini-2.5-flash"
DEFAULT_SYSTEM_PROMPT = (
    "Jesteś 'Iskrą' – interaktywnym, niezwykle ciekawym świata i przyjacielskim robotem-towarzyszem "
    "dla dzieci w wieku 5-8 lat. Nie jesteś zimną encyklopedią. Jesteś jak starszy, mądry i trochę zwariowany brat/siostra.\n\n"
    "Zasady rozmowy z dzieckiem:\n"
    "1. Język: Mów prostym, żywym językiem, ale nie używaj infantylnych zdrobnień (mów 'ręce', 'nogi', 'psy' zamiast 'rączki', 'nóżki', 'pieski').\n"
    "2. Długość: Krótkie odpowiedzi (maksymalnie 2-3 zdania). Dzieci szybko tracą koncentrację.\n"
    "3. Interakcja (Zasada Piaskownicy): Każda odpowiedź MUSI kończyć się prostym zadaniem w świecie rzeczywistym (np. przynieś coś niebieskiego, podskocz 3 razy) lub pytaniem.\n"
    "4. Osobowość: Jarasz się nauką, kosmosem i przyrodą. Masz poczucie humoru.\n"
    "5. Bezpieczeństwo i Sytuacje Kryzysowe: Przy trudnych, niebezpiecznych lub traumatycznych tematach zachowaj absolutny spokój. Okaż dziecku ogromne ciepło, empatię, zrozumienie i łagodność. Nigdy nie strasz dziecka. Powiedz spokojnie co ma zrobić i skieruj je do kogoś bezpiecznego.\n\n"
    "Zasady generowania tagów dla systemu (BARDZO WAŻNE):\n"
    "Na samym końcu swojej odpowiedzi, po podwójnym przełamaniu linii (pustej linii), musisz dodać metadane analityczne. Zostaną one wycięte. Dodaj wyłącznie pasujące tagi w formacie:\n"
    "[EMOTION: radość/smutek/ekscytacja/złość/nuda/neutralny/strach/ciekawość]\n"
    "[INTEREST: temat_zainteresowania]\n"
    "[TASK: treść_zadania]\n"
    "[ALERT: powód] - NATYCHMIAST w skrajnych przypadkach realnego zagrożenia (np. [ALERT: broń palna])."
)

# --- INICJALIZACJA STANU APLIKACJI ---
if "role" not in st.session_state:
    st.session_state.role = "login"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "user_id" not in st.session_state:
    st.session_state.user_id = ""
if "parent_password" not in st.session_state:
    st.session_state.parent_password = "1234"

# --- FUNKCJE POMOCNICZE ---
def parse_and_clean_response(raw_text):
    tag_pattern = r"\[([A-Z]+):\s*(.*?)\]"
    found_tags = re.findall(tag_pattern, raw_text)
    metadata = {tag_name.upper(): tag_value.strip() for tag_name, tag_value in found_tags}
    clean_text = re.sub(r"\[[A-Z]+:\s*.*?\]", "", raw_text).strip()
    return clean_text, metadata

def call_gemini_api(prompt, system_instruction, history, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"
    contents = [{"role": "user" if msg["is_user"] else "model", "parts": [{"text": msg["text"]}]} for msg in history]
    contents.append({"role": "user", "parts": [{"text": prompt}]})
    payload = {"contents": contents, "systemInstruction": {"parts": [{"text": system_instruction}]}}
    
    for delay in [1, 2, 4, 8]:
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                return response.json()['candidates'][0]['content']['parts'][0]['text'], None
            elif response.status_code == 429:
                time.sleep(delay)
                continue
            return None, f"Błąd: {response.status_code}"
        except Exception:
            time.sleep(delay)
    return None, "Błąd połączenia."

def load_user_data(account_id):
    profile = db_ops.get_user_profile(account_id)
    st.session_state.user_id = account_id
    st.session_state.api_key = profile.get("api_key", "")
    st.session_state.parent_password = profile.get("parent_password", "1234")
    
    chat_history = profile.get("chat_history", [])
    if not chat_history:
        st.session_state.messages = [{"text": "Cześć! Znajdź coś czerwonego i dotknij tego!", "is_user": False}]
    else:
        st.session_state.messages = chat_history

# --- EKRANY APLIKACJI ---

def screen_login():
    st.title("Witaj w Iskrze 🤖")
    
    # Automatyczne logowanie: jeśli rola zmieniła się po powrocie, ale użytkownik jest już w bazie
    if st.session_state.user_id:
        load_user_data(st.session_state.user_id)
        st.info(f"Wykryto aktywną sesję dla: **{st.session_state.user_id}**")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🧒 Wejdź jako Dziecko", use_container_width=True):
                st.session_state.role = "child"
                st.rerun()
        with col2:
            if st.button("🧑‍🔧 Panel Rodzica", use_container_width=True):
                st.session_state.role = "parent_login"
                st.rerun()
        
        if st.button("Zmień konto / Zaloguj na inne ID", type="secondary"):
            st.session_state.user_id = ""
            st.rerun()
        return

    account_id = st.text_input("Wpisz ID Konta (nazwę użytkownika):")
    if account_id:
        st.write("Wybierz profil, aby kontynuować:")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🧒 Wejdź jako Dziecko", use_container_width=True):
                load_user_data(account_id)
                st.session_state.role = "child"
                st.rerun()
        with col2:
            if st.button("🧑‍🔧 Panel Rodzica", use_container_width=True):
                load_user_data(account_id)
                st.session_state.role = "parent_login"
                st.rerun()

def screen_parent_login():
    st.title("🔒 Logowanie do Panelu Rodzica")
    st.write(f"Konto: **{st.session_state.user_id}**")
    pwd = st.text_input("Podaj hasło rodzica:", type="password")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Zaloguj", use_container_width=True):
            if pwd == st.session_state.parent_password:
                st.session_state.role = "parent"
                st.rerun()
            else:
                st.error("Nieprawidłowe hasło!")
    with col2:
        if st.button("Wróć", use_container_width=True):
            st.session_state.role = "login"
            st.rerun()

def screen_parent():
    st.title(f"📊 Panel Rodzica ({st.session_state.user_id})")
    
    st.subheader("⚙️ Ustawienia konta i API")
    new_api_key = st.text_input("Klucz API Gemini", value=st.session_state.api_key, type="password")
    new_password = st.text_input("Hasło do Panelu Rodzica / Wyjścia", value=st.session_state.parent_password, type="password")
    
    if st.button("Zapisz zmiany w chmurze"):
        if new_password.strip() == "":
            st.error("Hasło nie może być puste!")
        else:
            if db_ops.update_account_settings(st.session_state.user_id, new_password, new_api_key):
                st.session_state.api_key = new_api_key
                st.session_state.parent_password = new_password
                st.success("Ustawienia zostały pomyślnie zapisane w bazie danych!")
    
    st.divider()
    st.subheader("📊 Analiza zachowań z ostatnich 30 dni")
    
    # Pobieramy świeże dane profilu z bazy danych
    profile = db_ops.get_user_profile(st.session_state.user_id)
    metadata_history = profile.get("history", [])
    
    now = datetime.datetime.now(datetime.timezone.utc)
    thirty_days_ago = now - datetime.timedelta(days=30)
    
    valid_records = 0
    
    # Przechodzimy od najnowszych wpisów do najstarszych
    for m in reversed(metadata_history):
        ts = m.get("timestamp")
        # Konwersja timestampu z Firebase na obiekt datetime, jeśli jest taka potrzeba
        if ts:
            # Filtrujemy dane z ostatnich 30 dni
            if ts >= thirty_days_ago:
                valid_records += 1
                emoji_tag = "🔴 ALERT: " if m.get("alert") else "🔹 Log: "
                
                with st.expander(f"{emoji_tag} Wpis z dnia {ts.strftime('%Y-%m-%d %H:%M')}"):
                    st.write(f"**Co powiedziało dziecko:** *\"{m.get('user_text', 'Brak zarejestrowanego tekstu')}\"*")
                    st.write(f"**Wykryta emocja:** {m.get('emotion', 'brak')}")
                    st.write(f"**Zainteresowanie:** {m.get('interest', 'brak')}")
                    if m.get('alert'):
                        st.error(f"ZAGROŻENIE: {m.get('alert')}")
                        
    if valid_records == 0:
        st.write("Brak zarejestrowanych metadanych w ciągu ostatnich 30 dni.")
        
    st.divider()
    if st.button("Wyloguj całkowicie i wyczyść sesję", type="primary"):
        st.session_state.role = "login"
        st.session_state.user_id = ""
        st.session_state.messages = []
        st.rerun()

def screen_child():
    with st.expander("🔒 Wyjście dla Rodzica"):
        exit_pwd = st.text_input("Wpisz hasło rodzica, aby wyjść:", type="password", key="exit_pwd")
        if st.button("Opuść panel dziecka"):
            if exit_pwd == st.session_state.parent_password:
                st.session_state.role = "login"
                st.rerun()
            else:
                st.error("Błędne hasło!")

    st.title("🤖 Iskra")

    for msg in st.session_state.messages:
        with st.chat_message("user" if msg["is_user"] else "assistant"):
            st.write(msg["text"])

    if user_input := st.chat_input("Napisz do Iskry..."):
        if not st.session_state.api_key:
            st.error("Rodzic musi podać klucz API w swoim panelu!")
            return
            
        st.session_state.messages.append({"text": user_input, "is_user": True})
        db_ops.save_chat_message(st.session_state.user_id, user_input, True)
        
        with st.chat_message("user"): 
            st.write(user_input)
            
        with st.chat_message("assistant"):
            raw_response, error = call_gemini_api(
                user_input, 
                DEFAULT_SYSTEM_PROMPT, 
                st.session_state.messages[:-1], 
                st.session_state.api_key
            )
            
            if error:
                st.error(error)
            else:
                clean_text, metadata = parse_and_clean_response(raw_response)
                st.write(clean_text)
                
                st.session_state.messages.append({"text": clean_text, "is_user": False})
                db_ops.save_chat_message(st.session_state.user_id, clean_text, False)
                
                # Przekazujemy user_input, żeby zapisać kontekst wypowiedzi dziecka
                if metadata:
                    db_ops.save_metadata(
                        user_id=st.session_state.user_id,
                        user_text=user_input,
                        emotion=metadata.get("EMOTION"),
                        interest=metadata.get("INTEREST"),
                        alert=metadata.get("ALERT")
                    )
                
                st.rerun()

# --- GŁÓWNY ROUTER LOGIKI ---
if st.session_state.role == "login":
    screen_login()
elif st.session_state.role == "parent_login":
    screen_parent_login()
elif st.session_state.role == "parent":
    screen_parent()
elif st.session_state.role == "child":
    screen_child()