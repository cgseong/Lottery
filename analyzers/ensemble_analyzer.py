#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
앙상블 분석기 모듈
"""

import random
from typing import List, Dict, Optional, Set, Tuple, Any

# 상수 import
from utils.constants import *
from utils.helpers import check_consecutive_count, normalize_exclude_numbers
from utils.logging_config import get_logger

# 다른 분석기 import
from .statistical_analyzer import StatisticalAnalyzer
from .pattern_matching_analyzer import PatternMatchingAnalyzer
from .trend_analyzer import TrendAnalyzer
from .markov_chain_analyzer import MarkovChainAnalyzer
from .advanced_filter import AdvancedFilter

_log = get_logger(__name__)


class EnsembleAnalyzer:
    """앙상블 분석기"""
    def __init__(self, historical_data):
        self.statistical_analyzer = StatisticalAnalyzer(historical_data)
        self.pattern_analyzer = PatternMatchingAnalyzer(historical_data)
        self.trend_analyzer = TrendAnalyzer(historical_data)
        self.markov_analyzer = MarkovChainAnalyzer(historical_data)
        self.advanced_filter = AdvancedFilter(historical_data)
        self.historical_data = historical_data

    def check_consecutive_numbers(self, numbers):
        """연속 번호 쌍의 총 개수를 반환합니다. (utils.helpers 위임)"""
        return check_consecutive_count(numbers)

    def generate_recommendations(self, exclude_numbers=None, num_recommendations=5):
        """앙상블 방식으로 추천 번호 생성"""
        exclude_numbers = normalize_exclude_numbers(exclude_numbers)
        _log.info("앙상블 분석기 실행 중 (통계/패턴/트렌드)")

        recommendations = []
        attempts = 0
        max_attempts = num_recommendations * 200  # 필요한 개수에 비례한 시도 횟수

        while attempts < max_attempts:
            attempts += 1

            # 각 분석기에서 번호 생성
            numbers = self.generate_numbers(exclude_numbers)
            if not numbers:
                continue

            # 각 분석기의 점수 계산
            stat_score = self.statistical_analyzer.calculate_score(numbers)
            pattern_score = self.pattern_analyzer.calculate_score(numbers)
            trend_score = self.trend_analyzer.calculate_score(numbers)

            # 종합 점수 계산 (가중치 적용)
            total_score = (stat_score * 0.4 + pattern_score * 0.3 + trend_score * 0.3)

            # 연속 번호 개수 계산
            consecutive_count = self.check_consecutive_numbers(numbers)

            recommendations.append({
                'numbers': numbers,
                'stat_score': stat_score,
                'pattern_score': pattern_score,
                'trend_score': trend_score,
                'total_score': total_score,
                'consecutive_count': consecutive_count,
                'recent_overlap': set(),  # 기본값 설정
                'frequency_score': 0  # 기본값 설정
            })

            if len(recommendations) >= num_recommendations:
                break

        # 종합 점수 기준으로 정렬
        recommendations.sort(key=lambda x: x['total_score'], reverse=True)

        for i, rec in enumerate(recommendations, 1):
            _log.info(
                "%d번째 추천: %s  통계%.1f / 패턴%.1f / 트렌드%.1f → 종합%.1f  연속%d개",
                i, rec['numbers'],
                rec['stat_score'], rec['pattern_score'], rec['trend_score'],
                rec['total_score'], rec['consecutive_count'],
            )

        return recommendations

    def generate_numbers(self, exclude_numbers):
        """번호 생성"""
        exclude_numbers = normalize_exclude_numbers(exclude_numbers)

        available_numbers = [n for n in range(1, MAX_LOTTO_NUMBER + 1) if n not in exclude_numbers]
        if len(available_numbers) < NUM_LOTTO_NUMBERS_TO_PICK:
            return None

        # available_numbers가 시퀀스인지 확인하고 변환
        if isinstance(available_numbers, dict):
            available_numbers = sorted(available_numbers)
        elif isinstance(available_numbers, set):
            available_numbers = list(available_numbers)

        return sorted(random.sample(available_numbers, NUM_LOTTO_NUMBERS_TO_PICK))
