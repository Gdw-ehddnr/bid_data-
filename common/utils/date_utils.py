"""
날짜 유틸리티 함수
"""
import re
from datetime import datetime
from typing import Optional


def parse_date(date_str: str) -> Optional[str]:
    """
    날짜 문자열을 YYYY-MM-DD 형식으로 변환
    """
    if not date_str:
        return None
    
    # 다양한 날짜 형식 처리
    patterns = [
        (r'(\d{4})[.-](\d{1,2})[.-](\d{1,2})', '%Y-%m-%d'),  # 2025-03-12
        (r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일', '%Y-%m-%d'),  # 2025년 3월 12일
    ]
    
    for pattern, fmt in patterns:
        match = re.search(pattern, date_str)
        if match:
            try:
                year, month, day = match.groups()
                return f"{year}-{int(month):02d}-{int(day):02d}"
            except:
                continue
    
    return None


def normalize_date(date_str: str) -> Optional[str]:
    """날짜 정규화 (parse_date의 별칭)"""
    return parse_date(date_str)

