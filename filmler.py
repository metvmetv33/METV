import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import os

# --- AYARLAR ---
BASE_URL = "https://dizipal.bar"
# Burayı değiştirdik: Site yapısına göre doğrudan /filmler/ kullanıyoruz
TARGET_PATH = "/filmler/" 
OUTPUT_FILE = "filmler.json"

def scrape_filmler():
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--headless') # GitHub Actions için headless önemli

    results = {}
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                results = json.load(f)
        except: pass

    driver = uc.Chrome(options=options)

    try:
        print("Giriş yapılıyor...")
        driver.get(BASE_URL)
        time.sleep(10) # CF Geçişi

        page_num = 1
        max_pages = 50 # Güvenlik sınırı

        while page_num <= max_pages:
            # URL Oluşturma: 1. sayfa farklı, sonrakiler farklı yapıda olabilir
            if page_num == 1:
                current_url = f"{BASE_URL}{TARGET_PATH}"
            else:
                current_url = f"{BASE_URL}{TARGET_PATH}page/{page_num}/"

            print(f"\n--- Sayfa {page_num} Taranıyor: {current_url} ---")
            driver.get(current_url)
            time.sleep(5)

            # Sayfada film var mı kontrolü
            items = driver.find_elements(By.CLASS_NAME, "post-item")
            if not items:
                print("Bu sayfada içerik bulunamadı veya site bitti.")
                break

            # Sayfadaki her filmi işle
            for i in range(len(items)):
                # Sayfa yenilendiği için elementleri her seferinde tekrar bulmalıyız (StaleElement hatası almamak için)
                current_items = driver.find_elements(By.CLASS_NAME, "post-item")
                item = current_items[i]
                
                try:
                    anchor = item.find_element(By.TAG_NAME, "a")
                    title = anchor.get_attribute("title")
                    link = anchor.get_attribute("href")
                    
                    # Başlık temizleme ve kontrol
                    from filmler import clean_key # Eğer fonksiyonu buraya taşıdıysan
                    key = title.replace(" ", "-") # Basit key

                    if key in results:
                        continue

                    print(f"  > Detay: {title}")
                    
                    # Detay sayfasına git
                    driver.execute_script("window.open('');") # Yeni sekme aç
                    driver.switch_to.window(driver.window_handles[1])
                    driver.get(link)
                    time.sleep(3)

                    # Player'ı tetikle (Tıklama gerekiyorsa)
                    try:
                        # Bazı sitelerde iframe direkt gelmez, play butonuna basmak gerekir
                        play_btn = driver.find_element(By.CSS_SELECTOR, ".play-button, .player-trigger")
                        play_btn.click()
                        time.sleep(2)
                    except: pass

                    # Embed linkini (iframe) yakala
                    iframe = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "iframe"))
                    )
                    embed_src = iframe.get_attribute("src")

                    results[key] = {
                        "isim": title,
                        "link": embed_src
                    }

                    # Dosyayı her başarılı çekimde güncelle
                    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                        json.dump(results, f, ensure_ascii=False, indent=2)

                    # Sekmeyi kapat ve ana sayfaya dön
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])

                except Exception as e:
                    if len(driver.window_handles) > 1:
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                    print(f"Hata: {e}")

            page_num += 1

    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_filmler()
