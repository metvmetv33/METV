import requests
from bs4 import BeautifulSoup
import json

def kanallari_cek(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.selcuksportshd.is/'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        kanal_listesi = []

        # Tüm kanal listelerini (tab1, tab2 vb.) bul
        channels_div = soup.find('div', class_='channel-list')
        if not channels_div:
            # Eğer id ile aramak gerekirse (paylaştığınız örnekte id="tab1")
            channels_div = soup.find(id='tab1')

        if channels_div:
            items = channels_div.find_all('li')
            for item in items:
                link_tag = item.find('a', data_url=True)
                if link_tag:
                    name_div = item.find('div', class_='name')
                    time_tag = item.find('time', class_='time')
                    
                    kanal_bilgisi = {
                        "ad": name_div.get_text(strip=True) if name_div else "Bilinmiyor",
                        "url": link_tag['data-url'],
                        "saat": time_tag.get_text(strip=True) if time_tag else ""
                    }
                    kanal_listesi.append(kanal_bilgisi)

        return kanal_listesi

    except Exception as e:
        print(f"Hata oluştu: {e}")
        return []

# Hedef URL
target_url = "https://www.selcuksportshd688829a7bd.xyz/"
veriler = kanallari_cek(target_url)

# Sonuçları JSON formatında yazdır
if veriler:
    print(json.dumps(veriler, indent=4, ensure_ascii=False))
else:
    print("Kanal verisi bulunamadı veya siteye erişilemedi.")
