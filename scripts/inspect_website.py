#!/usr/bin/env python3
"""
웹사이트 구조 확인 스크립트
자동차리콜센터 웹사이트의 실제 HTML 구조를 확인하여 선택자를 파악
"""
import requests
from bs4 import BeautifulSoup
import json


def inspect_list_page():
    """목록 페이지 구조 확인"""
    print("=" * 60)
    print("목록 페이지 구조 확인")
    print("=" * 60)
    
    url = "https://www.car.go.kr/sd/newsDta/list.do"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # HTML 구조 확인
        print(f"\n페이지 제목: {soup.title.string if soup.title else 'N/A'}")
        
        # 가능한 선택자 패턴 확인
        print("\n[확인할 선택자 패턴]")
        
        # 테이블 기반 구조 확인
        tables = soup.find_all('table')
        if tables:
            print(f"\n테이블 발견: {len(tables)}개")
            for i, table in enumerate(tables[:3]):  # 처음 3개만
                print(f"\n테이블 {i+1}:")
                rows = table.find_all('tr')
                if rows:
                    print(f"  행 수: {len(rows)}")
                    # 첫 번째 행의 구조 확인
                    first_row = rows[0]
                    cells = first_row.find_all(['td', 'th'])
                    print(f"  첫 행 셀 수: {len(cells)}")
                    for j, cell in enumerate(cells[:5]):  # 처음 5개만
                        print(f"    셀 {j+1}: {cell.get_text(strip=True)[:50]}")
        
        # 리스트/div 기반 구조 확인
        divs_with_class = soup.find_all('div', class_=True)
        if divs_with_class:
            print(f"\n클래스가 있는 div: {len(divs_with_class)}개")
            # 자주 사용되는 클래스명 확인
            class_counts = {}
            for div in divs_with_class[:50]:
                classes = div.get('class', [])
                for cls in classes:
                    class_counts[cls] = class_counts.get(cls, 0) + 1
            
            print("\n자주 사용되는 클래스명 (상위 10개):")
            for cls, count in sorted(class_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  .{cls}: {count}회")
        
        # 링크 확인
        links = soup.find_all('a', href=True)
        recall_links = [a for a in links if 'recall' in a.get('href', '').lower() or '리콜' in a.get_text()]
        print(f"\n리콜 관련 링크: {len(recall_links)}개")
        if recall_links:
            print("\n처음 5개 링크:")
            for i, link in enumerate(recall_links[:5]):
                href = link.get('href', '')
                text = link.get_text(strip=True)
                print(f"  {i+1}. {text[:50]} -> {href[:80]}")
        
        # HTML 일부 저장 (분석용)
        with open('data/raw/list_page_sample.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print("\nHTML 샘플 저장: data/raw/list_page_sample.html")
        
    except Exception as e:
        print(f"오류 발생: {e}")


def inspect_detail_page(sample_url=None):
    """상세 페이지 구조 확인"""
    print("\n" + "=" * 60)
    print("상세 페이지 구조 확인")
    print("=" * 60)
    
    if not sample_url:
        print("샘플 URL이 제공되지 않았습니다.")
        print("목록 페이지에서 URL을 먼저 확인하세요.")
        return
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(sample_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print(f"\n페이지 제목: {soup.title.string if soup.title else 'N/A'}")
        
        # 주요 정보 필드 확인
        print("\n[주요 정보 필드 확인]")
        
        # 테이블 기반 정보 확인
        tables = soup.find_all('table')
        if tables:
            print(f"\n테이블 발견: {len(tables)}개")
            for i, table in enumerate(tables):
                print(f"\n테이블 {i+1}:")
                rows = table.find_all('tr')
                for row in rows[:10]:  # 처음 10개 행
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        print(f"  {label}: {value[:100]}")
        
        # div 기반 정보 확인
        info_divs = soup.find_all(['div', 'dl', 'ul'], class_=True)
        if info_divs:
            print(f"\n정보가 있는 div/dl/ul: {len(info_divs)}개")
            for div in info_divs[:20]:  # 처음 20개만
                classes = div.get('class', [])
                text = div.get_text(strip=True)
                if text and len(text) > 10:
                    print(f"  .{' '.join(classes)}: {text[:100]}")
        
        # HTML 일부 저장
        with open('data/raw/detail_page_sample.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print("\nHTML 샘플 저장: data/raw/detail_page_sample.html")
        
    except Exception as e:
        print(f"오류 발생: {e}")


def main():
    """메인 함수"""
    print("자동차리콜센터 웹사이트 구조 확인")
    print("=" * 60)
    
    # 목록 페이지 확인
    inspect_list_page()
    
    # 상세 페이지 확인 (URL이 있으면)
    # inspect_detail_page("https://www.car.go.kr/web/recall/recallDetail.do?recallId=...")
    
    print("\n" + "=" * 60)
    print("확인 완료!")
    print("=" * 60)
    print("\n다음 단계:")
    print("1. data/raw/list_page_sample.html 파일을 열어 실제 구조 확인")
    print("2. pi1/spiders/list_spider.py의 선택자 수정")
    print("3. 상세 페이지 URL을 찾아 inspect_detail_page() 실행")
    print("4. pi2/parsers/recall_parser.py의 선택자 수정")


if __name__ == '__main__':
    main()

