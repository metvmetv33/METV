import yt_dlp
import sys

CHANNEL_ID = "UCoIUysIrvGxoDw-GkdOGjRw"
OUTPUT_FILE = "ytb.m3u8"

url = f"https://www.youtube.com/channel/{CHANNEL_ID}/live"

ydl_opts = {
    'format': 'best',
    'quiet': True,
    'no_warnings': True,
    'extractor_args': {
        'youtube': {
            'player_client': ['ios'],  # iOS client — cookie gerektirmez
        }
    },
    'http_headers': {
        'User-Agent': 'com.google.ios.youtube/19.29.1 (iPhone16,2; U; CPU iOS 17_5_1 like Mac OS X;)',
    }
}

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        
        stream_url = None
        if 'url' in info:
            stream_url = info['url']
        elif 'formats' in info:
            # En iyi formatı seç
            for f in reversed(info['formats']):
                if f.get('url') and 'manifest.googlevideo.com' in f.get('url', ''):
                    stream_url = f['url']
                    break
            if not stream_url:
                stream_url = info['formats'][-1]['url']
        
        if not stream_url:
            print("Hata: Stream URL bulunamadı")
            sys.exit(1)
        
        m3u8 = (
            "#EXTM3U\n"
            "#EXT-X-VERSION:3\n"
            "#EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=1280x720\n"
            f"{stream_url}\n"
        )
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(m3u8)
        
        print(f"Basarili! {OUTPUT_FILE} olusturuldu.")
        print(f"URL: {stream_url[:80]}...")

except yt_dlp.utils.DownloadError as e:
    print(f"Hata: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Beklenmeyen hata: {e}")
    sys.exit(1)
