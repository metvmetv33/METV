import yt_dlp
import sys
import os

CHANNEL_ID = "UCoIUysIrvGxoDw-GkdOGjRw"
OUTPUT_FILE = "ytb.m3u8"
COOKIES_FILE = "cookies.txt"

url = f"https://www.youtube.com/channel/{CHANNEL_ID}/live"

if not os.path.exists(COOKIES_FILE):
    print(f"Hata: {COOKIES_FILE} bulunamadi")
    sys.exit(1)

CLIENTS = [
    "web_creator",
    "web_embedded",
    "web_music",
    "android",
    "android_embedded",
]

for client in CLIENTS:
    print(f"Deneniyor: {client}...")
    try:
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'cookiefile': COOKIES_FILE,
            'extractor_args': {
                'youtube': {
                    'player_client': [client],
                }
            },
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            stream_url = None
            if 'url' in info:
                stream_url = info['url']
            elif 'formats' in info and info['formats']:
                for f in reversed(info['formats']):
                    u = f.get('url', '')
                    if u and 'googlevideo.com' in u:
                        stream_url = u
                        break
                if not stream_url:
                    stream_url = info['formats'][-1].get('url')

            if stream_url:
                print(f"Basarili! Client: {client}")
                print(f"URL: {stream_url[:80]}...")

                with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                    f.write(
                        "#EXTM3U\n"
                        "#EXT-X-VERSION:3\n"
                        "#EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=1280x720\n"
                        f"{stream_url}\n"
                    )
                print(f"{OUTPUT_FILE} olusturuldu.")
                sys.exit(0)
            else:
                print(f"  URL bulunamadi.")

    except Exception as e:
        print(f"  Hata: {str(e)[-150:]}")

print("Tum clientlar basarisiz.")
sys.exit(1)
