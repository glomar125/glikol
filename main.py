# main.py
import streamlit as st
import hello
import pdf_importer_s # <- Importuj nową stronę

# Mapa stron
PAGES = {
    "Hello App": hello.hello_app,
    "Import PDF": pdf_importer_s.import_pdf_data,
}

def main():
    st.set_page_config(page_title="Główna Aplikacja GLIKOL", page_icon="⚙️")
    
    st.sidebar.title("Nawigacja")
    
    # Utworzenie menu rozwijanego w pasku bocznym
    selection = st.sidebar.selectbox("Wybierz stronę:", list(PAGES.keys()))
    
    # Wywołanie wybranej funkcji/strony
    page_function = PAGES[selection]
    page_function()

if __name__ == "__main__":
    main()