import yfinance as yf
import pandas as pd
import os
import time
from datetime import datetime, timedelta, timezone

# 각 카테고리별로 티커를 묶어서 관리하며, 주석으로 상세 설명을 추가했습니다.
CATEGORIES = {
    'currency': {
        'USDKRW': 'USDKRW=X',  # 달러/원: 한국 시장의 기준 환율
        'EURKRW': 'EURKRW=X',  # 유로/원: 유럽 경제 지표
        'JPYKRW': 'JPYKRW=X',  # 엔화/원: 아시아 안전자산 지표
        'CNYKRW': 'CNYKRW=X',  # 위안/원: 한국 수출 의존도 지표
        'GBPKRW': 'GBPKRW=X',  # 파운드/원: 영국 금융/경제 지표
        'AUDKRW': 'AUDKRW=X',  # 호주달러/원: 원자재 강국 통화
        'CADKRW': 'CADKRW=X',  # 캐나다달러/원: 북미 에너지 통화
        'CHFKRW': 'CHFKRW=X',  # 스위스프랑/원: 대표적 안전자산
        # 'RUBKRW': 'RUBKRW=X',  # 루블/원: 지정학적 리스크 지표
        'HKDKRW': 'HKDKRW=X',  # 홍콩달러/원: 아시아 금융 허브
        # 'MXNKRW': 'MXNKRW=X',  # 멕시코 페소/원: 신흥국 통화
        'BRLKRW': 'BRLKRW=X',  # 브라질 헤알/원: 남미 자원국 통화
        # 'TRYKRW': 'TRYKRW=X',  # 터키 리라/원: 신흥국 경제 리스크
        'ZARKRW': 'ZARKRW=X',  # 남아공 랜드/원: 아프리카 경제 지표
        # 'PLNKRW': 'PLNKRW=X',  # 폴란드 즐로티/원: 동유럽 지표
        'SEKKRW': 'SEKKRW=X',  # 스웨덴 크로나/원: 북유럽 지표
        # 'NOKKRW': 'NOKKRW=X',  # 노르웨이 크로네/원: 북유럽 지표
        'SGD': 'SGD=X'         # 싱가포르 달러: 아시아 금융 지표
    },
    'indices': {
        'KOSPI': '^KS11',      # 코스피: 한국 증시 지수
        'KOSDAQ': '^KQ11',     # 코스닥: 한국 성장주 지수
        'SP500': '^GSPC',      # S&P 500: 미국 시장 표준
        'NASDAQ': '^IXIC',     # 나스닥: 미국 기술주 중심
        'DJI': '^DJI',         # 다우존스: 미국 우량주 지수
        'RUT': '^RUT',         # 러셀2000: 미국 중소기업 지수
        'N225': '^N225',       # 니케이 225: 일본 증시
        'GDAXI': '^GDAXI',     # 독일 DAX: 유럽 시장 지표
        'FTSE': '^FTSE',       # 영국 FTSE 100: 영국 증시
        'HSI': '^HSI',         # 항셍: 홍콩 증시
        'SSEC': '000001.SS',   # 상해 종합: 중국 증시
        'BSESN': '^BSESN',     # 인도 SENSEX: 인도 성장 지표
        'BVSP': '^BVSP',       # 브라질 보베스파: 남미 증시
        'AXJO': '^AXJO',       # 호주 ASX 200: 호주 증시
        'FCHI': '^FCHI',       # 프랑스 CAC 40: 유럽 증시
        'GSPTSE': '^GSPTSE',   # 캐나다 TSX: 캐나다 증시
        'STI': '^STI',         # 싱가포르 STI: 싱가포르 증시
        'TWII': '^TWII',       # 대만 가권: 대만 반도체 지표
        'MXX': '^MXX',         # 멕시코 IPC: 멕시코 증시
        # 'TA125': '^TA125'      # 이스라엘 TA-125: 중동 지표
    },
    'tech': {
        'AAPL': 'AAPL',        # 애플: 소비자 가전/스마트폰
        'MSFT': 'MSFT',        # 마이크로소프트: 클라우드/AI 소프트웨어
        'NVDA': 'NVDA',        # 엔비디아: AI 반도체
        'GOOGL': 'GOOGL',      # 구글: 검색/AI
        'AMZN': 'AMZN',        # 아마존: 이커머스/AWS
        'META': 'META',        # 메타: 소셜미디어
        'TSLA': 'TSLA',        # 테슬라: 전기차/에너지
        'TSM': 'TSM',          # TSMC: 파운드리 반도체
        'AVGO': 'AVGO',        # 브로드컴: 네트워크 반도체
        'ASML': 'ASML',        # ASML: 노광장비(슈퍼을)
        'AMAT': 'AMAT',        # 어플라이드 머티리얼즈: 반도체 장비 1위
        'LRCX': 'LRCX',        # 램리서치: 식각 장비
        'AMD': 'AMD',          # AMD: 반도체 경쟁사
        'SEC': '005930.KS',    # 삼성전자: 한국 반도체/가전
        'SKH': '000660.KS',    # SK하이닉스: 메모리 반도체
        'LGES': '373220.KS',   # LG에너지솔루션: 글로벌 배터리
        'NAVER': '035420.KS'   # NAVER: 한국 플랫폼/AI
    },
    'commodities': {
        'CL_F': 'CL=F',        # WTI 원유: 글로벌 에너지
        'BZ_F': 'BZ=F',        # 브렌트유: 글로벌 유가
        'NG_F': 'NG=F',        # 천연가스: 산업 에너지
        'GC_F': 'GC=F',        # 금: 안전자산
        'SI_F': 'SI=F',        # 은: 산업용 금속
        'HG_F': 'HG=F',        # 구리: 실물 경기 선행지표
        'ZC_F': 'ZC=F',        # 옥수수: 식량 물가
        'ZW_F': 'ZW=F',        # 밀: 곡물 물가
        'SB_F': 'SB=F',        # 설탕: 식품 물가
        'KC_F': 'KC=F',        # 커피: 기호식품
        'ZS_F': 'ZS=F',        # 콩: 사료/곡물
        'PL_F': 'PL=F',        # 백금: 산업용 금속
        'PA_F': 'PA=F',        # 팔라듐: 자동차 산업
        'HO_F': 'HO=F',        # 난방유: 에너지
        'RB_F': 'RB=F'         # 휘발유: 에너지
    },
    'bonds': {
        'TNX': '^TNX',         # 미국 10년물: 글로벌 금리 기준
        'IRX': '^IRX',         # 미국 13주물: 단기 자금
        'FVX': '^FVX',         # 미국 5년물: 중기 금리
        'TYX': '^TYX',         # 미국 30년물: 장기 금리 전망
        # 'KR10Y': 'KR10YT=RR',  # 한국 10년물 금리
        'HYG': 'HYG',          # 하이일드 채권: 정크본드
        'LQD': 'LQD',          # 투자등급 채권: 회사채
        'TLT': 'TLT',          # 20년물 채권 ETF
        'SHY': 'SHY',          # 단기 채권 ETF
        'IEF': 'IEF'           # 중기 채권 ETF
    },
    'market_sentiment': {
        'VIX': '^VIX',         # 변동성지수: 시장 공포지수
        'VXN': '^VXN',         # 나스닥 변동성: 기술주 공포
        'SOX': '^SOX',         # 반도체지수: 산업 흐름
        'XLK': 'XLK',          # 테크 ETF: IT 산업
        'XLF': 'XLF',          # 금융 ETF: 은행권
        'XLE': 'XLE',          # 에너지 ETF: 오일/가스
        'IYR': 'IYR',          # 부동산 ETF: 리츠
        'XLP': 'XLP',          # 필수소비재: 경기방어
        'XLY': 'XLY',          # 경기소비재: 소비주
        'XLV': 'XLV',          # 헬스케어: 바이오
        'XLI': 'XLI',          # 산업재: 제조/기계
        'SMH': 'SMH',          # 반도체 ETF: 반도체
        'KWEB': 'KWEB',        # 중국 인터넷 ETF: 중국 성장주
        'ARKK': 'ARKK',        # 혁신기술 ETF: 성장성 테마
        'CIBR': 'CIBR'         # 사이버보안 ETF: 보안 테마
    },
    'crypto': {
        'BTC': 'BTC-USD',      # 비트코인: 대장주
        'ETH': 'ETH-USD',      # 이더리움: 스마트 컨트랙트
        'SOL': 'SOL-USD',      # 솔라나: 차세대 플랫폼
        'XRP': 'XRP-USD',      # 리플: 금융 결제
        'ADA': 'ADA-USD',      # 에이다: 플랫폼 코인
        'DOGE': 'DOGE-USD',    # 도지코인: 밈 코인
        'DOT': 'DOT-USD'       # 폴카닷: 멀티체인
    }
}

