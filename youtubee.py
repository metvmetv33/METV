import os
import re
import time
from typing import Optional
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ─── Ayarlar ───────────────────────────────────────────────
JSON_URL      = "https://raw.githubusercontent.com/metvmetv33/METV/refs/heads/main/muomube.json"
OUTPUT_FOLDER = "metv"
MAX_RETRIES   = 2
WAIT_TIME     = 3
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


def manifest_to_variant(manifest_url):
    # type: (str) -> str
    """
    manifest.googlevideo.com/api/manifest/hls_playlist/.../itag/96/.../playlist/index.m3u8
    → hls_variant URL'ye çevir (hem video hem ses içerir, tüm kaliteler)
    """
    url = manifest_url
    # hls_playlist → hls_variant
    url = url.replace("/hls_playlist/", "/hls_variant/")
    # itag/SAYI/ kaldır (variant'ta gerek yok)
    url = re.sub(r"/itag/\d+", "", url)
    # playlist/index.m3u8 → index.m3u8
    url = re.sub(r"/playlist/index\.m3u8$", "/index.m3u8", url)
    # sgoap / sgovp parametrelerini kaldır (variant'ta anlamsız)
    url = re.sub(r"/sgoap/[^/]+", "", url)
    url = re.sub(r"/sgovp/[^/]+", "", url)
    return url


