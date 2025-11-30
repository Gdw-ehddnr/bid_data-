#!/usr/bin/env python3
"""
Kafka 토픽 생성 스크립트
필요한 모든 토픽을 자동으로 생성합니다.
"""
import sys
import os
import subprocess
import yaml
import logging

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def setup_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )


def create_topic(bootstrap_servers: str, topic: str, partitions: int = 1, replication_factor: int = 1):
    """Kafka 토픽 생성"""
    logger = logging.getLogger(__name__)
    
    # kafka-topics.sh 경로 찾기
    kafka_home = os.environ.get('KAFKA_HOME', '')
    if not kafka_home:
        # 일반적인 경로들 시도
        possible_paths = [
            os.path.expanduser('~/kafka/kafka_2.13-3.5.0/bin/kafka-topics.sh'),
            '/opt/kafka/bin/kafka-topics.sh',
            'kafka-topics.sh'  # PATH에 있는 경우
        ]
        
        kafka_topics_cmd = None
        for path in possible_paths:
            if os.path.exists(path) or subprocess.run(['which', path.split('/')[-1])[0]], 
                                                      capture_output=True).returncode == 0:
                kafka_topics_cmd = path
                break
        
        if not kafka_topics_cmd:
            logger.error("kafka-topics.sh를 찾을 수 없습니다.")
            logger.info("KAFKA_HOME 환경 변수를 설정하거나 kafka-topics.sh가 PATH에 있는지 확인하세요.")
            return False
    else:
        kafka_topics_cmd = os.path.join(kafka_home, 'bin/kafka-topics.sh')
    
    # 토픽이 이미 존재하는지 확인
    check_cmd = [
        kafka_topics_cmd,
        '--bootstrap-server', bootstrap_servers,
        '--list'
    ]
    
    try:
        result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=10)
        if topic in result.stdout:
            logger.info(f"토픽 '{topic}'이 이미 존재합니다.")
            return True
    except Exception as e:
        logger.warning(f"토픽 목록 확인 실패: {e}")
    
    # 토픽 생성
    create_cmd = [
        kafka_topics_cmd,
        '--create',
        '--bootstrap-server', bootstrap_servers,
        '--topic', topic,
        '--partitions', str(partitions),
        '--replication-factor', str(replication_factor)
    ]
    
    try:
        result = subprocess.run(create_cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            logger.info(f"토픽 '{topic}' 생성 완료")
            return True
        else:
            if 'already exists' in result.stderr.lower():
                logger.info(f"토픽 '{topic}'이 이미 존재합니다.")
                return True
            else:
                logger.error(f"토픽 '{topic}' 생성 실패: {result.stderr}")
                return False
    except FileNotFoundError:
        logger.error(f"kafka-topics.sh를 찾을 수 없습니다: {kafka_topics_cmd}")
        logger.info("Kafka가 설치되어 있고 PATH에 있는지 확인하세요.")
        return False
    except subprocess.TimeoutExpired:
        logger.error(f"토픽 생성 시간 초과: {topic}")
        return False
    except Exception as e:
        logger.error(f"토픽 생성 중 오류: {e}")
        return False


def main():
    """메인 함수"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 설정 파일 경로
    config_path = 'config/config.yaml'
    if not os.path.exists(config_path):
        logger.error(f"설정 파일을 찾을 수 없습니다: {config_path}")
        logger.info("config/config.example.yaml을 복사하여 config/config.yaml을 생성하세요.")
        sys.exit(1)
    
    # 설정 로드
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    kafka_config = config.get('kafka', {})
    bootstrap_servers = kafka_config.get('bootstrap_servers', 'localhost:9092')
    topics = kafka_config.get('topics', {})
    
    logger.info("=" * 60)
    logger.info("Kafka 토픽 생성 시작")
    logger.info("=" * 60)
    logger.info(f"Bootstrap Servers: {bootstrap_servers}")
    logger.info("")
    
    # 필요한 토픽 목록
    required_topics = {
        'new_urls': topics.get('new_urls', 'recall-new-urls'),
        'parsed_recalls': topics.get('parsed_recalls', 'recall-parsed'),
        'db_records': topics.get('db_records', 'recall-db-records')
    }
    
    success_count = 0
    fail_count = 0
    
    for topic_key, topic_name in required_topics.items():
        logger.info(f"토픽 생성 중: {topic_name}")
        if create_topic(bootstrap_servers, topic_name):
            success_count += 1
        else:
            fail_count += 1
        logger.info("")
    
    # 결과 요약
    logger.info("=" * 60)
    logger.info("토픽 생성 결과")
    logger.info("=" * 60)
    logger.info(f"성공: {success_count}개")
    logger.info(f"실패: {fail_count}개")
    
    if fail_count > 0:
        logger.warning("일부 토픽 생성에 실패했습니다.")
        logger.info("Kafka 서버가 실행 중인지 확인하세요.")
        sys.exit(1)
    else:
        logger.info("모든 토픽 생성 완료!")
        
        # 토픽 목록 확인
        logger.info("\n생성된 토픽 목록:")
        for topic_key, topic_name in required_topics.items():
            logger.info(f"  - {topic_name}")


if __name__ == '__main__':
    main()

