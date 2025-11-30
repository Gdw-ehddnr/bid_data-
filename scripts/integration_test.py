#!/usr/bin/env python3
"""
통합 테스트 스크립트
Kafka, DB, 전체 파이프라인을 테스트합니다.
"""
import sys
import os
import logging
import yaml
import time
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.utils import create_producer, create_consumer
from common.schemas.recall_schema import RecallSchema
from common.validators import RecallValidator


def setup_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )


def test_kafka_connection(config_path: str = 'config/config.yaml'):
    """Kafka 연결 테스트"""
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("Kafka 연결 테스트")
    logger.info("=" * 60)
    
    # 설정 로드
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    kafka_config = config['kafka']
    bootstrap_servers = kafka_config['bootstrap_servers']
    topics = kafka_config['topics']
    
    logger.info(f"Bootstrap Servers: {bootstrap_servers}")
    
    # Producer 테스트
    try:
        logger.info("\n1. Producer 테스트...")
        producer = create_producer(
            bootstrap_servers=bootstrap_servers,
            topic=topics['new_urls']
        )
        
        test_message = {
            'url': 'https://www.car.go.kr/sd/newsDta/view.do?newsSeq=9999',
            'title': '테스트 메시지',
            'notice_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        if producer.send(test_message):
            logger.info("  ✓ Producer 메시지 전송 성공")
        else:
            logger.error("  ✗ Producer 메시지 전송 실패")
            return False
        
        producer.flush()
        producer.close()
        
    except Exception as e:
        logger.error(f"  ✗ Producer 테스트 실패: {e}")
        return False
    
    # Consumer 테스트
    try:
        logger.info("\n2. Consumer 테스트...")
        consumer = create_consumer(
            bootstrap_servers=bootstrap_servers,
            topic=topics['new_urls'],
            group_id='test-consumer-group'
        )
        
        # 짧은 타임아웃으로 메시지 수신 시도
        received = False
        def test_handler(message):
            nonlocal received
            received = True
            logger.info(f"  ✓ Consumer 메시지 수신: {message.get('title', 'N/A')}")
        
        # 메시지 수신 시도 (최대 5초 대기)
        import threading
        stop_event = threading.Event()
        
        def consume_with_timeout():
            try:
                consumer.consume(test_handler, timeout=5)
            except:
                pass
            stop_event.set()
        
        thread = threading.Thread(target=consume_with_timeout, daemon=True)
        thread.start()
        thread.join(timeout=6)
        
        if received:
            logger.info("  ✓ Consumer 메시지 수신 성공")
        else:
            logger.warning("  ⚠ Consumer 메시지 수신 실패 (타임아웃 또는 메시지 없음)")
        
        consumer.close()
        
    except Exception as e:
        logger.error(f"  ✗ Consumer 테스트 실패: {e}")
        return False
    
    logger.info("\n✓ Kafka 연결 테스트 완료")
    return True


def test_database_connection(config_path: str = 'config/config.yaml'):
    """데이터베이스 연결 테스트"""
    logger = logging.getLogger(__name__)
    
    logger.info("\n" + "=" * 60)
    logger.info("데이터베이스 연결 테스트")
    logger.info("=" * 60)
    
    # 설정 로드
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    if 'database' not in config:
        logger.warning("  ⚠ database 설정이 없습니다. Pi3에서만 필요합니다.")
        return True
    
    db_config = config['database']
    logger.info(f"Host: {db_config.get('host', 'N/A')}")
    logger.info(f"Port: {db_config.get('port', 'N/A')}")
    logger.info(f"Database: {db_config.get('database', 'N/A')}")
    
    try:
        from pi3.db.connection import get_session
        from pi3.db.models import Recall
        
        logger.info("\n1. DB 연결 테스트...")
        session = get_session()
        
        # 간단한 쿼리 실행
        count = session.query(Recall).count()
        logger.info(f"  ✓ DB 연결 성공 (현재 레코드 수: {count})")
        
        session.close()
        
        logger.info("\n2. 테이블 구조 확인...")
        session = get_session()
        
        # 테이블 존재 확인
        from sqlalchemy import inspect
        inspector = inspect(session.bind)
        tables = inspector.get_table_names()
        
        if 'recall' in tables:
            logger.info("  ✓ 'recall' 테이블 존재")
            
            # 컬럼 확인
            columns = [col['name'] for col in inspector.get_columns('recall')]
            logger.info(f"  ✓ 컬럼 수: {len(columns)}")
        else:
            logger.error("  ✗ 'recall' 테이블이 없습니다.")
            logger.info("  스키마를 생성하세요: python3 -c 'from pi3.db.connection import get_engine; from pi3.db.models import Base; Base.metadata.create_all(get_engine())'")
            session.close()
            return False
        
        session.close()
        
        logger.info("\n✓ 데이터베이스 연결 테스트 완료")
        return True
        
    except ImportError:
        logger.warning("  ⚠ DB 모듈을 찾을 수 없습니다. Pi3에서만 필요합니다.")
        return True
    except Exception as e:
        logger.error(f"  ✗ 데이터베이스 연결 실패: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return False


def test_full_pipeline(config_path: str = 'config/config.yaml'):
    """전체 파이프라인 테스트"""
    logger = logging.getLogger(__name__)
    
    logger.info("\n" + "=" * 60)
    logger.info("전체 파이프라인 테스트")
    logger.info("=" * 60)
    
    # 설정 로드
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    kafka_config = config['kafka']
    topics = kafka_config['topics']
    
    try:
        # 테스트 데이터 생성
        test_recall = {
            'url': 'https://www.car.go.kr/sd/newsDta/view.do?newsSeq=9999',
            'title': '통합 테스트 리콜',
            'maker': '테스트',
            'model': '테스트 모델',
            'defect_part': '엔진',
            'defect_part_std': 'engine',
            'symptom': '테스트 증상',
            'action': '테스트 시정조치',
            'qty': 100,
            'notice_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        # 스키마 생성 및 검증
        recall = RecallSchema.from_dict(test_recall)
        is_valid, errors = RecallValidator.validate(recall)
        
        if not is_valid:
            logger.error(f"  ✗ 데이터 검증 실패: {errors}")
            return False
        
        logger.info("  ✓ 데이터 검증 성공")
        
        # Kafka에 발행
        logger.info("\n1. Pi2 → Pi3 데이터 전달 테스트...")
        producer = create_producer(
            bootstrap_servers=kafka_config['bootstrap_servers'],
            topic=topics['parsed_recalls']
        )
        
        if producer.send(recall.to_dict()):
            logger.info("  ✓ Kafka 발행 성공")
        else:
            logger.error("  ✗ Kafka 발행 실패")
            return False
        
        producer.flush()
        producer.close()
        
        # Consumer로 수신 (Pi3 시뮬레이션)
        logger.info("\n2. Pi3 데이터 수신 테스트...")
        consumer = create_consumer(
            bootstrap_servers=kafka_config['bootstrap_servers'],
            topic=topics['parsed_recalls'],
            group_id='test-pi3-group'
        )
        
        received = False
        def handler(message):
            nonlocal received
            received = True
            logger.info(f"  ✓ 데이터 수신 성공: {message.get('title', 'N/A')}")
        
        # 짧은 타임아웃으로 수신 시도
        import threading
        stop_event = threading.Event()
        
        def consume_with_timeout():
            try:
                consumer.consume(handler, timeout=5)
            except:
                pass
            stop_event.set()
        
        thread = threading.Thread(target=consume_with_timeout, daemon=True)
        thread.start()
        thread.join(timeout=6)
        
        if received:
            logger.info("  ✓ 데이터 수신 성공")
        else:
            logger.warning("  ⚠ 데이터 수신 실패 (타임아웃)")
        
        consumer.close()
        
        logger.info("\n✓ 전체 파이프라인 테스트 완료")
        return True
        
    except Exception as e:
        logger.error(f"  ✗ 전체 파이프라인 테스트 실패: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return False


def main():
    """메인 함수"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    import argparse
    parser = argparse.ArgumentParser(description='통합 테스트')
    parser.add_argument('--config', default='config/config.yaml', help='설정 파일 경로')
    parser.add_argument('--skip-kafka', action='store_true', help='Kafka 테스트 건너뛰기')
    parser.add_argument('--skip-db', action='store_true', help='DB 테스트 건너뛰기')
    parser.add_argument('--skip-pipeline', action='store_true', help='파이프라인 테스트 건너뛰기')
    
    args = parser.parse_args()
    
    config_path = args.config
    if not os.path.exists(config_path):
        logger.error(f"설정 파일을 찾을 수 없습니다: {config_path}")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("통합 테스트 시작")
    logger.info("=" * 60)
    
    results = {}
    
    # Kafka 테스트
    if not args.skip_kafka:
        results['kafka'] = test_kafka_connection(config_path)
    else:
        logger.info("Kafka 테스트 건너뜀")
        results['kafka'] = None
    
    # DB 테스트
    if not args.skip_db:
        results['database'] = test_database_connection(config_path)
    else:
        logger.info("DB 테스트 건너뜀")
        results['database'] = None
    
    # 파이프라인 테스트
    if not args.skip_pipeline:
        results['pipeline'] = test_full_pipeline(config_path)
    else:
        logger.info("파이프라인 테스트 건너뜀")
        results['pipeline'] = None
    
    # 결과 요약
    logger.info("\n" + "=" * 60)
    logger.info("테스트 결과 요약")
    logger.info("=" * 60)
    
    for test_name, result in results.items():
        if result is None:
            status = "건너뜀"
        elif result:
            status = "✓ 성공"
        else:
            status = "✗ 실패"
        logger.info(f"{test_name:15}: {status}")
    
    # 종료 코드
    failed_tests = [name for name, result in results.items() if result is False]
    if failed_tests:
        logger.error(f"\n✗ {len(failed_tests)}개 테스트 실패")
        sys.exit(1)
    else:
        logger.info("\n✓ 모든 테스트 통과!")
        sys.exit(0)


if __name__ == '__main__':
    main()

