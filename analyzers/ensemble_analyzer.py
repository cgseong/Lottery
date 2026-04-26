#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
앙상블 분석기 모듈
"""

import random
from typing import List, Dict, Optional, Set, Tuple, Any

# 상수 import
from utils.constants import *

# 다른 분석기 import
from .statistical_analyzer import StatisticalAnalyzer
from .pattern_matching_analyzer import PatternMatchingAnalyzer
from .trend_analyzer import TrendAnalyzer


class EnsembleAnalyzer:
    """앙상블 분석기"""
    def __init__(self, historical_data):
        self.statistical_analyzer = StatisticalAnalyzer(historical_data)
        self.pattern_analyzer = PatternMatchingAnalyzer(historical_data)
        # RLAgent 대신 다른 분석기 사용
        self.trend_analyzer = TrendAnalyzer(historical_data)
        
    def check_consecutive_numbers(self, numbers):
        """연속 번호 개수 확인"""
        numbers = sorted(numbers)
        consecutive_count = 0
        max_consecutive = 0
        
        for i in range(len(numbers) - 1):
            if numbers[i+1] - numbers[i] == 1:
                consecutive_count += 1
                max_consecutive = max(max_consecutive, consecutive_count)
            else:
                consecutive_count = 0
        
        return max_consecutive
        
    def generate_recommendations(self, exclude_numbers=None, num_recommendations=5):
        """앙상블 방식으로 추천 번호 생성"""
        if exclude_numbers is None:
            exclude_numbers = set()
        else:
            # exclude_numbers가 딕셔너리인 경우 키만 추출
            if isinstance(exclude_numbers, dict):
                exclude_numbers = set(exclude_numbers.keys())
            elif isinstance(exclude_numbers, list):
                exclude_numbers = set(exclude_numbers)
            else:
                exclude_numbers = set(exclude_numbers)
            
        print("\n[CHECK] 앙상블 분석기 실행 중...")
        print("   - 통계 기반 분석")
        print("   - 패턴 매칭 분석")
        print("   - 트렌드 분석")
        
        recommendations = []
        attempts = 0
        max_attempts = 50000
        
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
        
        # 결과 출력
        print("\n 앙상블 분석 결과")
        print("=" * 60)
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}번째 추천: {rec['numbers']}")
            print(f"   [INFO] 통계 점수: {rec['stat_score']:.1f}")
            print(f"   [CHECK] 패턴 점수: {rec['pattern_score']:.1f}")
            print(f"    트렌드 점수: {rec['trend_score']:.1f}")
            print(f"    종합 점수: {rec['total_score']:.1f}")
            print(f"    연속번호: {rec['consecutive_count']}개")
        print("=" * 60)
        
        return recommendations
    
    def generate_numbers(self, exclude_numbers):
        """번호 생성"""
        # exclude_numbers가 딕셔너리인 경우 키만 추출
        if isinstance(exclude_numbers, dict):
            exclude_numbers = list(exclude_numbers.keys())
        elif isinstance(exclude_numbers, set):
            exclude_numbers = list(exclude_numbers)
        
        available_numbers = [n for n in range(1, MAX_LOTTO_NUMBER + 1) if n not in exclude_numbers]
        if len(available_numbers) < NUM_LOTTO_NUMBERS_TO_PICK:
            return None
        
        # available_numbers가 시퀀스인지 확인하고 변환
        if isinstance(available_numbers, dict):
            available_numbers = sorted(available_numbers)
        elif isinstance(available_numbers, set):
            available_numbers = list(available_numbers)
            
        return sorted(random.sample(available_numbers, NUM_LOTTO_NUMBERS_TO_PICK)) 