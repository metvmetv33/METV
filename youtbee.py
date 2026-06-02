import os
import re
import time
from typing import Optional
import requests

# ─── Ayarlar ───────────────────────────────────────────────
JSON_URL = (
    "https://raw.githubusercontent.com/metvmetv33/METV/refs/heads/main/muomube.json"
)
OUTPUT_FOLDER = "metv2"
MAX_RETRIES = 3
WAIT_TIME = 2

# ytdlp.online servisinin gerçek arka plan API mimarisi
YTDLP_ONLINE_API = "https://backend.ytdlp.online/api/graphql"  # Sitenin istekleri gönderdiği ana API havuzu
# ───────────────────────────────────────────────────────────


def get_channels():
    print("[*] Kanal listesi cekiliyor: {}".format(JSON_URL))
    try:
        r = requests.get(JSON_URL, timeout=20)
        r.raise_for_status()
        data = r.json()
        print("[+] {} kanal bulundu.".format(len(data)))
        return data
    except Exception as e:
        print("[!] Liste alinamadi: {}".format(e))
        return []


def get_stream_url_from_ytdlp_online(channel_url):
    # type: (str) -> Optional[str]
    """ytdlp.online sitesinin backend motoruna doğrudan bağlanarak

    reklam ve embed engellerine takılmayan ham m3u8 linkini çeker.
    """
    clean_url = channel_url.strip()

    # Sitenin sunucusuna gönderilen evrensel veri şeması
    payload = {
        "url": clean_url,
        "options": {
            "format": "best",
            "no_playlist": True,
            "extractor_args": "youtube:skip=hls,dash",
        },
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://ytdlp.online",
        "Referer": "https://ytdlp.online/",
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # ytdlp.online API'sine POST isteği gönderiyoruz
            # (Eğer ana sunucu yoğunsa sitenin diğer açık CDN/ayna adreslerine istek yönlendirilir)
            response = requests.post(
                "https://ytdlp.online/api/info",
                json=payload,
                headers=headers,
                timeout=25,
            )

            if response.status_code == 200:
                res_data = response.json()

                # Sitenin JSON çıktısından doğrudan m3u8 akış adresini avlayalım
                # ytdlp çıktısında genellikle 'url', 'formats' veya 'stream' altında yer alır
                stream_url = None
                if "url" in res_data:
                    stream_url = res_data["url"]
                elif "formats" in res_data and len(res_data["formats"]) > 0:
                    # En yüksek kaliteli (best) formata ait URL'yi seç
                    stream_url = res_data["formats"][-1].get("url")

                if stream_url and "googlevideo.com" in stream_url:
                    return stream_url

            # Alternatif İstek Geçidi (Sitenin proxy/mirror motoru devreye girer)
            alt_response = requests.post(
                "https://api.ytdlp.online/v1/process",
                json={"video_url": clean_url},
                headers=headers,
                timeout=20,
            )
            if alt_response.status_code == 200:
                alt_data = alt_response.json()
                url = alt_data.get("url") or alt_data.get("data", {}).get("url")
                if url:
                    return url

            print(
                "    Deneme {}/{}: ytdlp.online sunucusu meşgul (Kod: {})".format(
                    attempt, MAX_RETRIES, response.status_code
                )
            )

        except Exception as e:
            print(
                "    Deneme {}/{}: Siteden yanıt alınamadı — {}".format(
                    attempt, MAX_RETRIES, str(e)[:60]
                )
            )

        if attempt < MAX_RETRIES:
            time.sleep(WAIT_TIME)

    return None


def sanitize(name):
    return re.sub(r"[^\w\s\-]", "", name).strip().replace(" ", "_")


def save_m3u8(file_path, stream_url, channel_name, logo_url=""):
    tvg_logo = ' tvg-logo="{}"'.format(logo_url) if logo_url else ""
    content = (
        "#EXTM3U\n"
        "#EXT-X-VERSION:3\n"
        '#EXTINF:-1 tvg-name="{name}"{logo},{name}\n'
        "{url}\n"
    ).format(name=channel_name, logo=tvg_logo, url=stream_url)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    channels = get_channels()
    if not channels:
        print("[!] Kanal listesi bos, cikiliyor.")
        return

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    print("[*] Dosyalar '{}/' klasorune kaydedilecek.\n".format(OUTPUT_FOLDER))

    success_count = 0
    fail_count = 0
    failed_names = []

    for i, ch in enumerate(channels, 1):
        name = ch.get("name", "Kanal_{}".format(i))
        target_url = ch.get("url", "").strip()
        logo_url = ch.get("logo", "")

        if not target_url:
            continue

        print("[{}/{}] {}".format(i, len(channels), name))
        print("    Hedef: {}".format(target_url))

        # Doğrudan ytdlp.online kullanarak link çözüyoruz
        stream_url = get_stream_url_from_ytdlp_online(target_url)

        if stream_url:
            file_path = os.path.join(
                OUTPUT_FOLDER, "{}.m3u8".format(sanitize(name))
            )
            save_m3u8(file_path, stream_url, name, logo_url)
            print("    [OK] -> Ham Canlı Yayın Linki Yakalandı")
            success_count += 1
        else:
            print("    [FAIL] ytdlp.online bu kanalı çözemedi -> {}".format(name))
            fail_count += 1
            failed_names.append(name)

    # ─── Birleşik liste oluşturma (_METV2_COMBINED.m3u) ───
    combined_path = os.path.join(OUTPUT_FOLDER, "_METV2_COMBINED.m3u")
    header = "#EXTM3U\n"
    entries = []

    for m3u8_file in sorted(os.listdir(OUTPUT_FOLDER)):
        if not m3u8_file.endswith(".m3u8") or m3u8_file.startswith("_"):
            continue
        full = os.path.join(OUTPUT_FOLDER, m3u8_file)
        with open(full, encoding="utf-8") as f:
            content = f.read()
        body = re.sub(r"^#EXTM3U\n?#EXT-X-VERSION:[0-9]\n?", "", content).strip()
        entries.append(body)

    with open(combined_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(entries) + "\n")

    # ─── Özet ────────────────────────────────────────────
    print("\n" + "=" * 55)
    print(
        "TAMAMLANDI   OK:{}   FAIL:{}   TOPLAM:{}".format(
            success_count, fail_count, success_count + fail_count
        )
    )
    if failed_names:
        print("\nÇözülemeyen kanallar ({}):".format(len(failed_names)))
        for n in failed_names:
            print("  - {}".format(n))
    print("\n[+] Birlesik IPTV Listesi -> {}".format(combined_path))


if __name__ == "__main__":
    main()
