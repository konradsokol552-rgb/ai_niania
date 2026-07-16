import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json

def get_db():
    if not firebase_admin._apps:
        # Pamiętaj, aby mieć plik klucza w secrets lub skonfigurowany environment variable
        key_dict = json.loads(st.secrets["firebase"]["service_account"])
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    return firestore.client()

def save_metadata(user_id, emotion=None, interest=None, alert=None):
    """
    Zapisuje dane w strukturze: users/{user_id}/conversations/{timestamp}
    """
    db = get_db()
    
    # Tworzymy ścieżkę do konkretnego użytkownika
    user_ref = db.collection("users").document(user_id)
    
    # Tworzymy dokument z danymi
    data = {
        "timestamp": firestore.SERVER_TIMESTAMP,
        "emotion": emotion,
        "interest": interest,
        "alert": alert
    }
    
    # Dodajemy do podkolekcji 'conversations' danego użytkownika
    try:
        user_ref.collection("conversations").add(data)
    except Exception as e:
        st.error(f"Błąd zapisu do bazy: {e}")