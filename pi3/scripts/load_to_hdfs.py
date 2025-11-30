#!/usr/bin/env python3
"""
Pi3 HDFS 적재 스크립트
DB에서 데이터를 조회하여 CSV로 export 후 HDFS에 적재
"""
import sys
import os
import logging
import csv
import yaml
import subprocess
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from pi3.db.connection import get_session
from pi3.db.models import Recall


def setup_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler('pi3/logs/hdfs_loader.log'),
            logging.StreamHandler()
        ]
    )


def load_to_hdfs_from_db(limit: int = None, since_date: str = None, config_path: str = 'config/config.yaml'):
    """
    DB에서 직접 조회하여 HDFS에 적재
    
    Args:
        limit: 최대 레코드 수 (None이면 전체)
        since_date: 이 날짜 이후 데이터만 조회 (YYYY-MM-DD 형식)
    """
    logger = logging.getLogger(__name__)
    
    # 설정 로드
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    hadoop_config = config.get('hadoop', {})
    
    if not hadoop_config:
        logger.warning("Hadoop 설정이 없습니다. HDFS 적재를 건너뜁니다.")
        return
    
    # DB에서 데이터 조회
    session = get_session()
    
    try:
        # 데이터 조회
        query = session.query(Recall)
        
        # 날짜 필터
        if since_date:
            from datetime import datetime as dt
            since = dt.strptime(since_date, '%Y-%m-%d').date()
            query = query.filter(Recall.created_at >= since)
        
        if limit:
            query = query.limit(limit)
        
        recalls = query.all()
        
        if not recalls:
            logger.info("적재할 데이터가 없습니다.")
            return
        
        logger.info(f"총 {len(recalls)}개 레코드 조회")
        
        # CSV로 임시 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_csv = f'/tmp/recall_export_{timestamp}.csv'
        
        with open(temp_csv, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'id', 'url', 'title', 'maker', 'model', 'model_year',
                'defect_part', 'defect_part_std', 'symptom', 'action',
                'start_date', 'qty', 'notice_date', 'created_at', 'updated_at'
            ])
            writer.writeheader()
            
            for recall in recalls:
                row = recall.to_dict()
                # 날짜 객체를 문자열로 변환
                if row.get('start_date'):
                    row['start_date'] = str(row['start_date'])
                if row.get('notice_date'):
                    row['notice_date'] = str(row['notice_date'])
                if row.get('created_at'):
                    row['created_at'] = str(row['created_at'])
                if row.get('updated_at'):
                    row['updated_at'] = str(row['updated_at'])
                writer.writerow(row)
        
        logger.info(f"CSV 파일 생성 완료: {temp_csv}")
        
        # HDFS에 적재
        hdfs_path = hadoop_config.get('hdfs_path', '/recall_data')
        hdfs_file = f"{hdfs_path}/recall_{timestamp}.csv"
        
        # HDFS 명령 실행
        hdfs_cmd = hadoop_config.get('hdfs_command', 'hdfs')
        hdfs_namenode = hadoop_config.get('hdfs_namenode', '')
        
        # HDFS 명령 구성
        if hdfs_namenode and not hdfs_file.startswith('hdfs://'):
            hdfs_file = f"{hdfs_namenode}{hdfs_file}"
        
        try:
            result = subprocess.run(
                [hdfs_cmd, 'dfs', '-put', temp_csv, hdfs_file],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info(f"HDFS 적재 완료: {hdfs_file}")
            else:
                logger.error(f"HDFS 적재 실패: {result.stderr}")
                # HDFS 명령이 없거나 실패해도 계속 진행
        except FileNotFoundError:
            logger.warning(f"HDFS 명령을 찾을 수 없습니다 ({hdfs_cmd}). HDFS 적재를 건너뜁니다.")
        except subprocess.TimeoutExpired:
            logger.error("HDFS 적재 시간 초과")
        except Exception as e:
            logger.error(f"HDFS 적재 중 오류: {e}")
        
        # 임시 파일 삭제
        try:
            os.remove(temp_csv)
        except:
            pass
        
    except Exception as e:
        logger.error(f"HDFS 적재 중 오류: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()


def main():
    """메인 함수"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    import argparse
    parser = argparse.ArgumentParser(description='DB 데이터를 HDFS에 적재')
    parser.add_argument('--limit', '-l', type=int, help='최대 레코드 수')
    parser.add_argument('--since', '-s', help='이 날짜 이후 데이터만 조회 (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    try:
        load_to_hdfs_from_db(args.limit, args.since)
    except Exception as e:
        logger.error(f"실행 중 오류: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

