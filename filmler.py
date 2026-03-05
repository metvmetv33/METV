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
    try:
        output = subprocess.check_output(['google-chrome', '--version']).decode('utf-8')
        version = re.search(r'Google Chrome (\d+)', output).group(1)
        return int(version)
    except Exception:
        return None

def scrape_filmler():
    chrome_version = get_chrome_version()
    print(f"Tespit edilen Chrome Versiyonu: {chrome_version}")

    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # Pencere boyutu Cloudflare için önemlidir
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--start-maximized')

    try:
        driver = uc.Chrome(options=options, version_main=chrome_version, headless=False) # xvfb kullanıldığı için headless=False daha güvenli
    except Exception as e:
        print(f"Sürücü hatası: {e}")
        return

    results = {}
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                results = json.load(f)
        except: pass

    try:
        print("Giriş yapılıyor ve Cloudflare bekleniyor...")
        driver.get(BASE_URL)
        time.sleep(15) # Ana sayfada iyice bekle

        page_num = 1
        while page_num <= 50:
            current_url = f"{BASE_URL}{TARGET_PATH}" if page_num == 1 else f"{BASE_URL}{TARGET_PATH}page/{page_num}/"
            print(f"\n--- Sayfa {page_num} Taranıyor ---")
            
            driver.get(current_url)
            time.sleep(7)

            # ESNEK SEÇİCİ: 'post-item' bulamazsa link içeren article veya div'leri dene
            items = driver.find_elements(By.CSS_SELECTOR, ".post-item, article, .video-block")
            
            if not items:
                # Sayfa kaynağını kontrol et (Hata ayıklama için)
                if "Cloudflare" in driver.page_source:
                    print("Hala Cloudflare engelindeyiz, süre uzatılıyor...")
                    time.sleep(20)
                    continue
                print("İçerik bulunamadı. Yapı değişmiş olabilir.")
                break

            found_links = []
            for item in items:
                try:
                    anchor = item.find_element(By.TAG_NAME, "a")
                    link = anchor.get_attribute("href")
                    title = anchor.get_attribute("title") or anchor.text
                    if link and "/film/" in link or f"{BASE_URL}/" in link:
                        found_links.append({"title": title, "url": link})
                except: continue

            # Tekilleştir
            unique_links = {v['url']: v for v in found_links}.values()
            print(f"Bulunan film sayısı: {len(unique_links)}")

            for content in unique_links:
                key = content['url'].split('/')[-2]
                if key in results: continue

                try:
                    print(f"  > Detay çekiliyor: {content['title']}")
                    driver.get(content['url'])
                    time.sleep(5)

                    # Sayfayı biraz aşağı kaydır (Tetikleme için)
                    driver.execute_script("window.scrollTo(0, 500);")
                    time.sleep(2)

                    # Player Butonuna Tıkla
                    try:
                        # Farklı buton tiplerini dene
                        btns = driver.find_elements(By.CSS_SELECTOR, "div.play-button, .player-trigger, #play-video")
                        if btns:
                            driver.execute_script("arguments[0].click();", btns[0])
                            time.sleep(3)
                    except: pass

                    # Iframe'i Yakala
                    iframes = driver.find_elements(By.TAG_NAME, "iframe")
                    embed_src = ""
                    for f in iframes:
                        src = f.get_attribute("src")
                        if "embed" in src or "player" in src or "m3u8" in src:
                            embed_src = src
                            break
                    
                    if embed_src:
                        results[key] = {
                            "isim": content['title'],
                            "link": embed_src,
                            "kaynak": content['url']
                        }
                        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                            json.dump(results, f, ensure_ascii=False, indent=2)
                    else:
                        print("    ! Embed bulunamadı.")

                except Exception as e:
                    print(f"    ! Hata: {e}")

            page_num += 1

    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_filmler()
