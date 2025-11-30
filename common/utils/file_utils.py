"""
파일 유틸리티 함수
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Any


def save_json(data: Dict[Any, Any], filepath: str) -> None:
    """JSON 파일로 저장"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(filepath: str) -> Dict[Any, Any]:
    """JSON 파일 로드"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def read_urls_from_file(filepath: str) -> List[str]:
    """URL 목록 파일 읽기 (한 줄에 하나씩)"""
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


def write_urls_to_file(urls: List[str], filepath: str) -> None:
    """URL 목록 파일 쓰기 (한 줄에 하나씩)"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        for url in urls:
            f.write(f"{url}\n")

