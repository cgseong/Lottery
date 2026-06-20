#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
패턴 매칭 분석기 모듈
"""

import random
from collections import Counter
from typing import List, Dict, Optional, Set, Tuple, Any

# 상수 import
from utils.constants import *
from utils.helpers import check_consecutive_count, normalize_exclude_numbers, get_last_draw_numbers, exceeds_prev_draw_overlap
from utils.logging_config import get_logger

_log = get_logger(__name__)


class PatternMatchingAnalyzer:
    """패턴 매칭 분석기"""
    def __init__(self, historical_data):
        self.historical_data = historical_data
        self.patterns = self._analyze_patterns()
        self.section_weights = [1.0, 1.0, 1.0, 1.0, 1.0]  # 구간별 가중치

    def _analyze_patterns(self):
        """과거 데이터에서 패턴 분석"""
        patterns = {
            'odd_even_ratios': [],
            'sum_ranges': [],
            'consecutive_patterns': [],
            'section_distributions': []
        }

        for row in self.historical_data:
            # CSV 값은 문자열일 수 있으므로 int 변환 후 사용
            numbers = []
            for col in LOTTO_NUMBER_COLUMNS:
                if col in row and row[col] not in (None, ''):
                    try:
                        numbers.append(int(row[col]))
                    except (ValueError, TypeError):
                        pass
            if len(numbers) != NUM_LOTTO_NUMBERS_TO_PICK:
                continue
            numbers.sort()

            # 홀수/짝수 비율
            odd_count = sum(1 for n in numbers if n % 2 == 1)
            even_count = len(numbers) - odd_count
            patterns['odd_even_ratios'].append((odd_count, even_count))

            # 합계 범위
            patterns['sum_ranges'].append(sum(numbers))

            # 연속 번호 패턴 (check_consecutive_count 위임)
            patterns['consecutive_patterns'].append(check_consecutive_count(numbers))

            # 구간별 분포
            sections = [0] * 5
            for num in numbers:
                section = (num - 1) // 10
                if section < 5:
                    sections[section] += 1
            patterns['section_distributions'].append(tuple(sections))

        return patterns

    def calculate_score(self, numbers):
        """패턴 매칭 점수 계산"""
        score = 0

        # 1. 홀수/짝수 패턴 매칭
        odd_count = sum(1 for n in numbers if n % 2 == 1)
        even_count = len(numbers) - odd_count
        odd_even_pattern = (odd_count, even_count)
        odd_even_freq = Counter(self.patterns['odd_even_ratios'])
        if odd_even_pattern in odd_even_freq:
            score += odd_even_freq[odd_even_pattern] * 0.3

        # 2. 합계 범위 패턴 매칭
        total_sum = sum(numbers)
        sum_range_freq = Counter(self.patterns['sum_ranges'])
        if total_sum in sum_range_freq:
            score += sum_range_freq[total_sum] * 0.2

        # 3. 연속 번호 패턴 매칭 (check_consecutive_count — _analyze_patterns와 동일 기준)
        total_consecutive = check_consecutive_count(numbers)
        consecutive_freq = Counter(self.patterns['consecutive_patterns'])
        if total_consecutive in consecutive_freq:
            score += consecutive_freq[total_consecutive] * 0.2

        # 4. 구간별 분포 패턴 매칭
        sections = [0] * 5
        for num in numbers:
            section = (num - 1) // 10
            if section < 5:
                sections[section] += 1
        section_dist = tuple(sections)
        section_freq = Counter(self.patterns['section_distributions'])
        if section_dist in section_freq:
            score += section_freq[section_dist] * 0.3

        return score

    def check_consecutive_numbers(self, numbers):
        """연속 번호 쌍의 총 개수를 반환합니다. (utils.helpers 위임)"""
        return check_consecutive_count(numbers)

    def generate_recommendations(self, exclude_numbers=None, num_recommendations=5):
        """패턴 매칭 기반 추천 번호 생성"""
        exclude_numbers = normalize_exclude_numbers(exclude_numbers)
        _log.info("패턴 매칭 분석기 실행 중")
        prev_draw = get_last_draw_numbers(self.historical_data)

        best_combination = None
        best_score = -1
        max_attempts = 2000

        for attempt in range(1, max_attempts + 1):
            numbers = self.generate_numbers(exclude_numbers)
            if not numbers:
                continue

            # 직전 회차 당첨번호 2개 이상 포함 시 제외
            if exceeds_prev_draw_overlap(numbers, prev_draw):
                continue

            score = self.calculate_score(numbers)

            if score > best_score:
                best_score = score
                consecutive_count = self.check_consecutive_numbers(numbers)

                best_combination = {
                    'numbers': numbers,
                    'score': score,
                    'consecutive_count': consecutive_count,
                    'recent_overlap': set(),
                    'method': '패턴 매칭 분석'
                }
                _log.debug("새로운 최고 점수 (시도 %d): %.1f점 %s", attempt, score, numbers)

        if best_combination:
            _log.info(
                "패턴 매칭 결과: %s  점수%.1f  연속%d개",
                best_combination['numbers'],
                best_combination['score'],
                best_combination['consecutive_count'],
            )
            return [best_combination]

        return []

    def generate_numbers(self, exclude_numbers):
        """패턴 매칭 기반 번호 생성"""
        exclude_numbers = normalize_exclude_numbers(exclude_numbers)
        available_numbers = [n for n in range(1, MAX_LOTTO_NUMBER + 1) if n not in exclude_numbers]
        if len(available_numbers) < NUM_LOTTO_NUMBERS_TO_PICK:
            return []

        # 패턴 기반 가중치 사전 계산 (루프 밖)
        weights = []
        for num in available_numbers:
            weight = 1.2 if num % 2 == 1 else 0.8  # 홀수 선호
            section = (num - 1) // 10
            if section < 5:
                weight *= self.section_weights[section]
            weights.append(weight)

        if sum(weights) <= 0:
            weights = [1.0] * len(available_numbers)

        for _ in range(300):
            try:
                selected = random.choices(available_numbers, weights=weights, k=NUM_LOTTO_NUMBERS_TO_PICK)
                selected = sorted(set(selected))

                if len(selected) == NUM_LOTTO_NUMBERS_TO_PICK:
                    if check_consecutive_count(selected) < 4:
                        return selected

            except (ValueError, IndexError):
                continue

        # fallback: 무조건 반환
        return sorted(random.sample(available_numbers, NUM_LOTTO_NUMBERS_TO_PICK))
