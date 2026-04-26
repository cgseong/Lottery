#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
로또 분석 시스템 상수 정의
"""

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
DEFAULT_TICKETS_FILE = 'lotto_tickets.json'
DEFAULT_DNN_MODEL_PATH = 'lotto_dnn_model.keras'
DEFAULT_DNN_SCALER_PATH = 'lotto_dnn_scaler.pkl'
DEFAULT_AI_MODELS_PATH = 'ai_pattern_models.pkl'

# 메뉴 옵션
MENU_OPTIONS = {
    'MAIN_MENU': {
        'RECOMMEND': '1',
        'EXCLUDE': '2', 
        'TICKETS': '3',
        'STATISTICS': '4',
        'EXCLUDE_RECOMMEND': '5',
        'DATA_COLLECTION': '6',
        'DNN_PREDICT': '7',
        'ENSEMBLE': '8',
        'AI_PATTERN': '9',
        'LINE_PATTERN': '10',
        'SYSTEM_INFO': '11',
        'EXIT': '0'
    }
}

# 분석기 타입
ANALYZER_TYPES = {
    'STATISTICAL': 'statistical',
    'PATTERN_MATCHING': 'pattern_matching', 
    'ENSEMBLE': 'ensemble',
    'MERSENNE_TWISTER': 'mersenne_twister',
    'TREND': 'trend',
    'DNN': 'dnn',
    'AI_PATTERN': 'ai_pattern',
    'LINE_PATTERN': 'line_pattern'
}

# 패턴 타입
PATTERN_TYPES = {
    'DENSE': '밀집형',
    'BALANCED': '균형형', 
    'DISPERSED': '분산형',
    'BEND': '꺾임형',
    'ZIGZAG': '지그재그형',
    'COMPLEX': '복합형',
    'SINGLE': '단일점'
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
    'ROUND_URL': 'https://dhlottery.co.kr/gameResult.do?method=byWin&drwNo={}'
}

# 그리드 설정
GRID_CONFIG = {
    'ROWS': 7,
    'COLS': 7,
    'LAST_ROW_COLS': 3
}

# AI 모델 설정
AI_MODEL_CONFIG = {
    'DEFAULT_CLUSTERS': 5,
    'DEFAULT_GROUP_SIZE': 5,
    'DEFAULT_EPOCHS': 100,
    'DEFAULT_BATCH_SIZE': 32,
    'DEFAULT_WINDOW_SIZE': 10
}

# 점수 가중치
SCORE_WEIGHTS = {
    'FREQUENCY': 0.4,
    'SUM': 0.3,
    'CONSECUTIVE': 0.2,
    'PATTERN': 0.1
} 