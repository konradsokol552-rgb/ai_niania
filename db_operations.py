import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json

def get_db():
    """
    Inicjalizuje połączenie z Firestore.
    Musi być w tym samym pliku, co funkcje, które z niej korzystają.
    """
    if not firebase_admin._apps:
        # Pobieramy JSON z sekretów Streamlit
        key_dict = json.loads(st.secrets["firebase"]["service_account"])
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    return firestore.client()

def save_metadata(user_id, emotion=None, interest=None, alert=None):
    """
    Zapisuje dane bezpośrednio w dokumencie użytkownika: users/{user_id}
    """
    db = get_db()  # Teraz ta funkcja jest widoczna!
    
    # Referencja bezpośrednio do dokumentu użytkownika
    user_ref = db.collection("users").document(user_id)
    
    # Tworzymy słownik z danymi
    data = {
        "timestamp": firestore.SERVER_TIMESTAMP,
        "emotion": emotion,
        "interest": interest,
        "alert": alert
    }
    
    # Używamy set z merge=True, aby nadpisać pola w dokumencie bez tworzenia podkolekcji
    try:
        user_ref.set(data, merge=True)
    except Exception as e:
        st.error(f"Błąd zapisu do bazy: {e}")