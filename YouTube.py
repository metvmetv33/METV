import requests
import re
import sys
import json

CHANNEL_ID = "UCoIUysIrvGxoDw-GkdOGjRw"
OUTPUT_FILE = "ytb.m3u8"

def get_live_video_id(channel_id):
    url = f"https://www.youtube.com/channel/{channel_id}/live"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
        "Accept-Language": "tr-TR,tr;q=0.9",
    }
    r = requests.get(url, headers=headers)
    match = re.search(r'"videoId":"([^"]{11})"', r.text)
    if match:
        return match.group(1)
    return None

def get_stream_url(video_id):
    # YouTube InnerTube API
    api_url = "https://www.youtube.com/youtubei/v1/player"
    
    payload = {
        "videoId": video_id,
        "context": {
            "client": {
                "clientName": "ANDROID_TESTSUITE",
                "clientVersion": "1.9",
                "androidSdkVersion": 30,
                "hl": "tr",
                "gl": "TR",
                "utcOffsetMinutes": 180
            }
        }
    }
    
    headers = {
        "User-Agent": "com.google.android.youtube/1.9 (Linux; U; Android 11)",
        "Content-Type": "application/json",
        "X-YouTube-Client-Name": "30",
        "X-YouTube-Client-Version": "1.9",
    }
    
    r = requests.post(api_url, json=payload, headers=headers)
    data = r.json()
    
    # HLS manifest ara
    streaming = data.get("streamingData", {})
    
    # Önce HLS manifest
    hls_url = streaming.get("hlsManifestUrl")
    if hls_url:
        return hls_url
    
    # Sonra adaptive formats
    formats = streaming.get("adaptiveFormats", []) + streaming.get("formats", [])
    for f in reversed(formats):
        u = f.get("url", "")
        if u and "googlevideo.com" in u:
            return u
    
    return None

print("Video ID aliniyor...")
video_id = get_live_video_id(CHANNEL_ID)
if not video_id:
    print("Hata: Video ID bulunamadi")
    sys.exit(1)

print(f"Video ID: {video_id}")
print("Stream URL aliniyor...")

stream_url = get_stream_url(video_id)
if not stream_url:
    print("Hata: Stream URL bulunamadi")
    sys.exit(1)

print(f"Basarili! URL: {stream_url[:80]}...")

# HLS manifest ise direkt yaz, değilse m3u8 sar
if "manifest" in stream_url or ".m3u8" in stream_url:
    content = f"#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-STREAM-INF:BANDWIDTH=1280000\n{stream_url}\n"
else:
    content = f"#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=1280x720\n{stream_url}\n"

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print(f"{OUTPUT_FILE} olusturuldu.")
