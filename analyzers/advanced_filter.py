#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""고급 필터링 전략 모듈."""

from typing import List, Dict, Optional, Set, Tuple
from collections import Counter
from utils.logging_config import get_logger

_log = get_logger(__name__)

MAX_LOTTO_NUMBER = 45
NUM_LOTTO_NUMBERS_TO_PICK = 6


class AdvancedFilter:
    """역사적 패턴과 통계적 기준을 기반으로 번호 조합을 필터링합니다."""
    
    def __init__(self, historical_data: Optional[List[Dict]] = None):
        """
        Args:
            historical_data: 역사적 당첨 번호 데이터 (선택적)
        """
        self.historical_data = historical_data or []
        self.sum_stats: Dict = {}
        self.odd_even_stats: Dict = {}
        self.section_stats: Dict = {}
        self.consecutive_stats: Dict = {}
        self.ac_value_threshold: float = 0.0
        
        if self.historical_data:
            self._analyze_historical_patterns()
    
    def _analyze_historical_patterns(self):
        """역사적 데이터로부터 필터링 기준을 학습합니다."""
        # 합계 통계
        sums = []
        odd_counts = []
        section_counts = {'1-15': [], '16-30': [], '31-45': []}
        consecutive_counts = []
        
        for data in self.historical_data:
            numbers = self._extract_numbers(data)
            if not numbers:
                continue
            
            # 합계
            sums.append(sum(numbers))
            
            # 홀짝
            odd_count = sum(1 for n in numbers if n % 2 == 1)
            odd_counts.append(odd_count)
            
            # 구간별
            sec1 = sum(1 for n in numbers if 1 <= n <= 15)
            sec2 = sum(1 for n in numbers if 16 <= n <= 30)
            sec3 = sum(1 for n in numbers if 31 <= n <= 45)
            section_counts['1-15'].append(sec1)
            section_counts['16-30'].append(sec2)
            section_counts['31-45'].append(sec3)
            
            # 연속번호
            sorted_nums = sorted(numbers)
            consec = sum(1 for i in range(len(sorted_nums)-1) 
                        if sorted_nums[i+1] - sorted_nums[i] == 1)
            consecutive_counts.append(consec)
        
        if sums:
            avg_sum = sum(sums) / len(sums)
            variance = sum((s - avg_sum) ** 2 for s in sums) / len(sums)
            std_sum = variance ** 0.5
            self.sum_stats = {
                'min': min(sums),
                'max': max(sums),
                'avg': avg_sum,
                'std': std_sum,
                'percentiles': self._calculate_percentiles(sums)
            }
        
        if odd_counts:
            odd_counter = Counter(odd_counts)
            total = sum(odd_counter.values())
            # 12% 이상出现的인 홀짝 비율만 허용
            self.odd_even_stats = {
                'allowed': {odd for odd, cnt in odd_counter.items() 
                           if cnt / total >= 0.12},
                'distribution': dict(odd_counter)
            }
        
        if section_counts['1-15']:
            self.section_stats = {
                'avg': {
                    '1-15': sum(section_counts['1-15']) / len(section_counts['1-15']),
                    '16-30': sum(section_counts['16-30']) / len(section_counts['16-30']),
                    '31-45': sum(section_counts['31-45']) / len(section_counts['31-45'])
                }
            }
        
        if consecutive_counts:
            consec_counter = Counter(consecutive_counts)
            total = sum(consec_counter.values())
            # 5% 이상出现的인 연속번호 개수만 허용
            self.consecutive_stats = {
                'allowed': {c for c, cnt in consec_counter.items() 
                           if cnt / total >= 0.05}
            }
        
        # AC 값 임계값 (하위 5% 제외)
        ac_values = [self.calculate_ac_value(self._extract_numbers(d)) 
                    for d in self.historical_data]
        ac_values = [ac for ac in ac_values if ac is not None]
        if ac_values:
            ac_values.sort()
            idx_5pct = int(len(ac_values) * 0.05)
            self.ac_value_threshold = ac_values[idx_5pct] if idx_5pct < len(ac_values) else ac_values[0]
    
    def _calculate_percentiles(self, values: List[float]) -> Dict[str, float]:
        """퍼센타일 계산."""
        if not values:
            return {}
        
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        
        def percentile(p):
            k = (n - 1) * p / 100
            f = int(k)
            c = f + 1 if f + 1 < n else f
            return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)
        
        return {
            'p5': percentile(5),
            'p25': percentile(25),
            'p50': percentile(50),
            'p75': percentile(75),
            'p95': percentile(95)
        }
    
    def _extract_numbers(self, data: Dict) -> List[int]:
        """데이터에서 당첨 번호 추출."""
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
    
    def calculate_ac_value(self, numbers: List[int]) -> Optional[float]:
        """AC 값 (Complexity Index) 을 계산합니다.
        
        AC 값은 번호 조합의 복잡도를 나타내며, 너무 낮은 값은 단순한 패턴을 의미합니다.
        AC = D - (N - 1), where D 는 서로 다른 차이의 개수, N 은 번호 개수
        """
        if not numbers or len(numbers) < 2:
            return None
        
        differences = set()
        for i in range(len(numbers)):
            for j in range(i + 1, len(numbers)):
                diff = abs(numbers[i] - numbers[j])
                if diff > 0:
                    differences.add(diff)
        
        ac_value = len(differences) - (len(numbers) - 1)
        return ac_value
    
    def check_same_tens_place(self, numbers: List[int]) -> int:
        """동일한 십의자리를 가진 번호의 최대 개수를 반환합니다."""
        tens_counts = Counter(n // 10 for n in numbers)
        return max(tens_counts.values()) if tens_counts else 0
    
    def check_end_sum(self, numbers: List[int]) -> int:
        """끝수의 합을 계산합니다."""
        return sum(n % 10 for n in numbers)
    
    def check_low_high_ratio(self, numbers: List[int]) -> Tuple[int, int]:
        """저번호 (1-22) 와 고번호 (23-45) 의 개수를 반환합니다."""
        low = sum(1 for n in numbers if 1 <= n <= 22)
        high = sum(1 for n in numbers if 23 <= n <= 45)
        return low, high
    
    def passes_all_filters(self, numbers: List[int], strict_mode: bool = False) -> bool:
        """모든 필터를 통과하는지 확인합니다.
        
        Args:
            numbers: 검사할 번호 조합
            strict_mode: True 이면 더 엄격한 기준 적용
            
        Returns:
            모든 필터를 통과하면 True
        """
        if not numbers or len(numbers) != NUM_LOTTO_NUMBERS_TO_PICK:
            return False
        
        # 1. 합계 필터
        if self.sum_stats:
            total = sum(numbers)
            if strict_mode:
                # 엄격 모드: 평균 ± 1 시그마
                if abs(total - self.sum_stats['avg']) > self.sum_stats['std']:
                    return False
            else:
                # 일반 모드: 5~95 퍼센타일
                if 'percentiles' in self.sum_stats:
                    if not (self.sum_stats['percentiles']['p5'] <= total <= 
                            self.sum_stats['percentiles']['p95']):
                        return False
        
        # 2. 홀짝 비율 필터
        if self.odd_even_stats:
            odd_count = sum(1 for n in numbers if n % 2 == 1)
            if odd_count not in self.odd_even_stats.get('allowed', {2, 3, 4}):
                return False
        
        # 3. 구간 분포 필터
        if self.section_stats:
            sec1 = sum(1 for n in numbers if 1 <= n <= 15)
            sec2 = sum(1 for n in numbers if 16 <= n <= 30)
            sec3 = sum(1 for n in numbers if 31 <= n <= 45)
            
            avg = self.section_stats['avg']
            # 각 구간이 평균에서 ±1.5 벗어나지 않아야 함
            if strict_mode:
                tolerance = 1.0
            else:
                tolerance = 1.5
            
            if abs(sec1 - avg['1-15']) > tolerance:
                return False
            if abs(sec2 - avg['16-30']) > tolerance:
                return False
            if abs(sec3 - avg['31-45']) > tolerance:
                return False
        
        # 4. 연속번호 필터
        if self.consecutive_stats:
            sorted_nums = sorted(numbers)
            consec_count = sum(1 for i in range(len(sorted_nums)-1) 
                              if sorted_nums[i+1] - sorted_nums[i] == 1)
            if consec_count not in self.consecutive_stats.get('allowed', {0, 1, 2}):
                return False
        
        # 5. AC 값 필터
        ac_value = self.calculate_ac_value(numbers)
        if ac_value is not None and ac_value < self.ac_value_threshold:
            return False
        
        # 6. 동일 십의자리 필터 (최대 3 개까지 허용)
        same_tens = self.check_same_tens_place(numbers)
        if same_tens > 3:
            return False
        
        # 7. 끝수 합 필터 (0-45 범위 권장)
        end_sum = self.check_end_sum(numbers)
        if end_sum < 0 or end_sum > 45:
            return False
        
        # 8. 저고비율 필터
        low, high = self.check_low_high_ratio(numbers)
        # 극단적인 편중 방지 (0:6 또는 6:0)
        if low == 0 or high == 0:
            return False
        
        return True
    
    def filter_candidates(self, candidates: List[List[int]], 
                          strict_mode: bool = False) -> List[List[int]]:
        """후보 목록을 필터링합니다.
        
        Args:
            candidates: 후보 번호 조합 목록
            strict_mode: 엄격한 필터 적용 여부
            
        Returns:
            필터를 통과한 후보 목록
        """
        filtered = []
        for nums in candidates:
            if self.passes_all_filters(nums, strict_mode):
                filtered.append(nums)
        
        _log.info("필터링: %d개 → %d개 (%.1f%% 통과)", 
                 len(candidates), len(filtered),
                 (len(filtered) / max(1, len(candidates)) * 100))
        
        return filtered
    
    def get_filter_summary(self) -> Dict:
        """현재 필터 설정 요약을 반환합니다."""
        return {
            'sum_range': (self.sum_stats.get('avg', 0) - self.sum_stats.get('std', 0),
                         self.sum_stats.get('avg', 0) + self.sum_stats.get('std', 0)) 
                        if self.sum_stats else None,
            'allowed_odd_even': list(self.odd_even_stats.get('allowed', [])) 
                               if self.odd_even_stats else [2, 3, 4],
            'section_avg': self.section_stats.get('avg', {}) 
                          if self.section_stats else {},
            'allowed_consecutive': list(self.consecutive_stats.get('allowed', [])) 
                                  if self.consecutive_stats else [0, 1, 2],
            'min_ac_value': self.ac_value_threshold
        }
