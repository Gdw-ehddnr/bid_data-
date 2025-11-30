"""
공통 유틸리티 모듈
"""
from .file_utils import save_json, load_json, read_urls_from_file, write_urls_to_file
from .date_utils import parse_date, normalize_date

# Kafka 모듈은 선택적 import (kafka-python이 설치되지 않을 수 있음)
try:
    from .kafka_producer import RecallKafkaProducer, create_producer
    from .kafka_consumer import RecallKafkaConsumer, create_consumer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    # 더미 객체 생성 (테스트용)
    RecallKafkaProducer = None
    create_producer = None
    RecallKafkaConsumer = None
    create_consumer = None

__all__ = [
    'save_json',
    'load_json',
    'read_urls_from_file',
    'write_urls_to_file',
    'parse_date',
    'normalize_date',
    'KAFKA_AVAILABLE',
]

if KAFKA_AVAILABLE:
    __all__.extend([
        'RecallKafkaProducer',
        'create_producer',
        'RecallKafkaConsumer',
        'create_consumer'
    ])

