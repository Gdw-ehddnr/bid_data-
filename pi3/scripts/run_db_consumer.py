#!/usr/bin/env python3
"""
Pi3 DB 저장 및 HDFS 적재 Consumer 실행 스크립트
Kafka에서 파싱된 데이터를 수신하여 DB에 저장하고, 주기적으로 HDFS에 적재
"""
import sys
import os
import logging
import yaml
import threading
import time
from datetime import datetime, timedelta

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from common.utils import create_consumer, create_producer
from common.schemas.recall_schema import RecallSchema
from common.validators import RecallValidator
from pi3.db.connection import get_session
from pi3.db.repository import RecallRepository


def setup_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler('pi3/logs/db_consumer.log'),
            logging.StreamHandler()
        ]
    )


def main():
    """메인 함수"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 설정 로드
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    kafka_config = config['kafka']
    
    # Kafka Consumer 생성
    consumer = create_consumer(
        bootstrap_servers=kafka_config['bootstrap_servers'],
        topic=kafka_config['topics']['parsed_recalls'],
        group_id=kafka_config['consumer_groups']['pi3']
    )
    
    # Kafka Producer 생성 (선택적 - DB 저장 완료 메시지 발행용)
    producer = None
    if 'db_records' in kafka_config['topics']:
        producer = create_producer(
            bootstrap_servers=kafka_config['bootstrap_servers'],
            topic=kafka_config['topics']['db_records']
        )
    
    logger.info("Pi3 DB 저장 및 HDFS 적재 Consumer 시작")
    
    # 마지막 HDFS 적재 시간 추적
    last_hdfs_export = datetime.now()
    hadoop_config = config.get('hadoop', {})
    hdfs_export_interval = hadoop_config.get('export_interval_hours', 24)  # 기본 24시간
    
    def export_to_hdfs_periodically():
        """주기적으로 HDFS에 데이터 적재"""
        nonlocal last_hdfs_export
        
        while True:
            try:
                time.sleep(3600)  # 1시간마다 체크
                
                now = datetime.now()
                if (now - last_hdfs_export).total_seconds() >= hdfs_export_interval * 3600:
                    logger.info("주기적 HDFS 적재 시작")
                    try:
                        # 동적 import로 순환 참조 방지
                        import importlib.util
                        spec = importlib.util.spec_from_file_location(
                            "load_to_hdfs",
                            os.path.join(os.path.dirname(__file__), "load_to_hdfs.py")
                        )
                        load_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(load_module)
                        
                        # 마지막 export 이후의 데이터만 적재
                        since_date = last_hdfs_export.strftime('%Y-%m-%d')
                        load_module.load_to_hdfs_from_db(since_date=since_date)
                        last_hdfs_export = now
                        logger.info("주기적 HDFS 적재 완료")
                    except Exception as e:
                        logger.error(f"주기적 HDFS 적재 실패: {e}")
                        import traceback
                        logger.debug(traceback.format_exc())
            except Exception as e:
                logger.error(f"HDFS 적재 스레드 오류: {e}")
                time.sleep(60)  # 오류 시 1분 후 재시도
    
    # HDFS 적재 스레드 시작 (백그라운드)
    hdfs_thread = threading.Thread(target=export_to_hdfs_periodically, daemon=True)
    hdfs_thread.start()
    logger.info(f"HDFS 적재 스레드 시작 (간격: {hdfs_export_interval}시간)")
    
    def process_message(message):
        """메시지 처리 함수"""
        try:
            # RecallSchema 생성
            recall = RecallSchema.from_dict(message)
            
            # 데이터 검증
            is_valid, errors = RecallValidator.validate(recall)
            
            if not is_valid:
                logger.warning(f"검증 실패: {recall.url}, 오류: {errors}")
                return
            
            # DB 세션 생성
            session = get_session()
            repository = RecallRepository(session)
            
            try:
                # DB 저장
                success, error = repository.save(recall)
                
                if success:
                    logger.info(f"DB 저장 완료: {recall.url}")
                    
                    # (선택적) 저장 완료 메시지 발행
                    if producer:
                        producer.send({
                            'url': recall.url,
                            'status': 'saved',
                            'id': recall.url  # 실제로는 DB ID 사용
                        })
                else:
                    logger.warning(f"DB 저장 실패: {recall.url}, 오류: {error}")
                    
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"메시지 처리 중 오류: {e}, 메시지: {message}")
    
    # 메시지 소비
    try:
        consumer.consume(process_message)
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
    finally:
        consumer.close()
        if producer:
            producer.flush()
            producer.close()
        logger.info("Pi3 DB 저장 및 HDFS 적재 Consumer 종료")


if __name__ == '__main__':
    main()

