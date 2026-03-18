"""
nabii.py — Tabii/TRT kanallarından m3u8 URL çeker
Yöntem: https://www.tabii.com/tr/watch/live/{slug}?trackId={id}
sayfasındaki __NEXT_DATA__ JSON içinden drmSchema=clear HLS URL alınır.
Token gerekmez — herkese açık.
"""

import requests
import json
import re
import time

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9",
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
})

CHANNELS = [
    {"id": "trt1",           "trackId": "150002", "name": "TRT 1",            "group": "TABİİ",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/22938_0-0-1500-1500.png"},
    {"id": "trt2",           "trackId": "150007", "name": "TRT 2",            "group": "TABİİ",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/22942_0-0-1500-1500.png"},
    {"id": "trtspor",        "trackId": "150022", "name": "TRT Spor",         "group": "TABİİ Spor",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/22961_0-0-1500-1500.png"},
    {"id": "trthaber",       "trackId": "150017", "name": "TRT Haber",        "group": "TABİİ",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/22979_0-0-1500-1500.png"},
    {"id": "trtsporyildiz",  "trackId": "150028", "name": "TRT Spor Yıldız",  "group": "TABİİ Spor",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/22956_0-0-1500-1500.png"},
    {"id": "trtcocuk",       "trackId": "150038", "name": "TRT Çocuk",        "group": "TABİİ",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/22984_0-0-1500-1500.png"},
    {"id": "trtworld",       "trackId": "150063", "name": "TRT World",        "group": "TABİİ",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/22947.png"},
    {"id": "trtbelgesel",    "trackId": "150012", "name": "TRT Belgesel",     "group": "TABİİ",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/22988_0-0-1500-1500.png"},
    {"id": "trtmuzik",       "trackId": "150033", "name": "TRT Müzik",        "group": "TABİİ",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/22966_0-0-1500-1500.png"},
    {"id": "trtturk",        "trackId": "150043", "name": "TRT Türk",         "group": "TABİİ",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/22951_0-0-1500-1500.png"},
    {"id": "trtkurdi",       "trackId": "150053", "name": "TRT Kurdî",        "group": "TABİİ",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/22975_0-0-1500-1500.png"},
    {"id": "trtarabi",       "trackId": "150058", "name": "TRT Arabi",        "group": "TABİİ",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/22996_0-0-1500-1500.png"},
    {"id": "trtavaz",        "trackId": "150048", "name": "TRT Avaz",         "group": "TABİİ",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/51339_0-0-720-720.png"},
    {"id": "trtdiyanetcocuk","trackId": "171018", "name": "TRT Diyanet Çocuk","group": "TABİİ",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/24238_0-0-467-262.png"},
    {"id": "trteba",         "trackId": "293389", "name": "TRT EBA TV",       "group": "TABİİ",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/34581_0-0-2559-651.jpeg"},
    {"id": "trtgenc",        "trackId": "606324", "name": "TRT Genç",         "group": "TABİİ",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/60307_0-0-1500-1500.png"},
    {"id": "tabiispor",      "trackId": "419561", "name": "Tabii Spor",       "group": "TABİİ Spor",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/43022.png"},
    {"id": "tabiispor1",     "trackId": "401207", "name": "Tabii Spor 1",     "group": "TABİİ Spor",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/43216_0-0-1500-1500.png"},
    {"id": "tabiispor2",     "trackId": "404583", "name": "Tabii Spor 2",     "group": "TABİİ Spor",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/43211_0-0-1500-1500.png"},
    {"id": "tabiispor3",     "trackId": "404630", "name": "Tabii Spor 3",     "group": "TABİİ Spor",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/43212_0-0-1500-1500.png"},
    {"id": "tabiispor4",     "trackId": "404637", "name": "Tabii Spor 4",     "group": "TABİİ Spor",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/43213_0-0-1500-1500.png"},
    {"id": "tabiispor5",     "trackId": "404646", "name": "Tabii Spor 5",     "group": "TABİİ Spor",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/43214_0-0-1500-1500.png"},
    {"id": "tabiispor6",     "trackId": "404666", "name": "Tabii Spor 6",     "group": "TABİİ Spor",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/43215_0-0-1500-1500.png"},
    {"id": "tabiispor7",     "trackId": "517474", "name": "Tabii Spor 7",     "group": "TABİİ Spor",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/51611_0-0-1500-1500.png"},
    {"id": "tabiispor8",     "trackId": "610569", "name": "Tabii Spor 8",     "group": "TABİİ Spor",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/60593_0-0-1500-1500.png"},
    {"id": "tabiitv",        "trackId": "383911", "name": "Tabii TV",         "group": "TABİİ",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/45154_0-0-1500-1500.png"},
    {"id": "tabii-cocuk",    "trackId": "516992", "name": "Tabii Çocuk",      "group": "TABİİ",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/51550_0-0-1500-1500.png"},
]

def get_stream_url(channel):
    """
    Tabii sayfasındaki __NEXT_DATA__ JSON'dan drmSchema=clear HLS URL'yi çek.
    Bu veri token olmadan gelir — liveChannels listesinde tüm kanalların URL'leri var.
    """
    page_url = f"https://www.tabii.com/tr/watch/live/{channel['id']}?trackId={channel['trackId']}"
    try:
        r = SESSION.get(page_url, timeout=15)
        if r.status_code != 200:
            print(f"  HTTP {r.status_code}", end=" ")
            return None

        # __NEXT_DATA__ JSON bloğunu çıkar
        match = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
            r.text, re.DOTALL
        )
        if not match:
            print("  __NEXT_DATA__ yok", end=" ")
            return None

        data = json.loads(match.group(1))
        live_channels = data.get("props", {}).get("pageProps", {}).get("liveChannels", [])

        # Tüm kanallar listesinden ilgili kanalı bul
        track_id = int(channel["trackId"])
        target = None
        for ch in live_channels:
            if ch.get("id") == track_id or ch.get("slug") == channel["id"]:
                target = ch
                break

        # Bulunamazsa liveChannel alanına bak (mevcut sayfa kanalı)
        if not target:
            target = data.get("props", {}).get("pageProps", {}).get("liveChannel", {})

        if not target:
            print("  kanal bulunamadı", end=" ")
            return None

        # drmSchema=clear + type=hls → URL al
        best_url = None
        best_priority = 999
        for media in target.get("media", []):
            if media.get("drmSchema") == "clear" and media.get("type") == "hls":
                url = media.get("url", "")
                priority = media.get("priority", 99)
                if url and priority < best_priority:
                    best_url = url
                    best_priority = priority

        if not best_url:
            print("  clear HLS yok", end=" ")

        return best_url

    except Exception as e:
        print(f"  hata:{e}", end=" ")
        return None

def main():
    m3u_lines = ["#EXTM3U\n"]
    success = 0
    fail    = 0

    for ch in CHANNELS:
        print(f"[+] {ch['name']} çekiliyor...", end=" ", flush=True)
        stream_url = get_stream_url(ch)

        if stream_url:
            print(f"✓ {stream_url[:70]}")
            line = (
                f'#EXTINF:-1 tvg-id="{ch["id"]}" tvg-name="{ch["name"]}" '
                f'tvg-logo="{ch["logo"]}" group-title="{ch["group"]}",{ch["name"]}\n'
                f'{stream_url}\n'
            )
            m3u_lines.append(line)
            success += 1
        else:
            print("✗ bulunamadı")
            fail += 1

        time.sleep(0.5)  # Rate limit

    with open("tabii.m3u", "w", encoding="utf-8") as f:
        f.writelines(m3u_lines)

    print(f"\n[*] {success} başarılı, {fail} başarısız → tabii.m3u kaydedildi")

if __name__ == "__main__":
    main()
