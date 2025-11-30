"""
Kafka Consumer 유틸리티
"""
import json
import logging
from typing import Callable, Optional, Dict, Any
from kafka import KafkaConsumer
from kafka.errors import KafkaError


logger = logging.getLogger(__name__)


class RecallKafkaConsumer:
    """리콜 데이터용 Kafka Consumer"""
    
    def __init__(
        self,
        bootstrap_servers: str,
        topic: str,
        group_id: str,
        value_deserializer=None,
        auto_offset_reset: str = 'earliest',
        enable_auto_commit: bool = True
    ):
        """
        Args:
            bootstrap_servers: Kafka 브로커 주소
            topic: Kafka 토픽 이름
            group_id: Consumer 그룹 ID
            value_deserializer: 값 역직렬화 함수 (기본: JSON)
            auto_offset_reset: 오프셋 리셋 정책 ('earliest' 또는 'latest')
            enable_auto_commit: 자동 커밋 여부
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.group_id = group_id
        
        if value_deserializer is None:
            value_deserializer = lambda m: json.loads(m.decode('utf-8'))
        
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            value_deserializer=value_deserializer,
            auto_offset_reset=auto_offset_reset,
            enable_auto_commit=enable_auto_commit,
            consumer_timeout_ms=1000  # 타임아웃 설정 (ms)
        )
        logger.info(
            f"Kafka Consumer 초기화 완료: {bootstrap_servers}, "
            f"topic={topic}, group_id={group_id}"
        )
    
    def consume(self, callback: Callable[[Dict[Any, Any]], None], max_messages: Optional[int] = None):
        """
        메시지 소비 (폴링 방식)
        
        Args:
            callback: 메시지 처리 함수
            max_messages: 최대 처리 메시지 수 (None이면 무제한)
        """
        message_count = 0
        try:
            for message in self.consumer:
                try:
                    callback(message.value)
                    message_count += 1
                    
                    if max_messages and message_count >= max_messages:
                        break
                except Exception as e:
                    logger.error(f"메시지 처리 중 오류: {e}, message={message.value}")
        except KafkaError as e:
            logger.error(f"Kafka 소비 중 오류: {e}")
        finally:
            logger.info(f"총 {message_count}개 메시지 처리 완료")
    
    def consume_one(self) -> Optional[Dict[Any, Any]]:
        """
        단일 메시지 소비
        
        Returns:
            메시지 데이터 또는 None
        """
        try:
            message = next(self.consumer)
            return message.value
        except StopIteration:
            return None
        except KafkaError as e:
            logger.error(f"Kafka 소비 중 오류: {e}")
            return None
    
    def commit(self):
        """오프셋 커밋"""
        self.consumer.commit()
    
    def close(self):
        """Consumer 종료"""
        self.consumer.close()
        logger.info("Kafka Consumer 종료")


def create_consumer(
    bootstrap_servers: str,
    topic: str,
    group_id: str
) -> RecallKafkaConsumer:
    """Consumer 생성 헬퍼 함수"""
    return RecallKafkaConsumer(bootstrap_servers, topic, group_id)

