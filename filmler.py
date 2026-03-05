import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import re
import subprocess
import os
import html

# --- AYARLAR ---
BASE_URL = "https://dizipal.bar"
PLATFORM_SLUG = "filmler"
OUTPUT_FILE = "filmler.json"

def get_chrome_version():
    try:
        output = subprocess.check_output(['google-chrome', '--version']).decode('utf-8')
        version = re.search(r'Google Chrome (\d+)', output).group(1)
        return int(version)
    except:
        return None

def clean_key(text):
    text = html.unescape(text)
    text = re.sub(r'[\s\:\,\'’"”]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')

def get_full_res_image(srcset):
    if not srcset: return ""
    links = [s.strip().split(' ')[0] for s in srcset.split(',')]
    return links[-1] if links else ""

def scrape_hbomax():
    version = get_chrome_version()
    print(f"Sistem Chrome Versiyonu: {version}")

    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--lang=tr')

    results = {}
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                results = json.load(f)
        except: pass

    driver = uc.Chrome(options=options, version_main=version)

    try:
        print("Cloudflare geçişi bekleniyor...")
        driver.get(BASE_URL)
        time.sleep(10) 

        page_num = 1
        while True:
            platform_url = f"{BASE_URL}/platform/{PLATFORM_SLUG}/page/{page_num}/"
            print(f"\n--- Sayfa {page_num} Taranıyor ---")
            driver.get(platform_url)
            time.sleep(4)

            if "Sayfa bulunamadı" in driver.title or len(driver.find_elements(By.CLASS_NAME, "post-item")) == 0:
                print("İşlem tamamlandı.")
                break

            items = driver.find_elements(By.CLASS_NAME, "post-item")
            page_contents = []
            
            for item in items:
                try:
                    anchor = item.find_element(By.TAG_NAME, "a")
                    img = item.find_element(By.TAG_NAME, "img")
                    title = anchor.get_attribute("title")
                    key = clean_key(title)

                    if key in results and results[key].get("link"):
                        continue

                    page_contents.append({
                        "title": title,
                        "url": anchor.get_attribute("href"),
                        "img": get_full_res_image(img.get_attribute("srcset")) or img.get_attribute("src"),
                        "key": key
                    })
                except: continue
            
            for content in page_contents:
                try:
                    print(f"> Çekiliyor: {content['title']}")
                    driver.get(content['url'])
                    time.sleep(3)

                    # --- TIKLAMA VE EMBED YAKALAMA ---
                    # Eğer player üzerinde 'tıkla' uyarısı varsa butona tıkla
                    try:
                        # Video yükleme butonuna benzeyen elementleri ara
                        play_button = driver.find_element(By.CSS_SELECTOR, ".play-button, .player-loader, #video-yükle")
                        play_button.click()
                        time.sleep(2)
                    except:
                        pass # Buton yoksa veya zaten yüklüyse devam et

                    # Iframe'i bekle ve çek
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
                    iframe = driver.find_element(By.TAG_NAME, "iframe")
                    embed_link = iframe.get_attribute("src")

                    results[content['key']] = {
                        "isim": content['title'],
                        "resim": content['img'],
                        "link": embed_link
                    }

                    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                        json.dump(results, f, ensure_ascii=False, indent=2)

                except Exception as e:
                    print(f"Hata: {content['title']} -> {e}")

            page_num += 1

    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_hbomax()
