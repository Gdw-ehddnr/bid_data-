#!/usr/bin/env python3
"""
전체 파이프라인 테스트 스크립트
Pi1 → Pi2 → Pi3 (Kafka 없이 시뮬레이션)
"""
import sys
import os
import logging
import requests
from bs4 import BeautifulSoup
import re

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.utils import parse_date
from pi2.parsers.recall_parser import RecallParser
from common.schemas.recall_schema import RecallSchema
from common.validators import RecallValidator


def setup_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )


def test_full_pipeline():
    """전체 파이프라인 테스트 (Kafka 없이)"""
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("전체 파이프라인 테스트 시작")
    logger.info("=" * 60)
    
    # ===== Pi1: 목록 크롤링 =====
    logger.info("\n[Pi1] 목록 페이지 크롤링")
    logger.info("-" * 60)
    
    list_url = 'https://www.car.go.kr/sd/newsDta/list.do'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    response = requests.get(list_url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    items = soup.select('ul.board-hrznt-list li')
    logger.info(f"목록 항목 {len(items)}개 발견")
    
    # 첫 3개 항목만 테스트
    test_items = items[:3]
    urls_to_process = []
    
    for item in test_items:
        link_elem = item.select_one('a')
        if not link_elem:
            continue
        
        onclick = link_elem.get('onclick', '')
        match = re.search(r"detailView\(['\"]?(\d+)['\"]?\)", onclick)
        if not match:
            continue
        
        news_id = match.group(1)
        title_elem = item.select_one('a strong')
        title = title_elem.get_text(strip=True) if title_elem else ''
        
        date_items = item.select('ol li')
        notice_date = None
        if len(date_items) >= 2:
            date_str = date_items[1].get_text(strip=True)
            notice_date = parse_date(date_str)
        
        content_elem = item.select_one('p')
        content = content_elem.get_text() if content_elem else ''
        
        url = f'https://www.car.go.kr/sd/newsDta/view.do?newsSeq={news_id}'
        urls_to_process.append({
            'url': url,
            'title': title,
            'notice_date': notice_date,
            'content': content
        })
        logger.info(f"  - {title[:50]}")
        logger.info(f"    URL: {url}")
    
    logger.info(f"\n총 {len(urls_to_process)}개 URL 수집 완료")
    
    # ===== Pi2: 상세 페이지 파싱 =====
    logger.info("\n[Pi2] 상세 페이지 파싱")
    logger.info("-" * 60)
    
    parser = RecallParser()
    parsed_recalls = []
    
    for item_data in urls_to_process:
        logger.info(f"\n파싱 중: {item_data['title'][:50]}")
        
        parsed_data = parser.parse_from_text(
            item_data['content'],
            item_data['url'],
            item_data['title'],
            item_data['notice_date']
        )
        
        # 스키마 생성 및 검증
        try:
            recall = RecallSchema.from_dict(parsed_data)
            is_valid, errors = RecallValidator.validate(recall)
            
            if is_valid:
                parsed_recalls.append(recall)
                logger.info(f"  ✓ 파싱 및 검증 성공")
                logger.info(f"    제조사: {recall.maker}, 모델: {recall.model}")
                logger.info(f"    결함부위: {recall.defect_part}, 대상대수: {recall.qty}")
            else:
                logger.warning(f"  ✗ 검증 실패: {errors}")
        except Exception as e:
            logger.error(f"  ✗ 스키마 생성 실패: {e}")
    
    logger.info(f"\n총 {len(parsed_recalls)}개 리콜 데이터 파싱 완료")
    
    # ===== Pi3: DB 저장 시뮬레이션 =====
    logger.info("\n[Pi3] DB 저장 시뮬레이션")
    logger.info("-" * 60)
    
    saved_count = 0
    duplicate_count = 0
    
    for recall in parsed_recalls:
        # 실제로는 DB에 저장하지만, 여기서는 시뮬레이션
        logger.info(f"저장 시뮬레이션: {recall.title[:50]}")
        logger.info(f"  URL: {recall.url}")
        saved_count += 1
    
    logger.info(f"\n총 {saved_count}개 레코드 저장 완료 (중복: {duplicate_count}개)")
    
    # ===== 결과 요약 =====
    logger.info("\n" + "=" * 60)
    logger.info("전체 파이프라인 테스트 결과")
    logger.info("=" * 60)
    logger.info(f"Pi1 (목록 크롤링): {len(urls_to_process)}개 URL 수집")
    logger.info(f"Pi2 (상세 파싱): {len(parsed_recalls)}개 데이터 파싱")
    logger.info(f"Pi3 (DB 저장): {saved_count}개 레코드 저장")
    logger.info("\n✓ 전체 파이프라인 테스트 완료!")
    
    return len(parsed_recalls) > 0


if __name__ == '__main__':
    setup_logging()
    success = test_full_pipeline()
    sys.exit(0 if success else 1)

