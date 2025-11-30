"""
리콜 데이터 스키마 정의
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class RecallSchema:
    """리콜 공지 데이터 스키마"""
    maker: str  # 제조사
    model: str  # 모델/연식
    defect_part: str  # 결함부위
    symptom: str  # 증상
    action: str  # 시정조치
    url: str  # 상세링크 (PK 후보)
    title: str  # 제목
    model_year: Optional[int] = None  # 연식 (파싱된 숫자)
    defect_part_std: Optional[str] = None  # 표준부위 (매핑된 값)
    start_date: Optional[str] = None  # 시정개시 (YYYY-MM-DD)
    qty: Optional[int] = None  # 대상대수
    notice_date: Optional[str] = None  # 공지일 (YYYY-MM-DD)
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            'maker': self.maker,
            'model': self.model,
            'model_year': self.model_year,
            'defect_part': self.defect_part,
            'defect_part_std': self.defect_part_std,
            'symptom': self.symptom,
            'action': self.action,
            'start_date': self.start_date,
            'qty': self.qty,
            'notice_date': self.notice_date,
            'url': self.url,
            'title': self.title
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'RecallSchema':
        """딕셔너리에서 생성"""
        return cls(**data)

