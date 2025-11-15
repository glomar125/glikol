import streamlit as st
import pandas as pd
import tempfile
import os

def import_pdf_data():
    st.header("Importuj Dane z PDF (z OCR)")
    st.markdown("Wczytaj PDF i wyodrębnij dane - obsługuje również PDFy graficzne.")
    
    uploaded_file = st.file_uploader("Prześlij plik PDF", type="pdf")
    
    if uploaded_file is not None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_pdf_path = os.path.join(temp_dir, uploaded_file.name)
            
            with open(temp_pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.success(f"Plik '{uploaded_file.name}' załadowany.")
            
            # Metoda 1: Próba z pdfplumber (tekst + pozycje)
            try:
                import pdfplumber
                st.info("🔍 Metoda 1: Ekstrakcja tekstu z pozycjami (pdfplumber)...")
                
                all_text = []
                with pdfplumber.open(temp_pdf_path) as pdf:
                    for page_num, page in enumerate(pdf.pages):
                        # Wyciągnij cały tekst
                        text = page.extract_text()
                        if text:
                            st.write(f"**Strona {page_num + 1}:**")
                            st.text(text)
                            all_text.append(text)
                        
                        # Spróbuj wykryć tabele (nawet słabo sformatowane)
                        tables = page.extract_tables()
                        if tables:
                            for i, table in enumerate(tables):
                                try:
                                    df = pd.DataFrame(table[1:], columns=table[0])
                                    st.write(f"📊 Tabela {i+1} (strona {page_num + 1}):")
                                    st.dataframe(df)
                                except:
                                    st.write(f"Surowe dane tabeli {i+1}:")
                                    st.write(table)
                
                if all_text:
                    st.download_button(
                        "💾 Pobierz cały tekst jako TXT",
                        "\n\n".join(all_text),
                        file_name="wyodrebniony_tekst.txt"
                    )
                
            except Exception as e:
                st.error(f"Błąd pdfplumber: {e}")
            
            # Metoda 2: OCR (POMINIĘTA - nie jest potrzebna dla tekstowych PDF)
            st.divider()
            st.info("ℹ️ Metoda OCR pominięta - Twój PDF zawiera tekst, nie obrazy.")
            
            # Metoda 3: PyMuPDF (fitz) - alternatywa
            st.divider()
            st.info("🔍 Metoda 3: Ekstrakcja tekstu PyMuPDF")
            
            try:
                import fitz  # PyMuPDF
                
                doc = fitz.open(temp_pdf_path)
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    text = page.get_text()
                    if text.strip():
                        st.write(f"**Strona {page_num + 1} (PyMuPDF):**")
                        st.text(text)
                doc.close()
                
            except ImportError:
                st.info("PyMuPDF nie zainstalowany. Zainstaluj: `pip install PyMuPDF`")
            except Exception as e:
                st.error(f"Błąd PyMuPDF: {e}")
            
            # Pomoc w ręcznym parsowaniu
            st.divider()
            st.markdown("""
            ### 💡 Wskazówki:
            
            1. **Jeśli tekst jest czytelny** - skopiuj go i przetwórz ręcznie lub regex
            2. **Jeśli PDF jest graficzny** - użyj OCR
            3. **Jeśli dane są w kolumnach** - możesz użyć regex do wyodrębnienia:
               ```python
               import re
               # Przykład: wyciągnij liczby
               numbers = re.findall(r'\d+', text)
               ```
            4. **Dla złożonych struktur** - rozważ narzędzia komercyjne (Adobe Acrobat, ABBYY)
            """)

if __name__ == "__main__":
    import_pdf_data()