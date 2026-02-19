import requests
from bs4 import BeautifulSoup
import json
import time

def film_verilerini_cek(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': 'https://www.google.com/'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        film_listesi = []
        filmler = soup.find_all('li', class_='film')

        for film in filmler:
            try:
                # Başlık ve Link
                link_tag = film.find('a', class_='tt')
                if not link_tag: continue
                
                baslik_tr = film.find('span', class_='film-title').get_text(strip=True) if film.find('span', class_='film-title') else ""
                
                # Resim (Sizin paylaştığınız PHP kodundaki mantık: picture/img)
                img_tag = film.find('img')
                afis = ""
                if img_tag:
                    afis = img_tag.get('data-src') or img_tag.get('src') or img_tag.get('data-srcset')

                film_listesi.append({
                    "title": baslik_tr,
                    "link": link_tag['href'].rstrip('/'),
                    "image": afis.split(' ')[0] if afis else "https://via.placeholder.com/150",
                    "imdb": film.find('span', class_='imdb').get_text(strip=True) if film.find('span', class_='imdb') else "0",
                    "year": film.find('span', class_='film-yil').get_text(strip=True) if film.find('span', class_='film-yil') else "N/A"
                })
            except:
                continue
        return film_listesi
    except:
        return []

def main():
    base_url = "https://www.fullhdfilmizlesene.live/"
    kategoriler = ["yeni-filmler", "aksiyon-filmleri", "komedi-filmleri"] # Buraya istediğin kategorileri ekle
    max_sayfa = 2 # Her kategori için kaç sayfa çekilsin?
    
    tum_veriler = {}

    for kat in kategoriler:
        print(f"Kategori çekiliyor: {kat}")
        tum_veriler[kat] = []
        
        for sayfa in range(1, max_sayfa + 1):
            if kat == "yeni-filmler":
                url = f"{base_url}{kat}/" if sayfa == 1 else f"{base_url}{kat}/{sayfa}"
            else:
                url = f"{base_url}filmizle/{kat}/" if sayfa == 1 else f"{base_url}filmizle/{kat}/{sayfa}"
            
            print(f"Sayfa {sayfa} taranıyor: {url}")
            veriler = film_verilerini_cek(url)
            if not veriler: break
            tum_veriler[kat].extend(veriler)
            time.sleep(1) # Siteyi yormamak için kısa bekleme

    # GitHub'a kaydedilecek ana dosya
    with open('film.json', 'w', encoding='utf-8') as f:
        json.dump(tum_veriler, f, ensure_ascii=False, indent=4)
    
    print("İşlem tamamlandı, JSON güncellendi.")

if __name__ == "__main__":
    main()
