import re
import requests
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

def find_active_domain():
    # Güncel giriş adresleri buraya eklenebilir
    test_urls = ["https://www.selcuksportshd688829a7bd.xyz/", "https://www.selcuksportshd.is/"]
    for url in test_urls:
        try:
            res = requests.get(url, headers=HEADERS, timeout=10, verify=False)
            if res.status_code == 200 and "data-url" in res.text:
                return url, res.text
        except: continue
    return None, None

def get_m3u8(player_url, referer):
    try:
        res = requests.get(player_url, headers={"User-Agent": HEADERS["User-Agent"], "Referer": referer}, timeout=10, verify=False)
        base_url = re.search(r'this\.baseStreamUrl\s*=\s*["\']([^"\']+)["\']', res.text)
        stream_id = re.search(r"id=([a-zA-Z0-9_-]+)", player_url)
        if base_url and stream_id:
            return f"{base_url.group(1).rstrip('/')}/{stream_id.group(1)}/playlist.m3u8"
    except: return None
    return None

def run():
    domain, html = find_active_domain()
    if not domain: return
    
    soup = BeautifulSoup(html, "html.parser")
    items = soup.find_all("a", attrs={"data-url": True})
    m3u = ["#EXTM3U"]
    
    for item in items:
        raw_url = item["data-url"]
        if "gecersiz" in raw_url or not raw_url.startswith("http"): continue
        
        name = item.find("div", class_="name").get_text(strip=True) if item.find("div", class_="name") else "Kanal"
        link = get_m3u8(raw_url, domain)
        
        if link:
            m3u.append(f'#EXTINF:-1, {name}')
            m3u.append(f'#EXTVLCOPT:http-referrer={domain}')
            m3u.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
            m3u.append(link)
            
    with open("selcukk.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u))
    print(f"Bitti: {len(m3u)//4} kanal eklendi.")

if __name__ == "__main__":
    run()
