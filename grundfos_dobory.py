from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import subprocess

# Ustawienia dla obsługi cookies i retry
COOKIE_TOTAL_TIMEOUT = 300  # łączny czas (s) na powtarzanie prób akceptacji
COOKIE_RETRY_INTERVAL = 5  # interwał między kolejnymi próbami (s)
COOKIE_VERIFY_TIMEOUT = 10  # czas (s) na weryfikację, że baner zniknął po kliknięciu
WAIT_FOR_MANUAL_CONFIRM = False  # jeśli True, poprosi użytkownika o potwierdzenie ręczne

# Słowa kluczowe używane przy weryfikacji i diagnostyce
COOKIE_KEYWORDS = ['allow', 'accept', 'akcept', 'zgadz', 'cookie', 'consent', 'gdpr', 'privacy']

# Wyczyść ekran terminala
os.system('cls' if os.name == 'nt' else 'clear')
# Fallback: jeśli powyższe nie działa w PowerShell/integrowanym terminalu VSCode, spróbuj wywołać Clear-Host
if os.name == 'nt':
    try:
        subprocess.run(["powershell", "-Command", "Clear-Host"], check=False, shell=False)
    except Exception:
        pass

# Parametry do wpisania
PRZEPLYW = "17"  # m3/h
WYSOKOSC = "25"  # m

# Dodaj opcje Chrome
chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_argument('--start-maximized')

print("Uruchamiam Chrome...")

# ---------------------------------------------------------------------------
# Funkcje pomocnicze i dokumentacja (po polsku)
#
# Ten skrypt automatyzuje otwarcie strony Grundfos i próbuje zaakceptować
# baner cookies/consent. Niestety strony często mają różną strukturę DOM
# (czasem elementy znajdują się w iframe, mają niestandardowe teksty lub atrybuty),
# więc implementujemy heurystyki: kilka XPathów, skan widocznych przycisków,
# oraz kliknięcie przez JavaScript jako fallback.
#
# Wejście/wyjście:
# - wejście: obiekt `driver` (Selenium WebDriver) oraz opcjonalny `timeout`.
# - wyjście: funkcja zwraca True jeśli wykonała kliknięcie akceptujące cookies,
#   lub False jeśli nie znalazła/nie mogła kliknąć takiego elementu.
#
# Tryby błędów / zachowanie awaryjne:
# - funkcja nie przerywa działania skryptu jeśli nie znajdzie przycisku;
#   zwraca False i pozostawia stronę otwartą do ręcznej interwencji.
# - dodatkowo dostępna jest funkcja diagnostyczna `debug_cookie_elements`
#   która wypisuje podejrzane elementy gdy automatyczne kliknięcie nie zadziała.
# ---------------------------------------------------------------------------

def accept_cookies(driver, timeout=5):
    """Spróbuj automatycznie zaakceptować okno cookies.

    Wykorzystuje kilka heurystyk:
    - kilka XPathów dopasowanych case-insensitive do tekstów typu 'allow', 'accept',
      'allow selection'
    - przeszukanie widocznych przycisków i dopasowanie tekstu (polskie/angielskie)
    - jeśli zwykłe `click()` nie działa, próba kliknięcia przez JavaScript

    Zwraca True jeżeli wykonano kliknięcie, w przeciwnym razie False.
    """

    # Rozszerzona lista wzorców (ang./pl.) do wyszukania przycisków
    patterns = [
        'allow selection', 'allow selections', 'allow', 'accept', 'accept selection', 'accept selections',
        'accept all', 'akceptuj', 'zgadzam', 'akceptacja'
    ]

    # przygotuj XPathy bazujące na wzorcach (case-insensitive)
    xpaths = [
        f"//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{p}') ]" for p in patterns
    ]
    # dodatkowe selektory (aria-label, linki, role=button, span/button combination)
    xpaths += [
        f"//button[contains(translate(normalize-space(@aria-label), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{p}')]" for p in patterns
    ]
    xpaths += [f"//a[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{p}')]" for p in patterns]
    xpaths += [f"//*[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{p}') and (@role='button' or name() = 'button' or name() = 'a')]" for p in patterns]


