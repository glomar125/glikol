from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
import time

# Utworzenie przeglądarki Firefox
driver = webdriver.Firefox()

try:
    # Otworzenie pustej strony
    driver.get("about:blank")
    
    # Wstawienie tekstu "hello" do strony
    driver.execute_script('document.body.innerHTML = "<h1>hello</h1>"')
    
    # Czekamy 57 sekund
    time.sleep(7)

finally:
    # Zamknięcie przeglądarki
    driver.quit()
