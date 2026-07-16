def save_metadata(user_id, emotion=None, interest=None, alert=None):
    """
    Zapisuje dane bezpośrednio w głównym dokumencie użytkownika: users/{user_id}
    Dzięki merge=True, tylko te pola zostaną zaktualizowane.
    """
    db = get_db()
    
    # Referencja bezpośrednio do dokumentu użytkownika
    user_ref = db.collection("users").document(user_id)
    
    # Tworzymy słownik z danymi, które chcemy zaktualizować
    data = {
        "last_update": firestore.SERVER_TIMESTAMP,
        "emotion": emotion,
        "interest": interest,
        "alert": alert
    }
    
    # Używamy set z merge=True, aby nie nadpisać całego dokumentu (np. danych profilowych)
    try:
        user_ref.set(data, merge=True)
    except Exception as e:
        st.error(f"Błąd zapisu do bazy: {e}")