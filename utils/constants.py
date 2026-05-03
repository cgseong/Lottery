#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""로또 분석 시스템 상수 정의"""

# 로또 기본 상수
MAX_LOTTO_NUMBER = 45
NUM_LOTTO_NUMBERS_TO_PICK = 6
DEFAULT_RECENT_COUNT = 10

# 로또 번호 컬럼명
LOTTO_NUMBER_COLUMNS = [f'번호{i}' for i in range(1, 7)]
BONUS_COLUMN = '보너스번호'
ROUND_COLUMN = '회차'

# 파일 경로
DEFAULT_CSV_FILE = '로또당첨번호.csv'
DEFAULT_EXCLUDE_FILE = 'exclude_numbers.json'
DEFAULT_SAVED_FILE = 'saved_numbers.json'
DEFAULT_AI_MODELS_PATH = 'ai_models.pkl'

# 메뉴 옵션 (main.py 메뉴와 동기화)
MENU_OPTIONS = {
    'MAIN_MENU': {
        'ANALYZE': '1',
        'RECOMMEND': '2',
        'EXCLUDE': '3',
        'ADVANCED_RECOMMEND': '4',
        'SAVED': '5',
        'AI_PATTERN': '6',
        'DATA_UPDATE': '7',
        'COMPREHENSIVE': '8',
        'EXIT': '0',
    }
}

# 분석기 타입
ANALYZER_TYPES = {
    'STATISTICAL': 'statistical',
    'COMPREHENSIVE': 'comprehensive',
    'AI_PATTERN': 'ai_pattern',
}

# 패턴 타입
PATTERN_TYPES = {
    'DENSE': '밀집형',
    'BALANCED': '균형형',
    'DISPERSED': '분산형',
    'BEND': '꺾임형',
    'ZIGZAG': '지그재그형',
    'COMPLEX': '복합형',
    'SINGLE': '단일점',
}

# HTTP 헤더
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# URL 템플릿
URL_TEMPLATES = {
    'BASE_URL': 'https://dhlottery.co.kr',
    'SEARCH_URL': 'https://dhlottery.co.kr/gameResult.do?method=byWin',
    'ROUND_URL': 'https://dhlottery.co.kr/gameResult.do?method=byWin&drwNo={}',
}

# AI 모델 설정
AI_MODEL_CONFIG = {
    'WINDOW_SIZE': 5,
    'FEATURE_DIM': 125,
    'MAX_ITER': 100,
    'RANDOM_STATE': 42,
}

# 기본 점수 가중치
DEFAULT_SCORE_WEIGHTS = {
    'frequency': 0.45,
    'sum': 0.20,
    'trend': 0.20,
    'distribution': 0.15,
}

# 상금 분배 최적화 구간
PRIZE_SHARING_BIRTHDAY_MAX = 31   # 생일 선택 편향 상한 (1~31)
PRIZE_SHARING_HIGH_MULT = 1.40    # 비생일 구간 가중치
PRIZE_SHARING_LOW_MULT = 0.75     # 생일 구간 가중치
PRIZE_SHARING_ROUND_MULT = 0.85   # 5의 배수 추가 감소