import webview
import subprocess
import time
import sys

# Uruchomienie streamlit w procesie w tle
def run_server():
    subprocess.Popen([sys.executable, "-m", "streamlit", "run", "twoja_aplikacja.py"])

if __name__ == '__main__':
    run_server()
    time.sleep(3) # Czekamy chwilę aż serwer wstanie
    webview.create_window('Moja Aplikacja', 'http://localhost:8501')
    webview.start()