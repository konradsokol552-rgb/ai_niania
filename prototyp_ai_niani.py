import streamlit as st
import requests
import time
import re
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
    "Na samym końcu swojej odpowiedzi, po podwójnym przełamaniu linii (pustej linii), musisz dodać metadane analityczne. "
    "Zostaną one wycięte. Dodaj wyłącznie pasujące tagi w formacie:\n"
    "[EMOTION: radość/smutek/ekscytacja/złość/nuda/neutralny/strach/ciekawość] - subiektywna emocja dziecka.\n"
    "[INTEREST: temat_zainteresowania] - pasja dziecka.\n"
    "[TASK: treść_zadania] - jeśli zadałeś fizyczne zadanie.\n"
    "[ALERT: powód] - NATYCHMIAST w skrajnych przypadkach realnego zagrożenia (np. [ALERT: broń palna]).\n\n"
    "Przykład końca odpowiedzi:\n"
    "Kosmos jest niesamowity! Leć szybko do kuchni, znajdź coś okrągłego jak planeta i przynieś przed ekran!\n\n"
    "[EMOTION: ekscytacja]\n"
    "[INTEREST: kosmos]\n"
    "[TASK: przynieś coś okrągłego]"
)

# --- INICJALIZACJA STANU APLIKACJI ---
if "role" not in st.session_state:
    st.session_state.role = "login"  # Dostępne: login, parent_login, child, parent
if "messages" not in st.session_state:
    st.session_state.messages = [{"text": "Cześć! Znajdź coś czerwonego i dotknij tego!", "is_user": False}]
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "user_id" not in st.session_state:
    st.session_state.user_id = "konrad_demo"
if "last_metadata" not in st.session_state:
    st.session_state.last_metadata = {}

# --- FUNKCJE POMOCNICZE ---
def check_password(password):
    # Weryfikacja hasła bezpośrednio z bazy danych Firestore dla danego profilu dziecka
    correct_password = db_ops.get_parent_password(st.session_state.user_id)
    return password == correct_password

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

# --- EKRANY APLIKACJI ---

def screen_login():
    st.title("Witaj w Iskrze 🤖")
    st.write("Wybierz profil, aby kontynuować:")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧒 Wejdź jako Dziecko", use_container_width=True):
            st.session_state.role = "child"
            st.rerun()
    with col2:
        if st.button("🧑‍🔧 Panel Rodzica", use_container_width=True):
            st.session_state.role = "parent_login"
            st.rerun()

def screen_parent_login():
    st.title("🔒 Logowanie do Panelu Rodzica")
    pwd = st.text_input("Podaj hasło rodzica:", type="password")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Zaloguj", use_container_width=True):
            if check_password(pwd):
                st.session_state.role = "parent"
                st.rerun()
            else:
                st.error("Nieprawidłowe hasło! (Domyślne to 1234)")
    with col2:
        if st.button("Wróć", use_container_width=True):
            st.session_state.role = "login"
            st.rerun()

def screen_parent():
    st.title("📊 Panel Rodzica")
    
    st.subheader("⚙️ Ustawienia systemowe")
    new_api_key = st.text_input("Klucz API Gemini", value=st.session_state.api_key, type="password")
    new_user_id = st.text_input("ID Dziecka w Bazie", value=st.session_state.user_id)
    
    if st.button("Zapisz klucz i ID dziecka"):
        st.session_state.api_key = new_api_key
        st.session_state.user_id = new_user_id
        st.success("Ustawienia systemowe zapisane lokalnie!")
        
    st.divider()
    st.subheader("🔑 Bezpieczeństwo i Hasło")
    current_db_pass = db_ops.get_parent_password(st.session_state.user_id)
    new_password = st.text_input("Zmień hasło do Panelu Rodzica / Wyjścia z aplikacji", value=current_db_pass, type="password")
    
    if st.button("Zapisz nowe hasło w bazie"):
        if new_password.strip() == "":
            st.error("Hasło nie może być puste!")
        else:
            if db_ops.update_parent_password(st.session_state.user_id, new_password):
                st.success("Hasło zostało pomyślnie zaktualizowane w bazie danych Firestore!")
    
    st.divider()
    st.subheader("📊 Ostatni odczyt z bazy (Metadane)")
    m = st.session_state.last_metadata
    if m:
        st.info(f"Ostatnia Emocja: {m.get('EMOTION', 'brak')}")
        st.info(f"Ostatnie Zainteresowanie: {m.get('INTEREST', 'brak')}")
        if m.get('ALERT'): 
            st.error(f"⚠️ OSTATNI ALERT: {m['ALERT']}")
    else:
        st.write("Brak danych z bieżącej sesji czatu.")
        
    st.divider()
    if st.button("Wyloguj i wróć do ekranu startowego", type="primary"):
        st.session_state.role = "login"
        st.rerun()

def screen_child():
    # Ukryty, mały panel wyjścia
    with st.expander("🔒 Wyjście dla Rodzica"):
        exit_pwd = st.text_input("Wpisz hasło rodzica, aby wyjść:", type="password", key="exit_pwd")
        if st.button("Opuść panel dziecka"):
            if check_password(exit_pwd):
                st.session_state.role = "login"
                st.rerun()
            else:
                st.error("Błędne hasło!")

    st.title("🤖 Iskra")

    # Wyświetlanie czatu
    for msg in st.session_state.messages:
        with st.chat_message("user" if msg["is_user"] else "assistant"):
            st.write(msg["text"])

    # Obsługa wiadomości
    if user_input := st.chat_input("Napisz do Iskry..."):
        if not st.session_state.api_key:
            st.error("Rodzic musi najpierw podać klucz API w swoim panelu!")
            return
            
        st.session_state.messages.append({"text": user_input, "is_user": True})
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
                
                if metadata:
                    st.session_state.last_metadata = metadata
                    
                    db_ops.save_metadata(
                        user_id=st.session_state.user_id,
                        emotion=metadata.get("EMOTION"),
                        interest=metadata.get("INTEREST"),
                        alert=metadata.get("ALERT")
                    )
                
                st.session_state.messages.append({"text": clean_text, "is_user": False})
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