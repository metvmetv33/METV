"""
nabii.py — Tabii/TRT kanallarından m3u8 URL çeker
- Sabit kanallar: requests ile direkt
- Hashli Tabii Spor kanalları: Playwright ile ağ isteği yakalama
"""

import asyncio
import re
import requests
from playwright.async_api import async_playwright

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer":    "https://www.tabii.com/",
})

CHANNELS = [
    # ── Sabit URL'li TRT kanalları ───────────────────────────
    {"id": "trt1",           "name": "TRT 1",            "group": "TABİİ",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/80196fc2-f4f6-4e35-ae29-7925a5885a20.png",
     "static": "https://tv-trt1.medya.trt.com.tr/master.m3u8"},
    {"id": "trt2",           "name": "TRT 2",            "group": "TABİİ",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/14a65b49-958f-497f-be22-52d958ef8498.png",
     "static": "https://tv-trt2.medya.trt.com.tr/master.m3u8"},
    {"id": "trthaber",       "name": "TRT Haber",        "group": "TABİİ",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/02ef58a4-349a-49a6-8df2-82fb71c6554d.png",
     "static": "https://tv-trthaber.medya.trt.com.tr/master.m3u8"},
    {"id": "trtworld",       "name": "TRT World",        "group": "TABİİ",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/500/500/channels/logos/acd68840-492b-43c5-9635-bbaf32148e2a.png",
     "static": "https://tv-trtworld.medya.trt.com.tr/master.m3u8"},
    {"id": "trtbelgesel",    "name": "TRT Belgesel",     "group": "TABİİ",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/6925f7f0-2d64-4a15-99ec-e4a19c117279.png",
     "static": "https://tv-trtbelgesel.medya.trt.com.tr/master.m3u8"},
    {"id": "trtmuzik",       "name": "TRT Müzik",        "group": "TABİİ",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/81ac5eb4-6201-47ce-977e-736a4247da91.png",
     "static": "https://tv-trtmuzik.medya.trt.com.tr/master.m3u8"},
    {"id": "trtturk",        "name": "TRT Türk",         "group": "TABİİ",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/0acb34e5-4b37-434e-b555-c7eb0271ba9d.png",
     "static": "https://tv-trtturk.medya.trt.com.tr/master.m3u8"},
    {"id": "trtkurdi",       "name": "TRT Kurdî",        "group": "TABİİ",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/1d937ced-d803-47eb-aa0c-90586e4e162e.png",
     "static": "https://tv-trtkurdi.medya.trt.com.tr/master.m3u8"},
    {"id": "trtgenc",        "name": "TRT Genç",         "group": "TABİİ",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/39f0e8c7-d450-4b90-b8fc-58211e3da29c.png",
     "static": "https://tv-trtgenc.medya.trt.com.tr/master.m3u8"},
    {"id": "trtarabi",       "name": "TRT Arabi",        "group": "TABİİ",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/1857f0c2-3a80-4b95-bb35-ffcefdcf4729.png",
     "static": "https://tv-trtarabi.medya.trt.com.tr/master.m3u8"},
    {"id": "trtavaz",        "name": "TRT Avaz",         "group": "TABİİ",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/4a3026d6-b1be-4373-bb83-447117196e55.png",
     "static": "https://tv-trtavaz.medya.trt.com.tr/master.m3u8"},
    {"id": "trtcocuk",       "name": "TRT Çocuk",        "group": "TABİİ",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/3261c5eb-0e08-4c96-b8fc-58211e3da29c.png",
     "static": "https://tv-trtcocuk.medya.trt.com.tr/master.m3u8"},
    {"id": "trtdiyanetcocuk","name": "TRT Diyanet Çocuk","group": "TABİİ",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/7e733bf8-6c0e-4d6e-b18a-5864e571894b.png",
     "static": "https://tv-trtdiyanetcocuk.medya.trt.com.tr/master.m3u8"},
    {"id": "trteba",         "name": "TRT EBA TV",       "group": "TABİİ",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/47fcca43-c2ac-4ab8-ae92-2b007655be9f.png",
     "static": "https://tv-e-okul01.medya.trt.com.tr/master.m3u8"},
    {"id": "trtspor",        "name": "TRT Spor",         "group": "TABİİ Spor",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/46319886-6c97-4640-8d63-8e4b11511c74.png",
     "static": "https://trt.daioncdn.net/trtspor/master.m3u8?app=clean"},
    {"id": "trtsporyildiz",  "name": "TRT Spor Yıldız",  "group": "TABİİ Spor",
     "logo": "https://feo.kablowebtv.com/resize/168A635D265A4328C2883FB4CD8FF/0/0/Vod/HLS/02ef58a4-349a-49a6-8df2-82fb71c6554d.png",
     "static": "https://trt.daioncdn.net/trtspor-yildiz/master.m3u8?app=clean"},

    # ── Hashli Tabii Spor — Playwright ile çekilecek ─────────
    {"id": "tabiispor",  "name": "Tabii Spor",   "group": "TABİİ Spor", "trackId": "419561",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/43023.jpeg"},
    {"id": "tabiispor1", "name": "Tabii Spor 1", "group": "TABİİ Spor", "trackId": "401207",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/43005.jpeg"},
    {"id": "tabiispor2", "name": "Tabii Spor 2", "group": "TABİİ Spor", "trackId": "404583",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/43008.jpeg"},
    {"id": "tabiispor3", "name": "Tabii Spor 3", "group": "TABİİ Spor", "trackId": "404630",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/43011.jpeg"},
    {"id": "tabiispor4", "name": "Tabii Spor 4", "group": "TABİİ Spor", "trackId": "404637",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/43014.jpeg"},
    {"id": "tabiispor5", "name": "Tabii Spor 5", "group": "TABİİ Spor", "trackId": "404646",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/43017.jpeg"},
    {"id": "tabiispor6", "name": "Tabii Spor 6", "group": "TABİİ Spor", "trackId": "404666",
     "logo": "https://cms-tabii-public-image.tabii.com/int/webp/w600/q84/43020.jpeg"},
    {"id": "tabiitv",    "name": "Tabii TV",     "group": "TABİİ",      "trackId": "383911",
     "logo": "https://cms-tabii-public-image.tabii.com/int/w300/45155_0-0-1919-1080.jpeg"},
]

async def fetch_dynamic_urls(dynamic_channels):
    """Playwright ile hashli URL'leri yakala"""
    results = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

        for ch in dynamic_channels:
            print(f"[+] {ch['name']} çekiliyor...", end=" ", flush=True)
            found = None

            page = await context.new_page()

            async def on_request(request):
                nonlocal found
                url = request.url
                if found is None and ".m3u8" in url and "medya.trt.com.tr" in url:
                    found = url.split("?")[0]  # query string temizle

            page.on("request", on_request)

            try:
                page_url = f"https://www.tabii.com/tr/watch/live/{ch['id']}?trackId={ch['trackId']}"
                await page.goto(page_url, wait_until="domcontentloaded", timeout=25000)
                # Video player'ın stream URL'sini yüklemesi için bekle
                await asyncio.sleep(5)
            except Exception as e:
                print(f"  sayfa hatası: {e}", end=" ")

            await page.close()

            if found:
                results[ch["id"]] = found
                print(f"✓ {found[:65]}")
            else:
                print("✗ bulunamadı")

        await browser.close()

    return results

def main():
    static_channels  = [ch for ch in CHANNELS if ch.get("static")]
    dynamic_channels = [ch for ch in CHANNELS if not ch.get("static")]

    m3u_lines = ["#EXTM3U\n"]
    success = 0
    fail    = 0

    # Sabit kanalları ekle
    for ch in static_channels:
        print(f"[+] {ch['name']} çekiliyor... ✓ (sabit)")
        line = (
            f'#EXTINF:-1 tvg-id="{ch["id"]}" tvg-name="{ch["name"]}" '
            f'tvg-logo="{ch["logo"]}" group-title="{ch["group"]}",{ch["name"]}\n'
            f'{ch["static"]}\n'
        )
        m3u_lines.append(line)
        success += 1

    # Dinamik kanalları Playwright ile çek
    if dynamic_channels:
        dynamic_urls = asyncio.run(fetch_dynamic_urls(dynamic_channels))
        for ch in dynamic_channels:
            url = dynamic_urls.get(ch["id"])
            if url:
                line = (
                    f'#EXTINF:-1 tvg-id="{ch["id"]}" tvg-name="{ch["name"]}" '
                    f'tvg-logo="{ch["logo"]}" group-title="{ch["group"]}",{ch["name"]}\n'
                    f'{url}\n'
                )
                m3u_lines.append(line)
                success += 1
            else:
                fail += 1

    with open("tabii.m3u", "w", encoding="utf-8") as f:
        f.writelines(m3u_lines)

    print(f"\n[*] {success} başarılı, {fail} başarısız → tabii.m3u kaydedildi")

if __name__ == "__main__":
    main()
