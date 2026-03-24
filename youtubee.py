import requests
import re
import os
import urllib.parse
import urllib3
import time
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

JSON_URL = "https://raw.githubusercontent.com/metvmetv33/METV/refs/heads/main/muomube.json"
MAX_RETRIES = 3
WAIT_TIME = 5

def update():
    try:
        print(f"Liste çekiliyor: {JSON_URL}")
        response = requests.get(JSON_URL, timeout=15)
        # JSON yüklerken oluşabilecek hataları yakala
        try:
            channels = response.json()
        except json.JSONDecodeError as e:
            print(f"KRİTİK HATA: JSON formatı bozuk! Satır: {e.lineno}, Sütun: {e.colno}")
            print(f"Hata mesajı: {e.msg}")
            return

        for channel in channels:
            name = channel.get("name", "Bilinmeyen").replace(" ", "_")
            live_url = channel.get("url", "").strip()
            
            if not live_url: continue

            print(f"İşleniyor: {name}")
            if not os.path.exists(name): os.makedirs(name)

            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    r1 = requests.get("https://ytdlp.online/", timeout=10, verify=False)
                    token = r1.cookies.get("session")
                    if not token: continue

                    cmd = urllib.parse.quote(f"--get-url {live_url}")
                    r2 = requests.get(f"https://ytdlp.online/stream?command={cmd}", 
                                     headers={"Cookie": f"session={token}", "Referer": "https://ytdlp.online/"}, 
                                     timeout=20, verify=False)
                    
                    match = re.search(r'data:\s*(https://manifest\.googlevideo\.com[^\s]+)', r2.text)
                    if match:
                        link = match.group(1).strip()
                        content = f"#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=1280x720\n{link}"
                        with open(f"{name}/{name}.m3u8", "w", encoding="utf-8") as f:
                            f.write(content)
                        print(f"Başarılı: {name}")
                        break
                except Exception as e:
                    print(f"Hata ({name}): {e}")
                time.sleep(WAIT_TIME)

    except Exception as e:
        print(f"Genel Hata: {e}")

if __name__ == "__main__":
    update()
