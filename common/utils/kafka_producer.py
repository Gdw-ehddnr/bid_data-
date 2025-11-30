"""
Kafka Producer 유틸리티
"""
import json
import logging
from typing import Any, Dict, Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError


logger = logging.getLogger(__name__)


class RecallKafkaProducer:
    """리콜 데이터용 Kafka Producer"""
    
    def __init__(
        self,
        bootstrap_servers: str,
        topic: str,
        value_serializer=None
    ):
        """
        Args:
            bootstrap_servers: Kafka 브로커 주소 (예: "localhost:9092" 또는 "192.168.1.10:9092")
            topic: Kafka 토픽 이름
            value_serializer: 값 직렬화 함수 (기본: JSON)
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        
        if value_serializer is None:
            value_serializer = lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8')
        
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=value_serializer,
            acks='all',  # 모든 리플리카에 쓰기 확인
            retries=3,
            max_in_flight_requests_per_connection=1,
            enable_idempotence=True
        )
        logger.info(f"Kafka Producer 초기화 완료: {bootstrap_servers}, topic={topic}")
    
    def send(self, value: Any, key: Optional[str] = None) -> bool:
        """
        메시지 전송
        
        Args:
            value: 전송할 데이터
            key: 파티션 키 (선택)
        
        Returns:
            성공 여부
        """
        try:
            future = self.producer.send(self.topic, value=value, key=key)
            # 동기적으로 전송 확인
            record_metadata = future.get(timeout=10)
            logger.debug(
                f"메시지 전송 성공: topic={record_metadata.topic}, "
                f"partition={record_metadata.partition}, offset={record_metadata.offset}"
            )
            return True
        except KafkaError as e:
            logger.error(f"Kafka 전송 실패: {e}")
            return False
    
    def send_batch(self, messages: list, key_func=None) -> int:
        """
        여러 메시지 일괄 전송
        
        Args:
            messages: 전송할 메시지 리스트
            key_func: 키 생성 함수 (선택)
        
        Returns:
            성공한 메시지 수
        """
        success_count = 0
        for msg in messages:
            key = key_func(msg) if key_func else None
            if self.send(msg, key=key):
                success_count += 1
        return success_count
    
    def flush(self):
        """버퍼에 있는 모든 메시지 전송"""
        self.producer.flush()
    
    def close(self):
        """Producer 종료"""
        self.producer.close()
        logger.info("Kafka Producer 종료")


def create_producer(bootstrap_servers: str, topic: str) -> RecallKafkaProducer:
    """Producer 생성 헬퍼 함수"""
    return RecallKafkaProducer(bootstrap_servers, topic)

