import requests
import re
import sys
import time

CHANNEL_ID = "UCoIUysIrvGxoDw-GkdOGjRw"
OUTPUT_FILE = "ytb.m3u8"

# Piped public instance listesi
PIPED_INSTANCES = [
    "https://pipedapi.kavin.rocks",
    "https://piped-api.garudalinux.org",
    "https://api.piped.projectsegfau.lt",
    "https://piped.video/api",
    "https://pipedapi.reallyaweso.me",
    "https://pipedapi.coldforge.xyz",
]

def get_video_id(channel_id):
    url = f"https://www.youtube.com/channel/{channel_id}/live"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36"
    }
    try:
        r = requests.get(url, headers=headers, timeout=15)
        match = re.search(r'"videoId":"([^"]{11})"', r.text)
        if match:
            return match.group(1)
    except Exception as e:
        print(f"  Video ID hatasi: {e}")
    return None

def get_stream_from_piped(video_id):
    for instance in PIPED_INSTANCES:
        print(f"  Piped instance: {instance}...")
        try:
            url = f"{instance}/streams/{video_id}"
            r = requests.get(url, timeout=15)
            if r.status_code != 200:
                print(f"    HTTP {r.status_code}")
                continue
            data = r.json()

            # HLS stream ara
            hls = data.get("hls")
            if hls:
                print(f"    HLS bulundu!")
                return hls

            # Audio/Video streams
            streams = data.get("videoStreams", []) + data.get("audioStreams", [])
            for s in reversed(streams):
                u = s.get("url", "")
                if u:
                    print(f"    Stream URL bulundu!")
                    return u

            print(f"    Stream bulunamadi. Keys: {list(data.keys())}")

        except Exception as e:
            print(f"    Hata: {e}")
        time.sleep(2)
    return None

def get_stream_from_invidious(video_id):
    instances = [
        "https://invidious.snopyta.org",
        "https://vid.puffyan.us",
        "https://invidious.kavin.rocks",
        "https://y.com.sb",
        "https://invidious.nerdvpn.de",
    ]
    for instance in instances:
        print(f"  Invidious instance: {instance}...")
        try:
            url = f"{instance}/api/v1/videos/{video_id}"
            r = requests.get(url, timeout=15)
            if r.status_code != 200:
                print(f"    HTTP {r.status_code}")
                continue
            data = r.json()

            # Live stream
            hls = data.get("hlsUrl")
            if hls:
                print(f"    HLS bulundu!")
                return hls

            # Format streams
            formats = data.get("formatStreams", []) + data.get("adaptiveFormats", [])
            for f in reversed(formats):
                u = f.get("url", "")
                if u:
                    print(f"    Stream URL bulundu!")
                    return u

            print(f"    Stream bulunamadi.")

        except Exception as e:
            print(f"    Hata: {e}")
        time.sleep(2)
    return None

# Ana akış
print("Video ID aliniyor...")
video_id = get_video_id(CHANNEL_ID)
if not video_id:
    print("Hata: Video ID alinamadi")
    sys.exit(1)
print(f"Video ID: {video_id}")

stream_url = None

print("\nYontem 1: Piped API...")
stream_url = get_stream_from_piped(video_id)

if not stream_url:
    print("\nYontem 2: Invidious API...")
    stream_url = get_stream_from_invidious(video_id)

if not stream_url:
    print("Tum yontemler basarisiz.")
    sys.exit(1)

print(f"\nBasarili! URL: {stream_url[:80]}...")

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(
        "#EXTM3U\n"
        "#EXT-X-VERSION:3\n"
        "#EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=1280x720\n"
        f"{stream_url}\n"
    )
print(f"{OUTPUT_FILE} olusturuldu.")
