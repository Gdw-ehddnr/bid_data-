#!/usr/bin/env python3
"""
상세 페이지 파서 테스트 스크립트
목록 페이지의 본문에서 리콜 정보를 추출하는 테스트
"""
import sys
import os
import requests
from bs4 import BeautifulSoup

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pi2.parsers.recall_parser import RecallParser
from common.utils import parse_date


def test_parser_from_list_content():
    """목록 페이지의 본문에서 파싱 테스트"""
    print("=" * 60)
    print("상세 페이지 파서 테스트")
    print("=" * 60)
    
    # 목록 페이지에서 첫 번째 항목 가져오기
    url = 'https://www.car.go.kr/sd/newsDta/list.do'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 첫 번째 항목
    first_item = soup.select_one('ul.board-hrznt-list li')
    if not first_item:
        print("항목을 찾을 수 없습니다.")
        return
    
    # 제목
    title_elem = first_item.select_one('a strong')
    title = title_elem.get_text(strip=True) if title_elem else ''
    
    # 본문
    content_elem = first_item.select_one('p')
    content = content_elem.get_text() if content_elem else ''
    
    # 날짜
    date_items = first_item.select('ol li')
    notice_date = None
    if len(date_items) >= 2:
        date_str = date_items[1].get_text(strip=True)
        notice_date = parse_date(date_str)
    
    # URL
    onclick = first_item.select_one('a').get('onclick', '')
    import re
    match = re.search(r"detailView\(['\"]?(\d+)['\"]?\)", onclick)
    news_id = match.group(1) if match else ''
    detail_url = f'https://www.car.go.kr/sd/newsDta/view.do?newsSeq={news_id}'
    
    print(f"\n제목: {title}")
    print(f"URL: {detail_url}")
    print(f"날짜: {notice_date}")
    print(f"\n본문 (일부):\n{content[:300]}...")
    
    # 파서로 데이터 추출 시도
    # 실제로는 Scrapy Response가 필요하지만, 여기서는 텍스트 기반으로 테스트
    print("\n" + "=" * 60)
    print("파서 테스트 (텍스트 기반)")
    print("=" * 60)
    
    # 간단한 텍스트 파싱
    import re
    
    # 제조사 추출 (예: "메르세데스-벤츠코리아㈜", "현대자동차㈜")
    makers = re.findall(r'([가-힣]+(?:자동차|코리아|㈜))', content)
    print(f"\n제조사 후보: {list(set(makers))[:5]}")
    
    # 차종 추출 (예: "E 350 4MATIC", "아반떼")
    models = re.findall(r'([A-Z0-9\s]+(?:차종|대)|[가-힣]+(?:차종|대))', content)
    print(f"차종 후보: {models[:5]}")
    
    # 대상대수 추출
    qty_matches = re.findall(r'(\d{1,3}(?:,\d{3})*)\s*대', content)
    print(f"대상대수: {qty_matches[:5]}")
    
    # 결함부위 추출 (예: "엔진제어장치", "제동장치")
    defect_keywords = ['엔진', '제동', '브레이크', '에어백', '변속기', '서스펜션', '타이어']
    defects = []
    for keyword in defect_keywords:
        if keyword in content:
            # 키워드 주변 텍스트 추출
            pattern = rf'.{{0,30}}{keyword}.{{0,30}}'
            matches = re.findall(pattern, content)
            if matches:
                defects.extend(matches[:2])
    print(f"결함부위 후보: {defects[:3]}")
    
    print("\n" + "=" * 60)
    print("결론: 보도자료 본문에서 텍스트 파싱이 필요합니다")
    print("=" * 60)


if __name__ == '__main__':
    test_parser_from_list_content()

