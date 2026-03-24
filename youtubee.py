import requests
import re
import os
import urllib.parse
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ayarlar
JSON_URL = "https://raw.githubusercontent.com/metvmetv33/METV/refs/heads/main/muomube.json"
MAX_RETRIES = 5
WAIT_TIME = 10

def update():
    try:
        channels = requests.get(JSON_URL).json()
    except Exception as e:
        print(f"Liste alınamadı: {e}")
        return

    for channel in channels:
        name = channel.get("name").replace(" ", "_").replace("/", "-")
        live_url = channel.get("url").strip()
        
        # Klasör oluşturma
        if not os.path.exists(name):
            os.makedirs(name)

        success = False
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                # Session ve Token alma
                h1 = {"User-Agent": "Mozilla/5.0 (SMART-TV; LINUX; Tizen 6.0)"}
                r1 = requests.get("https://ytdlp.online/", headers=h1, verify=False, timeout=15)
                token = r1.cookies.get("session")

                if not token:
                    time.sleep(WAIT_TIME)
                    continue

                # Stream Linki Çekme
                cmd = urllib.parse.quote(f"--get-url {live_url}")
                api_url = f"https://ytdlp.online/stream?command={cmd}"
                h2 = {
                    "User-Agent": "Mozilla/5.0 (SMART-TV; LINUX; Tizen 6.0)",
                    "Cookie": f"session={token}",
                    "Referer": "https://ytdlp.online/"
                }
                
                r2 = requests.get(api_url, headers=h2, verify=False, timeout=20)
                match = re.search(r'data:\s*(https://manifest\.googlevideo\.com[^\s]+)', r2.text)

                if match:
                    final_link = match.group(1).strip()
                    m3u8_payload = f"#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=1280x720\n{final_link}"
                    
                    with open(f"{name}/{name}.m3u8", "w", encoding="utf-8") as f:
                        f.write(m3u8_payload)
                    
                    print(f"Tamamlandı: {name}")
                    success = True
                    break
            except:
                pass
            time.sleep(WAIT_TIME)

if __name__ == "__main__":
    update()
