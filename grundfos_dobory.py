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
wait = WebDriverWait(driver, 7)  # globalny timeout 7s

try:
    url = ("https://login.grundfos.com/grundfosauth.onmicrosoft.com/"
           "b2c_1a_signingf/oauth2/v2.0/authorize?client_id=54f0a982-d4a8-491a-8d6e-d2ef35e6858e"
           "&nonce=&redirect_uri=https://www.grundfos.com/authenticate.html&response_type=code"
           "&response_mode=form_post&scope=offline_access+openid+https://GrundfosAuth.onmicrosoft.com/API/General"
           "+https://GrundfosAuth.onmicrosoft.com/API/GPI&ui_locales=pl&style=ux"
           "&state=https%3A%2F%2Fwww.grundfos.com%2Fpl%2Fmygrundfos%2Flist-price-and-availability")

    driver.get(url)
    
    # Spróbuj automatycznie kliknąć przycisk akceptacji cookies
    cookies_clicked = False
    cookie_selectors = [
        (By.XPATH, "//button[contains(text(),'Akceptuj') or contains(text(),'Zgadzam się') or contains(text(),'Accept') or contains(text(),'OK') or contains(text(),'Potwierdź') or contains(text(),'Accept all') or contains(text(),'accept')]"),
        (By.ID, "acceptAllBtn"),
        (By.CSS_SELECTOR, "button#acceptAllBtn, button.cookie-accept, button[aria-label*='akceptuj'], button[aria-label*='accept']")
    ]
    for by, sel in cookie_selectors:
        try:
            cookie_btn = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((by, sel)))
            try:
                cookie_btn.click()
            except Exception:
                driver.execute_script("arguments[0].click();", cookie_btn)
            print(f"Automatycznie kliknięto przycisk cookies: {sel}")
            cookies_clicked = True
            break
        except Exception:
            continue
    if not cookies_clicked:
        print("Nie znaleziono przycisku cookies lub nie kliknięto automatycznie. Możesz zaakceptować ręcznie.")
    # Poczekaj na zniknięcie overlay po akceptacji
    try:
        WebDriverWait(driver, 5).until(EC.invisibility_of_element_located((By.CLASS_NAME, "cookieOverlay")))
    except Exception:
        pass
    time.sleep(1)
    # Diagnostyka: zapisz HTML po próbie kliknięcia cookies (zawsze)
    with open("debug_after_cookies.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print("Zapisano HTML po próbie kliknięcia cookies do debug_after_cookies.html")

    # --- PRZYKŁADOWE: czekaj na pole e-mail i wpisz login ---
    # Użyj bezpośrednich, pewnych selektorów z debug_after_cookies.html
    try:
        email_input = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "signInName")))
    except TimeoutException:
        print("Pole e-mail nieaktywne (id='signInName'). Debug HTML:")
        print(driver.page_source[:2000])
        raise
    email_input.clear()
    email_input.send_keys(USERNAME)

    try:
        pwd_input = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "password")))
    except TimeoutException:
        print("Pole hasła nieaktywne (id='password'). Debug HTML:")
        print(driver.page_source[:2000])
        raise
    pwd_input.clear()
    pwd_input.send_keys(PASSWORD)

    try:
        signin_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "next")))
        # Usuwamy atrybut 'disabled' jeśli występuje
        driver.execute_script("arguments[0].removeAttribute('disabled');", signin_btn)
        signin_btn.click()
        print("Kliknięto przycisk logowania (id='next').")
    except Exception:
        print("Nie znaleziono przycisku logowania (id='next'). Debug HTML:")
        print(driver.page_source[:2000])
        raise

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
    # Pozostaw okno otwarte do ręcznego zamknięcia
    input("Naciśnij Enter, aby zamknąć przeglądarkę...")
    driver.quit()

    # --- Opcjonalne: poczekaj i zakończ ---
    time.sleep(5)

finally:
    driver.quit()