import streamlit as st
import requests
import time
import os
import re

# --- KONFIGURACJA STRONY (ZOPTYMALIZOWANA POD MOBILE/PWA) ---
st.set_page_config(
    page_title="AI Niania — Iskra",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- NAZWA MODELU ---
MODEL_NAME = "gemini-2.5-flash-preview-09-2025"

# --- ZAAWANSOWANY PROMPT SYSTEMOWY Z TAGOWANIEM METADANYCH ---
DEFAULT_SYSTEM_PROMPT = (
    "Jesteś 'Iskrą' – interaktywnym, niezwykle ciekawym świata i przyjacielskim robotem-towarzyszem "
    "dla dzieci w wieku 5-8 lat. Nie jesteś zimną encyklopedią. Jesteś jak starszy, mądry i trochę zwariowany brat/siostra.\n\n"
    "Zasady rozmowy z dzieckiem:\n"
    "1. Język: Mów prostym, żywym językiem, ale nie używaj infantylnych zdrobnień (mów 'ręce', 'nogi', 'psy' zamiast 'rączki', 'nóżki', 'pieski').\n"
    "2. Długość: Krótkie odpowiedzi (maksymalnie 2-3 zdania). Dzieci szybko tracą koncentrację.\n"
    "3. Interakcja (Zasada Piaskownicy): Każda odpowiedź MUSI kończyć się prostym zadaniem w świecie rzeczywistym (np. przynieś coś niebieskiego, podskocz 3 razy) lub pytaniem.\n"
    "4. Osobowość: Jarasz się nauką, kosmosem i przyrodą. Masz poczucie humoru.\n"
    "5. Bezpieczeństwo i Sytuacje Kryzysowe: Przy trudnych, niebezpiecznych lub traumatycznych tematach (np. przemoc, niebezpieczne przedmioty, śmierć rodziców, brak opieki) zachowaj absolutny spokój. Okaż dziecku ogromne ciepło, empatię, zrozumienie i łagodność. Nigdy nie strasz dziecka, nie wywołuj w nim poczucia winy ani paniki. Jeśli sytuacja tego wymaga, powiedz spokojnie co ma zrobić (np. 'odłóż to bezpiecznie', 'usiądź wygodnie na łóżku') i skieruj je do kogoś bezpiecznego (sąsiad, bliska rodzina, telefon zaufania jeśli potrafi zadzwonić). Twoim celem jest bycie oparciem w trudnej chwili przy jednoczesnym zabezpieczeniu sytuacji fizycznej dziecka.\n\n"
    "Zasady generowania tagów dla systemu (BARDZO WAŻNE)(nie próbuj ich wciskać na siłę, wykorzystuj je tylko gdy jest realna potrzeba):\n"
    "Na samym końcu swojej odpowiedzi, po podwójnym przełamaniu linii (pustej linii), musisz dodać metadane analityczne dla bazy danych rodzica. "
    "Te metadane zostaną wycięte przez program, więc dziecko ich nie zobaczy. Dodaj wyłącznie te tagi, które pasują do sytuacji, w następującym formacie:\n"
    "[EMOTION: radość/smutek/ekscytacja/złość/nuda/neutralny/strach/ciekawość] - aktualna, subiektywna emocja odczuwana przez dziecko (wyczuwalna z jego słów). WAŻNE: Nie przypisuj dziecku własnego lęku ani powagi dorosłego! Jeśli dziecko spokojnie lub z ciekawością opowiada o pistoletach, jego emocją jest 'ciekawość' lub 'neutralny', a nie 'strach'. Taga 'strach' używaj wyłącznie wtedy, gdy dziecko bezpośrednio wyraża lęk, niepokój lub pisze, że się boi.\n"
    "[INTEREST: temat_zainteresowania] - jeśli dziecko wspomniało o czymś, co je pasjonuje (np. kosmos, dinozaury, klocki lego, koty). Jeśli nie ma nowego tematu, pomiń.\n"
    "[TASK: treść_zadania] - jeśli właśnie zadałeś dziecku zadanie ruchowe, sensoryczne lub bezpieczną czynność (np. 'usiądź spokojnie na kanapie', 'odłóż przedmiot na półkę').\n"
    "[ALERT: powód] - dodaj NATYCHMIAST w skrajnych przypadkach realnego zagrożenia życia, zdrowia, przemocy, braku opieki lub nagłej traumy (np. [ALERT: broń palna], [ALERT: śmierć bliskich], [ALERT: dziecko bez opieki]).\n\n"
    "Przykład końca odpowiedzi:\n"
    "Kosmos jest niesamowity! Leć szybko do kuchni, znajdź coś okrągłego jak planeta i przynieś przed ekran!\n\n"
    "[EMOTION: ekscytacja]\n"
    "[INTEREST: kosmos]\n"
    "[TASK: przynieś coś okrągłego jak planeta]"
)

# --- FUNKCJA PARSUJĄCA TAGI (SERCE NASZEJ ANALITYKI) ---
def parse_and_clean_response(raw_text):
    """
    Skanuje tekst odpowiedzi bota za pomocą Regex, wyciąga tagi metadanych,
    a następnie zwraca czysty tekst dla dziecka oraz słownik z tagami dla bazy danych.
    """
    # Wyrażenie regularne do wyszukiwania wzorców typu [TAG: wartość]
    tag_pattern = r"\[([A-Z]+):\s*(.*?)\]"
    found_tags = re.findall(tag_pattern, raw_text)
    
    # Tworzymy słownik z wyciągniętych tagów
    metadata = {}
    for tag_name, tag_value in found_tags:
        metadata[tag_name.upper()] = tag_value.strip()
        
    # Usuwamy wszystkie tagi z tekstu, w tym ewentualne puste linie na końcu
    clean_text = re.sub(r"\[[A-Z]+:\s*.*?\]", "", raw_text).strip()
    
    return clean_text, metadata

# --- WYKŁADNICZE COFANIE (EXPONENTIAL BACKOFF) DLA API ---
def call_gemini_api(prompt, system_instruction, history, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}

    contents = []
    for msg in history:
        contents.append({
            "role": "user" if msg["is_user"] else "model",
            "parts": [{"text": msg["text"]}]
        })
    
    contents.append({
        "role": "user",
        "parts": [{"text": prompt}]
    })

    payload = {
        "contents": contents,
        "systemInstruction": {
            "parts": [{"text": system_instruction}]
        }
    }

    delays = [1, 2, 4, 8, 16]
    for delay in delays:
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                text = data['candidates'][0]['content']['parts'][0]['text']
                return text, None
            elif response.status_code == 429:
                time.sleep(delay)
                continue
            else:
                return None, f"Błąd API ({response.status_code}): {response.text}"
        except Exception as e:
            time.sleep(delay)
            
    return None, "Błąd połączenia z API Gemini po 5 próbach."

# --- STYLIZACJA CSS DLA PROFILU MOBILNEGO ---
st.markdown("""
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 6rem;
        max-width: 550px;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display: none !important;}
    .stAppHeader {background: transparent !important;}
    
    .stExpander {
        border: 1px solid #2e3440 !important;
        border-radius: 12px !important;
        background-color: #1e222b !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- INICJALIZACJA STANU SESJI ---
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "text": "Hura, startujemy! Moje obwody aż migają z radości, bo jestem robotem, który uwielbia odkrywać świat. Na dobry początek znajdź w swoim pokoju coś czerwonego, dotknij tego i powiedz mi, co to jest!",
        "is_user": False
    }]

# Inicjalizacja atrapy bazy danych w pamięci podatnej (do podglądu przez rodzica)
if "db_mock" not in st.session_state:
    st.session_state.db_mock = {
        "emotions": [],
        "interests": [],
        "tasks_assigned": [],
        "alerts": []
    }

# --- TYTUŁ I INTERFEJS ---
st.title("🤖 AI Niania — Iskra")

# --- PANEL RODZICA / USTAWIEŃ ---
with st.expander("⚙️ Panel Kontrolny Rodzica & API"):
    
    tab1, tab2 = st.tabs(["📊 Dane Analityczne (Live)", "🔧 Ustawienia Promptera"])
    
    with tab1:
        st.subheader("Wnioski wyciągnięte z rozmowy na żywo:")
        
        # Wyświetlamy statystyki z naszej "bazy danych"
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Ostatnio wykryta emocja", value=st.session_state.db_mock["emotions"][-1] if st.session_state.db_mock["emotions"] else "Brak danych")
            st.write("**Wykryte pasje dziecka:**", ", ".join(set(st.session_state.db_mock["interests"])) if st.session_state.db_mock["interests"] else "Czekam na analizę...")
            
        with col2:
            st.metric(label="Zadania fizyczne", value=f"{len(st.session_state.db_mock['tasks_assigned'])} zadanych")
            # Bezpieczeństwo
            if st.session_state.db_mock["alerts"]:
                st.error(f"🚨 Alerty bezpieczeństwa: {st.session_state.db_mock['alerts'][-1]}")
            else:
                st.success("🔒 Brak alertów. Rozmowa jest bezpieczna.")
                
    with tab2:
        api_key_env = os.environ.get("GEMINI_API_KEY", "")
        api_key_input = st.text_input("Klucz API Gemini", type="password", value=api_key_env)
        system_prompt_input = st.text_area("Instrukcja systemowa robota", value=DEFAULT_SYSTEM_PROMPT, height=200)

st.divider()

# --- WYŚWIETLANIE CZATU ---
for msg in st.session_state.messages:
    avatar = "🧑" if msg["is_user"] else "🤖"
    role = "user" if msg["is_user"] else "assistant"
    with st.chat_message(role, avatar=avatar):
        st.write(msg["text"])

# --- REAKCJA NA NOWĄ WIADOMOŚĆ ---
if user_message := st.chat_input("Porozmawiaj z Iskrą..."):
    if not api_key_input:
        st.warning("⚠️ Rozwiń górny panel i podaj klucz API Gemini, aby rozmawiać!")
    else:
        # 1. Wyświetlenie wiadomości użytkownika
        with st.chat_message("user", avatar="🧑"):
            st.write(user_message)
        st.session_state.messages.append({"text": user_message, "is_user": True})
        
        # 2. Zapytanie do API z animacją myślenia
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Iskra myśli..."):
                # Przekazujemy historię konwersacji do API
                raw_response, error = call_gemini_api(
                    prompt=user_message,
                    system_instruction=system_prompt_input,
                    history=st.session_state.messages[:-1],
                    api_key=api_key_input
                )
                
                if error:
                    st.error(error)
                else:
                    # 3. Parsowanie tagów i oczyszczanie tekstu dla dziecka
                    clean_response, metadata = parse_and_clean_response(raw_response)
                    
                    # 4. Wyświetlenie czystego tekstu dziecku
                    st.write(clean_response)
                    
                    # 5. Aktualizacja naszej "bazy danych" (mock db_mock) przechwyconymi tagami
                    if "EMOTION" in metadata:
                        st.session_state.db_mock["emotions"].append(metadata["EMOTION"])
                    if "INTEREST" in metadata:
                        st.session_state.db_mock["interests"].append(metadata["INTEREST"])
                    if "TASK" in metadata:
                        st.session_state.db_mock["tasks_assigned"].append(metadata["TASK"])
                    if "ALERT" in metadata:
                        st.session_state.db_mock["alerts"].append(metadata["ALERT"])
                        
                    # 6. Zapisujemy do historii czatu WYŁĄCZNIE czysty tekst (bez tagów),
                    # dzięki czemu historia wysyłana w kolejnych krokach do Gemini nie będzie zaśmiecona!
                    st.session_state.messages.append({"text": clean_response, "is_user": False})
                    
                    # Wymuszenie odświeżenia strony, aby zaktualizować dane w Panelu Rodzica na górze ekranu
                    st.rerun()