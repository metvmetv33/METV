import requests
from bs4 import BeautifulSoup
import json
import os
import time

# Dosyaların saklanacağı klasör
if not os.path.exists('data'):
    os.makedirs('data')

def sayfa_cek_ve_kaydet(page_num):
    base_url = f"https://www.fullhdfilmizlesene.live/yeni-filmler/{page_num}"
    if page_num == 1:
        base_url = "https://www.fullhdfilmizlesene.live/yeni-filmler/"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
        'Referer': 'https://www.google.com/'
    }

    try:
        response = requests.get(base_url, headers=headers, timeout=20)
        if response.status_code != 200:
            print(f"Sayfa {page_num} hatası: {response.status_code}")
            return False

        soup = BeautifulSoup(response.text, 'html.parser')
        films = soup.find_all('li', class_='film')
        
        movie_data = []
        for film in films:
            title = film.find('span', class_='film-title')
            link = film.find('a', class_='tt')
            if title and link:
                movie_data.append({
                    "title": title.get_text(strip=True),
                    "link": link['href'].rstrip('/'),
                    "imdb": film.find('span', class_='imdb').get_text(strip=True) if film.find('span', class_='imdb') else "0",
                    "year": film.find('span', class_='film-yil').get_text(strip=True) if film.find('span', class_='film-yil') else "",
                    "image": (film.find('img').get('data-src') or film.find('img').get('src')) if film.find('img') else ""
                })

        if movie_data:
            with open(f'data/yeni-filmler-{page_num}.json', 'w', encoding='utf-8') as f:
                json.dump(movie_data, f, ensure_ascii=False, indent=4)
            return True
    except Exception as e:
        print(f"Hata oluştu: {e}")
    return False

def main():
    # 1113 sayfa çok uzun sürebilir, ilk etapta 50-100 sayfa ile test etmeni öneririm
    # Tümünü çekmek istersen 1114 yapabilirsin
    hedef_sayfa = 100 
    
    for p in range(1, hedef_sayfa + 1):
        print(f"Sayfa {p} işleniyor...")
        success = sayfa_cek_ve_kaydet(p)
        if not success:
            print("Sayfa çekilemedi, durduruluyor.")
            break
        # Cloudflare'e yakalanmamak için kısa bir mola
        if p % 5 == 0:
            time.sleep(1)

if __name__ == "__main__":
    main()
