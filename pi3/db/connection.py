"""
데이터베이스 연결 모듈
"""
import logging
import yaml
from typing import Optional
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool


logger = logging.getLogger(__name__)


class DatabaseConnection:
    """데이터베이스 연결 관리 클래스"""
    
    def __init__(self, config_path: str = 'config/config.yaml'):
        """
        Args:
            config_path: 설정 파일 경로
        """
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        db_config = config['database']
        
        # 연결 문자열 생성
        connection_string = (
            f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
            f"?charset=utf8mb4"
        )
        
        # 엔진 생성
        self.engine = create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,  # 연결 유효성 자동 확인
            echo=False
        )
        
        # 세션 팩토리 생성
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False
        )
        
        logger.info(f"데이터베이스 연결 초기화 완료: {db_config['host']}:{db_config['port']}/{db_config['database']}")
    
    def get_session(self) -> Session:
        """새로운 세션 반환"""
        return self.SessionLocal()
    
    def close(self):
        """연결 종료"""
        self.engine.dispose()
        logger.info("데이터베이스 연결 종료")


# 전역 연결 인스턴스
_db_connection: Optional[DatabaseConnection] = None


def get_db_connection(config_path: str = 'config/config.yaml') -> DatabaseConnection:
    """데이터베이스 연결 인스턴스 반환 (싱글톤)"""
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection(config_path)
    return _db_connection


def get_session(config_path: str = 'config/config.yaml') -> Session:
    """새로운 데이터베이스 세션 반환"""
    db = get_db_connection(config_path)
    return db.get_session()

