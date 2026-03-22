import requests
import re
import urllib.parse
import urllib3
import time
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CHANNELS = {
    "UC9TDTjbOjFB9jADmPhSAPsw": "kanal1",
    "UCoIUysIrvGxoDw-GkdOGjRw": "kanal2",
}

max_retries = 15
wait_time = 20

def get_manifest(live_id):
    for attempt in range(1, max_retries + 1):
        print(f"[{live_id}] Deneme {attempt}/{max_retries}")
        try:
            r1 = requests.get("https://ytdlp.online/", 
                headers={"User-Agent": "Mozilla/5.0 (SMART-TV; LINUX; Tizen 6.0)"},
                verify=False, timeout=15)
            
            if "session" not in r1.cookies:
                time.sleep(wait_time)
                continue

            token = r1.cookies.get("session")
            encoded = urllib.parse.quote(f"--get-url https://www.youtube.com/channel/{live_id}/live")
            
            r2 = requests.get(f"https://ytdlp.online/stream?command={encoded}",
                headers={
                    "User-Agent": "Mozilla/5.0 (SMART-TV; LINUX; Tizen 6.0)",
                    "Accept": "text/event-stream",
                    "Referer": "https://ytdlp.online/",
                    "Cookie": f"session={token}"
                }, verify=False, timeout=20)

            match = re.search(r'data:\s*(https://manifest\.googlevideo\.com[^\s\n]+)', r2.text)
            if match:
                print(f"[{live_id}] Başarılı!")
                return match.group(1).strip()
            
            time.sleep(wait_time)
        except Exception as e:
            print(f"Hata: {e}")
            time.sleep(wait_time)
    return None

# manifest.txt dosyasına yaz
results = {}
for channel_id, name in CHANNELS.items():
    url = get_manifest(channel_id)
    if url:
        results[name] = url
        print(f"{name}: {url[:60]}...")
    else:
        print(f"{name}: BULUNAMADI")

with open("manifest.txt", "w") as f:
    for name, url in results.items():
        f.write(f"{name}={url}\n")

print("manifest.txt güncellendi.")
