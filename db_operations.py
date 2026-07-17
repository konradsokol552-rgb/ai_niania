import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json

def get_db():
    if not firebase_admin._apps:
        key_dict = json.loads(st.secrets["firebase"]["service_account"])
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    return firestore.client()

def save_metadata(user_id, emotion=None, interest=None, alert=None):
    """
    Zapisuje wiadomość jako mapę w tablicy 'history' w dokumencie użytkownika.
    """
    db = get_db()
    
    # Referencja do dokumentu użytkownika
    user_ref = db.collection("users").document(user_id)
    
    # Tworzymy mapę (obiekt) z danymi tej jednej wiadomości
    new_message_map = {
        "timestamp": firestore.SERVER_TIMESTAMP,
        "emotion": emotion,
        "interest": interest,
        "alert": alert
    }
    
    # Używamy array_union, aby dopisać tę mapę do pola 'history'
    try:
        # Próba dodania do istniejącej tablicy
        user_ref.update({
            "history": firestore.ArrayUnion([new_message_map])
        })
    except Exception:
        # Jeśli dokument nie istnieje, set stworzy go z pierwszym elementem w tablicy
        user_ref.set({
            "history": [new_message_map]
        }, merge=True)