import sys
import os
import time
import webview
import subprocess
import threading

def run_server():
    # Uruchomienie Streamlita w tle za pomocą wątku lub bezpiecznego procesu
    # Zamiast sys.executable do subprocess, lepiej wskazać moduł streamlit bezpośrednio
    import streamlit.web.cli as stcli
    
    def run_streamlit():
        sys.argv = ["streamlit", "run", "prototyp_ai_niani.py", "--global.developmentMode=false"]
        stcli.main()

    # Odpalamy Streamlita w osobnym wątku wewnątrz tej samej aplikacji, 
    # zamiast tworzyć zewnętrzny subprocess, co eliminuje problem pętli!
    t = threading.Thread(target=run_streamlit)
    t.daemon = True
    t.start()

if __name__ == '__main__':
    run_server()
    time.sleep(2)  # Krótka chwila, żeby Streamlit wstał w tle
    
    # Tworzymy okno pywebview skierowane na lokalny port Streamlita
    webview.create_window('Iskra - AI Niania', 'http://localhost:8501', width=1000, height=700)
    webview.start()