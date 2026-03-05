import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import os
import re
import subprocess

# --- AYARLAR ---
BASE_URL = "https://dizipal.bar"
TARGET_PATH = "/filmler/" 
OUTPUT_FILE = "filmler.json"

def get_chrome_version():
    """Sistemdeki Chrome versiyonunu tespit eder"""
    try:
        output = subprocess.check_output(['google-chrome', '--version']).decode('utf-8')
        version = re.search(r'Google Chrome (\d+)', output).group(1)
        return int(version)
    except Exception:
        return None

def scrape_filmler():
    # Chrome versiyonunu al ve sürücüyü ona göre başlat
    chrome_version = get_chrome_version()
    print(f"Tespit edilen Chrome Versiyonu: {chrome_version}")

    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--headless') # GitHub Actions için şart

    # UYUMSUZLUK BURADA ÇÖZÜLÜYOR: version_main eklendi
    try:
        driver = uc.Chrome(options=options, version_main=chrome_version)
    except Exception as e:
        print(f"Sürücü başlatılamadı, alternatif deneniyor: {e}")
        driver = uc.Chrome(options=options) # Hata olursa varsayılanı dene

    results = {}
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                results = json.load(f)
        except: pass

    try:
        print("Giriş yapılıyor...")
        driver.get(BASE_URL)
        time.sleep(12) # Cloudflare için geniş süre

        page_num = 1
        while page_num <= 50:
            current_url = f"{BASE_URL}{TARGET_PATH}" if page_num == 1 else f"{BASE_URL}{TARGET_PATH}page/{page_num}/"
            print(f"\n--- Sayfa {page_num} Taranıyor: {current_url} ---")
            
            driver.get(current_url)
            time.sleep(5)

            items = driver.find_elements(By.CLASS_NAME, "post-item")
            if not items:
                print("Sayfa boş. İşlem bitti.")
                break

            for i in range(len(items)):
                # Sayfa her değiştiğinde listeyi tazele (StaleElement önlemi)
                fresh_items = driver.find_elements(By.CLASS_NAME, "post-item")
                item = fresh_items[i]
                
                try:
                    anchor = item.find_element(By.TAG_NAME, "a")
                    title = anchor.get_attribute("title")
                    link = anchor.get_attribute("href")
                    
                    # Key oluşturma
                    key = title.replace(" ", "-").replace(":", "").replace("'", "")

                    if key in results and results[key].get("link"):
                        continue

                    print(f"  > İşleniyor: {title}")
                    
                    # Detay sayfasına git (Aynı sekmede gitmek daha az RAM harcar)
                    driver.get(link)
                    time.sleep(4)

                    # --- TIKLAMA MANTIĞI ---
                    # Player yüklenmesi için tıklanması gereken butonları bul
                    try:
                        # Siteye göre bu selector değişebilir (Genelde .play-button veya #video-yükle)
                        click_targets = driver.find_elements(By.CSS_SELECTOR, ".play-button, .player-trigger, [id*='play']")
                        if click_targets:
                            click_targets[0].click()
                            time.sleep(3)
                    except: pass

                    # Embed iframe yakala
                    try:
                        iframe = WebDriverWait(driver, 15).until(
                            EC.presence_of_element_located((By.TAG_NAME, "iframe"))
                        )
                        embed_src = iframe.get_attribute("src")

                        results[key] = {
                            "isim": title,
                            "link": embed_src
                        }

                        # Anlık kaydet
                        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                            json.dump(results, f, ensure_ascii=False, indent=2)
                    except:
                        print(f"    ! Iframe bulunamadı: {title}")

                    # Listeye geri dön
                    driver.back()
                    time.sleep(3)

                except Exception as e:
                    print(f"    ! Hata: {e}")
                    driver.get(current_url) # Hata olursa sayfayı yenile
                    time.sleep(3)

            page_num += 1

    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_filmler()
