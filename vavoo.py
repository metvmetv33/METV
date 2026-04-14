import requests
import json
import time
import os

BASE_DIR = os.path.dirname(__file__)

with open(os.path.join(BASE_DIR, "countries.json"), encoding="utf-8") as f:
    COUNTRIES = json.load(f)

# ================= SIGNATURE =================
def get_signature():
    url = "https://www.vavoo.tv/api/app/ping"

    headers = {
        "user-agent": "okhttp/4.11.0",
        "accept": "application/json",
        "content-type": "application/json; charset=utf-8",
        "accept-encoding": "gzip"
    }

    data = {
        "token": "tosFwQCJMS8qrW_AjLoHPQ41646J5dRNha6ZWHnijoYQQQoXYSo7ki7O5-CsgN4CH0uRk6EEoJ0728ar9scCRQW3ZkbfrPfeCXW2VgopSW2FWDqPOoVYIuVPAOnXCZ5g",
        "reason": "app-blur",
        "locale": "de",
        "theme": "dark",
        "metadata": {
            "device": {
                "type": "Handset",
                "brand": "google",
                "model": "Nexus",
                "name": "21081111RG",
                "uniqueId": "d10e5d99ab665233"
            },
            "os": {
                "name": "android",
                "version": "7.1.2",
                "abis": ["arm64-v8a", "armeabi-v7a", "armeabi"],
                "host": "android"
            },
            "app": {
                "platform": "android",
                "version": "3.1.20",
                "buildId": "289515000",
                "engine": "hbc85",
                "signatures": ["6e8a975e3cbf07d5de823a760d4c2547f86c1403105020adee5de67ac510999e"],
                "installer": "app.revanced.manager.flutter"
            },
            "version": {
                "package": "tv.vavoo.app",
                "binary": "3.1.20",
                "js": "3.1.20"
            }
        },
        "appFocusTime": 0,
        "playerActive": False,
        "playDuration": 0,
        "devMode": False,
        "hasAddon": True,
        "castConnected": False,
        "package": "tv.vavoo.app",
        "version": "3.1.20",
        "process": "app",
        "firstAppStart": 1743962904623,
        "lastAppStart": 1743962904623,
        "ipLocation": "",
        "adblockEnabled": True,
        "proxy": {
            "supported": ["ss", "openvpn"],
            "engine": "ss",
            "ssVersion": 1,
            "enabled": True,
            "autoServer": True,
            "id": "pl-waw"
        },
        "iap": {
            "supported": False
        }
    }

    for i in range(3):
        try:
            print(f"[INFO] Signature deneniyor... ({i+1}/3)")
            r = requests.post(url, json=data, headers=headers, timeout=15)

            if r.status_code == 200:
                sig = r.json().get("addonSig")
                if sig:
                    print("✅ Signature alındı")
                    return sig

            time.sleep(2)

        except Exception as e:
            print("[HATA]", e)

    return None


# ================= CHANNEL =================
def get_channels(signature, country):
    headers = {
        "user-agent": "okhttp/4.11.0",
        "accept": "application/json",
        "content-type": "application/json",
        "mediahubmx-signature": signature
    }

    channels = []
    cursor = 0

    while True:
        try:
            data = {
                "language": "de",
                "region": "AT",
                "catalogId": "iptv",
                "id": "iptv",
                "adult": False,
                "search": "",
                "sort": "name",
                "filter": {"group": country},
                "cursor": cursor,
                "clientVersion": "3.0.2"
            }

            r = requests.post(
                "https://vavoo.tv/mediahubmx-catalog.json",
                json=data,
                headers=headers,
                timeout=15
            )

            js = r.json()

            if "items" not in js:
                break

            channels.extend(js["items"])

            if not js.get("nextCursor"):
                break

            cursor = js["nextCursor"]

        except Exception as e:
            print(f"[HATA] {country}:", e)
            break

    return channels


# ================= SAVE =================
def save_m3u(country, channels):
    filename = f"{country.replace(' ', '_')}.m3u"

    with open(filename, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for ch in channels:
            if not ch.get("url"):
                continue

            name = ch.get("name", "Unknown")

            if isinstance(ch.get("ids"), dict) and ch["ids"].get("id"):
                link = f"https://vavoo.to/vavoo-iptv/play/{ch['ids']['id']}"
            else:
                link = ch["url"]

            f.write(f'#EXTINF:-1 group-title="{country}",{name}\n')
            f.write(link + "\n")

    print(f"✅ {filename} ({len(channels)} kanal)")


# ================= MAIN =================
def main():
    sig = get_signature()

    if not sig:
        print("❌ Signature alınamadı → script durdu")
        return

    for country in COUNTRIES:
        print(f"\n🌍 {country} çekiliyor...")

        channels = get_channels(sig, country)

        if not channels:
            print(f"⚠️ {country} boş geldi")
            continue

        save_m3u(country, channels)
        time.sleep(2)


if __name__ == "__main__":
    main()
