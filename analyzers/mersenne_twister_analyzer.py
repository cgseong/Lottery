#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
메르센 트위스터 분석기 모듈
"""

import random
from datetime import datetime
from typing import List, Dict, Optional, Set, Tuple, Any

# 상수 import
from utils.constants import *
from utils.helpers import check_consecutive_count, normalize_exclude_numbers
from utils.logging_config import get_logger

_log = get_logger(__name__)


class MersenneTwisterAnalyzer:
    """메르센 트위스터 기반 분석기"""
    def __init__(self, historical_data):
        self.historical_data = historical_data
        self.frequency = self.analyze_frequency()
        self.recent_numbers = self.analyze_recent_patterns()
        self.mt = random.Random()  # Python의 random은 메르센 트위스터 사용
        self._initialize_seed()

    @staticmethod
    def _safe_int(val) -> int:
        """CSV 문자열·숫자를 모두 int로 변환합니다."""
        try:
            return int(val)
        except (ValueError, TypeError):
            return 0

    def _initialize_seed(self):
        """시드를 현재 시간과 과거 데이터 기반으로 초기화"""
        current_time = int(datetime.now().timestamp() * 1000)
        historical_sum = sum(
            sum(self._safe_int(row.get(col, 0)) for col in LOTTO_NUMBER_COLUMNS)
            for row in self.historical_data[-10:]
        )
        seed = current_time + historical_sum
        self.mt.seed(seed)
        _log.debug("메르센 트위스터 시드 초기화: %d", seed)

    def analyze_frequency(self) -> dict:
        """번호별 출현 빈도 분석 (키를 int로 통일)"""
        frequency: dict = {}
        for row in self.historical_data:
            for col in LOTTO_NUMBER_COLUMNS:
                if col in row and row[col] not in (None, ''):
                    num = self._safe_int(row[col])
                    if num:
                        frequency[num] = frequency.get(num, 0) + 1
        return frequency

    def analyze_recent_patterns(self, recent_count=DEFAULT_RECENT_COUNT) -> set:
        """최근 회차의 패턴 분석 (int 집합으로 반환)"""
        actual_recent_count = min(recent_count, len(self.historical_data))
        recent_data = self.historical_data[-actual_recent_count:]
        recent_numbers: set = set()
        for row in recent_data:
            for col in LOTTO_NUMBER_COLUMNS:
                if col in row and row[col] not in (None, ''):
                    num = self._safe_int(row[col])
                    if num:
                        recent_numbers.add(num)
        return recent_numbers

    def calculate_score(self, numbers):
        """메르센 트위스터 기반 점수 계산"""
        score = 0

        # 1. 빈도 기반 점수 (가중치 낮춤 - 난수 특성 반영)
        freq_score = sum(self.frequency.get(num, 0) for num in numbers)
        score += freq_score * 0.3  # 기존 0.5에서 0.3으로 감소

        # 2. 최근 출현 패널티 (최근에 나온 번호는 점수 감소)
        recent_overlap = set(numbers) & self.recent_numbers
        score -= len(recent_overlap) * 15

        # 3. 연속번호 패널티
        consecutive_count = self.check_consecutive_numbers(numbers)
        score -= consecutive_count * 20

        # 4. 홀짝 균형 점수
        odd_count = sum(1 for n in numbers if n % 2 == 1)
        balance_score = 1 - abs(odd_count - (len(numbers) - odd_count)) / len(numbers)
        score += balance_score * 25

        # 5. 구간 분포 점수
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
        section_variance = sum((s - 1.2) ** 2 for s in sections)  # 6개 번호를 5구간에 분배
        score += (10 - section_variance) * 3

        return score

    def check_consecutive_numbers(self, numbers):
        """연속 번호 쌍의 총 개수를 반환합니다. (utils.helpers 위임)"""
        return check_consecutive_count(numbers)

    def generate_recommendations(self, exclude_numbers=None, num_recommendations=5):
        """메르센 트위스터 기반 추천 번호 생성"""
        exclude_numbers = normalize_exclude_numbers(exclude_numbers)
        _log.info("메르센 트위스터 분석기 실행 중 (고품질 난수 + 가중치)")

        best_combination = None
        best_score = -1
        max_attempts = 2000

        for attempt in range(1, max_attempts + 1):
            # 메르센 트위스터로 번호 생성
            numbers = self.generate_numbers_mt(exclude_numbers)
            if not numbers:
                continue

            # 점수 계산
            score = self.calculate_score(numbers)

            if score > best_score:
                best_score = score
                consecutive_count = self.check_consecutive_numbers(numbers)
                recent_overlap = set(numbers) & self.recent_numbers

                best_combination = {
                    'numbers': numbers,
                    'score': score,
                    'consecutive_count': consecutive_count,
                    'recent_overlap': recent_overlap,
                    'method': '메르센 트위스터'
                }
                _log.debug("새로운 최고 점수 (시도 %d): %.1f점 %s", attempt, score, numbers)

        if best_combination:
            _log.info(
                "메르센 트위스터 결과: %s  점수%.1f  연속%d개",
                best_combination['numbers'],
                best_combination['score'],
                best_combination['consecutive_count'],
            )
            return [best_combination]

        # 실패 시 기본 조합 생성
        _log.warning("조건에 맞는 추천번호를 찾지 못해 무작위 조합을 반환합니다.")
        available_numbers = [n for n in range(1, MAX_LOTTO_NUMBER + 1) if n not in exclude_numbers]
        if len(available_numbers) >= NUM_LOTTO_NUMBERS_TO_PICK:
            basic_numbers = sorted(self.mt.sample(available_numbers, NUM_LOTTO_NUMBERS_TO_PICK))
            basic_score = self.calculate_score(basic_numbers)
            consecutive_count = self.check_consecutive_numbers(basic_numbers)
            recent_overlap = set(basic_numbers) & self.recent_numbers

            return [{
                'numbers': basic_numbers,
                'score': basic_score,
                'consecutive_count': consecutive_count,
                'recent_overlap': recent_overlap,
                'method': '메르센 트위스터(무작위)'
            }]
        else:
            _log.warning("가능한 번호가 부족합니다. 제외번호를 줄여주세요.")
            return []

    def generate_numbers_mt(self, exclude_numbers):
        """메르센 트위스터를 사용한 번호 생성.

        단일 루프에서 최대 연속 구간 제한을 점진적으로 완화하여
        매우 빠르게 유효한 조합을 반환합니다.
        """
        exclude_numbers = normalize_exclude_numbers(exclude_numbers)
        available_numbers = [n for n in range(1, MAX_LOTTO_NUMBER + 1) if n not in exclude_numbers]
        if len(available_numbers) < NUM_LOTTO_NUMBERS_TO_PICK:
            return []

        # 점진적 완화: 처음 500번은 max_run<4, 다음 200번은 <5, 이후는 제한 없음
        for attempt in range(701):
            try:
                selected = self.mt.sample(available_numbers, NUM_LOTTO_NUMBERS_TO_PICK)
                selected.sort()
                max_run = self._get_max_consecutive(selected)
                if attempt < 500 and max_run >= 4:
                    continue
                if attempt < 700 and max_run >= 5:
                    continue
                return selected
            except (ValueError, IndexError):
                continue

        _log.warning("generate_numbers_mt: 701회 시도 후 유효한 조합을 찾지 못했습니다.")
        return []

    def _get_max_consecutive(self, numbers):
        """정렬된 번호 목록에서 가장 긴 연속 구간의 길이(쌍 수)를 반환합니다.

        check_consecutive_count()가 총 쌍 수를 반환하는 것과 달리,
        이 메서드는 단일 연속 구간의 최대 길이(쌍 수)를 반환합니다.
        예: [1,2,3,7,8] → 2  (1-2-3 구간의 쌍 수)
        """
        consecutive_count = 0
        max_consecutive = 0
        for i in range(len(numbers) - 1):
            if numbers[i + 1] - numbers[i] == 1:
                consecutive_count += 1
                max_consecutive = max(max_consecutive, consecutive_count)
            else:
                consecutive_count = 0
        return max_consecutive
