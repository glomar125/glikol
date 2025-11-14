import os
import time
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ---- Załaduj dane z .env ----
load_dotenv()  # szuka .env w bieżącym katalogu
USERNAME = os.getenv("LOGIN_EMAIL")
PASSWORD = os.getenv("LOGIN_PASS")

if not USERNAME or not PASSWORD:
    raise SystemExit("Brakuje LOGIN_EMAIL lub LOGIN_PASS w pliku .env")

# ---- Konfiguracja WebDrivera ----
options = webdriver.ChromeOptions()
# jeśli chcesz widzieć okno przeglądarki, usuń argument "--headless=new"
# options.add_argument("--headless=new")   # tryb headless (bez GUI)
options.add_argument("--start-maximized")
options.add_argument("--disable-gpu")
# opcjonalnie: options.add_argument("--no-sandbox")

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

    # --- PRZYKŁADOWE: czekaj na pole e-mail i wpisz login ---
    # Uwaga: musisz dopasować selektory do rzeczywistej strony (ID / NAME / XPATH)
    try:
        email_input = wait.until(EC.presence_of_element_located((By.ID, "signInName")))  # przykład selektora MS
    except TimeoutException:
        # Spróbuj innego selektora lub wydrukuj źródło, by znaleźć pola
        print("Pole e-mail nie znalezione — wypisz źródło strony dla debugowania.")
        print(driver.page_source[:2000])
        raise

    email_input.clear()
    email_input.send_keys(USERNAME)

    # przycisk "Next" / "Dalej" (dopasuj selektor)
    try:
        next_btn = driver.find_element(By.ID, "idSIButton9")  # przykład dla MS login
        next_btn.click()
    except NoSuchElementException:
        # inna wersja strony — spróbuj przycisku typu submit
        email_input.submit()

    # --- czekaj na pole hasła ---
    try:
        pwd_input = wait.until(EC.presence_of_element_located((By.NAME, "passwd")))
    except TimeoutException:
        print("Pole hasła nie pojawiło się — możliwe przekierowanie / MFA / różna wersja strony.")
        raise

    pwd_input.clear()
    pwd_input.send_keys(PASSWORD)

    # przycisk zaloguj (dopasuj selektor)
    try:
        signin_btn = driver.find_element(By.ID, "idSIButton9")
        signin_btn.click()
    except NoSuchElementException:
        pwd_input.submit()

    # --- opcjonalnie: obsługa "Stay signed in?" ---
    try:
        stay_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "idBtn_Back"))
        )
        # jeśli występuje: kliknij "No" (lub "Tak" w zależności od logiki)
        # stay_btn.click()
    except TimeoutException:
        # nie ma takiego pola, OK
        pass

    # --- czekaj na przekierowanie / element potwierdzający zalogowanie ---
    try:
        # przykład: czekaj na element, który pojawia się po udanym logowaniu
        success_marker = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "selector_po_zalogowaniu"))
        )
        print("Zalogowano pomyślnie!")
    except TimeoutException:
        print("Nie znaleziono potwierdzenia zalogowania. Może wymagane MFA lub inna ścieżka.")
        # dla debugowania wypisz aktualny URL:
        print("Aktualny URL:", driver.current_url)
        # możesz też zapisać HTML:
        with open("debug_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)

    # --- Opcjonalne: poczekaj i zakończ ---
    time.sleep(5)

finally:
    driver.quit()