"""
데이터베이스 모델 정의
"""
from sqlalchemy import Column, BigInteger, String, Integer, Date, Text, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import Optional

Base = declarative_base()


class Recall(Base):
    """리콜 데이터 모델"""
    __tablename__ = 'recall'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    url = Column(String(500), nullable=False, unique=True, comment='상세링크 (PK 후보)')
    title = Column(String(500), nullable=False, comment='제목')
    maker = Column(String(100), nullable=False, comment='제조사')
    model = Column(String(200), nullable=False, comment='모델/연식')
    model_year = Column(Integer, nullable=True, comment='연식 (파싱된 숫자)')
    defect_part = Column(String(200), nullable=False, comment='결함부위')
    defect_part_std = Column(String(100), nullable=True, comment='표준부위 (매핑된 값)')
    symptom = Column(Text, nullable=False, comment='증상')
    action = Column(Text, nullable=False, comment='시정조치')
    start_date = Column(Date, nullable=True, comment='시정개시 (YYYY-MM-DD)')
    qty = Column(Integer, nullable=True, comment='대상대수')
    notice_date = Column(Date, nullable=True, comment='공지일 (YYYY-MM-DD)')
    created_at = Column(TIMESTAMP, default=datetime.now, comment='레코드 생성 시간')
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now, comment='레코드 수정 시간')
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            'id': self.id,
            'url': self.url,
            'title': self.title,
            'maker': self.maker,
            'model': self.model,
            'model_year': self.model_year,
            'defect_part': self.defect_part,
            'defect_part_std': self.defect_part_std,
            'symptom': self.symptom,
            'action': self.action,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'qty': self.qty,
            'notice_date': self.notice_date.isoformat() if self.notice_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_schema(cls, schema) -> 'Recall':
        """RecallSchema에서 모델 생성"""
        from common.schemas.recall_schema import RecallSchema
        
        data = schema.to_dict() if isinstance(schema, RecallSchema) else schema
        
        # 날짜 문자열을 Date 객체로 변환
        start_date = None
        notice_date = None
        
        if data.get('start_date'):
            try:
                start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            except:
                pass
        
        if data.get('notice_date'):
            try:
                notice_date = datetime.strptime(data['notice_date'], '%Y-%m-%d').date()
            except:
                pass
        
        return cls(
            url=data['url'],
            title=data['title'],
            maker=data['maker'],
            model=data['model'],
            model_year=data.get('model_year'),
            defect_part=data['defect_part'],
            defect_part_std=data.get('defect_part_std'),
            symptom=data['symptom'],
            action=data['action'],
            start_date=start_date,
            qty=data.get('qty'),
            notice_date=notice_date
        )
    
    def __repr__(self):
        return f"<Recall(id={self.id}, url={self.url}, maker={self.maker}, model={self.model})>"

