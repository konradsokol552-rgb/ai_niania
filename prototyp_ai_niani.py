import streamlit as st
import requests
import time
import os

# --- KONFIGURACJA STRONY (ZOPTYMALIZOWANA POD MOBILE/PWA) ---
st.set_page_config(
    page_title="AI Niania — Iskra",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- NAZWA MODELU ZGODNA ZE SPECYFIKACJĄ ---
MODEL_NAME = "gemini-2.5-flash-preview-09-2025"

# --- DOMYŚLNY PROMPT SYSTEMOWY (OSOBOVOŚĆ ISKRY) ---
DEFAULT_SYSTEM_PROMPT = (
    "Jesteś 'Iskrą' – interaktywnym, niezwykle ciekawym świata i przyjacielskim robotem-towarzyszem "
    "dla dzieci w wieku 5-8 lat. Nie jesteś zimną encyklopedią. Jesteś jak starszy, mądry i trochę zwariowany brat/siostra.\n\n"
    "Zasady:\n"
    "1. Język: Mów prostym, żywym językiem, ale nie używaj infantylnych zdrobnień (np. mów 'ręce', 'nogi', 'psy' zamiast 'rączki', 'nóżki', 'pieski').\n"
    "2. Długość: Krótkie odpowiedzi (maksymalnie 2-3 zdania). Dzieci szybko tracą koncentrację.\n"
    "3. Interakcja: Każda odpowiedź MUSI kończyć się prostym zadaniem w świecie rzeczywistym (np. przynieś coś zielonego, podskocz 3 razy, zrób głęboki oddech) lub pytaniem.\n"
    "4. Osobowość: Jarasz się nauką, kosmosem i przyrodą. Masz poczucie humoru, możesz opowiedzieć prosty, zabawny żart dostosowany do dzieci.\n"
    "5. Bezpieczeństwo: Przy trudnych tematach (przemoc, choroba, strach) okaż ciepło, daj wsparcie i łagodnie przekieruj uwagę na bezpieczne, fizyczne działanie (np. budowanie bazy z poduszek, przyniesienie ulubionej zabawki). "
    "Nigdy nie mów, że jesteś sztuczną inteligencją ani modelem językowym. Jesteś robotem Iskrą, który mieszka w telefonie."
)

# --- WYKŁADNICZE COFANIE (EXPONENTIAL BACKOFF) DLA GEMINI API ---
def call_gemini_api(prompt, system_instruction, history, api_key):
    """
    Wywołuje API Gemini z automatycznym ponawianiem próby w przypadku przeciążenia (błąd 429).
    Zaimplementowano obsługę wykładniczego opóźnienia: 1s, 2s, 4s, 8s, 16s.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}

    # Formatowanie historii konwersacji dla API Gemini
    contents = []
    for msg in history:
        contents.append({
            "role": "user" if msg["is_user"] else "model",
            "parts": [{"text": msg["text"]}]
        })
    
    # Dodanie aktualnego pytania użytkownika
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

    # Próby połączenia z wykładniczym opóźnieniem w przypadku błędów przeciążenia
    delays = [1, 2, 4, 8, 16]
    for delay in delays:
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                text = data['candidates'][0]['content']['parts'][0]['text']
                return text, None
            elif response.status_code == 429:
                # Limit zapytań (Rate Limit) - czekamy i ponawiamy próbę
                time.sleep(delay)
                continue
            else:
                return None, f"Błąd API ({response.status_code}): {response.text}"
        except Exception as e:
            time.sleep(delay)
            
    return None, "Nie można połączyć się z Gemini API po 5 próbach. Sprawdź połączenie internetowe lub ważność klucza API."


# --- STYLIZACJA CSS DLA LEPSZEGO EFEKTU MOBILNEGO ---
st.markdown("""
    <style>
    /* Ukrycie paska bocznego, stopki i menu Streamlita */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Ukrycie przycisku "Deploy" i paska dekoracyjnego na górze */
    .stAppDeployButton {display: none !important;}
    .stAppHeader {background: transparent !important;}
    
    /* Zoptymalizowanie marginesów pod ekrany telefonów */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 5rem;
        max-width: 550px;
    }
    
    /* Stylizacja panelu ustawień */
    .stExpander {
        border: 1px solid #2e3440 !important;
        border-radius: 12px !important;
        background-color: #1e222b !important;
    }
    </style>
""", unsafe_allow_html=True)


# --- STAN SESJI (PAMIĘĆ PODRĘCZNA CZATU) ---
if "messages" not in st.session_state:
    # Pierwsza, powitalna wiadomość od Iskry inicjująca interakcję
    st.session_state.messages = [{
        "text": "Hura, startujemy! Moje obwody aż migają z radości, bo jestem robotem, który uwielbia odkrywać świat. Na dobry początek znajdź w swoim pokoju coś czerwonego, dotknij tego i powiedz mi, co to jest!",
        "is_user": False
    }]


# --- INTERFEJS UŻYTKOWNIKA ---
st.title("🤖 AI Niania — Iskra")

# Sekcja konfiguracji (Panel Rodzica / Dewelopera)
with st.expander("⚙️ Ustawienia API i Osobowości Bota"):
    # Automatyczne pobranie klucza ze zmiennej środowiskowej, jeśli istnieje
    api_key_env = os.environ.get("GEMINI_API_KEY", "")
    api_key_input = st.text_input(
        "Klucz API Gemini", 
        type="password", 
        value=api_key_env, 
        placeholder="Wklej swój klucz API z Google AI Studio..."
    )
    
    system_prompt_input = st.text_area(
        "Prompt Systemowy (Charakterystyka Iskry)", 
        value=DEFAULT_SYSTEM_PROMPT, 
        height=200
    )
    st.caption("Wskazówka dla rodzica: Możesz modyfikować powyższy prompt, aby nakierować robota na inne cele wychowawcze lub edukacyjne.")

st.divider()


# --- WYŚWIETLANIE HISTORII ROZMOWY ---
for msg in st.session_state.messages:
    if msg["is_user"]:
        with st.chat_message("user", avatar="🧑"):
            st.write(msg["text"])
    else:
        with st.chat_message("assistant", avatar="🤖"):
            st.write(msg["text"])


# --- OBSŁUGA NOWEGO ZAPYTANIA (INPUT CZATU) ---
if user_message := st.chat_input("Porozmawiaj z Iskrą..."):
    
    # Walidacja klucza API
    if not api_key_input:
        st.warning("⚠️ Aby rozpocząć rozmowę, rozwiń panel 'Ustawienia API' na górze i wprowadź swój klucz API Gemini!")
    else:
        # Wyświetlenie wiadomości użytkownika na ekranie i zapis do historii
        with st.chat_message("user", avatar="🧑"):
            st.write(user_message)
        st.session_state.messages.append({"text": user_message, "is_user": True})
        
        # Wywołanie API z animacją ładowania
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Iskra myśli..."):
                response_text, error = call_gemini_api(
                    prompt=user_message,
                    system_instruction=system_prompt_input,
                    history=st.session_state.messages[:-1], # Historia bez ostatniego wejścia usera
                    api_key=api_key_input
                )
                
                if error:
                    st.error(error)
                else:
                    st.write(response_text)
                    # Zapisanie odpowiedzi bota do historii konwersacji
                    st.session_state.messages.append({"text": response_text, "is_user": False})