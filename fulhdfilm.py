import requests
from bs4 import BeautifulSoup
import json

def film_cek():
    url = "https://www.fullhdfilmizlesene.live/"
    
    # Tarayıcı taklidi (Sizin gönderdiğiniz güncel User-Agent)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': 'https://www.google.com/'
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code != 200:
            print(f"Hata: Siteye erisilemedi. Kod: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        film_listesi = []

        # Tüm li.film öğelerini bul
        filmler = soup.find_all('li', class_='film')

        for film in filmler:
            try:
                baslik_tr = film.find('span', class_='film-title').get_text(strip=True) if film.find('span', class_='film-title') else ""
                baslik_en = film.find('span', class_='kt').get_text(strip=True) if film.find('span', class_='kt') else ""
                imdb = film.find('span', class_='imdb').get_text(strip=True) if film.find('span', class_='imdb') else "N/A"
                yil = film.find('span', class_='film-yil').get_text(strip=True) if film.find('span', class_='film-yil') else ""
                tur = film.find('span', class_='ktt').get_text(strip=True) if film.find('span', class_='ktt') else ""
                url_link = film.find('a', class_='tt')['href'] if film.find('a', class_='tt') else ""
                
                # Afiş çekme (data-src veya src)
                img_tag = film.find('img')
                afis = ""
                if img_tag:
                    afis = img_tag.get('data-src') or img_tag.get('src')

                if baslik_tr:
                    film_listesi.append({
                        "baslik_tr": baslik_tr,
                        "baslik_en": baslik_en,
                        "imdb": imdb,
                        "yil": yil,
                        "tur": tur,
                        "afis": afis,
                        "url": url_link
                    })
            except Exception as e:
                continue

        # JSON dosyasına kaydet
        with open('film.json', 'w', encoding='utf-8') as f:
            json.dump(film_listesi, f, ensure_ascii=False, indent=4)
        
        print(f"Başarılı: {len(film_listesi)} film kaydedildi.")

    except Exception as e:
        print(f"Sistem Hatası: {e}")

if __name__ == "__main__":
    film_cek()
