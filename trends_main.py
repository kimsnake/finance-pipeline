import requests
import pandas as pd
import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}
COUNTRIES = {
    'KR': 'https://trends.google.com/trending/rss?geo=KR',
    'US': 'https://trends.google.com/trending/rss?geo=US',
    'JP': 'https://trends.google.com/trending/rss?geo=JP'
}

def fetch_and_save():
    for code, url in COUNTRIES.items():
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code != 200: continue
            
            # BeautifulSoup으로 XML 파싱
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')
            data = []

            for item in items:
                # pubDate 파싱 (KST 변환)
                pub_date_str = item.pubDate.text
                pub_date = pd.to_datetime(pub_date_str, utc=True).tz_convert('Asia/Seoul')
                
                row = {
                    'pubDate_KST': pub_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'keyword': item.title.text,
                    'traffic': item.find('ht:approx_traffic').text if item.find('ht:approx_traffic') else 'N/A'
                }
                
                # 뉴스 추출 (ht:news_item을 찾아서 하나씩 저장)
                news_items = item.find_all('ht:news_item')
                for i in range(3):
                    idx = i + 1
                    if i < len(news_items):
                        n = news_items[i]
                        row[f'news{idx}_title'] = n.find('ht:news_item_title').text if n.find('ht:news_item_title') else 'N/A'
                        row[f'news{idx}_url'] = n.find('ht:news_item_url').text if n.find('ht:news_item_url') else 'N/A'
                        row[f'news{idx}_source'] = n.find('ht:news_item_source').text if n.find('ht:news_item_source') else 'N/A'
                    else:
                        row[f'news{idx}_title'] = 'N/A'
                        row[f'news{idx}_url'] = 'N/A'
                        row[f'news{idx}_source'] = 'N/A'
                
                data.append(row)
            
            new_df = pd.DataFrame(data)

            folder_path = os.path.join("data/trends", code)
            os.makedirs(folder_path, exist_ok=True)
            file_path = os.path.join(folder_path, f"{datetime.now().strftime('%Y%m')}_{code}_trends.csv")

            if os.path.exists(file_path):
                existing_df = pd.read_csv(file_path)
                existing_df['pubDate_KST'] = pd.to_datetime(existing_df['pubDate_KST'])
                
                # 중복 및 변화 감지 로직 적용
                to_save = []
                for _, new_row in new_df.iterrows():
                    match = existing_df[(existing_df['keyword'] == new_row['keyword']) & 
                                       (existing_df['pubDate_KST'] == new_row['pubDate_KST'])]
                    if match.empty:
                        to_save.append(new_row)
                
                if to_save:
                    pd.DataFrame(to_save).to_csv(file_path, mode='a', header=False, index=False, encoding='utf-8-sig')
            else:
                new_df.to_csv(file_path, index=False, encoding='utf-8-sig')
                
            print(f"[{code}] 수집 완료: 뉴스 포함")
            
        except Exception as e:
            print(f"[{code}] 오류 발생: {e}")

if __name__ == "__main__":
    fetch_and_save()