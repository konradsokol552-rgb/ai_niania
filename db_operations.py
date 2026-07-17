def save_metadata(user_id, emotion=None, interest=None, alert=None):
    db = get_db()
    
    # Referencja bezpośrednio do dokumentu użytkownika o nazwie user_id
    user_ref = db.collection("users").document(user_id)
    
    # Tworzymy słownik z danymi
    data = {
        "timestamp": firestore.SERVER_TIMESTAMP,
        "emotion": emotion,
        "interest": interest,
        "alert": alert
    }
    
    # Używamy set z merge=True, aby nadpisać pola w tym samym dokumencie
    try:
        user_ref.set(data, merge=True)
    except Exception as e:
        st.error(f"Błąd zapisu do bazy: {e}")