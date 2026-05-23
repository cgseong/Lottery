#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""마르코프 체인 기반 번호 전이 확률 분석기."""

import numpy as np
from typing import List, Dict, Optional, Tuple, Set
from collections import defaultdict
from utils.logging_config import get_logger

_log = get_logger(__name__)

MAX_LOTTO_NUMBER = 45
NUM_LOTTO_NUMBERS_TO_PICK = 6


class MarkovChainAnalyzer:
    """마르코프 체인을 이용한 번호 간 전이 확률 분석기.
    
    이전 회차의 번호들이 다음 회차에서 어떤 번호로 전이되는지 확률 행렬을 구축하고,
    이를 기반으로 차기 당첨 예상 번호를 예측합니다.
    """
    
    def __init__(self, historical_data: List[Dict], order: int = 1):
        """
        Args:
            historical_data: 역사적 당첨 번호 데이터
            order: 마르코프 체인 차수 (1: 1차, 2: 2차 등)
        """
        self.historical_data = historical_data
        self.order = order
        self.transition_matrix: Optional[np.ndarray] = None
        self.state_transition_probs: Dict[Tuple, Dict[int, float]] = {}
        self.number_cooccurrence: Dict[int, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
        
    def build_transition_matrix(self) -> np.ndarray:
        """번호 간 전이 확률 행렬을 구축합니다 (45x45)."""
        if not self.historical_data:
            return np.zeros((MAX_LOTTO_NUMBER, MAX_LOTTO_NUMBER))
        
        # 전이 카운트 행렬 초기화
        transition_counts = np.zeros((MAX_LOTTO_NUMBER, MAX_LOTTO_NUMBER))
        
        # 연속된 회차 간 전이 관계 카운트
        for i in range(len(self.historical_data) - 1):
            current_numbers = self._extract_numbers(self.historical_data[i])
            next_numbers = self._extract_numbers(self.historical_data[i + 1])
            
            # 현재 번호 → 다음 번호 전이 카운트
            for curr_num in current_numbers:
                for next_num in next_numbers:
                    if 1 <= curr_num <= MAX_LOTTO_NUMBER and 1 <= next_num <= MAX_LOTTO_NUMBER:
                        transition_counts[curr_num - 1, next_num - 1] += 1
        
        # 행 정규화 (확률로 변환)
        row_sums = transition_counts.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1  # 0 으로 나누기 방지
        self.transition_matrix = transition_counts / row_sums
        
        _log.info("마르코프 전이 행렬 구축 완료 (%dx%d)", MAX_LOTTO_NUMBER, MAX_LOTTO_NUMBER)
        return self.transition_matrix
    
    def build_state_transition_probs(self) -> Dict[Tuple, Dict[int, float]]:
        """특정 번호 조합 (상태) 에서 다음 번호로의 전이 확률을 구축합니다."""
        if not self.historical_data:
            return {}
        
        state_transitions: Dict[Tuple, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
        state_totals: Dict[Tuple, int] = defaultdict(int)
        
        for i in range(len(self.historical_data) - 1):
            current_numbers = tuple(sorted(self._extract_numbers(self.historical_data[i])))
            next_numbers = self._extract_numbers(self.historical_data[i + 1])
            
            # 현재 상태 (6 개 번호) 에서 다음 회차 각 번호로의 전이 카운트
            for next_num in next_numbers:
                state_transitions[current_numbers][next_num] += 1
                state_totals[current_numbers] += 1
        
        # 확률로 변환
        for state, transitions in state_transitions.items():
            total = state_totals[state]
            if total > 0:
                self.state_transition_probs[state] = {
                    num: count / total for num, count in transitions.items()
                }
        
        _log.info("상태 전이 확률 구축 완료 (%d개 상태)", len(self.state_transition_probs))
        return self.state_transition_probs
    
    def analyze_cooccurrence(self) -> Dict[int, Dict[int, float]]:
        """번호 간 공동 출현 빈도를 분석합니다."""
        if not self.historical_data:
            return {}
        
        # 공동 출현 카운트
        for data in self.historical_data:
            numbers = self._extract_numbers(data)
            for i, num1 in enumerate(numbers):
                for num2 in numbers[i+1:]:
                    self.number_cooccurrence[num1][num2] += 1
                    self.number_cooccurrence[num2][num1] += 1
        
        # 확률로 변환 (각 번호가 나올 때 함께 나올 조건부 확률)
        number_freq: Dict[int, int] = defaultdict(int)
        for data in self.historical_data:
            for num in self._extract_numbers(data):
                number_freq[num] += 1
        
        cooccurrence_probs: Dict[int, Dict[int, float]] = {}
        for num1, cooccur_dict in self.number_cooccurrence.items():
            cooccurrence_probs[num1] = {}
            for num2, count in cooccur_dict.items():
                if number_freq[num1] > 0:
                    cooccurrence_probs[num1][num2] = count / number_freq[num1]
        
        return cooccurrence_probs
    
    def predict_next_numbers(self, recent_numbers: List[int], top_k: int = 15) -> List[Tuple[int, float]]:
        """최근 번호들을 기반으로 다음 회차 예상 번호를 예측합니다.
        
        Args:
            recent_numbers: 최근 회차 당첨 번호 (6 개)
            top_k: 반환할 상위 번호 개수
            
        Returns:
            [(번호, 확률), ...] 형태의 정렬된 목록
        """
        if self.transition_matrix is None:
            self.build_transition_matrix()
        
        if not recent_numbers:
            return []
        
        # 최근 번호들로부터 전이 확률 집계
        next_probs: Dict[int, float] = defaultdict(float)
        
        for num in recent_numbers:
            if 1 <= num <= MAX_LOTTO_NUMBER:
                row_idx = num - 1
                for next_num in range(1, MAX_LOTTO_NUMBER + 1):
                    col_idx = next_num - 1
                    prob = self.transition_matrix[row_idx, col_idx]
                    # 가중치 부여 (최근 번호와 가까울수록 높은 가중치)
                    next_probs[next_num] += prob
        
        # 이미 나온 번호는 제외
        for num in recent_numbers:
            if num in next_probs:
                del next_probs[num]
        
        # 확률 기준으로 정렬
        sorted_probs = sorted(next_probs.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_probs[:top_k]
    
    def calculate_sequence_probability(self, sequence: List[List[int]]) -> float:
        """연속된 번호 시퀀스의 발생 확률을 계산합니다.
        
        Args:
            sequence: 연속된 회차 번호들 [[회차1_번호들], [회차2_번호들], ...]
            
        Returns:
            해당 시퀀스가 발생할 로그 확률
        """
        if self.transition_matrix is None:
            self.build_transition_matrix()
        
        log_prob = 0.0
        for i in range(len(sequence) - 1):
            current_numbers = sequence[i]
            next_numbers = sequence[i + 1]
            
            for next_num in next_numbers:
                max_prob = 0.0
                for curr_num in current_numbers:
                    if 1 <= curr_num <= MAX_LOTTO_NUMBER and 1 <= next_num <= MAX_LOTTO_NUMBER:
                        prob = self.transition_matrix[curr_num - 1, next_num - 1]
                        max_prob = max(max_prob, prob)
                
                if max_prob > 0:
                    log_prob += np.log(max_prob)
                else:
                    log_prob += np.log(1e-10)  # 매우 작은 값으로 페널티
        
        return log_prob
    
    def generate_recommendations(self, recent_numbers: List[int], 
                                  exclude_numbers: Optional[Set[int]] = None,
                                  num_recommendations: int = 5) -> List[Dict]:
        """마르코프 체인 기반 추천 번호를 생성합니다.
        
        Args:
            recent_numbers: 최근 회차 당첨 번호
            exclude_numbers: 제외할 번호
            num_recommendations: 생성할 추천 수
            
        Returns:
            추천 번호 목록
        """
        if not recent_numbers or len(recent_numbers) != NUM_LOTTO_NUMBERS_TO_PICK:
            return []
        
        exclude_numbers = exclude_numbers or set()
        
        # 전이 확률이 높은 번호들 추출
        top_predictions = self.predict_next_numbers(recent_numbers, top_k=20)
        
        recommendations = []
        attempts = 0
        max_attempts = num_recommendations * 50
        
        while len(recommendations) < num_recommendations and attempts < max_attempts:
            attempts += 1
            
            # 상위 확률 번호들에서 샘플링
            candidate_nums = [num for num, _ in top_predictions if num not in exclude_numbers]
            
            if len(candidate_nums) < NUM_LOTTO_NUMBERS_TO_PICK:
                # 부족하면 전체 번호에서 보충
                remaining = [n for n in range(1, MAX_LOTTO_NUMBER + 1) 
                            if n not in exclude_numbers and n not in candidate_nums]
                candidate_nums.extend(remaining[:NUM_LOTTO_NUMBERS_TO_PICK - len(candidate_nums)])
            
            if len(candidate_nums) < NUM_LOTTO_NUMBERS_TO_PICK:
                continue
            
            # 확률 가중치로 샘플링
            import random
            weights = []
            for num in candidate_nums:
                prob_dict = dict(top_predictions)
                weight = prob_dict.get(num, 0.01)
                weights.append(max(weight, 0.01))
            
            # 가중치 샘플링
            selected = self._weighted_sample(candidate_nums, weights, NUM_LOTTO_NUMBERS_TO_PICK)
            
            if not selected or len(set(selected)) != NUM_LOTTO_NUMBERS_TO_PICK:
                continue
            
            selected = sorted(selected)
            
            # 중복 검사
            if any(rec['numbers'] == selected for rec in recommendations):
                continue
            
            # 점수 계산 (평균 전이 확률)
            avg_prob = sum(dict(top_predictions).get(num, 0) for num in selected) / NUM_LOTTO_NUMBERS_TO_PICK
            
            recommendations.append({
                'numbers': selected,
                'score': avg_prob,
                'method': '마르코프 체인',
                'consecutive_count': self._count_consecutive(selected),
                'sum': sum(selected)
            })
        
        # 점수순 정렬
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:num_recommendations]
    
    def _extract_numbers(self, data: Dict) -> List[int]:
        """데이터에서 당첨 번호를 추출합니다."""
        numbers = []
        for i in range(1, 7):
            key = f'번호{i}'
            if key in data:
                try:
                    num = int(data[key])
                    if 1 <= num <= MAX_LOTTO_NUMBER:
                        numbers.append(num)
                except (ValueError, TypeError):
                    pass
        return numbers
    
    def _count_consecutive(self, numbers: List[int]) -> int:
        """연속된 번호 쌍의 개수를 셉니다."""
        if not numbers:
            return 0
        
        sorted_nums = sorted(numbers)
        count = 0
        for i in range(len(sorted_nums) - 1):
            if sorted_nums[i + 1] - sorted_nums[i] == 1:
                count += 1
        return count
    
    def _weighted_sample(self, population: List[int], weights: List[float], k: int) -> List[int]:
        """가중치 기반 비복원 추출."""
        import random
        
        if k <= 0 or not population or len(population) < k:
            return []
        
        items = list(population)
        probs = [max(0.0, float(w)) for w in weights]
        selected = []
        
        for _ in range(k):
            if not items:
                break
            total = sum(probs)
            if total <= 0:
                idx = random.randrange(len(items))
            else:
                idx = random.choices(range(len(items)), weights=probs, k=1)[0]
            selected.append(items.pop(idx))
            probs.pop(idx)
        
        return selected
