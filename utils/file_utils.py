"""
파일 처리 유틸리티
"""

import os


# 데이터 파일 관련 상수
DEFAULT_DATA_FILE = '로또당첨번호.csv'
ADDITIONAL_DATA_FILE_CANDIDATES = [
    'lotto_winning_numbers.csv',
    '로또_당첨번호.csv',
    'lotto_results.csv',
]


def resolve_data_file():
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
