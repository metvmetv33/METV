import requests
import json

def get_m3u():
    # Ana kanal listesi URL'si
    list_url = "https://itvepg10004.tmp.tivibu.com.tr/iptvepg/frame3046/sdk_getchannellist.jsp?columncode=020000&pageno=1&numperpage=500&ordertype=1&isqueryfavorite=1&isqueryprevue=1&ischecklock=1"
    
    # Oynatma URL'si şablonu
    play_url_base = "https://itvepg10004.tmp.tivibu.com.tr/iptvepg/frame3046/sdk_getppvtvplayurl.jsp?channelcode={}&columncode=030000&urlredirect=1&playtype=0&productcode=5237"

    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(list_url, headers=headers)
        data = response.json()
        channels = data.get('data', [])
        
        m3u_content = "#EXTM3U\n"
        
        for ch in channels:
            ch_name = ch.get('channelname', 'Unknown')
            ch_code = ch.get('channelcode', '')
            
            if ch_code:
                # Her kanal için özel oynatma isteği atılıyor
                p_res = requests.get(play_url_base.format(ch_code), headers=headers)
                p_data = p_res.json()
                
                # 'playurl' veya 'httpsplayurl' anahtarını alıyoruz
                stream_url = p_data.get('playurl', p_data.get('httpsplayurl', ''))
                
                if stream_url:
                    m3u_content += f'#EXTINF:-1 tvg-id="{ch_code}" tvg-name="{ch_name}",{ch_name}\n'
                    m3u_content += f'{stream_url}\n'
        
        with open("tbu.m3u", "w", encoding="utf-8") as f:
            f.write(m3u_content)
            
        print("tbu.m3u başarıyla oluşturuldu.")

    except Exception as e:
        print(f"Hata oluştu: {e}")

if __name__ == "__main__":
    get_m3u()
