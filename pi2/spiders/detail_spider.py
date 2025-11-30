"""
상세 페이지 크롤러 스파이더
Kafka에서 URL을 수신하여 상세 페이지를 크롤링하고 파싱
"""
import scrapy
import logging
import yaml
from typing import Dict
from common.utils import create_consumer, create_producer
from common.schemas.recall_schema import RecallSchema
from pi2.parsers.recall_parser import RecallParser


logger = logging.getLogger(__name__)


class DetailSpider(scrapy.Spider):
    """리콜 상세 페이지 크롤러"""
    
    name = 'recall_detail'
    
    def __init__(self, config_path='config/config.yaml', *args, **kwargs):
        super(DetailSpider, self).__init__(*args, **kwargs)
        
        # 설정 로드
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # 크롤링 설정
        self.crawling_config = self.config['crawling']
        
        # Kafka Consumer 초기화
        kafka_config = self.config['kafka']
        self.consumer = create_consumer(
            bootstrap_servers=kafka_config['bootstrap_servers'],
            topic=kafka_config['topics']['new_urls'],
            group_id=kafka_config['consumer_groups']['pi2']
        )
        
        # Kafka Producer 초기화
        self.producer = create_producer(
            bootstrap_servers=kafka_config['bootstrap_servers'],
            topic=kafka_config['topics']['parsed_recalls']
        )
        
        # 파서 초기화
        self.parser = RecallParser()
        
        logger.info("DetailSpider 초기화 완료")
    
    def start_requests(self):
        """Kafka에서 URL 수신하여 요청 생성"""
        # Kafka에서 메시지 수신
        message = self.consumer.consume_one()
        
        if message:
            url = message.get('url')
            if url:
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_detail,
                    meta={'original_message': message},
                    errback=self.errback_handler
                )
    
    def parse_detail(self, response):
        """상세 페이지 파싱"""
        original_message = response.meta.get('original_message', {})
        url = original_message.get('url', response.url)
        title = original_message.get('title', '')
        
        try:
            # 파서로 데이터 추출
            parsed_data = self.parser.parse(response, url, title)
            
            # RecallSchema 생성
            recall = RecallSchema.from_dict(parsed_data)
            
            # Kafka에 발행
            if self.producer.send(recall.to_dict()):
                logger.info(f"파싱 완료 및 발행: {url}")
            else:
                logger.error(f"파싱 데이터 발행 실패: {url}")
                
        except Exception as e:
            logger.error(f"파싱 중 오류 발생: {url}, 오류: {e}")
    
    def errback_handler(self, failure):
        """에러 핸들러"""
        logger.error(f"요청 실패: {failure.request.url}, 오류: {failure.value}")
    
    def closed(self, reason):
        """스파이더 종료 시 처리"""
        self.consumer.close()
        self.producer.flush()
        self.producer.close()
        logger.info(f"DetailSpider 종료: {reason}")

