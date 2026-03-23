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

with open(COOKIES_FILE, "r") as f:
    ilk_satir = f.readline().strip()
    if "Netscape" not in ilk_satir:
        print(f"Hata: Cookie formati yanlis. Ilk satir: '{ilk_satir}'")
        sys.exit(1)

print("Cookie dosyasi gecerli.")

ydl_opts = {
    'format': 'best',
    'quiet': False,
    'no_warnings': False,
    'cookiefile': COOKIES_FILE,
    'extractor_args': {
        'youtube': {
            'player_client': ['web'],
        }
    },
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36',
        'Accept-Language': 'tr-TR,tr;q=0.9',
    }
}

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        print(f"URL isleniyor: {url}")
        info = ydl.extract_info(url, download=False)

        stream_url = None

        if 'url' in info:
            stream_url = info['url']
        elif 'formats' in info:
            for f in reversed(info['formats']):
                u = f.get('url', '')
                if 'googlevideo.com' in u or 'manifest.googlevideo' in u:
                    stream_url = u
                    break
            if not stream_url:
                stream_url = info['formats'][-1]['url']

        if not stream_url:
            print("Hata: Stream URL bulunamadi")
            sys.exit(1)

        print(f"Stream URL bulundu: {stream_url[:80]}...")

        m3u8 = (
            "#EXTM3U\n"
            "#EXT-X-VERSION:3\n"
            "#EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=1280x720\n"
            f"{stream_url}\n"
        )

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(m3u8)

        print(f"Basarili! {OUTPUT_FILE} olusturuldu.")

except yt_dlp.utils.DownloadError as e:
    print(f"Hata: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Beklenmeyen hata: {e}")
    sys.exit(1)
