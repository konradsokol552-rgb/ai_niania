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

def save_metadata(user_id, emotion=None, interest=None, alert=None):
    db = get_db()
    user_ref = db.collection("users").document(user_id)
    
    current_time = datetime.datetime.now(datetime.timezone.utc)
    
    new_message_map = {
        "timestamp": current_time,
        "emotion": emotion,
        "interest": interest,
        "alert": alert
    }
    
    try:
        user_ref.set({
            "history": firestore.ArrayUnion([new_message_map])
        }, merge=True)
    except Exception as e:
        st.error(f"Błąd krytyczny bazy danych: {e}")

# --- NOWE FUNKCJE OBSŁUGI HASŁA ---

def get_parent_password(user_id):
    """Pobiera hasło rodzica z Firestore. Jeśli dokument lub pole nie istnieje, zwraca domyślne '1234'"""
    try:
        db = get_db()
        doc = db.collection("users").document(user_id).get()
        if doc.exists:
            data = doc.to_dict()
            return data.get("parent_password", "1234")
        return "1234"
    except Exception:
        return "1234"

def update_parent_password(user_id, new_password):
    """Zapisuje nowe hasło rodzica w dokumencie użytkownika w Firestore"""
    try:
        db = get_db()
        user_ref = db.collection("users").document(user_id)
        user_ref.set({
            "parent_password": new_password
        }, merge=True)
        return True
    except Exception as e:
        st.error(f"Błąd zapisu nowego hasła w bazie: {e}")
        return False