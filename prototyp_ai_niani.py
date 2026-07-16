import streamlit as st
import requests
import time
import os
import re
import db_operations as db_ops  # Import Twojego modułu do Firestore

# --- KONFIGURACJA STRONY ---
st.set_page_config(
    page_title="AI Niania — Iskra",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    /* Ukrycie niepotrzebnych elementów Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display: none !important;}
    .stAppHeader {background: transparent !important;}
    
    /* Centrowanie i czyszczenie kontenera */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 5rem;
        max-width: 550px;
    }
    
    /* Stylizacja expandera (Panelu) */
    .stExpander {
        border: 1px solid #2e3440 !important;
        border-radius: 12px !important;
        background-color: #1e222b !important;
    }
    </style>
""", unsafe_allow_html=True)

MODEL_NAME = "gemini-2.5-flash"

# Prompt systemowy (skrócony dla przejrzystości)
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
    
    for delay in [1, 2, 4, 8, 16]:
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

# --- INTERFEJS ---
st.title("🤖 AI Niania — Iskra")

# Ustawienia w expanderze
with st.expander("⚙️ Konfiguracja"):
    api_key = st.text_input("Klucz API", type="password")
    user_id = st.text_input("ID Dziecka (dla bazy danych)", value="konrad_demo")

# Historia czatu
if "messages" not in st.session_state:
    st.session_state.messages = [{"text": "Cześć! Znajdź coś czerwonego i dotknij tego!", "is_user": False}]

for msg in st.session_state.messages:
    with st.chat_message("user" if msg["is_user"] else "assistant"):
        st.write(msg["text"])

# Obsługa czatu
if user_input := st.chat_input("Napisz do Iskry..."):
    if not api_key:
        st.error("Podaj klucz API!")
    else:
        st.session_state.messages.append({"text": user_input, "is_user": True})
        with st.chat_message("user"): st.write(user_input)
        
        with st.chat_message("assistant"):
            raw_response, error = call_gemini_api(user_input, DEFAULT_SYSTEM_PROMPT, st.session_state.messages[:-1], api_key)
            if error:
                st.error(error)
            else:
                clean_text, metadata = parse_and_clean_response(raw_response)
                st.write(clean_text)
                
                # ZAPIS DO FIRESTORE przez Twój moduł db_operations
                if metadata:
                    db_ops.save_metadata(
                        user_id=user_id,
                        emotion=metadata.get("EMOTION"),
                        interest=metadata.get("INTEREST"),
                        alert=metadata.get("ALERT")
                    )
                
                st.session_state.messages.append({"text": clean_text, "is_user": False})
                st.rerun()