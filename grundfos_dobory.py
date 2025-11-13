import os
import time
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# By.NAME było importowane dwa razy, usunięto duplikat
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ---- Załaduj dane z .env ----
load_dotenv()
USERNAME = os.getenv("LOGIN_EMAIL")
PASSWORD = os.getenv("LOGIN_PASS")

if not USERNAME or not PASSWORD:
    raise SystemExit("Brakuje LOGIN_EMAIL lub LOGIN_PASS w pliku .env")

# ---- Konfiguracja WebDrivera ----
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-gpu")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 20)  # globalny timeout 20s

try:
    url = ("https://login.grundfos.com/grundfosauth.onmicrosoft.com/"
           "b2c_1a_signingf/oauth2/v2.0/authorize?client_id=54f0a982-d4a8-491a-8d6e-d2ef35e6858e"
           "&nonce=&redirect_uri=https://www.grundfos.com/authenticate.html&response_type=code"
           "&response_mode=form_post&scope=offline_access+openid+https://GrundfosAuth.onmicrosoft.com/API/General"
           "+https://GrundfosAuth.onmicrosoft.com/API/GPI&ui_locales=pl&style=ux"
           "&state=https%3A%2F%2Fwww.grundfos.com%2Fpl%2Fmygrundfos%2Flist-price-and-availability")

    driver.get(url)

    # --- KROK 1: Obsługa Ciasteczek (Cookie Banner) ---
    # Musimy zamknąć baner, aby odsłonić formularz logowania.
    print("Szukam okna z ciasteczkami...")
    try:
        # Typowy selektor dla przycisku 'Akceptuj wszystko' w Cookiebot
        # ID: CybotCookiebotDialogBodyLevelButtonAccept lub XPATH //button[@title='Akceptuj wszystkie']
        cookie_accept_button = wait.until(
            EC.element_to_be_clickable((By.ID, "CybotCookiebotDialogBodyLevelButtonAccept"))
        )
        cookie_accept_button.click()
        print("Kliknięto 'Akceptuję' ciasteczka.")
        time.sleep(1) # Krótka pauza na zniknięcie banera
    except TimeoutException:
        print("Baner ciasteczek nie znaleziony lub już zamknięty. Kontynuuję.")
        pass # Jeśli baner nie występuje, po prostu kontynuuj


    # --- KROK 2: Czekaj na pole E-MAIL i wpisz login ---
    try:
        # Używamy By.ID "i0116", który jest bardziej uniwersalny dla MS login
        email_input = wait.until(
            EC.presence_of_element_located((By.ID, "i0116"))
        )
        email_input.clear()
        email_input.send_keys(USERNAME)
        print("Wpisano email.")
    except TimeoutException:
        print("BŁĄD: Pola e-mail (ID: i0116) nie znaleziono w wymaganym czasie.")
        print("Aktualny URL:", driver.current_url)
        # Zapisz HTML do debugowania
        with open("debug_email_fail.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        raise

    # przycisk "Next" / "Dalej" (ID: idSIButton9 jest uniwersalne dla MS)
    try:
        next_btn = driver.find_element(By.ID, "idSIButton9")
        next_btn.click()
        print("Kliknięto 'Dalej'.")
    except NoSuchElementException:
        # Jeśli przycisk nie ma ID, spróbuj wysłać enter
        email_input.submit()


    # --- KROK 3: Czekaj na pole HASŁA ---
    try:
        # Pole hasła w MS login to zazwyczaj ID "i0118"
        pwd_input = wait.until(EC.presence_of_element_located((By.ID, "i0118")))
    except TimeoutException:
        print("BŁĄD: Pole hasła (ID: i0118) nie pojawiło się — możliwe MFA lub inna ścieżka.")
        # Zapisz HTML do debugowania
        with open("debug_pwd_fail.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        raise

    pwd_input.clear()
    pwd_input.send_keys(PASSWORD)

    # przycisk zaloguj
    try:
        signin_btn = driver.find_element(By.ID, "idSIButton9")
        signin_btn.click()
        print("Kliknięto 'Zaloguj się'.")
    except NoSuchElementException:
        pwd_input.submit()

    # --- KROK 4: Opcjonalnie: obsługa "Stay signed in?" ---
    try:
        stay_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "idBtn_Back")) # Przycisk "Nie" / "Back"
        )
        stay_btn.click()
        print("Kliknięto 'Nie' w zapytaniu 'Pozostań zalogowany?'.")
    except TimeoutException:
        pass # Pole nie występuje, kontynuuj


    # --- KROK 5: Czekaj na element potwierdzający zalogowanie ---
    try:
        # Czekaj na przekierowanie do strony z której startowaliśmy
        success_marker = WebDriverWait(driver, 20).until(
             EC.url_contains("/mygrundfos/list-price-and-availability")
        )
        print("\n✅ Zalogowano pomyślnie i przekierowano do pożądanej strony!")
        
        # --- TUTAJ DALEJ TWOJA LOGIKA POBIERANIA DANYCH ---

    except TimeoutException:
        print("\n❌ BŁĄD: Nie znaleziono potwierdzenia zalogowania (brak przekierowania do docelowego URL).")
        print("Aktualny URL:", driver.current_url)
        with open("debug_final_fail.html", "w", encoding="utf-8") as f:
             f.write(driver.page_source)

    # --- Opcjonalne: poczekaj i zakończ ---
    time.sleep(5)

