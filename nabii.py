import requests
import time

WORKER_BASE = "https://tabii.metvmetv33.workers.dev/?id="

CHANNELS = [
    {"id": "trt1",          "name": "TRT 1",           "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/TRT_1_logo_%282021%29.svg/200px-TRT_1_logo_%282021%29.svg.png"},
    {"id": "trt2",          "name": "TRT 2",           "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/TRT_2_logo_%282021%29.svg/200px-TRT_2_logo_%282021%29.svg.png"},
    {"id": "trtspor",       "name": "TRT Spor",        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/28/TRT_Spor_logo_%282021%29.svg/200px-TRT_Spor_logo_%282021%29.svg.png"},
    {"id": "trthaber",      "name": "TRT Haber",       "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/TRT_Haber_logo_%282021%29.svg/200px-TRT_Haber_logo_%282021%29.svg.png"},
    {"id": "trtsporyildiz", "name": "TRT Spor Yıldız", "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/28/TRT_Spor_logo_%282021%29.svg/200px-TRT_Spor_logo_%282021%29.svg.png"},
    {"id": "trtcocuk",      "name": "TRT Çocuk",       "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/TRT_%C3%87ocuk_logo_%282021%29.svg/200px-TRT_%C3%87ocuk_logo_%282021%29.svg.png"},
    {"id": "trtmuzik",      "name": "TRT Müzik",       "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/TRT_M%C3%BCzik_logo_%282021%29.svg/200px-TRT_M%C3%BCzik_logo_%282021%29.svg.png"},
    {"id": "trtkurdi",      "name": "TRT Kurdî",       "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/TRT_logo.svg/200px-TRT_logo.svg.png"},
    {"id": "tabiispor",     "name": "Tabii Spor",      "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/28/TRT_Spor_logo_%282021%29.svg/200px-TRT_Spor_logo_%282021%29.svg.png"},
    {"id": "tabiispor1",    "name": "Tabii Spor 1",    "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/28/TRT_Spor_logo_%282021%29.svg/200px-TRT_Spor_logo_%282021%29.svg.png"},
    {"id": "tabiispor2",    "name": "Tabii Spor 2",    "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/28/TRT_Spor_logo_%282021%29.svg/200px-TRT_Spor_logo_%282021%29.svg.png"},
    {"id": "tabiispor3",    "name": "Tabii Spor 3",    "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/28/TRT_Spor_logo_%282021%29.svg/200px-TRT_Spor_logo_%282021%29.svg.png"},
    {"id": "tabiispor4",    "name": "Tabii Spor 4",    "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/28/TRT_Spor_logo_%282021%29.svg/200px-TRT_Spor_logo_%282021%29.svg.png"},
    {"id": "tabiispor5",    "name": "Tabii Spor 5",    "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/28/TRT_Spor_logo_%282021%29.svg/200px-TRT_Spor_logo_%282021%29.svg.png"},
    {"id": "tabiispor6",    "name": "Tabii Spor 6",    "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/28/TRT_Spor_logo_%282021%29.svg/200px-TRT_Spor_logo_%282021%29.svg.png"},
    {"id": "tabiitv",       "name": "Tabii TV",        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/TRT_logo.svg/200px-TRT_logo.svg.png"},
]

def get_m3u8(channel_id):
    """Worker 302 redirect yapar — Location header'dan m3u8 URL'sini al"""
    url = WORKER_BASE + channel_id
    try:
        # allow_redirects=False → 302 redirect URL'sini yakala
        r = requests.get(url, allow_redirects=False, timeout=15)
        if r.status_code in (301, 302, 303, 307, 308):
            loc = r.headers.get("Location", "")
            return loc
        elif r.status_code == 200:
            # Direkt içerik dönmüşse URL'yi kullan
            return url
        else:
            print(f"  HTTP {r.status_code}: {r.text[:100]}")
            return ""
    except Exception as e:
        print(f"  Hata: {e}")
        return ""

def main():
    m3u_lines = ["#EXTM3U\n"]
    success = 0
    fail    = 0

    for ch in CHANNELS:
        print(f"[+] {ch['name']} çekiliyor...", end=" ", flush=True)
        stream_url = get_m3u8(ch["id"])

        if stream_url and "m3u8" in stream_url:
            line = (
                f'#EXTINF:-1 tvg-id="{ch["id"]}" tvg-name="{ch["name"]}" '
                f'tvg-logo="{ch["logo"]}" group-title="TABİİ",{ch["name"]}\n'
                f'{stream_url}\n'
            )
            m3u_lines.append(line)
            print(f"✓  {stream_url[:70]}")
            success += 1
        else:
            print("✗  bulunamadı")
            fail += 1

        time.sleep(0.3)

    with open("tabii.m3u", "w", encoding="utf-8") as f:
        f.writelines(m3u_lines)

    print(f"\n[*] {success} başarılı, {fail} başarısız → tabii.m3u kaydedildi")

if __name__ == "__main__":
    main()
