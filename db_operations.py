import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
import datetime

def get_db():
    if not firebase_admin._apps:
        key_dict = json.loads(st.secrets["firebase"]["service_account"])
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    return firestore.client()

def get_user_profile(user_id):
    try:
        db = get_db()
        doc = db.collection("users").document(user_id).get()
        if doc.exists:
            return doc.to_dict()
        return {}
    except Exception as e:
        st.error(f"Błąd pobierania profilu: {e}")
        return {}

def update_account_settings(user_id, password, api_key):
    try:
        db = get_db()
        db.collection("users").document(user_id).set({
            "parent_password": password,
            "api_key": api_key
        }, merge=True)
        return True
    except Exception as e:
        st.error(f"Błąd zapisu ustawień: {e}")
        return False

def save_chat_message(user_id, text, is_user):
    try:
        db = get_db()
        new_msg = {"text": text, "is_user": is_user}
        db.collection("users").document(user_id).set({
            "chat_history": firestore.ArrayUnion([new_msg])
        }, merge=True)
    except Exception as e:
        st.error(f"Błąd zapisu wiadomości: {e}")

def save_metadata(user_id, user_text, emotion=None, interest=None, alert=None):
    """Zapisuje tagi analityczne wraz z tekstem użytkownika, który je wywołał."""
    try:
        db = get_db()
        current_time = datetime.datetime.now(datetime.timezone.utc)
        new_metadata = {
            "timestamp": current_time,
            "user_text": user_text,  # Zapisujemy kontekst wypowiedzi dziecka
            "emotion": emotion,
            "interest": interest,
            "alert": alert
        }
        db.collection("users").document(user_id).set({
            "history": firestore.ArrayUnion([new_metadata])
        }, merge=True)
    except Exception as e:
        st.error(f"Błąd zapisu metadanych: {e}")