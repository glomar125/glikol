import streamlit as st
import time

# Konfiguracja strony
st.set_page_config(page_title="Hello App", page_icon="👋")

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