def _verify_cookie_banner_gone(driver, keywords, timeout=10, screenshot_prefix='cookie'):
    """Po kliknięciu spróbuj potwierdzić, że baner cookies zniknął.

    - zapisuje zrzuty ekranu (przed/po/timeout) z prefiksem `screenshot_prefix`.
    - czeka do `timeout` sekund na brak widocznych elementów zawierających słowa kluczowe.
    Zwraca True jeśli baner zniknął, w przeciwnym razie False.
    """
    import datetime
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    checks = " or ".join([f"contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{k}')" for k in keywords])
    indicator = f"//*[{checks}]"
    try:
        try:
            driver.save_screenshot(f"{screenshot_prefix}_before_{ts}.png")
        except Exception:
            pass
        for _ in range(timeout):
            try:
                els = driver.find_elements(By.XPATH, indicator)
                visible = [e for e in els if e.is_displayed()]
            except Exception:
                visible = []
            if not visible:
                try:
                    driver.save_screenshot(f"{screenshot_prefix}_after_{ts}.png")
                except Exception:
                    pass
                return True
            time.sleep(1)
        try:
            driver.save_screenshot(f"{screenshot_prefix}_timeout_{ts}.png")
        except Exception:
            pass
    except Exception:
        pass
    return False
    # wielokrotne próby (retry) - strony często ładują elementy z opóźnieniem
    attempts = 3
    for attempt in range(attempts):
        for xp in xpaths:
            try:
                el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xp)))
                try:
                    el.click()
                    print(f"✓ Kliknięto element cookie (XPath): {xp}")
                    time.sleep(1)
                    if _verify_cookie_banner_gone(driver, patterns, timeout=10, screenshot_prefix='cookie'):
                        print("✓ Potwierdzono zniknięcie banera po kliknięciu")
                        return True
                    else:
                        print("⚠ Kliknięcie nie usunęło banera, kontynuuję próby...")
                except Exception as e:
                    print(f"⚠ Błąd podczas klikania elementu (XPath): {e} - spróbuję kliknąć przez JS")
                    try:
                        driver.execute_script("arguments[0].click();", el)
                        print(f"✓ Kliknięto element cookie przez JS (XPath): {xp}")
                        time.sleep(1)
                        if _verify_cookie_banner_gone(driver, patterns, timeout=10, screenshot_prefix='cookie'):
                            print("✓ Potwierdzono zniknięcie banera po kliknięciu przez JS")
                            return True
                        else:
                            print("⚠ Kliknięcie przez JS nie usunęło banera, kontynuuję próby...")
                    except Exception as e2:
                        print(f"⚠ Nie udało się kliknąć przez JS: {e2}")
            except Exception:
                # nie znaleziono elementu w bieżącym kontekście - spróbuj w iframe'ach
                pass

        # próba w iframe'ach: przejdź przez wszystkie iframe i spróbuj tych samych xpathów
        iframes = driver.find_elements(By.TAG_NAME, 'iframe')
        for i, fr in enumerate(iframes):
            try:
                driver.switch_to.frame(fr)
                for xp in xpaths:
                    try:
                        elems = driver.find_elements(By.XPATH, xp)
                        for el in elems:
                            try:
                                if not el.is_displayed():
                                    continue
                                try:
                                    el.click()
                                    print(f"✓ Kliknięto element cookie wewnątrz iframe (index {i}) (XPath): {xp}")
                                    time.sleep(1)
                                    if _verify_cookie_banner_gone(driver, patterns, timeout=10, screenshot_prefix=f'cookie_iframe_{i}'):
                                        print("✓ Potwierdzono zniknięcie banera po kliknięciu wewnątrz iframe")
                                        try:
                                            driver.switch_to.default_content()
                                        except Exception:
                                            pass
                                        return True
                                    else:
                                        print("⚠ Kliknięcie wewnątrz iframe nie usunęło banera, kontynuuję próby...")
                                        try:
                                            driver.switch_to.default_content()
                                        except Exception:
                                            pass
                                except Exception:
                                    try:
                                        driver.execute_script("arguments[0].click();", el)
                                        print(f"✓ Kliknięto element cookie przez JS wewnątrz iframe (index {i}) (XPath): {xp}")
                                        time.sleep(1)
                                        if _verify_cookie_banner_gone(driver, patterns, timeout=10, screenshot_prefix=f'cookie_iframe_{i}'):
                                            print("✓ Potwierdzono zniknięcie banera po kliknięciu przez JS wewnątrz iframe")
                                            try:
                                                driver.switch_to.default_content()
                                            except Exception:
                                                pass
                                            return True
                                        else:
                                            print("⚠ Kliknięcie przez JS wewnątrz iframe nie usunęło banera, kontynuuję próby...")
                                            try:
                                                driver.switch_to.default_content()
                                            except Exception:
                                                pass
                                    except Exception as e3:
                                        print(f"⚠ Nie udało się kliknąć wewnątrz iframe: {e3}")
                            except Exception:
                                pass
                    except Exception:
                        pass
            except Exception:
                pass
            finally:
                try:
                    driver.switch_to.default_content()
                except Exception:
                    pass

        # jeśli nie znaleziono jeszcze, krótka pauza i powtórzenie
        time.sleep(1)

    # Fallback: przeszukaj widoczne przyciski/odnośniki i spróbuj kliknąć bazując na prostej detekcji tekstu
    try:
        buttons = driver.find_elements(By.TAG_NAME, "button")
        links = driver.find_elements(By.TAG_NAME, "a")
        candidates = buttons + links
        for btn in candidates:
            try:
                if not btn.is_displayed():
                    continue
                tekst = (btn.text or '').strip().replace('\n', ' ').lower()
                aria = (btn.get_attribute('aria-label') or '').lower()
                if any(p in tekst for p in ['allow', 'accept', 'akcept', 'zgadz']) or any(p in aria for p in ['allow', 'accept', 'akcept', 'zgadz']):
                    try:
                        btn.click()
                        print(f"✓ Kliknięto dopasowany element (tekst/aria): '{tekst}' / '{aria}'")
                        time.sleep(1)
                        if _verify_cookie_banner_gone(driver, patterns, timeout=10, screenshot_prefix='cookie_candidate'):
                            print("✓ Potwierdzono zniknięcie banera po kliknięciu dopasowanego elementu")
                            return True
                        else:
                            print("⚠ Kliknięcie dopasowanego elementu nie usunęło banera, kontynuuję próby...")
                    except Exception:
                        try:
                            driver.execute_script("arguments[0].click();", btn)
                            print(f"✓ Kliknięto dopasowany element przez JS (tekst/aria): '{tekst}' / '{aria}'")
                            time.sleep(1)
                            if _verify_cookie_banner_gone(driver, patterns, timeout=10, screenshot_prefix='cookie_candidate'):
                                print("✓ Potwierdzono zniknięcie banera po kliknięciu przez JS dopasowanego elementu")
                                return True
                            else:
                                print("⚠ Kliknięcie przez JS dopasowanego elementu nie usunęło banera, kontynuuję próby...")
                        except Exception:
                            pass
            except Exception:
                pass
    except Exception:
        pass

    # jeśli nadal nie zadziałało, uruchom diagnostykę aby wypisać elementy do analizy
    print("⚠ Automatyczne akceptowanie cookies nie powiodło się po kilku próbach. Uruchamiam diagnostykę...")
    try:
        debug_cookie_elements(driver)
    except Exception as e:
        print(f"Błąd podczas diagnostyki: {e}")

    return False