finally:
    driver.quit()import os
import time
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# By.NAME było importowane dwa razy, usunięto duplikat
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ---- Załaduj dane z .env ----
load_dotenv()
USERNAME = os.getenv("LOGIN_EMAIL")
PASSWORD = os.getenv("LOGIN_PASS")

if not USERNAME or not PASSWORD:
    raise SystemExit("Brakuje LOGIN_EMAIL lub LOGIN_PASS w pliku .env")

# ---- Konfiguracja WebDrivera ----
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-gpu")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 20)  # globalny timeout 20s

try:
    url = ("https://login.grundfos.com/grundfosauth.onmicrosoft.com/"
           "b2c_1a_signingf/oauth2/v2.0/authorize?client_id=54f0a982-d4a8-491a-8d6e-d2ef35e6858e"
           "&nonce=&redirect_uri=https://www.grundfos.com/authenticate.html&response_type=code"
           "&response_mode=form_post&scope=offline_access+openid+https://GrundfosAuth.onmicrosoft.com/API/General"
           "+https://GrundfosAuth.onmicrosoft.com/API/GPI&ui_locales=pl&style=ux"
           "&state=https%3A%2F%2Fwww.grundfos.com%2Fpl%2Fmygrundfos%2Flist-price-and-availability")

    driver.get(url)

    # --- KROK 1: Obsługa Ciasteczek (Cookie Banner) ---
    # Musimy zamknąć baner, aby odsłonić formularz logowania.
    print("Szukam okna z ciasteczkami...")
    try:
        # Typowy selektor dla przycisku 'Akceptuj wszystko' w Cookiebot
        # ID: CybotCookiebotDialogBodyLevelButtonAccept lub XPATH //button[@title='Akceptuj wszystkie']
        cookie_accept_button = wait.until(
            EC.element_to_be_clickable((By.ID, "CybotCookiebotDialogBodyLevelButtonAccept"))
        )
        cookie_accept_button.click()
        print("Kliknięto 'Akceptuję' ciasteczka.")
        time.sleep(1) # Krótka pauza na zniknięcie banera
    except TimeoutException:
        print("Baner ciasteczek nie znaleziony lub już zamknięty. Kontynuuję.")
        pass # Jeśli baner nie występuje, po prostu kontynuuj


    # --- KROK 2: Czekaj na pole E-MAIL i wpisz login ---
    try:
        # Używamy By.ID "i0116", który jest bardziej uniwersalny dla MS login
        email_input = wait.until(
            EC.presence_of_element_located((By.ID, "i0116"))
        )
        email_input.clear()
        email_input.send_keys(USERNAME)
        print("Wpisano email.")
    except TimeoutException:
        print("BŁĄD: Pola e-mail (ID: i0116) nie znaleziono w wymaganym czasie.")
        print("Aktualny URL:", driver.current_url)
        # Zapisz HTML do debugowania
        with open("debug_email_fail.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        raise

    # przycisk "Next" / "Dalej" (ID: idSIButton9 jest uniwersalne dla MS)
    try:
        next_btn = driver.find_element(By.ID, "idSIButton9")
        next_btn.click()
        print("Kliknięto 'Dalej'.")
    except NoSuchElementException:
        # Jeśli przycisk nie ma ID, spróbuj wysłać enter
        email_input.submit()


    # --- KROK 3: Czekaj na pole HASŁA ---
    try:
        # Pole hasła w MS login to zazwyczaj ID "i0118"
        pwd_input = wait.until(EC.presence_of_element_located((By.ID, "i0118")))
    except TimeoutException:
        print("BŁĄD: Pole hasła (ID: i0118) nie pojawiło się — możliwe MFA lub inna ścieżka.")
        # Zapisz HTML do debugowania
        with open("debug_pwd_fail.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        raise

    pwd_input.clear()
    pwd_input.send_keys(PASSWORD)

    # przycisk zaloguj
    try:
        signin_btn = driver.find_element(By.ID, "idSIButton9")
        signin_btn.click()
        print("Kliknięto 'Zaloguj się'.")
    except NoSuchElementException:
        pwd_input.submit()

    # --- KROK 4: Opcjonalnie: obsługa "Stay signed in?" ---
    try:
        stay_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "idBtn_Back")) # Przycisk "Nie" / "Back"
        )
        stay_btn.click()
        print("Kliknięto 'Nie' w zapytaniu 'Pozostań zalogowany?'.")
    except TimeoutException:
        pass # Pole nie występuje, kontynuuj


    # --- KROK 5: Czekaj na element potwierdzający zalogowanie ---
    try:
        # Czekaj na przekierowanie do strony z której startowaliśmy
        success_marker = WebDriverWait(driver, 20).until(
             EC.url_contains("/mygrundfos/list-price-and-availability")
        )
        print("\n✅ Zalogowano pomyślnie i przekierowano do pożądanej strony!")
        
        # --- TUTAJ DALEJ TWOJA LOGIKA POBIERANIA DANYCH ---

    except TimeoutException:
        print("\n❌ BŁĄD: Nie znaleziono potwierdzenia zalogowania (brak przekierowania do docelowego URL).")
        print("Aktualny URL:", driver.current_url)
        with open("debug_final_fail.html", "w", encoding="utf-8") as f:
             f.write(driver.page_source)

    # --- Opcjonalne: poczekaj i zakończ ---
    time.sleep(5)

finally:
    driver.quit()