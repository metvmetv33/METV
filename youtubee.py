import requests
import re
import sys
import urllib.parse
import urllib3
import time
import os

# Uyarıları kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ayarlar
JSON_URL = "https://raw.githubusercontent.com/metvmetv33/METV/refs/heads/main/muomube.json"
MAX_RETRIES = 5 # Her kanal için deneme sayısı (isteğe göre 10 yapabilirsin)
WAIT_TIME = 10

def get_streams():
    # 1. JSON Verisini Çek
    try:
        print("Kanal listesi indiriliyor...")
        channels = requests.get(JSON_URL).json()
    except Exception as e:
        sys.exit(f"JSON listesi alınamadı: {e}")

    for channel in channels:
        name = channel.get("name").replace(" ", "_") # Klasör adı için boşlukları temizle
        live_url = channel.get("url").strip()
        
        print(f"\n--- {name} İşleniyor ---")
        
        # Klasör oluştur
        if not os.path.exists(name):
            os.makedirs(name)

        success = False
        for attempt in range(1, MAX_RETRIES + 1):
            print(f"Deneme {attempt}/{MAX_RETRIES}...")
            
            try:
                # Session Al
                headers1 = {"User-Agent": "Mozilla/5.0 (SMART-TV; LINUX; Tizen 6.0)"}
                session_res = requests.get("https://ytdlp.online/", headers=headers1, verify=False, timeout=15)
                
                if "session" not in session_res.cookies:
                    time.sleep(WAIT_TIME)
                    continue

                token = session_res.cookies.get("session")
                encoded_command = urllib.parse.quote(f"--get-url {live_url}")
                stream_api_url = f"https://ytdlp.online/stream?command={encoded_command}"

                headers2 = {
                    "User-Agent": "Mozilla/5.0 (SMART-TV; LINUX; Tizen 6.0)",
                    "Accept": "text/event-stream",
                    "Referer": "https://ytdlp.online/",
                    "Cookie": f"session={token}"
                }

                response2 = requests.get(stream_api_url, headers=headers2, verify=False, timeout=20)
                text = response2.text

                # Manifest Linkini Bul
                manifest_match = re.search(r'data:\s*(https://manifest\.googlevideo\.com[^\s]+)', text)

                if manifest_match:
                    final_link = manifest_match.group(1).strip()
                    m3u8_content = f"#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=1280x720\n{final_link}"

                    # Klasörün içine kaydet
                    file_path = os.path.join(name, f"{name}.m3u8")
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(m3u8_content)
                    
                    print(f"BAŞARILI: {name} linki kaydedildi -> {file_path}")
                    success = True
                    break # Bir sonraki kanala geç
                else:
                    print(f"Manifest bulunamadı, bekleniyor...")

            except Exception as e:
                print(f"Hata: {e}")
            
            if not success:
                time.sleep(WAIT_TIME)

        if not success:
            print(f"UYARI: {name} için 10 deneme sonunda link bulunamadı.")

if __name__ == "__main__":
    get_streams()