def fetch_financial_data():
    # KST 시간대 설정
    KST = timezone(timedelta(hours=9))
    timestamp = datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')
    
    base_folder = os.path.join("data", "finance")
    month_str = datetime.now(KST).strftime('%Y%m')

    print(f"[{timestamp}] 금융 데이터 수집 시작...")

    for category, tickers in CATEGORIES.items():
        # 카테고리별 폴더 생성: data/finance/currency/, data/finance/tech/ 등
        category_folder = os.path.join(base_folder, category)
        os.makedirs(category_folder, exist_ok=True)
        
        results = {'timestamp': timestamp}
        print(f"-> 카테고리 수집 중: {category}")
        
        for name, ticker in tickers.items():
            try:
                time.sleep(0.25)
                stock = yf.Ticker(ticker)
                hist = stock.history(period="1d")
                
                results[name] = hist['Close'].iloc[-1] if not hist.empty else 'N/A'
            except Exception:
                results[name] = 'N/A'
        
        # 파일 저장 경로를 category 폴더 안으로 설정
        file_path = os.path.join(category_folder, f"{month_str}_{category}.csv")
        df = pd.DataFrame([results])
        header = not os.path.exists(file_path)
        df.to_csv(file_path, mode='a', header=header, index=False, encoding='utf-8-sig')
        
    print("모든 카테고리 저장 완료.")

if __name__ == "__main__":
    fetch_financial_data()