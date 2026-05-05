"""
파일 처리 유틸리티
"""

import csv
import os
from typing import Dict, List


# 데이터 파일 관련 상수
DEFAULT_DATA_FILE = '로또당첨번호.csv'
ADDITIONAL_DATA_FILE_CANDIDATES = [
    'lotto_winning_numbers.csv',
    '로또_당첨번호.csv',
    'lotto_results.csv',
]

# CSV 인코딩 시도 순서
_CSV_ENCODINGS = ('utf-8', 'cp949', 'euc-kr')


def resolve_data_file() -> str:
    """현재 작업 디렉터리에서 사용할 당첨 번호 CSV 파일을 결정합니다."""
    for name in [DEFAULT_DATA_FILE] + ADDITIONAL_DATA_FILE_CANDIDATES:
        if os.path.exists(name):
            return name

    try:
        for entry in os.listdir('.'):
            lower = entry.lower()
            if lower.endswith('.csv') and ('lotto' in lower or '로또' in entry):
                return entry
    except OSError:
        pass

    return DEFAULT_DATA_FILE


def load_csv_data(filename: str) -> List[Dict]:
    """인코딩 자동 감지로 로또 당첨번호 CSV를 로드합니다.

    '번호1' 컬럼이 포함된 파일만 유효한 데이터로 인정합니다.
    읽기 실패 시 빈 리스트를 반환합니다.
    """
    if not os.path.exists(filename):
        return []

    for enc in _CSV_ENCODINGS:
        try:
            with open(filename, 'r', encoding=enc, newline='') as f:
                reader = csv.DictReader(f)
                data = list(reader)
                if data and any('번호1' in str(k) for k in data[0].keys()):
                    return data
        except Exception:
            continue

    return []
