"""
리콜 데이터 검증 모듈
"""
from typing import List, Optional
from datetime import datetime
from ..schemas.recall_schema import RecallSchema


class RecallValidator:
    """리콜 데이터 검증 클래스"""
    
    @staticmethod
    def validate(recall: RecallSchema) -> tuple[bool, List[str]]:
        """
        데이터 검증
        Returns: (is_valid, error_messages)
        """
        errors = []
        
        # 필수 필드 검증
        if not recall.maker:
            errors.append("maker 필드는 필수입니다")
        if not recall.model:
            errors.append("model 필드는 필수입니다")
        if not recall.defect_part:
            errors.append("defect_part 필드는 필수입니다")
        if not recall.symptom:
            errors.append("symptom 필드는 필수입니다")
        if not recall.action:
            errors.append("action 필드는 필수입니다")
        if not recall.url:
            errors.append("url 필드는 필수입니다")
        if not recall.title:
            errors.append("title 필드는 필수입니다")
        
        # 날짜 형식 검증
        if recall.start_date and not RecallValidator._is_valid_date(recall.start_date):
            errors.append(f"start_date 형식이 올바르지 않습니다: {recall.start_date}")
        if recall.notice_date and not RecallValidator._is_valid_date(recall.notice_date):
            errors.append(f"notice_date 형식이 올바르지 않습니다: {recall.notice_date}")
        
        # 숫자 필드 검증
        if recall.model_year is not None and recall.model_year < 1900:
            errors.append(f"model_year가 유효하지 않습니다: {recall.model_year}")
        if recall.qty is not None and recall.qty < 0:
            errors.append(f"qty가 음수입니다: {recall.qty}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _is_valid_date(date_str: str) -> bool:
        """날짜 형식 검증 (YYYY-MM-DD)"""
        if not date_str:
            return False
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except (ValueError, TypeError):
            return False