def debug_cookie_elements(driver):
    """Wypisz potencjalne elementy cookies dla diagnostyki (tekst, aria-label, id, class, outerHTML w skrócie)."""
    print("\n--- DIAGNOSTYKA: potencjalne elementy cookie ---")
    try:
        elems = []
        # zbierz przyciski, linki oraz elementy z atrybutami związanymi z cookie/consent
        elems += driver.find_elements(By.TAG_NAME, 'button')
        elems += driver.find_elements(By.TAG_NAME, 'a')
        # elementy z id/class zawierającymi cookie/consent/gdpr
        candidates = driver.find_elements(By.XPATH, "//*[contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'cookie') or contains(translate(@class, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'cookie') or contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'consent') or contains(translate(@class, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'consent') or contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'gdpr') or contains(translate(@class, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'gdpr')]")
        elems += candidates

        seen = set()
        for el in elems:
            try:
                if not el.is_displayed():
                    continue
                txt = el.text.strip().replace('\n', ' ')
                aria = el.get_attribute('aria-label') or ''
                eid = el.get_attribute('id') or ''
                eclass = el.get_attribute('class') or ''
                key = (txt, aria, eid, eclass)
                if key in seen:
                    continue
                seen.add(key)
                outer = el.get_attribute('outerHTML') or ''
                outer_short = (outer[:300] + '...') if len(outer) > 300 else outer
                print(f"TEXT: '{txt}' | ARIA: '{aria}' | id: '{eid}' | class: '{eclass}'\nOUTER: {outer_short}\n")
            except Exception:
                pass

        # sprawdź iframe'y
        iframes = driver.find_elements(By.TAG_NAME, 'iframe')
        if iframes:
            print(f"Znaleziono {len(iframes)} iframe(s) - sprawdzam zawartość iframe'ów dla cookie...")
            for i, fr in enumerate(iframes):
                try:
                    driver.switch_to.frame(fr)
                    sub_buttons = driver.find_elements(By.TAG_NAME, 'button')
                    for sb in sub_buttons:
                        try:
                            if not sb.is_displayed():
                                continue
                            txt = sb.text.strip().replace('\n', ' ')
                            aria = sb.get_attribute('aria-label') or ''
                            eid = sb.get_attribute('id') or ''
                            eclass = sb.get_attribute('class') or ''
                            outer = sb.get_attribute('outerHTML') or ''
                            outer_short = (outer[:300] + '...') if len(outer) > 300 else outer
                            print(f"[iframe {i}] TEXT: '{txt}' | ARIA: '{aria}' | id: '{eid}' | class: '{eclass}'\nOUTER: {outer_short}\n")
                        except Exception:
                            pass
                except Exception:
                    pass
                finally:
                    try:
                        driver.switch_to.default_content()
                    except Exception:
                        pass
    except Exception as e:
        print(f"Błąd diagnostyki: {e}")
    print("--- KONIEC DIAGNOSTYKI ---\n")

try:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(60)
    
    print("Otwieram stronę Grundfos...")
    driver.get("https://product-selection.grundfos.com/advanced-selection?sQcid=2802952038")
    
    print("Strona otwarta!")
    print("Czekam na pojawienie się okna cookies (max 5 sekund)...")
    
    # Spróbuj wykryć okno cookies / przycisk allow/accept i kliknąć automatycznie
    cookie_element = None
    try:
        # Poczekaj krótko na dowolny indykator cookie/allow/accept
        xpath_indicator = (
            "//*[contains(translate(., 'COOKIE', 'cookie'), 'cookie') or "
            "contains(translate(., 'ALLOW', 'allow'), 'allow') or "
            "contains(translate(., 'ACCEPT', 'accept'), 'accept')]"
        )
        cookie_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, xpath_indicator))
        )
        print("✓ Wykryto okno cookies!")
    except Exception:
        print("⚠ Nie wykryto okna cookies w ciągu 5 sekund")

    print("✓ Próba automatycznego zaakceptowania cookies...")

    # Pętla retry: powtarzaj próbę akceptacji dopóki nie zniknie baner lub nie upłynie limit COOKIE_TOTAL_TIMEOUT
    clicked = False
    start_ts = time.time()
    last_exception = None
    attempt = 0
    gone = False
    while time.time() - start_ts < COOKIE_TOTAL_TIMEOUT:
        attempt += 1
        try:
            print(f"Próba #{attempt}: uruchamiam accept_cookies() (timeout wewnętrzny=5s)")
            clicked = accept_cookies(driver, timeout=5)
            if clicked:
                print("✓ Wywołano kliknięcie - weryfikuję czy baner został usunięty...")
                gone = _verify_cookie_banner_gone(driver, COOKIE_KEYWORDS, timeout=COOKIE_VERIFY_TIMEOUT, screenshot_prefix=f'cookie_attempt_{attempt}')
                if gone:
                    print("✓ Potwierdzono zniknięcie banera cookies po kliknięciu")
                    break
                else:
                    print(f"⚠ Kliknięcie nie spowodowało zniknięcia banera (próba #{attempt})")
            else:
                print(f"⚠ accept_cookies() nie znalazł/nie kliknął elementu (próba #{attempt})")
        except Exception as e:
            last_exception = e
            print(f"⚠ Błąd w accept_cookies(): {e} (próba #{attempt})")

        # jeśli nie udało się, poczekaj i spróbuj ponownie
        remaining = COOKIE_TOTAL_TIMEOUT - (time.time() - start_ts)
        if remaining <= 0:
            break
        wait = min(COOKIE_RETRY_INTERVAL, max(1, int(remaining)))
        print(f"Czekam {wait}s przed kolejną próbą...")
        time.sleep(wait)

    if clicked and gone:
        print("✓ Cookies powinny być zaakceptowane automatycznie")
    else:
        print("⚠ Nie udało się automatycznie zaakceptować cookies po wszystkich próbach")
        if WAIT_FOR_MANUAL_CONFIRM:
            input("Proszę ręcznie zamknąć baner cookies, a następnie naciśnij Enter, aby kontynuować...")
        else:
            print(">>> Jeśli okno cookies jest widoczne, skrypt spróbuje dalej - w przeciwnym razie proszę kliknąć ręcznie <<<")
    
    print("\n=== Strona gotowa ===")
    print("Czekam 5 sekund na załadowanie strony...")
    time.sleep(5)
    
except Exception as e:
    print(f"\n❌ Wystąpił błąd: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    try:
        driver.quit()
        print("\n=== Przeglądarka zamknięta ===")
    except:
        pass