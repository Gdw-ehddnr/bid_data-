#!/usr/bin/env python3
"""
상세 페이지 크롤러 테스트 스크립트
목록 페이지에서 URL을 가져와서 본문에서 리콜 정보 추출
"""
import sys
import os
import logging
import requests
from bs4 import BeautifulSoup
import re

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from pi2.parsers.recall_parser import RecallParser
from common.utils import parse_date
from common.schemas.recall_schema import RecallSchema
from common.validators import RecallValidator


def setup_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler('pi2/logs/test_detail_crawler.log'),
            logging.StreamHandler()
        ]
    )


def test_detail_parsing():
    """상세 페이지 파싱 테스트"""
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("상세 페이지 크롤러 테스트")
    logger.info("=" * 60)
    
    # 목록 페이지에서 첫 번째 항목 가져오기
    list_url = 'https://www.car.go.kr/sd/newsDta/list.do'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    logger.info(f"목록 페이지 접근: {list_url}")
    response = requests.get(list_url, headers=headers, timeout=10)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 첫 번째 항목
    first_item = soup.select_one('ul.board-hrznt-list li')
    if not first_item:
        logger.error("항목을 찾을 수 없습니다.")
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
    match = re.search(r"detailView\(['\"]?(\d+)['\"]?\)", onclick)
    news_id = match.group(1) if match else ''
    detail_url = f'https://www.car.go.kr/sd/newsDta/view.do?newsSeq={news_id}'
    
    logger.info(f"\n제목: {title}")
    logger.info(f"URL: {detail_url}")
    logger.info(f"날짜: {notice_date}")
    logger.info(f"본문 길이: {len(content)}자")
    
    # 파서로 데이터 추출
    parser = RecallParser()
    parsed_data = parser.parse_from_text(content, detail_url, title, notice_date)
    
    logger.info("\n" + "=" * 60)
    logger.info("파싱된 데이터")
    logger.info("=" * 60)
    
    for key, value in parsed_data.items():
        logger.info(f"{key:20}: {value}")
    
    # 스키마 생성 및 검증
    logger.info("\n" + "=" * 60)
    logger.info("데이터 검증")
    logger.info("=" * 60)
    
    try:
        recall = RecallSchema.from_dict(parsed_data)
        is_valid, errors = RecallValidator.validate(recall)
        
        if is_valid:
            logger.info("✓ 데이터 검증 성공")
        else:
            logger.warning(f"✗ 데이터 검증 실패: {errors}")
        
        # 딕셔너리로 변환하여 출력
        logger.info("\n최종 데이터:")
        final_data = recall.to_dict()
        for key, value in final_data.items():
            logger.info(f"  {key}: {value}")
            
    except Exception as e:
        logger.error(f"스키마 생성 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    setup_logging()
    test_detail_parsing()

