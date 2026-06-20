#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
트렌드 분석기 모듈
"""

import random
from typing import List, Dict, Optional, Set, Tuple, Any

# 상수 import
from utils.constants import *
from utils.helpers import check_consecutive_count, normalize_exclude_numbers, get_last_draw_numbers, exceeds_prev_draw_overlap
from utils.logging_config import get_logger

_log = get_logger(__name__)


class TrendAnalyzer:
    """최근 추세 분석기"""
    def __init__(self, historical_data):
        self.historical_data = historical_data
        self.frequency = self.analyze_frequency()
        self.recent_trends = self.analyze_recent_trends()
        self.momentum_scores = self.calculate_momentum_scores()
        self.volatility_patterns = self.analyze_volatility_patterns()

    def analyze_frequency(self) -> dict:
        """번호별 출현 빈도 분석 (키를 int로 통일)"""
        frequency: dict = {}
        for row in self.historical_data:
            for col in LOTTO_NUMBER_COLUMNS:
                if col in row and row[col] not in (None, ''):
                    try:
                        num = int(row[col])
                        frequency[num] = frequency.get(num, 0) + 1
                    except (ValueError, TypeError):
                        pass
        return frequency

    def analyze_recent_trends(self, recent_count=20):
        """최근 추세 분석"""
        if len(self.historical_data) < recent_count:
            recent_count = len(self.historical_data)

        recent_data = self.historical_data[-recent_count:]
        trends = {}

        # 각 번호별로 최근 출현 추세 분석
        for num in range(1, MAX_LOTTO_NUMBER + 1):
            appearances = []
            for i, row in enumerate(recent_data):
                # CSV 문자열 → int 변환 후 비교
                numbers = []
                for col in LOTTO_NUMBER_COLUMNS:
                    if col in row and row[col] not in (None, ''):
                        try:
                            numbers.append(int(row[col]))
                        except (ValueError, TypeError):
                            pass
                if num in numbers:
                    appearances.append(i)

            if appearances:
                # 출현 간격 분석
                intervals = []
                for i in range(1, len(appearances)):
                    intervals.append(appearances[i] - appearances[i-1])

                # 추세 계산 (최근 출현일수록 높은 가중치)
                trend_score = 0
                for i, appearance in enumerate(appearances):
                    weight = (i + 1) / len(appearances)  # 최근일수록 높은 가중치
                    trend_score += weight

                # 평균 간격
                avg_interval = sum(intervals) / len(intervals) if intervals else recent_count

                trends[num] = {
                    'appearances': appearances,
                    'count': len(appearances),
                    'trend_score': trend_score,
                    'avg_interval': avg_interval,
                    'last_appearance': appearances[-1] if appearances else recent_count
                }
            else:
                trends[num] = {
                    'appearances': [],
                    'count': 0,
                    'trend_score': 0,
                    'avg_interval': recent_count,
                    'last_appearance': recent_count
                }

        return trends

    def calculate_momentum_scores(self):
        """모멘텀 점수 계산 (최근 출현 패턴 기반)"""
        momentum = {}

        for num in range(1, MAX_LOTTO_NUMBER + 1):
            trend = self.recent_trends[num]

            # 1. 최근 출현 빈도 점수
            frequency_score = trend['count'] * 10

            # 2. 추세 점수 (최근에 나온 번호일수록 높은 점수)
            trend_score = trend['trend_score'] * 15

            # 3. 간격 점수 (적당한 간격일수록 높은 점수)
            interval_score = 0
            if trend['avg_interval'] > 0:
                # 3-5회차 간격이 가장 이상적
                if 3 <= trend['avg_interval'] <= 5:
                    interval_score = 50
                elif 2 <= trend['avg_interval'] <= 7:
                    interval_score = 30
                elif trend['avg_interval'] <= 10:
                    interval_score = 15

            # 4. 마지막 출현 점수 (너무 최근이면 패널티, 너무 오래면 보너스)
            last_appearance_score = 0
            if trend['last_appearance'] <= 2:  # 최근 2회차 이내
                last_appearance_score = -30
            elif trend['last_appearance'] >= 8:  # 8회차 이상 안 나옴
                last_appearance_score = 40
            elif trend['last_appearance'] >= 5:  # 5회차 이상 안 나옴
                last_appearance_score = 20

            momentum[num] = frequency_score + trend_score + interval_score + last_appearance_score

        return momentum

    def analyze_volatility_patterns(self):
        """변동성 패턴 분석"""
        volatility = {}

        for num in range(1, MAX_LOTTO_NUMBER + 1):
            trend = self.recent_trends[num]

            if len(trend['appearances']) >= 2:
                # 출현 간격의 표준편차 계산
                intervals = []
                for i in range(1, len(trend['appearances'])):
                    intervals.append(trend['appearances'][i] - trend['appearances'][i-1])

                if intervals:
                    mean_interval = sum(intervals) / len(intervals)
                    variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
                    std_dev = variance ** 0.5

                    # 변동성이 낮을수록(일정한 패턴) 높은 점수
                    if std_dev <= 1.5:
                        volatility[num] = 30
                    elif std_dev <= 2.5:
                        volatility[num] = 20
                    elif std_dev <= 4.0:
                        volatility[num] = 10
                    else:
                        volatility[num] = 0
                else:
                    volatility[num] = 0
            else:
                volatility[num] = 0

        return volatility

    def calculate_score(self, numbers):
        """최근 추세 기반 점수 계산"""
        score = 0

        # 1. 모멘텀 점수
        momentum_score = sum(self.momentum_scores.get(num, 0) for num in numbers)
        score += momentum_score * 0.4

        # 2. 변동성 점수
        volatility_score = sum(self.volatility_patterns.get(num, 0) for num in numbers)
        score += volatility_score * 0.3

        # 3. 빈도 점수 (가중치 낮춤)
        freq_score = sum(self.frequency.get(num, 0) for num in numbers)
        score += freq_score * 0.2

        # 4. 연속번호 패널티
        consecutive_count = self.check_consecutive_numbers(numbers)
        score -= consecutive_count * 25

        # 5. 홀짝 균형 점수
        odd_count = sum(1 for n in numbers if n % 2 == 1)
        even_count = len(numbers) - odd_count
        balance_score = 1 - abs(odd_count - even_count) / len(numbers)
        score += balance_score * 20

        # 6. 구간 분포 점수
        sections = [0] * 5  # 1-9, 10-19, 20-29, 30-39, 40-45
        for num in numbers:
            if 1 <= num <= 9:
                sections[0] += 1
            elif 10 <= num <= 19:
                sections[1] += 1
            elif 20 <= num <= 29:
                sections[2] += 1
            elif 30 <= num <= 39:
                sections[3] += 1
            else:
                sections[4] += 1

        # 균등 분포일수록 높은 점수
        section_variance = sum((s - 1.2) ** 2 for s in sections)
        score += (10 - section_variance) * 2

        return score

    def check_consecutive_numbers(self, numbers):
        """연속 번호 쌍의 총 개수를 반환합니다. (utils.helpers 위임)"""
        return check_consecutive_count(numbers)

    def generate_recommendations(self, exclude_numbers=None, num_recommendations=5):
        """최근 추세 기반 추천 번호 생성"""
        exclude_numbers = normalize_exclude_numbers(exclude_numbers)
        _log.info("최근 추세 분석기 실행 중 (최근 20회차 모멘텀/변동성)")
        prev_draw = get_last_draw_numbers(self.historical_data)

        best_combination = None
        best_score = -1
        max_attempts = 2000

        for attempt in range(1, max_attempts + 1):
            # 추세 기반 번호 생성
            numbers = self.generate_numbers_trend(exclude_numbers)
            if not numbers:
                continue

            # 직전 회차 당첨번호 2개 이상 포함 시 제외
            if exceeds_prev_draw_overlap(numbers, prev_draw):
                continue

            # 점수 계산
            score = self.calculate_score(numbers)

            if score > best_score:
                best_score = score
                consecutive_count = self.check_consecutive_numbers(numbers)

                best_combination = {
                    'numbers': numbers,
                    'score': score,
                    'consecutive_count': consecutive_count,
                    'recent_overlap': set(),
                    'method': '최근 추세 분석'
                }
                _log.debug("새로운 최고 점수 (시도 %d): %.1f점 %s", attempt, score, numbers)

        if best_combination:
            for num in best_combination['numbers']:
                trend = self.recent_trends[num]
                momentum = self.momentum_scores[num]
                volatility = self.volatility_patterns[num]
                _log.debug(
                    "  %2d번: 출현%2d회, 모멘텀%4.0f점, 변동성%2d점",
                    num, trend['count'], momentum, volatility,
                )
            _log.info(
                "추세 분석 결과: %s  점수%.1f  연속%d개",
                best_combination['numbers'],
                best_combination['score'],
                best_combination['consecutive_count'],
            )
            return [best_combination]

        return []

    def generate_numbers_trend(self, exclude_numbers):
        """최근 추세 기반 번호 생성"""
        exclude_numbers = normalize_exclude_numbers(exclude_numbers)
        available_numbers = [n for n in range(1, MAX_LOTTO_NUMBER + 1) if n not in exclude_numbers]
        if len(available_numbers) < NUM_LOTTO_NUMBERS_TO_PICK:
            return []

        # 추세 기반 가중치 설정
        weights = [
            max(0.1, 1.0 + (self.momentum_scores.get(n, 0) / 100) + (self.volatility_patterns.get(n, 0) / 50))
            for n in available_numbers
        ]

        for _ in range(300):
            try:
                if sum(weights) > 0:
                    selected = random.choices(available_numbers, weights=weights, k=NUM_LOTTO_NUMBERS_TO_PICK)
                else:
                    selected = random.sample(available_numbers, NUM_LOTTO_NUMBERS_TO_PICK)

                # 중복 제거 후 정렬
                selected = sorted(set(selected))

                if len(selected) == NUM_LOTTO_NUMBERS_TO_PICK:
                    if check_consecutive_count(selected) < 4:
                        return selected

            except (ValueError, IndexError):
                continue

        # fallback: 무조건 반환
        return sorted(random.sample(available_numbers, NUM_LOTTO_NUMBERS_TO_PICK))
