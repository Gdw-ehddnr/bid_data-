#!/usr/bin/env python3
"""
설정 파일 검증 스크립트
각 Pi의 설정 파일이 올바르게 구성되었는지 확인합니다.
"""
import sys
import os
import yaml
import logging
from typing import Dict, List, Tuple

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def setup_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )


def validate_config(config: Dict, pi_id: str) -> Tuple[bool, List[str]]:
    """설정 파일 검증"""
    logger = logging.getLogger(__name__)
    errors = []
    warnings = []
    
    # 필수 섹션 확인
    required_sections = ['kafka', 'crawling']
    for section in required_sections:
        if section not in config:
            errors.append(f"필수 섹션 '{section}'이 없습니다.")
    
    # Kafka 설정 검증
    if 'kafka' in config:
        kafka = config['kafka']
        
        if 'bootstrap_servers' not in kafka:
            errors.append("kafka.bootstrap_servers가 설정되지 않았습니다.")
        elif not kafka['bootstrap_servers']:
            errors.append("kafka.bootstrap_servers가 비어있습니다.")
        elif 'localhost' in kafka['bootstrap_servers'] and pi_id != 'pi1':
            warnings.append("kafka.bootstrap_servers가 localhost입니다. 실제 IP 주소를 사용하는 것이 좋습니다.")
        
        if 'topics' in kafka:
            required_topics = ['new_urls', 'parsed_recalls']
            for topic_key in required_topics:
                if topic_key not in kafka['topics']:
                    errors.append(f"kafka.topics.{topic_key}가 설정되지 않았습니다.")
    
    # Pi별 특정 검증
    if pi_id == 'pi3':
        if 'database' not in config:
            errors.append("pi3는 database 설정이 필요합니다.")
        else:
            db = config['database']
            required_db_fields = ['host', 'port', 'user', 'password', 'database']
            for field in required_db_fields:
                if field not in db:
                    errors.append(f"database.{field}가 설정되지 않았습니다.")
                elif not db[field]:
                    errors.append(f"database.{field}가 비어있습니다.")
            
            if 'password' in db and db['password'] == 'your_password_here':
                warnings.append("database.password가 기본값입니다. 실제 비밀번호로 변경하세요.")
        
        if 'hadoop' in config:
            hadoop = config['hadoop']
            if 'hdfs_path' not in hadoop:
                warnings.append("hadoop.hdfs_path가 설정되지 않았습니다.")
    
    # 크롤링 설정 검증
    if 'crawling' in config:
        crawling = config['crawling']
        if 'base_url' not in crawling:
            errors.append("crawling.base_url이 설정되지 않았습니다.")
    
    return len(errors) == 0, errors, warnings


def main():
    """메인 함수"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    import argparse
    parser = argparse.ArgumentParser(description='설정 파일 검증')
    parser.add_argument('--pi', choices=['pi1', 'pi2', 'pi3', 'pi4'], help='Pi ID')
    parser.add_argument('--config', default='config/config.yaml', help='설정 파일 경로')
    
    args = parser.parse_args()
    
    config_path = args.config
    if not os.path.exists(config_path):
        logger.error(f"설정 파일을 찾을 수 없습니다: {config_path}")
        sys.exit(1)
    
    # Pi ID 자동 감지
    pi_id = args.pi
    if not pi_id:
        # 설정 파일에서 pi.id 확인
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        pi_id = config.get('pi', {}).get('id', 'unknown')
    
    logger.info("=" * 60)
    logger.info(f"설정 파일 검증: {config_path}")
    logger.info(f"Pi ID: {pi_id}")
    logger.info("=" * 60)
    
    # 설정 파일 로드
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # 검증
    is_valid, errors, warnings = validate_config(config, pi_id)
    
    # 결과 출력
    if errors:
        logger.error("\n오류:")
        for error in errors:
            logger.error(f"  ✗ {error}")
    
    if warnings:
        logger.warning("\n경고:")
        for warning in warnings:
            logger.warning(f"  ⚠ {warning}")
    
    if is_valid:
        logger.info("\n✓ 설정 파일이 올바르게 구성되었습니다!")
        
        # 주요 설정 출력
        logger.info("\n주요 설정:")
        if 'kafka' in config:
            logger.info(f"  Kafka: {config['kafka'].get('bootstrap_servers', 'N/A')}")
        if 'database' in config:
            db = config['database']
            logger.info(f"  Database: {db.get('host', 'N/A')}:{db.get('port', 'N/A')}/{db.get('database', 'N/A')}")
        if 'hadoop' in config:
            logger.info(f"  HDFS: {config['hadoop'].get('hdfs_path', 'N/A')}")
        
        sys.exit(0)
    else:
        logger.error("\n✗ 설정 파일에 오류가 있습니다. 위의 오류를 수정하세요.")
        sys.exit(1)


if __name__ == '__main__':
    main()

