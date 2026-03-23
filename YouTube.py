import yt_dlp
import subprocess

def get_live_url(channel_id):
    url = f"https://www.youtube.com/channel/{channel_id}/live"
    
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'cookiesfrombrowser': ('chrome',),  # Chrome oturumunu kullan
        'extractor_args': {
            'youtube': {
                'player_client': ['web'],  # TV client yerine web
            }
        },
        'sleep_interval_requests': 2,  # Rate limit için bekle
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'tr-TR,tr;q=0.9',
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('url') or info['formats'][-1]['url']
    except Exception as e:
        print(f"Hata: {e}")
        return None

stream_url = get_live_url("UCoIUysIrvGxoDw-GkdOGjRw")
if stream_url:
    with open("kemal-sunal-filmleri.m3u8", "w") as f:
        f.write(f"#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1280000\n{stream_url}\n")
    print("Kaydedildi.")
