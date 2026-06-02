import os
import re
import time
from typing import Optional
import requests

# ─── Ayarlar ───────────────────────────────────────────────
JSON_URL = (
    "https://raw.githubusercontent.com/metvmetv33/METV/refs/heads/main/muomube.json"
)
OUTPUT_FOLDER = "metv"
MAX_RETRIES = 2
WAIT_TIME = 3
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


def get_stream_url_via_worker_logic(channel_url):
    # type: (str) -> Optional[str]
    """Cloudflare Worker kodundaki session ve text/event-stream mantığını

    kullanarak ytdlp.online üzerinden kesin link üretir.
    """
    # 1. Kanal URL'sinden Kanal ID'sini temizle ve ayıkla
    # Örn: https://www.youtube.com/channel/UCV6zcRug6Hqp1UX_FdyUeBg/live -> UCV6zcRug6Hqp1UX_FdyUeBg
    channel_id_match = re.search(r"channel/(UC[a-zA-Z0-9_\-]+)", channel_url)
    if not channel_id_match:
        # Eğer link zaten doğrudan sadece kanal ID'siyse veya farklı formatta ise koru
        channel_id = channel_url.strip().split("/")[-1].replace("/live", "")
    else:
        channel_id = channel_id_match.group(1)

    shared_headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
    }

    session = requests.Session()

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # ADIM 1: Ana sayfaya istek atıp 'set-cookie' içindeki session'ı yakala
            home_resp = session.get(
                "https://ytdlp.online/tr/", headers=shared_headers, timeout=15
            )
            cookies_dict = home_resp.cookies.get_dict()

            # Session çerezini kontrol et
            session_cookie = cookies_dict.get("session")
            if not session_cookie:
                # Çerez dict içinde doğrudan yoksa header metninden ara
                set_cookie_header = home_resp.headers.get("set-cookie", "")
                session_match = re.search(
                    r"session=([^;]+)", set_cookie_header, re.IGNORECASE
                )
                if session_match:
                    session_cookie = session_match.group(1)

            if not session_cookie:
                print(
                    "    Deneme {}/{}: [Hata] Siteden Session alınamadı".format(
                        attempt, MAX_RETRIES
                    )
                )
                continue

            # ADIM 2: Komutu hazırla ve API URL'sini oluştur
            command = "--get-url https://m.youtube.com/channel/{}/live".format(
                channel_id
            )
            encoded_command = requests.utils.quote(command)
            api_url = "https://ytdlp.online/api/v1/stream?command={}".format(
                encoded_command
            )

            # ADIM 3: Event-Stream header'ları ile API'ye istek gönder
            stream_headers = {
                "accept": "text/event-stream",
                "cookie": "session={}".format(session_cookie),
                "referer": "https://ytdlp.online/tr/",
                "user-agent": shared_headers["user-agent"],
            }

            stream_resp = session.get(
                api_url, headers=stream_headers, timeout=30
            )

            if stream_resp.status_code == 200:
                response_text = stream_resp.text

                # ADIM 4: Dönen metin akışından manifest.googlevideo.com linkini regex ile ayıkla
                manifest_match = re.search(
                    r"https://manifest\.googlevideo\.com/[^\s\"'<>]+",
                    response_text,
                )
                if manifest_match:
                    return manifest_match.group(0)

            print(
                "    Deneme {}/{}: Akış yanıtı boş döndü veya çözülemedi (Durum: {})".format(
                    attempt, MAX_RETRIES, stream_resp.status_code
                )
            )

        except Exception as e:
            print(
                "    Deneme {}/{}: İstek sırasında hata oluştu — {}".format(
                    attempt, MAX_RETRIES, str(e)[:70]
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

        # Paylaştığın worker algoritması devrede
        stream_url = get_stream_url_via_worker_logic(target_url)

        if stream_url:
            file_path = os.path.join(
                OUTPUT_FOLDER, "{}.m3u8".format(sanitize(name))
            )
            save_m3u8(file_path, stream_url, name, logo_url)
            print("    [OK] -> Orijinal Manifest URL Başarıyla Yakalandı")
            success_count += 1
        else:
            print("    [FAIL] ytdlp.online linki üretemedi -> {}".format(name))
            fail_count += 1
            failed_names.append(name)

    # ─── Birleşik liste oluşturma (_METV_COMBINED.m3u) ───
    combined_path = os.path.join(OUTPUT_FOLDER, "_METV_COMBINED.m3u")
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
