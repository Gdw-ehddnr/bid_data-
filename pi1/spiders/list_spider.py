"""
목록 크롤러 스파이더
자동차리콜센터 목록 페이지에서 신규 공지 URL을 추출하여 Kafka에 발행
"""
import scrapy
import logging
import yaml
import re
import os
from datetime import datetime
from typing import List, Dict
from urllib.parse import urljoin
from common.utils import create_producer, parse_date


logger = logging.getLogger(__name__)


class ListSpider(scrapy.Spider):
    """리콜 목록 크롤러"""
    
    name = 'recall_list'
    
    def __init__(self, config_path='config/config.yaml', *args, **kwargs):
        super(ListSpider, self).__init__(*args, **kwargs)
        
        # 설정 로드
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # 크롤링 설정
        self.crawling_config = self.config['crawling']
        self.base_url = self.crawling_config['base_url']
        
        # Kafka Producer 초기화
        kafka_config = self.config['kafka']
        self.producer = create_producer(
            bootstrap_servers=kafka_config['bootstrap_servers'],
            topic=kafka_config['topics']['new_urls']
        )
        
        # 이미 처리한 URL 저장 (증분 크롤링용)
        self.processed_urls = set()
        
        logger.info(f"ListSpider 초기화 완료: {self.base_url}")
    
    def start_requests(self):
        """시작 요청 생성"""
        # 리콜보도자료 목록 페이지 URL
        # https://www.car.go.kr/sd/newsDta/list.do
        list_url = urljoin(self.base_url, '/sd/newsDta/list.do')
        
        yield scrapy.Request(
            url=list_url,
            callback=self.parse_list,
            meta={'page': 1}
        )
    
    def parse_list(self, response):
        """목록 페이지 파싱"""
        # 리콜보도자료 목록 페이지 구조 분석
        # 실제 페이지: https://www.car.go.kr/sd/newsDta/list.do
        # 구조: <ul class="board-hrznt-list"> > <li> > <a onclick="$main.event.detailView('ID')">
        
        # 리스트 항목 찾기 (board-hrznt-list 클래스)
        notice_items = response.css('ul.board-hrznt-list li')
        
        if not notice_items:
            # 대체 패턴 시도
            notice_items = response.css('ul li, .list-item, .news-item')
            logger.debug("대체 선택자 사용")
        
        if not notice_items:
            logger.warning("목록 항목을 찾을 수 없습니다. HTML 구조를 확인하세요.")
            # 디버깅을 위해 HTML 일부 저장
            os.makedirs('data/raw', exist_ok=True)
            with open('data/raw/list_page_debug.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.info("디버그 HTML 저장: data/raw/list_page_debug.html")
            return
        
        logger.info(f"목록 항목 {len(notice_items)}개 발견")
        
        new_urls_count = 0
        
        for item in notice_items:
            # URL 추출 - onclick 이벤트에서 ID 추출
            # onclick="$main.event.detailView('2483');" 형태
            onclick = item.css('a::attr(onclick)').get()
            if not onclick:
                continue
            
            # detailView 함수의 인자(ID) 추출
            match = re.search(r"detailView\(['\"]?(\d+)['\"]?\)", onclick)
            if not match:
                continue
            
            news_id = match.group(1)
            # 상세 페이지 URL 생성: /sd/newsDta/view.do?newsSeq=ID
            relative_url = f'/sd/newsDta/view.do?newsSeq={news_id}'
            full_url = urljoin(self.base_url, relative_url)
            
            # 제목 추출 - <strong> 태그 안의 텍스트
            title = item.css('a strong::text').get()
            if title:
                title = title.strip()
            else:
                # 대체: a 태그의 첫 번째 텍스트
                title = item.css('a::text').get()
                if title:
                    title = title.strip()
            
            if not title:
                continue
            
            # 공지일 추출 - <ol> 안의 두 번째 <li> (날짜)
            # 구조: <ol><li>작성자</li><li>날짜</li><li>조회수</li></ol>
            date_items = item.css('ol li::text').getall()
            notice_date = None
            if len(date_items) >= 2:
                # 두 번째 항목이 날짜
                date_str = date_items[1].strip()
                notice_date = parse_date(date_str)
            
            # 중복 체크
            if full_url in self.processed_urls:
                continue
            
            self.processed_urls.add(full_url)
            
            # Kafka에 발행
            message = {
                'url': full_url,
                'title': title or '',
                'notice_date': notice_date
            }
            
            if self.producer.send(message):
                new_urls_count += 1
                logger.info(f"신규 URL 발행: {full_url} - {title[:50]}")
            else:
                logger.error(f"URL 발행 실패: {full_url}")
        
        logger.info(f"총 {new_urls_count}개의 신규 URL 발행 완료")
        
        # 다음 페이지 처리 (페이징이 있는 경우)
        # 페이지 번호 링크 찾기 (예: 1, 2, 3, ... 118)
        current_page = response.meta.get('page', 1)
        next_page_num = current_page + 1
        
        # 다음 페이지 링크 확인
        # URL 패턴: /sd/newsDta/list.do?page=2
        next_page_url = f'/sd/newsDta/list.do?page={next_page_num}'
        
        # 마지막 페이지 확인 (예: "전체 470건 (페이지 1/118)")
        page_info = response.css('::text').re(r'페이지\s+(\d+)/(\d+)')
        if page_info:
            total_pages = int(page_info[1])
            if next_page_num <= total_pages:
                next_url = urljoin(self.base_url, next_page_url)
                yield response.follow(
                    next_url,
                    callback=self.parse_list,
                    meta={'page': next_page_num}
                )
                logger.info(f"다음 페이지 요청: {next_page_num}/{total_pages}")
    
    def closed(self, reason):
        """스파이더 종료 시 처리"""
        self.producer.flush()
        self.producer.close()
        logger.info(f"ListSpider 종료: {reason}")

