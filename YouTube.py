import yt_dlp
import sys

live_id = "UCoIUysIrvGxoDw-GkdOGjRw"
youtube_url = f"https://www.youtube.com/channel/{live_id}/live"

ydl_opts = {
    'quiet': True,
    'no_warnings': True,
    'format': 'best',
}

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        # Canlı yayın m3u8 linkini çekiyoruz
        final_link = info.get('url')

        if final_link:
            m3u8_content = f"#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=1280x720\n{final_link}"
            with open("ytb.m3u8", "w", encoding="utf-8") as f:
                f.write(m3u8_content)
            print("Başarılı! Kendi motorumuzla linki aldık.")
        else:
            print("Link bulunamadı.")
except Exception as e:
    print(f"Hata: {e}")
