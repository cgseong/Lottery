#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
트렌드 분석기 모듈
"""

import random
from typing import List, Dict, Optional, Set, Tuple, Any

# 상수 import
from utils.constants import *


class TrendAnalyzer:
    """최근 추세 분석기"""
    def __init__(self, historical_data):
        self.historical_data = historical_data
        self.frequency = self.analyze_frequency()
        self.recent_trends = self.analyze_recent_trends()
        self.momentum_scores = self.calculate_momentum_scores()
        self.volatility_patterns = self.analyze_volatility_patterns()
        
    def analyze_frequency(self):
        """번호별 출현 빈도 분석"""
        frequency = {}
        for row in self.historical_data:
            for col in LOTTO_NUMBER_COLUMNS:
                num = row[col]
                frequency[num] = frequency.get(num, 0) + 1
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
                numbers = [row[col] for col in LOTTO_NUMBER_COLUMNS]
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
        """최근 추세 기반 추천 번호 생성"""
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
            
        print("\n 최근 추세 분석기 실행 중...")
        print("   - 최근 20회차 패턴 분석")
        print("   - 모멘텀 및 변동성 계산")
        print("   - 추세 기반 점수화")
        
        best_combination = None
        best_score = -1
        attempts = 0
        max_attempts = 15000
        last_progress = 0
        
        while attempts < max_attempts:
            attempts += 1
            
            # 진행률 표시 (10% 단위)
            progress = (attempts * 100) // max_attempts
            if progress >= last_progress + 10:
                print(f"   진행률: {progress}% ({attempts}/{max_attempts} 시도)")
                last_progress = progress
            
            # 추세 기반 번호 생성
            numbers = self.generate_numbers_trend(exclude_numbers)
            if not numbers:
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
                print(f"    새로운 최고 점수 발견: {score:.1f}점")
            
            # 무한 루프 방지를 위한 조기 종료 조건
            if attempts >= max_attempts:
                break
        
        # 결과 출력
        if best_combination:
            print("\n 최근 추세 분석 결과")
            print("=" * 60)
            print(f" 최고 점수 추천: {best_combination['numbers']}")
            print(f"    점수: {best_combination['score']:.1f}")
            print(f"    연속번호: {best_combination['consecutive_count']}개")
            
            # 추세 정보 출력
            print("\n[INFO] 추천 번호별 추세 정보:")
            for num in best_combination['numbers']:
                trend = self.recent_trends[num]
                momentum = self.momentum_scores[num]
                volatility = self.volatility_patterns[num]
                print(f"   {num:2d}번: 출현{trend['count']:2d}회, 모멘텀{momentum:4.0f}점, 변동성{volatility:2d}점")
            
            print("=" * 60)
            
            return [best_combination]
        
        return []
    
    def generate_numbers_trend(self, exclude_numbers):
        """최근 추세 기반 번호 생성"""
        # exclude_numbers가 딕셔너리인 경우 키만 추출
        if isinstance(exclude_numbers, dict):
            exclude_numbers = list(exclude_numbers.keys())
        elif isinstance(exclude_numbers, set):
            exclude_numbers = list(exclude_numbers)
        
        available_numbers = [n for n in range(1, MAX_LOTTO_NUMBER + 1) if n not in exclude_numbers]
        if len(available_numbers) < NUM_LOTTO_NUMBERS_TO_PICK:
            return []
        
        # 추세 기반 가중치 설정
        weights = []
        for num in available_numbers:
            # 모멘텀 점수를 가중치로 사용
            momentum = self.momentum_scores.get(num, 0)
            volatility = self.volatility_patterns.get(num, 0)
            
            # 기본 가중치 + 모멘텀 + 변동성
            weight = 1.0 + (momentum / 100) + (volatility / 50)
            weights.append(max(0.1, weight))  # 최소 0.1 보장
        
        # 최대 시도 횟수 제한
        max_attempts = 5000
        attempts = 0
        last_progress = 0
        
        while attempts < max_attempts:
            attempts += 1
            
            # 진행률 표시 (20% 단위)
            progress = (attempts * 100) // max_attempts
            if progress >= last_progress + 20:
                print(f"      진행률: {progress}% ({attempts}/{max_attempts} 시도)")
                last_progress = progress
            
            try:
                # available_numbers가 시퀀스인지 확인하고 변환
                if isinstance(available_numbers, dict):
                    available_numbers = sorted(available_numbers)
                elif isinstance(available_numbers, set):
                    available_numbers = list(available_numbers)
                
                # available_numbers와 weights의 길이가 일치하는지 확인
                if len(available_numbers) != len(weights):
                    weights = weights[:len(available_numbers)]
                
                # 추세 기반 가중치로 선택
                if sum(weights) > 0:
                    selected = random.choices(available_numbers, weights=weights, k=NUM_LOTTO_NUMBERS_TO_PICK)
                else:
                    selected = random.sample(available_numbers, NUM_LOTTO_NUMBERS_TO_PICK)
                
                # 중복 제거
                selected = list(set(selected))
                selected.sort()
                
                # 충분한 번호가 있는지 확인
                if len(selected) == NUM_LOTTO_NUMBERS_TO_PICK:
                    # 연속 번호 검사
                    consecutive_count = 0
                    max_consecutive = 0
                    for i in range(len(selected) - 1):
                        if selected[i+1] - selected[i] == 1:
                            consecutive_count += 1
                            max_consecutive = max(max_consecutive, consecutive_count)
                        else:
                            consecutive_count = 0
                    
                    # 연속 번호가 4개 미만이면 유효한 조합
                    if max_consecutive < 4:
                        return selected
                        
            except (ValueError, IndexError):
                continue
            
            # 무한 루프 방지를 위한 조기 종료
            if attempts >= max_attempts:
                break
        
        # 최대 시도 횟수에 도달했거나 유효한 조합을 찾지 못한 경우
        if len(available_numbers) >= NUM_LOTTO_NUMBERS_TO_PICK:
            # available_numbers가 시퀀스인지 확인하고 변환
            if isinstance(available_numbers, dict):
                available_numbers = sorted(available_numbers)
            elif isinstance(available_numbers, set):
                available_numbers = list(available_numbers)
            return sorted(random.sample(available_numbers, NUM_LOTTO_NUMBERS_TO_PICK))
        
        return [] 