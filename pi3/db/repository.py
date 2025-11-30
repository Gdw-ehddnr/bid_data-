"""
데이터베이스 저장소 모듈
"""
import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .models import Recall
from common.schemas.recall_schema import RecallSchema


logger = logging.getLogger(__name__)


class RecallRepository:
    """리콜 데이터 저장소"""
    
    def __init__(self, session: Session):
        """
        Args:
            session: 데이터베이스 세션
        """
        self.session = session
    
    def save(self, recall_schema: RecallSchema) -> tuple[bool, Optional[str]]:
        """
        리콜 데이터 저장 (중복 체크 포함)
        
        Args:
            recall_schema: RecallSchema 객체
        
        Returns:
            (성공 여부, 오류 메시지)
        """
        try:
            # URL로 기존 레코드 확인
            existing = self.session.query(Recall).filter_by(url=recall_schema.url).first()
            
            if existing:
                logger.debug(f"이미 존재하는 레코드: {recall_schema.url}")
                return False, "이미 존재하는 URL입니다"
            
            # 새 레코드 생성
            recall = Recall.from_schema(recall_schema)
            self.session.add(recall)
            self.session.commit()
            
            logger.info(f"리콜 데이터 저장 완료: {recall_schema.url}")
            return True, None
            
        except IntegrityError as e:
            self.session.rollback()
            error_msg = f"중복 또는 무결성 오류: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            self.session.rollback()
            error_msg = f"저장 중 오류 발생: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def save_batch(self, recall_schemas: List[RecallSchema]) -> dict:
        """
        여러 리콜 데이터 일괄 저장
        
        Args:
            recall_schemas: RecallSchema 객체 리스트
        
        Returns:
            {'success': int, 'failed': int, 'duplicates': int}
        """
        result = {'success': 0, 'failed': 0, 'duplicates': 0}
        
        for schema in recall_schemas:
            success, error = self.save(schema)
            if success:
                result['success'] += 1
            elif error and '이미 존재' in error:
                result['duplicates'] += 1
            else:
                result['failed'] += 1
        
        return result
    
    def get_by_url(self, url: str) -> Optional[Recall]:
        """URL로 레코드 조회"""
        return self.session.query(Recall).filter_by(url=url).first()
    
    def exists(self, url: str) -> bool:
        """URL 존재 여부 확인"""
        return self.session.query(Recall).filter_by(url=url).first() is not None
    
    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[Recall]:
        """모든 레코드 조회"""
        query = self.session.query(Recall)
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()
    
    def count(self) -> int:
        """전체 레코드 수"""
        return self.session.query(Recall).count()

