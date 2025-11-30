#!/usr/bin/env python3
"""
Pi1 목록 크롤러 실행 스크립트
"""
import sys
import os
import logging
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from pi1.spiders.list_spider import ListSpider


def setup_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler('pi1/logs/spider.log'),
            logging.StreamHandler()
        ]
    )


def main():
    """메인 함수"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Scrapy 설정
    settings = get_project_settings()
    settings.set('USER_AGENT', 'Mozilla/5.0 (compatible; RecallBot/1.0)')
    settings.set('DOWNLOAD_DELAY', 1)
    settings.set('RANDOMIZE_DOWNLOAD_DELAY', True)
    settings.set('CONCURRENT_REQUESTS', 1)
    settings.set('LOG_LEVEL', 'INFO')
    
    # 크롤러 프로세스 생성
    process = CrawlerProcess(settings)
    
    # 스파이더 실행
    logger.info("목록 크롤러 시작")
    process.crawl(ListSpider)
    process.start()


if __name__ == '__main__':
    main()

