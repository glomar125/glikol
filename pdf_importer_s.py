# pdf_importer.py
import streamlit as st
import pandas as pd
from tabula import read_pdf
import tempfile
import os

def import_pdf_data():
    st.header("Importuj Dane z PDF (Tabele)")
    st.markdown("Użyj tej strony, aby przesłać plik PDF i spróbować wyodrębnić z niego tabele.")

    # Widget do przesłania pliku
    uploaded_file = st.file_uploader("Prześlij plik PDF", type="pdf")

    if uploaded_file is not None:
        # Streamlit dostarcza dane w formie BytesIO, musimy zapisać je tymczasowo na dysku
        # Ponieważ biblioteki do PDF, takie jak tabula, wymagają ścieżki do pliku
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_pdf_path = os.path.join(temp_dir, uploaded_file.name)
            
            # Zapisz przesłany plik tymczasowo
            with open(temp_pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.success(f"Plik '{uploaded_file.name}' załadowany. Próbuję wyodrębnić tabele...")
            
            try:
                # 1. Użyj tabula-py do odczytu PDF
                # pages='all' - spróbuje znaleźć tabele na wszystkich stronach
                # multiple_tables=True - zwróci listę DataFrame'ów
                tables = read_pdf(
                    temp_pdf_path, 
                    pages="all", 
                    multiple_tables=True,
                    stream=True # Użycie metody 'stream' jest często lepsze dla tabel opartych na odstępach
                )

                if tables:
                    st.subheader(f"Znaleziono {len(tables)} tabel(e) w pliku:")
                    
                    # Wyświetl znalezione tabele
                    for i, df in enumerate(tables):
                        st.write(f"--- Tabela nr {i+1} ---")
                        st.dataframe(df)

                else:
                    st.warning("Nie znaleziono żadnych tabel w tym pliku PDF.")
                
            except Exception as e:
                st.error(f"Wystąpił błąd podczas przetwarzania PDF: {e}")
                # Alternatywa: spróbuj pdfplumber
                try:
                    import pdfplumber
                    st.info("Próbuję wyodrębnić tabele za pomocą pdfplumber...")
                    tables_found = False
                    with pdfplumber.open(temp_pdf_path) as pdf:
                        for page_num, page in enumerate(pdf.pages):
                            table = page.extract_table()
                            if table:
                                df = pd.DataFrame(table[1:], columns=table[0])
                                st.write(f"--- Tabela z pdfplumber, strona {page_num+1} ---")
                                st.dataframe(df)
                                tables_found = True
                    if not tables_found:
                        st.warning("pdfplumber: Nie znaleziono tabel w tym pliku PDF.")
                except Exception as e2:
                    st.error(f"pdfplumber również nie odczytał tabel: {e2}")

# Opcjonalnie: Uruchomienie jako samodzielny skrypt
if __name__ == "__main__":
    import_pdf_data()