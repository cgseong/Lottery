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


class MersenneTwisterAnalyzer:
    """메르센 트위스터 기반 분석기"""
    def __init__(self, historical_data):
        self.historical_data = historical_data
        self.frequency = self.analyze_frequency()
        self.recent_numbers = self.analyze_recent_patterns()
        self.mt = random.Random()  # Python의 random은 메르센 트위스터 사용
        self._initialize_seed()
        
    def _initialize_seed(self):
        """시드를 현재 시간과 과거 데이터 기반으로 초기화"""
        current_time = int(datetime.now().timestamp() * 1000)
        historical_sum = sum(sum(row[col] for col in LOTTO_NUMBER_COLUMNS) for row in self.historical_data[-10:])
        seed = current_time + historical_sum
        self.mt.seed(seed)
        print(f"    메르센 트위스터 시드 초기화: {seed}")
        
    def analyze_frequency(self):
        """번호별 출현 빈도 분석"""
        frequency = {}
        for row in self.historical_data:
            for col in LOTTO_NUMBER_COLUMNS:
                num = row[col]
                frequency[num] = frequency.get(num, 0) + 1
        return frequency
    
    def analyze_recent_patterns(self, recent_count=DEFAULT_RECENT_COUNT):
        """최근 회차의 패턴 분석"""
        recent_numbers_list = []
        actual_recent_count = min(recent_count, len(self.historical_data))
        recent_data = self.historical_data[-actual_recent_count:]
        
        for row in recent_data:
            for col in LOTTO_NUMBER_COLUMNS:
                recent_numbers_list.append(row[col])
        
        return set(recent_numbers_list)
    
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
        even_count = len(numbers) - odd_count
        balance_score = 1 - abs(odd_count - even_count) / len(numbers)
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
        """메르센 트위스터 기반 추천 번호 생성"""
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
            
        print("\n 메르센 트위스터 분석기 실행 중...")
        print("   - 고품질 난수 생성")
        print("   - 과거 데이터 기반 가중치 적용")
        print("   - 패턴 분석 및 점수화")
        
        best_combination = None
        best_score = -1
        attempts = 0
        max_attempts = 12000
        last_progress = 0
        
        while attempts < max_attempts:
            attempts += 1
            
            # 진행률 표시 (10% 단위)
            progress = (attempts * 100) // max_attempts
            if progress >= last_progress + 10:
                print(f"   진행률: {progress}% ({attempts}/{max_attempts} 시도)")
                last_progress = progress
            
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
                print(f"    새로운 최고 점수 발견: {score:.1f}점")
            
            # 무한 루프 방지를 위한 조기 종료 조건
            if attempts >= max_attempts:
                break
        
        # 결과 출력
        if best_combination:
            print("\n 메르센 트위스터 분석 결과")
            print("=" * 60)
            print(f" 최고 점수 추천: {best_combination['numbers']}")
            print(f"    점수: {best_combination['score']:.1f}")
            print(f"    연속번호: {best_combination['consecutive_count']}개")
            if best_combination['recent_overlap']:
                print(f"    최근번호: {sorted(best_combination['recent_overlap'])}")
            print("=" * 60)
            
            return [best_combination]
        
        # 최종적으로도 실패한 경우, 기본 조합 생성
        print("\n[WARN] 조건에 맞는 추천번호를 찾지 못해 무작위 조합을 반환합니다.")
        available_numbers = [n for n in range(1, MAX_LOTTO_NUMBER + 1) if n not in exclude_numbers]
        if len(available_numbers) >= NUM_LOTTO_NUMBERS_TO_PICK:
            basic_numbers = sorted(self.mt.sample(available_numbers, NUM_LOTTO_NUMBERS_TO_PICK))
            basic_score = self.calculate_score(basic_numbers)
            consecutive_count = self.check_consecutive_numbers(basic_numbers)
            recent_overlap = set(basic_numbers) & self.recent_numbers
            
            basic_combination = {
                'numbers': basic_numbers,
                'score': basic_score,
                'consecutive_count': consecutive_count,
                'recent_overlap': recent_overlap,
                'method': '메르센 트위스터(무작위)'
            }
            
            print("\n 메르센 트위스터 기본 분석 결과")
            print("=" * 60)
            print(f" 무작위 추천: {basic_combination['numbers']}")
            print(f"    점수: {basic_combination['score']:.1f}")
            print(f"    연속번호: {basic_combination['consecutive_count']}개")
            if basic_combination['recent_overlap']:
                print(f"    최근번호: {sorted(basic_combination['recent_overlap'])}")
            print("=" * 60)
            
            return [basic_combination]
        else:
            print("[WARN] 가능한 번호가 부족합니다. 제외번호를 줄여주세요.")
            return []
    
    def generate_numbers_mt(self, exclude_numbers):
        """메르센 트위스터를 사용한 번호 생성 (완화된 조건)"""
        # exclude_numbers가 딕셔너리인 경우 키만 추출
        if isinstance(exclude_numbers, dict):
            exclude_numbers = list(exclude_numbers.keys())
        elif isinstance(exclude_numbers, set):
            exclude_numbers = list(exclude_numbers)
        
        available_numbers = [n for n in range(1, MAX_LOTTO_NUMBER + 1) if n not in exclude_numbers]
        if len(available_numbers) < NUM_LOTTO_NUMBERS_TO_PICK:
            return []

        max_attempts = 15000  # 시도 횟수 더 증가
        attempts = 0
        last_progress = 0

        # 1차: 연속번호 4개 미만 (매우 엄격한 조건)
        while attempts < max_attempts:
            attempts += 1
            
            # 진행률 표시 (20% 단위)
            progress = (attempts * 100) // max_attempts
            if progress >= last_progress + 20:
                print(f"      진행률: {progress}% ({attempts}/{max_attempts} 시도)")
                last_progress = progress
            
            try:
                selected = self.mt.sample(available_numbers, NUM_LOTTO_NUMBERS_TO_PICK)
                selected.sort()
                max_consecutive = self._get_max_consecutive(selected)
                if max_consecutive < 4:
                    return selected
            except (ValueError, IndexError):
                continue

        # 2차: 연속번호 5개 미만 (완화된 조건)
        print("      [WARN] 엄격한 조건으로 조합을 찾지 못해 조건을 완화합니다.")
        for _ in range(3000):
            try:
                selected = self.mt.sample(available_numbers, NUM_LOTTO_NUMBERS_TO_PICK)
                selected.sort()
                max_consecutive = self._get_max_consecutive(selected)
                if max_consecutive < 5:
                    return selected
            except (ValueError, IndexError):
                continue

        # 3차: 연속번호 6개 미만 (더 완화된 조건)
        print("      [WARN] 조건을 더 완화합니다.")
        for _ in range(2000):
            try:
                selected = self.mt.sample(available_numbers, NUM_LOTTO_NUMBERS_TO_PICK)
                selected.sort()
                max_consecutive = self._get_max_consecutive(selected)
                if max_consecutive < 6:
                    return selected
            except (ValueError, IndexError):
                continue

        # 4차: 연속번호가 6개여도 허용 (모든 번호가 연속인 경우만 제외)
        print("      [WARN] 최대한 완화된 조건으로 시도합니다.")
        for _ in range(1000):
            try:
                selected = self.mt.sample(available_numbers, NUM_LOTTO_NUMBERS_TO_PICK)
                selected.sort()
                # 모든 번호가 연속인 경우만 제외 (1,2,3,4,5,6 같은 경우)
                is_all_consecutive = True
                for i in range(len(selected) - 1):
                    if selected[i+1] - selected[i] != 1:
                        is_all_consecutive = False
                        break
                if not is_all_consecutive:
                    return selected
            except (ValueError, IndexError):
                continue

        # 모든 조건을 만족하지 못한 경우 빈 리스트 반환
        print("      [WARN] 모든 조건을 만족하는 조합을 찾지 못했습니다.")
        return []

    def _get_max_consecutive(self, numbers):
        consecutive_count = 0
        max_consecutive = 0
        for i in range(len(numbers) - 1):
            if numbers[i+1] - numbers[i] == 1:
                consecutive_count += 1
                max_consecutive = max(max_consecutive, consecutive_count)
            else:
                consecutive_count = 0
        return max_consecutive 