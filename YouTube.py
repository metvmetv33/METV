import requests
import re
import sys
import urllib.parse
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CHANNEL_ID = "UCoIUysIrvGxoDw-GkdOGjRw"
OUTPUT_FILE = "ytb.m3u8"

def yontem_ytdlp_online(channel_id):
    print("ytdlp.online deneniyor...")
    youtube_link = f"https://www.youtube.com/channel/{channel_id}/live"
    encoded = urllib.parse.quote(f"--get-url {youtube_link}")
    
    for attempt in range(1, 11):
        print(f"  Deneme {attempt}/10...")
        try:
            r1 = requests.get(
                "https://ytdlp.online/",
                headers={"User-Agent": "Mozilla/5.0 (SMART-TV; LINUX; Tizen 6.0)"},
                verify=False, timeout=15
            )
            
            if "session" not in r1.cookies:
                print("  Session alinamadi.")
                time.sleep(15)
                continue
            
            token = r1.cookies.get("session")
            
            r2 = requests.get(
                f"https://ytdlp.online/stream?command={encoded}",
                headers={
                    "User-Agent": "Mozilla/5.0 (SMART-TV; LINUX; Tizen 6.0)",
                    "Accept": "text/event-stream",
                    "Referer": "https://ytdlp.online/",
                    "Cookie": f"session={token}"
                },
                verify=False, timeout=60
            )
            
            text = r2.text
            
            for pattern in [
                r'data:\s*(https://manifest\.googlevideo\.com[^\s\n<]+)',
                r'data:\s*(https://[^\s\n<]*googlevideo[^\s\n<]+)',
                r'data:\s*(https://[^\s\n<]+\.m3u8[^\s\n<]*)',
            ]:
                match = re.search(pattern, text)
                if match:
                    print(f"  URL bulundu!")
                    return match.group(1).strip()
            
            # Son satırları göster
            son_satirlar = [l for l in text.split('\n') if l.strip()][-5:]
            print(f"  Son satirlar: {son_satirlar}")
            time.sleep(15)

        except Exception as e:
            print(f"  Hata: {e}")
            time.sleep(15)
    
    return None

stream_url = yontem_ytdlp_online(CHANNEL_ID)

if not stream_url:
    print("Basarisiz.")
    sys.exit(1)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(
        "#EXTM3U\n"
        "#EXT-X-VERSION:3\n"
        "#EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=1280x720\n"
        f"{stream_url}\n"
    )
print(f"Basarili! {OUTPUT_FILE} olusturuldu.")
