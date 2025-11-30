#!/usr/bin/env python3
"""
Pi2 상세 크롤러 실행 스크립트
Kafka에서 URL을 수신하여 상세 페이지를 크롤링하고 파싱
"""
import sys
import os
import logging
import time
import yaml
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from pi2.spiders.detail_spider import DetailSpider
from common.utils import create_consumer, create_producer
from pi2.parsers.recall_parser import RecallParser
import scrapy
from scrapy.http import Request


def setup_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler('pi2/logs/consumer.log'),
            logging.StreamHandler()
        ]
    )


def crawl_url(url: str, title: str, notice_date: str = None):
    """단일 URL 크롤링"""
    settings = get_project_settings()
    settings.set('USER_AGENT', 'Mozilla/5.0 (compatible; RecallBot/1.0)')
    settings.set('DOWNLOAD_DELAY', 1)
    settings.set('CONCURRENT_REQUESTS', 1)
    
    process = CrawlerProcess(settings)
    
    # 스파이더에 메타데이터 전달
    def start_crawl():
        spider = DetailSpider()
        request = Request(
            url=url,
            callback=spider.parse_detail,
            meta={'original_message': {'url': url, 'title': title, 'notice_date': notice_date}}
        )
        return request
    
    # 간단한 동기 방식으로 크롤링
    # 실제로는 Scrapy의 비동기 처리 활용 필요
    pass


def main():
    """메인 함수 - Kafka Consumer로 URL 수신 및 처리"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 설정 로드
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    kafka_config = config['kafka']
    crawling_config = config['crawling']
    
    # Kafka Consumer 생성
    consumer = create_consumer(
        bootstrap_servers=kafka_config['bootstrap_servers'],
        topic=kafka_config['topics']['new_urls'],
        group_id=kafka_config['consumer_groups']['pi2']
    )
    
    # Kafka Producer 생성
    producer = create_producer(
        bootstrap_servers=kafka_config['bootstrap_servers'],
        topic=kafka_config['topics']['parsed_recalls']
    )
    
    # 파서 생성
    parser = RecallParser()
    
    # Scrapy 설정
    settings = get_project_settings()
    settings.set('USER_AGENT', crawling_config['user_agent'])
    settings.set('DOWNLOAD_DELAY', crawling_config['delay'])
    settings.set('CONCURRENT_REQUESTS', 1)
    
    logger.info("Pi2 상세 크롤러 시작")
    
    def process_message(message):
        """메시지 처리 함수"""
        url = message.get('url')
        title = message.get('title', '')
        notice_date = message.get('notice_date')
        
        if not url:
            logger.warning("URL이 없는 메시지 무시")
            return
        
        logger.info(f"URL 처리 시작: {url}")
        
        try:
            # Scrapy로 페이지 다운로드 및 파싱
            # 실제 구현은 Scrapy의 비동기 처리 활용 필요
            # 여기서는 간단한 requests 기반 예시
            import requests
            from bs4 import BeautifulSoup
            
            response = requests.get(url, timeout=crawling_config['timeout'])
            response.raise_for_status()
            
            # 목록 페이지에서 본문 추출 (보도자료 형식)
            # 실제로는 상세 페이지를 크롤링하지만, 여기서는 목록 페이지의 본문 사용
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 목록 페이지에서 해당 항목 찾기
            items = soup.select('ul.board-hrznt-list li')
            content = ''
            for item in items:
                item_onclick = item.select_one('a').get('onclick', '')
                item_match = re.search(r"detailView\(['\"]?(\d+)['\"]?\)", item_onclick)
                if item_match and item_match.group(1) in url:
                    content_elem = item.select_one('p')
                    if content_elem:
                        content = content_elem.get_text()
                    break
            
            # 파서로 데이터 추출 (텍스트 기반)
            parsed_data = parser.parse_from_text(content, url, title, notice_date)
            
            # RecallSchema 생성 및 검증
            from common.schemas.recall_schema import RecallSchema
            from common.validators import RecallValidator
            
            recall = RecallSchema.from_dict(parsed_data)
            is_valid, errors = RecallValidator.validate(recall)
            
            if is_valid:
                # Kafka에 발행
                if producer.send(recall.to_dict()):
                    logger.info(f"파싱 완료 및 발행: {url}")
                else:
                    logger.error(f"파싱 데이터 발행 실패: {url}")
            else:
                logger.warning(f"검증 실패: {url}, 오류: {errors}")
                
        except Exception as e:
            logger.error(f"URL 처리 중 오류: {url}, 오류: {e}")
    
    # 메시지 소비
    try:
        consumer.consume(process_message)
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
    finally:
        consumer.close()
        producer.flush()
        producer.close()
        logger.info("Pi2 상세 크롤러 종료")


if __name__ == '__main__':
    main()

