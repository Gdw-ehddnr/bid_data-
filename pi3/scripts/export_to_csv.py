#!/usr/bin/env python3
"""
Pi3 DB 데이터 CSV Export 스크립트
DB에서 데이터를 조회하여 CSV로 내보내기 (Pi4로 전달용)
"""
import sys
import os
import logging
import csv
import yaml
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
            logging.FileHandler('pi3/logs/export.log'),
            logging.StreamHandler()
        ]
    )


def export_to_csv(output_path: str = None, limit: int = None):
    """DB 데이터를 CSV로 내보내기"""
    logger = logging.getLogger(__name__)
    
    # 출력 파일 경로
    if not output_path:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f'data/export/recall_export_{timestamp}.csv'
    
    # 디렉토리 생성
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # DB 세션 생성
    session = get_session()
    
    try:
        # 데이터 조회
        query = session.query(Recall)
        if limit:
            query = query.limit(limit)
        
        recalls = query.all()
        
        logger.info(f"총 {len(recalls)}개 레코드 조회")
        
        # CSV 작성
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'id', 'url', 'title', 'maker', 'model', 'model_year',
                'defect_part', 'defect_part_std', 'symptom', 'action',
                'start_date', 'qty', 'notice_date', 'created_at', 'updated_at'
            ])
            
            writer.writeheader()
            
            for recall in recalls:
                row = recall.to_dict()
                writer.writerow(row)
        
        logger.info(f"CSV 내보내기 완료: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"CSV 내보내기 중 오류: {e}")
        raise
    finally:
        session.close()


def main():
    """메인 함수"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    import argparse
    parser = argparse.ArgumentParser(description='DB 데이터를 CSV로 내보내기')
    parser.add_argument('--output', '-o', help='출력 파일 경로')
    parser.add_argument('--limit', '-l', type=int, help='최대 레코드 수')
    
    args = parser.parse_args()
    
    try:
        output_path = export_to_csv(args.output, args.limit)
        print(f"CSV 파일 생성 완료: {output_path}")
    except Exception as e:
        logger.error(f"실행 중 오류: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

