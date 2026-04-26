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


class PatternMatchingAnalyzer:
    """패턴 매칭 분석기"""
    def __init__(self, historical_data):
        self.historical_data = historical_data
        self.patterns = self._analyze_patterns()
        self.section_weights = [1.0, 1.0, 1.0, 1.0, 1.0]  # 구간별 가중치 추가
        
    def _analyze_patterns(self):
        """과거 데이터에서 패턴 분석"""
        patterns = {
            'odd_even_ratios': [],
            'sum_ranges': [],
            'consecutive_patterns': [],
            'section_distributions': []
        }
        
        for row in self.historical_data:
            numbers = [row[col] for col in LOTTO_NUMBER_COLUMNS]
            
            # 홀수/짝수 비율
            odd_count = sum(1 for n in numbers if n % 2 == 1)
            even_count = len(numbers) - odd_count
            patterns['odd_even_ratios'].append((odd_count, even_count))
            
            # 합계 범위
            total_sum = sum(numbers)
            patterns['sum_ranges'].append(total_sum)
            
            # 연속 번호 패턴
            consecutive_count = 0
            max_consecutive = 0
            for i in range(len(numbers) - 1):
                if numbers[i+1] - numbers[i] == 1:
                    consecutive_count += 1
                    max_consecutive = max(max_consecutive, consecutive_count)
                else:
                    consecutive_count = 0
            patterns['consecutive_patterns'].append(max_consecutive)
            
            # 구간별 분포
            sections = [0] * 5
            for num in numbers:
                section = (num - 1) // 10
                if section < 5:
                    sections[section] += 1
            patterns['section_distributions'].append(tuple(sections))  # 리스트를 튜플로 변환
        
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
        
        # 3. 연속 번호 패턴 매칭
        consecutive_count = 0
        max_consecutive = 0
        for i in range(len(numbers) - 1):
            if numbers[i+1] - numbers[i] == 1:
                consecutive_count += 1
                max_consecutive = max(max_consecutive, consecutive_count)
            else:
                consecutive_count = 0
        consecutive_freq = Counter(self.patterns['consecutive_patterns'])
        if max_consecutive in consecutive_freq:
            score += consecutive_freq[max_consecutive] * 0.2
        
        # 4. 구간별 분포 패턴 매칭
        sections = [0] * 5
        for num in numbers:
            section = (num - 1) // 10
            if section < 5:
                sections[section] += 1
        section_dist = tuple(sections)  # 리스트를 튜플로 변환
        section_freq = Counter(self.patterns['section_distributions'])
        if section_dist in section_freq:
            score += section_freq[section_dist] * 0.3
        
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
        """패턴 매칭 기반 추천 번호 생성"""
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
            
        print("\n[CHECK] 패턴 매칭 분석기 실행 중...")
        
        best_combination = None
        best_score = -1
        attempts = 0
        max_attempts = 15000  # 30000에서 15000으로 감소
        last_progress = 0
        
        while attempts < max_attempts:
            attempts += 1
            
            # 진행률 표시 (10% 단위)
            progress = (attempts * 100) // max_attempts
            if progress >= last_progress + 10:
                print(f"   진행률: {progress}% ({attempts}/{max_attempts} 시도)")
                last_progress = progress
            
            # 번호 생성
            numbers = self.generate_numbers(exclude_numbers)
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
                    'method': '패턴 매칭 분석'
                }
                print(f"    새로운 최고 점수 발견: {score:.1f}점")
            
            # 무한 루프 방지를 위한 조기 종료 조건
            if attempts >= max_attempts:
                break
        
        # 결과 출력
        if best_combination:
            print("\n[CHECK] 패턴 매칭 분석 결과")
            print("=" * 60)
            print(f" 최고 점수 추천: {best_combination['numbers']}")
            print(f"   [CHECK] 점수: {best_combination['score']:.1f}")
            print(f"    연속번호: {best_combination['consecutive_count']}개")
            print("=" * 60)
            
            return [best_combination]
        
        return []

    def generate_numbers(self, exclude_numbers):
        """패턴 매칭 기반 번호 생성"""
        # exclude_numbers가 딕셔너리인 경우 키만 추출
        if isinstance(exclude_numbers, dict):
            exclude_numbers = list(exclude_numbers.keys())
        elif isinstance(exclude_numbers, set):
            exclude_numbers = list(exclude_numbers)
        
        available_numbers = [n for n in range(1, MAX_LOTTO_NUMBER + 1) if n not in exclude_numbers]
        if len(available_numbers) < NUM_LOTTO_NUMBERS_TO_PICK:
            return []
            
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
            
            # 패턴 기반 가중치 적용
            weights = []
            for num in available_numbers:
                weight = 1.0
                # 홀수/짝수 패턴 가중치
                if num % 2 == 1:  # 홀수
                    weight *= 1.2
                else:  # 짝수
                    weight *= 0.8
                
                # 구간별 가중치
                section = (num - 1) // 10
                if section < 5:
                    weight *= self.section_weights[section]
                
                weights.append(weight)
            
            if sum(weights) <= 0:
                weights = [1.0] * len(available_numbers)
            
            try:
                # available_numbers가 시퀀스인지 확인하고 변환
                if isinstance(available_numbers, dict):
                    available_numbers = sorted(available_numbers)
                elif isinstance(available_numbers, set):
                    available_numbers = list(available_numbers)
                
                # available_numbers와 weights의 길이가 일치하는지 확인
                if len(available_numbers) != len(weights):
                    weights = weights[:len(available_numbers)]
                
                selected = random.choices(available_numbers, weights=weights, k=NUM_LOTTO_NUMBERS_TO_PICK)
                selected = list(set(selected))  # 중복 제거
                
                if len(selected) == NUM_LOTTO_NUMBERS_TO_PICK:
                    selected.sort()
                    
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