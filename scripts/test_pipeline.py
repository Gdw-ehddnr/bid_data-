#!/usr/bin/env python3
"""
파이프라인 테스트 스크립트
각 단계별로 데이터 흐름을 확인
"""
import sys
import os
import logging
import yaml
import time

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.utils import create_producer, create_consumer


def setup_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )


def test_kafka_connection():
    """Kafka 연결 테스트"""
    logger = logging.getLogger(__name__)
    
    try:
        with open('config/config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        kafka_config = config['kafka']
        bootstrap_servers = kafka_config['bootstrap_servers']
        
        logger.info(f"Kafka 연결 테스트: {bootstrap_servers}")
        
        # Producer 테스트
        producer = create_producer(
            bootstrap_servers=bootstrap_servers,
            topic=kafka_config['topics']['new_urls']
        )
        
        test_message = {
            'url': 'https://www.car.go.kr/test',
            'title': '테스트 메시지',
            'notice_date': '2025-01-01'
        }
        
        if producer.send(test_message):
            logger.info("✓ Kafka Producer 연결 성공")
        else:
            logger.error("✗ Kafka Producer 연결 실패")
            return False
        
        producer.close()
        
        # Consumer 테스트
        consumer = create_consumer(
            bootstrap_servers=bootstrap_servers,
            topic=kafka_config['topics']['new_urls'],
            group_id='test-group'
        )
        
        # 메시지 수신 시도 (타임아웃 설정)
        message = consumer.consume_one()
        if message:
            logger.info(f"✓ Kafka Consumer 연결 성공 (메시지 수신: {message})")
        else:
            logger.info("✓ Kafka Consumer 연결 성공 (메시지 없음)")
        
        consumer.close()
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Kafka 연결 실패: {e}")
        return False


def test_db_connection():
    """DB 연결 테스트"""
    logger = logging.getLogger(__name__)
    
    try:
        with open('config/config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        if 'database' not in config:
            logger.info("DB 설정이 없습니다 (Pi3가 아닌 경우)")
            return True
        
        from pi3.db.connection import get_session
        from pi3.db.models import Recall
        
        session = get_session()
        try:
            # 간단한 쿼리 테스트
            count = session.query(Recall).count()
            logger.info(f"✓ DB 연결 성공 (레코드 수: {count})")
            return True
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"✗ DB 연결 실패: {e}")
        return False


def test_website_access():
    """웹사이트 접근 테스트"""
    logger = logging.getLogger(__name__)
    
    try:
        import requests
        
        with open('config/config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        base_url = config['crawling']['base_url']
        headers = {'User-Agent': config['crawling']['user_agent']}
        
        logger.info(f"웹사이트 접근 테스트: {base_url}")
        
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        logger.info(f"✓ 웹사이트 접근 성공 (상태 코드: {response.status_code})")
        return True
        
    except Exception as e:
        logger.error(f"✗ 웹사이트 접근 실패: {e}")
        return False


def main():
    """메인 함수"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("파이프라인 테스트 시작")
    logger.info("=" * 60)
    
    results = {}
    
    # 1. 설정 파일 확인
    logger.info("\n[1] 설정 파일 확인")
    if os.path.exists('config/config.yaml'):
        logger.info("✓ config/config.yaml 파일 존재")
        results['config'] = True
    else:
        logger.error("✗ config/config.yaml 파일이 없습니다")
        logger.info("  → config/config.example.yaml을 복사하여 수정하세요")
        results['config'] = False
        return
    
    # 2. 웹사이트 접근 테스트
    logger.info("\n[2] 웹사이트 접근 테스트")
    results['website'] = test_website_access()
    
    # 3. Kafka 연결 테스트
    logger.info("\n[3] Kafka 연결 테스트")
    results['kafka'] = test_kafka_connection()
    
    # 4. DB 연결 테스트 (Pi3인 경우)
    logger.info("\n[4] DB 연결 테스트")
    results['db'] = test_db_connection()
    
    # 결과 요약
    logger.info("\n" + "=" * 60)
    logger.info("테스트 결과 요약")
    logger.info("=" * 60)
    
    for test_name, result in results.items():
        status = "✓ 통과" if result else "✗ 실패"
        logger.info(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n✓ 모든 테스트 통과!")
    else:
        logger.warning("\n✗ 일부 테스트 실패. 설정을 확인하세요.")
    
    return all_passed


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

