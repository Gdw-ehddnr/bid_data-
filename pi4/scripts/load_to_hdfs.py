#!/usr/bin/env python3
"""
Pi4 HDFS 적재 스크립트
Kafka에서 데이터를 수신하거나 DB에서 조회하여 HDFS에 적재
"""
import sys
import os
import logging
import yaml
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from common.utils import create_consumer


def setup_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler('pi4/logs/hdfs_loader.log'),
            logging.StreamHandler()
        ]
    )


def load_to_hdfs_from_kafka():
    """Kafka에서 데이터를 수신하여 HDFS에 적재"""
    logger = logging.getLogger(__name__)
    
    # 설정 로드
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    kafka_config = config['kafka']
    hadoop_config = config['hadoop']
    
    # Kafka Consumer 생성
    consumer = create_consumer(
        bootstrap_servers=kafka_config['bootstrap_servers'],
        topic=kafka_config['topics']['db_records'],
        group_id=kafka_config['consumer_groups']['pi4']
    )
    
    logger.info("Pi4 HDFS 적재 Consumer 시작")
    
    # HDFS 경로
    hdfs_path = hadoop_config['hdfs_path']
    
    def process_message(message):
        """메시지 처리 함수"""
        try:
            # 메시지에서 데이터 추출
            url = message.get('url')
            status = message.get('status')
            
            if status != 'saved':
                logger.warning(f"저장되지 않은 레코드 무시: {url}")
                return
            
            # HDFS 적재 로직
            # 실제 구현은 hadoop/hdfs 클라이언트 사용
            # 예시: hdfs3, pyarrow, 또는 subprocess로 hdfs 명령 실행
            
            logger.info(f"HDFS 적재: {url}")
            
            # 실제 HDFS 적재 코드 (예시)
            # import subprocess
            # subprocess.run(['hdfs', 'dfs', '-put', local_file, hdfs_path])
            
        except Exception as e:
            logger.error(f"메시지 처리 중 오류: {e}, 메시지: {message}")
    
    # 메시지 소비
    try:
        consumer.consume(process_message)
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
    finally:
        consumer.close()
        logger.info("Pi4 HDFS 적재 Consumer 종료")


def load_to_hdfs_from_db():
    """DB에서 직접 조회하여 HDFS에 적재"""
    logger = logging.getLogger(__name__)
    
    # 설정 로드
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    hadoop_config = config['hadoop']
    
    # DB에서 데이터 조회
    from pi3.db.connection import get_session
    from pi3.db.models import Recall
    
    session = get_session()
    
    try:
        # 최근 데이터 조회 (예: 오늘 생성된 데이터)
        recalls = session.query(Recall).all()
        
        logger.info(f"총 {len(recalls)}개 레코드 조회")
        
        # CSV로 임시 저장
        import csv
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_csv = f'/tmp/recall_export_{timestamp}.csv'
        
        with open(temp_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'id', 'url', 'title', 'maker', 'model', 'model_year',
                'defect_part', 'defect_part_std', 'symptom', 'action',
                'start_date', 'qty', 'notice_date'
            ])
            writer.writeheader()
            
            for recall in recalls:
                row = recall.to_dict()
                # 날짜 객체를 문자열로 변환
                if row.get('start_date'):
                    row['start_date'] = str(row['start_date'])
                if row.get('notice_date'):
                    row['notice_date'] = str(row['notice_date'])
                writer.writerow(row)
        
        # HDFS에 적재
        hdfs_path = hadoop_config['hdfs_path']
        hdfs_file = f"{hdfs_path}/recall_{timestamp}.csv"
        
        # HDFS 명령 실행 (실제 환경에 맞게 수정)
        import subprocess
        result = subprocess.run(
            ['hdfs', 'dfs', '-put', temp_csv, hdfs_file],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info(f"HDFS 적재 완료: {hdfs_file}")
        else:
            logger.error(f"HDFS 적재 실패: {result.stderr}")
        
        # 임시 파일 삭제
        os.remove(temp_csv)
        
    except Exception as e:
        logger.error(f"HDFS 적재 중 오류: {e}")
        raise
    finally:
        session.close()


def main():
    """메인 함수"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    import argparse
    parser = argparse.ArgumentParser(description='HDFS에 데이터 적재')
    parser.add_argument(
        '--source',
        choices=['kafka', 'db'],
        default='db',
        help='데이터 소스 (kafka 또는 db)'
    )
    
    args = parser.parse_args()
    
    try:
        if args.source == 'kafka':
            load_to_hdfs_from_kafka()
        else:
            load_to_hdfs_from_db()
    except Exception as e:
        logger.error(f"실행 중 오류: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

