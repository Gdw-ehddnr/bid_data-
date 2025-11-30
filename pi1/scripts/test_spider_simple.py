#!/usr/bin/env python3
"""
간단한 스파이더 테스트 스크립트 (Kafka 없이)
"""
import sys
import os
import logging

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from pi1.spiders.list_spider import ListSpider


def setup_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler('pi1/logs/test_spider.log'),
            logging.StreamHandler()
        ]
    )


def test_spider_without_kafka():
    """Kafka 없이 스파이더 테스트 (URL만 수집)"""
    logger = logging.getLogger(__name__)
    
    # Kafka 없이 테스트하기 위해 스파이더 수정
    class TestListSpider(ListSpider):
        def __init__(self, *args, **kwargs):
            # 부모 클래스 초기화 (Kafka Producer 생성 시도)
            try:
                super().__init__(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Kafka 초기화 실패 (계속 진행): {e}")
                # Kafka 없이도 작동하도록 설정
                import yaml
                with open('config/config.yaml', 'r') as f:
                    self.config = yaml.safe_load(f)
                self.crawling_config = self.config['crawling']
                self.base_url = self.crawling_config['base_url']
                self.processed_urls = set()
                self.producer = None  # Kafka Producer 없음
        
        def parse_list(self, response):
            """목록 페이지 파싱 (Kafka 없이 URL만 출력)"""
            from urllib.parse import urljoin
            import re
            from common.utils import parse_date
            
            notice_items = response.css('ul.board-hrznt-list li')
            
            if not notice_items:
                notice_items = response.css('ul li, .list-item, .news-item')
            
            if not notice_items:
                logger.warning("목록 항목을 찾을 수 없습니다.")
                os.makedirs('data/raw', exist_ok=True)
                with open('data/raw/list_page_debug.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                logger.info("디버그 HTML 저장: data/raw/list_page_debug.html")
                return
            
            logger.info(f"목록 항목 {len(notice_items)}개 발견")
            new_urls_count = 0
            
            for item in notice_items:
                onclick = item.css('a::attr(onclick)').get()
                if not onclick:
                    continue
                
                match = re.search(r"detailView\(['\"]?(\d+)['\"]?\)", onclick)
                if not match:
                    continue
                
                news_id = match.group(1)
                relative_url = f'/sd/newsDta/view.do?newsSeq={news_id}'
                full_url = urljoin(self.base_url, relative_url)
                
                title = item.css('a strong::text').get()
                if title:
                    title = title.strip()
                else:
                    title = item.css('a::text').get()
                    if title:
                        title = title.strip()
                
                if not title:
                    continue
                
                date_items = item.css('ol li::text').getall()
                notice_date = None
                if len(date_items) >= 2:
                    date_str = date_items[1].strip()
                    notice_date = parse_date(date_str)
                
                # Kafka 대신 콘솔에 출력
                logger.info(f"[{new_urls_count + 1}] 제목: {title[:60]}")
                logger.info(f"     URL: {full_url}")
                logger.info(f"     날짜: {notice_date or 'N/A'}")
                
                new_urls_count += 1
                
                # 최대 5개만 테스트
                if new_urls_count >= 5:
                    logger.info("테스트를 위해 5개만 수집합니다.")
                    break
            
            logger.info(f"총 {new_urls_count}개의 URL 수집 완료")
        
        def closed(self, reason):
            """스파이더 종료 시 처리"""
            if self.producer:
                self.producer.flush()
                self.producer.close()
            logger.info(f"TestListSpider 종료: {reason}")
    
    # Scrapy 설정
    settings = get_project_settings()
    settings.set('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    settings.set('DOWNLOAD_DELAY', 2)
    settings.set('RANDOMIZE_DOWNLOAD_DELAY', True)
    settings.set('CONCURRENT_REQUESTS', 1)
    settings.set('LOG_LEVEL', 'INFO')
    settings.set('ROBOTSTXT_OBEY', False)
    
    # 크롤러 프로세스 생성
    process = CrawlerProcess(settings)
    
    # 스파이더 실행
    logger.info("목록 크롤러 테스트 시작 (Kafka 없이)")
    process.crawl(TestListSpider)
    process.start()


if __name__ == '__main__':
    setup_logging()
    test_spider_without_kafka()