def get_stream_url(channel_url):
    # type: (str) -> Optional[str]
    channel_id_match = re.search(r"channel/(UC[a-zA-Z0-9_\-]+)", channel_url)
    if channel_id_match:
        channel_id = channel_id_match.group(1)
    else:
        channel_id = channel_url.strip().rstrip("/").split("/")[-1].replace("live", "").strip("/")

    shared_headers = {
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/137.0.0.0 Safari/537.36"
        )
    }

    session = requests.Session()

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # ADIM 1: Session cookie al
            home_resp = session.get(
                "https://ytdlp.online/tr/",
                headers=shared_headers,
                timeout=15,
                verify=False
            )
            cookies_dict = home_resp.cookies.get_dict()
            session_cookie = cookies_dict.get("session")

            if not session_cookie:
                set_cookie_header = home_resp.headers.get("set-cookie", "")
                m = re.search(r"session=([^;]+)", set_cookie_header, re.IGNORECASE)
                if m:
                    session_cookie = m.group(1)

            if not session_cookie:
                print("    Deneme {}/{}: Session alinamadi (HTTP {})".format(
                    attempt, MAX_RETRIES, home_resp.status_code))
                time.sleep(WAIT_TIME)
                continue

            # ADIM 2: ytdlp.online API komutu
            # -f "93/94/95/96/best" → muxed HLS formatlarını tercih et
            # itag 91=240p 92=360p 93=480p 94=720p 95=1080p (hepsi ses+video)
            # itag 96=1080p video only → bunu KULLANMA
            command = (
                '-f "95/94/93/92/91/best[acodec!=none]" '
                '--get-url https://m.youtube.com/channel/{}/live'.format(channel_id)
            )
            encoded_command = requests.utils.quote(command)
            api_url = "https://ytdlp.online/api/v1/stream?command={}".format(encoded_command)

            stream_headers = {
                "accept":     "text/event-stream",
                "cookie":     "session={}".format(session_cookie),
                "referer":    "https://ytdlp.online/tr/",
                "user-agent": shared_headers["user-agent"],
            }

            # ADIM 3: Stream yanıtını al
            stream_resp = session.get(
                api_url,
                headers=stream_headers,
                timeout=40,
                verify=False
            )

            if stream_resp.status_code != 200:
                print("    Deneme {}/{}: HTTP {}".format(
                    attempt, MAX_RETRIES, stream_resp.status_code))
                time.sleep(WAIT_TIME)
                continue

            response_text = stream_resp.text

            # ADIM 4: Yanıtten URL'yi çek
            # Önce hls_variant URL ara (muxed = ses+video)
            variant_match = re.search(
                r"https://manifest\.googlevideo\.com/api/manifest/hls_variant/[^\s\"'<>\n]+",
                response_text
            )
            if variant_match:
                return variant_match.group(0)

            # hls_playlist URL varsa variant'a çevir
            playlist_match = re.search(
                r"https://manifest\.googlevideo\.com/api/manifest/hls_playlist/[^\s\"'<>\n]+",
                response_text
            )
            if playlist_match:
                raw_url = playlist_match.group(0)
                # itag 91-95 arası = muxed (ses+video) → direkt kullan
                itag_m = re.search(r"/itag/(\d+)", raw_url)
                if itag_m:
                    itag = int(itag_m.group(1))
                    if itag in (91, 92, 93, 94, 95):
                        return raw_url   # zaten muxed, direkt kullan
                # itag=96 veya bilinmeyen → variant URL'ye çevir
                return manifest_to_variant(raw_url)

            # Herhangi bir googlevideo URL'si
            gv_match = re.search(
                r"https://[a-z0-9\-]+\.googlevideo\.com/[^\s\"'<>\n]+",
                response_text
            )
            if gv_match:
                return gv_match.group(0)

            print("    Deneme {}/{}: URL bulunamadi.".format(attempt, MAX_RETRIES))

        except Exception as e:
            print("    Deneme {}/{}: Hata — {}".format(attempt, MAX_RETRIES, str(e)[:80]))

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
    fail_count    = 0
    failed_names  = []

    for i, ch in enumerate(channels, 1):
        name       = ch.get("name", "Kanal_{}".format(i))
        target_url = ch.get("url", "").strip()
        logo_url   = ch.get("logo", "")

        if not target_url:
            continue

        print("[{}/{}] {}".format(i, len(channels), name))

        stream_url = get_stream_url(target_url)

        if stream_url:
            file_path = os.path.join(OUTPUT_FOLDER, "{}.m3u8".format(sanitize(name)))
            save_m3u8(file_path, stream_url, name, logo_url)
            # URL türünü logla
            if "hls_variant" in stream_url:
                url_type = "hls_variant (ses+video)"
            elif "hls_playlist" in stream_url:
                itag_m = re.search(r"/itag/(\d+)", stream_url)
                itag = itag_m.group(1) if itag_m else "?"
                url_type = "hls_playlist itag={} ({})".format(
                    itag, "ses+video" if itag_m and int(itag_m.group(1)) in (91,92,93,94,95) else "sadece-video!"
                )
            else:
                url_type = "googlevideo"
            print("    [OK] {} -> {}".format(url_type, file_path))
            success_count += 1
        else:
            print("    [FAIL] -> {}".format(name))
            fail_count += 1
            failed_names.append(name)

        time.sleep(1)

    # ─── Birleşik liste ──────────────────────────────────
    combined_path = os.path.join(OUTPUT_FOLDER, "_METV_COMBINED.m3u")
    entries = []
    for m3u8_file in sorted(os.listdir(OUTPUT_FOLDER)):
        if not m3u8_file.endswith(".m3u8") or m3u8_file.startswith("_"):
            continue
        full = os.path.join(OUTPUT_FOLDER, m3u8_file)
        with open(full, encoding="utf-8") as f:
            content = f.read()
        body = re.sub(r"^#EXTM3U\n?(?:#EXT-X-VERSION:[0-9]\n?)?", "", content).strip()
        entries.append(body)

    with open(combined_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n" + "\n".join(entries) + "\n")

    print("\n" + "=" * 55)
    print("TAMAMLANDI   OK:{}   FAIL:{}   TOPLAM:{}".format(
        success_count, fail_count, success_count + fail_count))
    if failed_names:
        print("\nCozulemeyen kanallar ({}):".format(len(failed_names)))
        for n in failed_names:
            print("  - {}".format(n))
    print("\n[+] Birlesik IPTV Listesi -> {}".format(combined_path))


if __name__ == "__main__":
    main()
