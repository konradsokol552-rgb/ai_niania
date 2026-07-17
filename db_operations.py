import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
import datetime  # 1. Dodaj ten import

def get_db():
    if not firebase_admin._apps:
        key_dict = json.loads(st.secrets["firebase"]["service_account"])
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    return firestore.client()

def save_metadata(user_id, emotion=None, interest=None, alert=None):
    db = get_db()
    user_ref = db.collection("users").document(user_id)
    
    # Używamy czasu UTC
    current_time = datetime.datetime.now(datetime.timezone.utc)
    
    new_message_map = {
        "timestamp": current_time,
        "emotion": emotion,
        "interest": interest,
        "alert": alert
    }
    
    # Ta jedna linijka załatwia cały problem:
    # merge=True sprawia, że jeśli dokument nie istnieje, to zostanie stworzony.
    # Jeśli istnieje, to tylko pole 'history' zostanie zaktualizowane o nowy element.
    try:
        user_ref.set({
            "history": firestore.ArrayUnion([new_message_map])
        }, merge=True)
    except Exception as e:
        st.error(f"Błąd krytyczny bazy danych: {e}")