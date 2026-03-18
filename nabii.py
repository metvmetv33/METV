"""
tabii_m3u.py — Playwright ile Tabii kanallarından gerçek m3u8 URL'lerini çeker.

Kurulum:
    pip install playwright
    playwright install chromium

Çalıştır:
    python tabii_m3u.py

Çıktı: tabii.m3u
"""

import asyncio
import re
from playwright.async_api import async_playwright

CHANNELS = [
    # ── TRT Ana (sabit URL'ler — değişmiyor) ─────────────────
    {"id": "trt1",           "name": "TRT 1",           "group": "TABİİ",      "trackId": "150002",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/80196fc2-f4f6-4e35-ae29-7925a5885a20.png",
     "static_url": "https://tv-trt1.medya.trt.com.tr/master.m3u8"},
    {"id": "trt2",           "name": "TRT 2",           "group": "TABİİ",      "trackId": "150007",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/14a65b49-958f-497f-be22-52d958ef8498.png",
     "static_url": "https://tv-trt2.medya.trt.com.tr/master.m3u8"},
    {"id": "trthaber",       "name": "TRT Haber",       "group": "TABİİ",      "trackId": "150017",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/02ef58a4-349a-49a6-8df2-82fb71c6554d.png",
     "static_url": "https://tv-trthaber.medya.trt.com.tr/master.m3u8"},
    {"id": "trtworld",       "name": "TRT World",       "group": "TABİİ",      "trackId": "150063",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/500/500/channels/logos/acd68840-492b-43c5-9635-bbaf32148e2a.png",
     "static_url": "https://tv-trtworld.medya.trt.com.tr/master.m3u8"},
    {"id": "trtbelgesel",    "name": "TRT Belgesel",    "group": "TABİİ",      "trackId": "150012",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/6925f7f0-2d64-4a15-99ec-e4a19c117279.png",
     "static_url": "https://tv-trtbelgesel.medya.trt.com.tr/master.m3u8"},
    {"id": "trtmuzik",       "name": "TRT Müzik",       "group": "TABİİ",      "trackId": "150033",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/81ac5eb4-6201-47ce-977e-736a4247da91.png",
     "static_url": "https://tv-trtmuzik.medya.trt.com.tr/master.m3u8"},
    {"id": "trtturk",        "name": "TRT Türk",        "group": "TABİİ",      "trackId": "150043",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/0acb34e5-4b37-434e-b555-c7eb0271ba9d.png",
     "static_url": "https://tv-trtturk.medya.trt.com.tr/master.m3u8"},
    {"id": "trtkurdi",       "name": "TRT Kurdî",       "group": "TABİİ",      "trackId": "150053",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/1d937ced-d803-47eb-aa0c-90586e4e162e.png",
     "static_url": "https://tv-trtkurdi.medya.trt.com.tr/master.m3u8"},
    {"id": "trtgenc",        "name": "TRT Genç",        "group": "TABİİ",      "trackId": "606324",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/39f0e8c7-d450-4b90-b8fc-58211e3da29c.png",
     "static_url": "https://tv-trtgenc.medya.trt.com.tr/master.m3u8"},
    {"id": "trtarabi",       "name": "TRT Arabi",       "group": "TABİİ",      "trackId": "150058",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/1857f0c2-3a80-4b95-bb35-ffcefdcf4729.png",
     "static_url": "https://tv-trtarabi.medya.trt.com.tr/master.m3u8"},
    {"id": "trtavaz",        "name": "TRT Avaz",        "group": "TABİİ",      "trackId": "150048",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/4a3026d6-b1be-4373-bb83-447117196e55.png",
     "static_url": "https://tv-trtavaz.medya.trt.com.tr/master.m3u8"},
    {"id": "trtcocuk",       "name": "TRT Çocuk",       "group": "TABİİ",      "trackId": "150038",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/3261c5eb-0e08-4c96-b8fc-58211e3da29c.png",
     "static_url": "https://tv-trtcocuk.medya.trt.com.tr/master.m3u8"},
    {"id": "trtdiyanetcocuk","name": "TRT Diyanet Çocuk","group": "TABİİ",     "trackId": "171018",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/7e733bf8-6c0e-4d6e-b18a-5864e571894b.png",
     "static_url": "https://tv-trtdiyanetcocuk.medya.trt.com.tr/master.m3u8"},
    {"id": "trteba",         "name": "TRT EBA TV",      "group": "TABİİ",      "trackId": "293389",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/47fcca43-c2ac-4ab8-ae92-2b007655be9f.png",
     "static_url": "https://tv-e-okul01.medya.trt.com.tr/master.m3u8"},
    # ── TRT Spor (daioncdn — sabit) ───────────────────────────
    {"id": "trtspor",        "name": "TRT Spor",        "group": "TABİİ Spor", "trackId": "150022",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/46319886-6c97-4640-8d63-8e4b11511c74.png",
     "static_url": "https://trt.daioncdn.net/trtspor/master.m3u8?app=clean"},
    {"id": "trtsporyildiz",  "name": "TRT Spor Yıldız", "group": "TABİİ Spor", "trackId": "150028",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/02ef58a4-349a-49a6-8df2-82fb71c6554d.png",
     "static_url": "https://trt.daioncdn.net/trtspor-yildiz/master.m3u8?app=clean"},
    # ── Tabii Spor (hashli — Playwright ile çekilecek) ────────
    {"id": "tabiispor",      "name": "Tabii Spor",      "group": "TABİİ Spor", "trackId": "419561",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/43023.jpeg"},
    {"id": "tabiispor1",     "name": "Tabii Spor 1",    "group": "TABİİ Spor", "trackId": "401207",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/43005.jpeg"},
    {"id": "tabiispor2",     "name": "Tabii Spor 2",    "group": "TABİİ Spor", "trackId": "404583",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/43008.jpeg"},
    {"id": "tabiispor3",     "name": "Tabii Spor 3",    "group": "TABİİ Spor", "trackId": "404630",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/43011.jpeg"},
    {"id": "tabiispor4",     "name": "Tabii Spor 4",    "group": "TABİİ Spor", "trackId": "404637",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/43014.jpeg"},
    {"id": "tabiispor5",     "name": "Tabii Spor 5",    "group": "TABİİ Spor", "trackId": "404646",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/43017.jpeg"},
    {"id": "tabiispor6",     "name": "Tabii Spor 6",    "group": "TABİİ Spor", "trackId": "404666",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/43020.jpeg"},
    {"id": "tabiitv",        "name": "Tabii TV",        "group": "TABİİ",      "trackId": "383911",
     "logo": "https://cms-tabii-public-image.tabii.com/int/w300/45155_0-0-1919-1080.jpeg"},
    {"id": "tabiicocuk",     "name": "Tabii Çocuk",     "group": "TABİİ",      "trackId": "516992",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/3261c5eb-0e08-4c96-b8fc-58211e3da29c.png"},
]

async def get_m3u8_playwright(page, channel):
    """Playwright ile sayfayı aç, ağ isteklerini dinle, m3u8 URL'yi yakala"""
    found_url = None

    def on_request(request):
        nonlocal found_url
        url = request.url
        if ".m3u8" in url and "medya.trt.com.tr" in url and found_url is None:
            found_url = url

    page.on("request", on_request)

    page_url = f"https://www.tabii.com/tr/watch/live/{channel['id']}?trackId={channel['trackId']}"
    try:
        await page.goto(page_url, wait_until="networkidle", timeout=20000)
        # Video player yüklenene kadar biraz bekle
        await asyncio.sleep(3)
    except Exception as e:
        print(f"  Sayfa hatası: {e}")

    page.remove_listener("request", on_request)
    return found_url

async def main():
    m3u_lines = ["#EXTM3U\n"]
    success = 0
    fail = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

        for ch in CHANNELS:
            print(f"[+] {ch['name']} çekiliyor...", end=" ", flush=True)

            # Sabit URL'si varsa direkt kullan
            if ch.get("static_url"):
                stream_url = ch["static_url"]
                print(f"✓ (sabit) {stream_url[:60]}")
            else:
                # Playwright ile hashli URL'yi çek
                page = await context.new_page()
                stream_url = await get_m3u8_playwright(page, ch)
                await page.close()

                if stream_url:
                    # master_1080p yerine master kullan (daha uyumlu)
                    stream_url = stream_url.split("?")[0]  # query string temizle
                    if "master_1080p" not in stream_url:
                        stream_url = stream_url.replace("master.m3u8", "master_1080p.m3u8")
                    print(f"✓ {stream_url[:60]}")
                else:
                    print("✗ bulunamadı")
                    fail += 1
                    continue

            line = (
                f'#EXTINF:-1 tvg-id="{ch["id"]}" tvg-name="{ch["name"]}" '
                f'tvg-logo="{ch["logo"]}" group-title="{ch["group"]}",{ch["name"]}\n'
                f'{stream_url}\n'
            )
            m3u_lines.append(line)
            success += 1

        await browser.close()

    with open("tabii.m3u", "w", encoding="utf-8") as f:
        f.writelines(m3u_lines)

    print(f"\n[*] {success} başarılı, {fail} başarısız → tabii.m3u kaydedildi")

if __name__ == "__main__":
    asyncio.run(main())
