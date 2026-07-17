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
    
    # 2. Używamy aktualnego czasu w formacie UTC
    current_time = datetime.datetime.now(datetime.timezone.utc)
    
    new_message_map = {
        "timestamp": current_time, # Używamy wygenerowanego czasu
        "emotion": emotion,
        "interest": interest,
        "alert": alert
    }
    
    try:
        user_ref.update({
            "history": firestore.ArrayUnion([new_message_map])
        })
    except Exception:
        # Jeśli dokument nie istnieje, set stworzy go z pierwszym elementem w tablicy
        user_ref.set({
            "history": [new_message_map]
        }, merge=True)