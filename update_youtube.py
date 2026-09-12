#!/usr/bin/env python3
"""
YouTube Canlı Yayın Güncelleyici (Channel ID Bazlı)
- youtube.json'daki channel ID'lerini kullanır
- Her kanal için canlı yayın video ID'sini bulur
- YouTube OEmbed'den başlık ve thumbnail çeker
- youtube.json'u günceller
"""

import json
import re
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

# ── Sabitler ────────────────────────────────────────────
JSON_FILE = Path(__file__).parent.parent / "youtube.json"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
TIMEOUT = 15


def fetch_live_video_id(channel_id):
    """
    Kanalın /live sayfasından canlı yayın video ID'sini çeker.
    """
    url = f"https://www.youtube.com/channel/{channel_id}/live"

    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
        "Cookie": "CONSENT=YES+cb",
    })

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            html = response.read().decode("utf-8", errors="ignore")

        # Farklı regex'lerle video ID'sini ara
        patterns = [
            r'<link rel="canonical" href="https://www\.youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})"',
            r'<meta property="og:url" content="https://www\.youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})"',
            r'"videoId":"([a-zA-Z0-9_-]{11})"',
            r'watch\?v=([a-zA-Z0-9_-]{11})',
        ]

        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)

        return None
    except Exception as e:
        print(f"  ⚠️  Kanal hatası: {e}")
        return None


def fetch_oembed(video_id):
    """YouTube OEmbed API'sinden başlık ve thumbnail çeker."""
    params = urllib.parse.urlencode({
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "format": "json"
    })
    url = f"https://www.youtube.com/oembed?{params}"

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))
            return {
                "title": data.get("title", ""),
                "author_name": data.get("author_name", ""),
                "thumbnail_url": data.get("thumbnail_url", ""),
            }
    except Exception as e:
        print(f"  ⚠️  OEmbed hatası: {e}")
        return None


def main():
    print("=" * 70)
    print("📺 YouTube Canlı Yayın Güncelleyici")
    print("=" * 70)

    # 1. JSON'u oku
    if not JSON_FILE.exists():
        print(f"❌ HATA: {JSON_FILE} bulunamadı!")
        return

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    channels = data.get("channels", [])
    print(f"📋 Toplam kanal: {len(channels)}\n")

    videos = []
    success_count = 0

    # 2. Her kanal için video ID bul
    for i, channel in enumerate(channels, 1):
        channel_id = channel.get("channelId", "")
        name = channel.get("name", "?")
        order = channel.get("order", i)

        print(f"[{i}/{len(channels)}] {name}")
        print(f"  🔗 Channel ID: {channel_id}")

        if not channel_id:
            print(f"  ⏭️  Atlandı (Channel ID yok)")
            continue

        # Canlı yayın video ID'sini çek
        video_id = fetch_live_video_id(channel_id)

        if not video_id:
            print(f"  ❌ Canlı yayın bulunamadı")
            videos.append({
                "id": "",
                "channelId": channel_id,
                "name": name,
                "order": order,
                "isLive": False,
                "embedUrl": "",
                "thumbnail": "",
                "title": "",
                "error": "Canlı yayın bulunamadı"
            })
            continue

        print(f"  ✅ Video ID: {video_id}")

        # OEmbed'den başlık ve thumbnail çek
        oembed = fetch_oembed(video_id)
        title = oembed["title"] if oembed else name
        thumbnail = oembed["thumbnail_url"] if oembed else f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

        videos.append({
            "id": video_id,
            "channelId": channel_id,
            "name": name,
            "title": title,
            "order": order,
            "isLive": True,
            "embedUrl": f"https://www.youtube-nocookie.com/embed/{video_id}",
            "thumbnail": thumbnail
        })
        success_count += 1
        print(f"  📝 Başlık: {title[:60]}")

    # 3. JSON'u güncelle
    data["success"] = True
    data["count"] = len(videos)
    data["live_count"] = success_count
    data["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    data["source"] = "github-actions"
    data["videos"] = videos

    # 4. Kaydet
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print()
    print("=" * 70)
    print(f"✅ {success_count}/{len(channels)} kanal canlı yayında")
    print(f"💾 Kaydedildi: {JSON_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    main()
