import streamlit as st
import time

def hello_app():
    """Funkcja wyświetlająca aplikację Hello w Streamlit"""

    # Wyświetlenie tekstu
    st.title("Hello")

    # Dodanie przycisku do odświeżenia
    if st.button("Odśwież"):
        st.balloons()  # Efekt balonów po kliknięciu

    # Dodanie licznika czasu (opcjonalne)
    placeholder = st.empty()
    for i in range(5, 0, -1):
        placeholder.text(f"Ta strona odświeży się za {i} sekund...")
        time.sleep(1)
    placeholder.text("Czas minął!")

if __name__ == "__main__":
    hello_app()
