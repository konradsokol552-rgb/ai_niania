import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json

def get_db():
    """
    Inicjalizuje połączenie z Firestore. 
    Używa sekretów ze Streamlit dla bezpieczeństwa.
    """
    if not firebase_admin._apps:
        # Pobieramy JSON z sekretów Streamlit
        # Klucz powinien być w formacie:
        # [firebase]
        # service_account = '{"type": "service_account", ...}'
        key_dict = json.loads(st.secrets["firebase"]["service_account"])
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    
    return firestore.client()

def save_metadata(user_id, emotion=None, interest=None, alert=None):
    """
    Zapisuje metadane rozmowy do Firestore w kolekcji 'conversations'.
    """
    db = get_db()
    
    # Tworzymy dokument z danymi
    data = {
        "timestamp": firestore.SERVER_TIMESTAMP,
        "user_id": user_id,
        "emotion": emotion,
        "interest": interest,
        "alert": alert
    }
    
    # Dodajemy rekord do kolekcji
    try:
        db.collection("conversations").add(data)
    except Exception as e:
        st.error(f"Błąd zapisu do bazy: {e}")