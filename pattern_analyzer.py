from collections import Counter, defaultdict
from typing import List, Dict, Set, Tuple
import numpy as np
from itertools import combinations
import matplotlib.pyplot as plt
import matplotlib
import platform
import random
if platform.system() == 'Windows':
    matplotlib.rc('font', family='Malgun Gothic')
else:
    matplotlib.rc('font', family='AppleGothic')
matplotlib.rcParams['axes.unicode_minus'] = False

class PatternAnalyzer:
    def __init__(self, historical_data: List[Dict]):
        self.historical_data = historical_data
        self.number_frequencies = self._analyze_number_frequencies()
        self.pair_frequencies = self._analyze_pair_frequencies()
        self.sum_statistics = self._analyze_sum_statistics()
        self.odd_even_patterns = self._analyze_odd_even_patterns()
        self.high_low_patterns = self._analyze_high_low_patterns()
        self.consecutive_patterns = self._analyze_consecutive_patterns()
        
    def _analyze_number_frequencies(self) -> Dict[int, int]:
        """각 번호의 출현 빈도를 분석합니다."""
        all_numbers = []
        for row in self.historical_data:
            numbers = [row[f'번호{i}'] for i in range(1, 7)]
            all_numbers.extend(numbers)
        return Counter(all_numbers)
    
    def _analyze_pair_frequencies(self) -> Dict[Tuple[int, int], int]:
        """두 번호가 함께 나온 빈도를 분석합니다."""
        pair_counts = Counter()
        for row in self.historical_data:
            numbers = [row[f'번호{i}'] for i in range(1, 7)]
            for pair in combinations(sorted(numbers), 2):
                pair_counts[pair] += 1
        return dict(pair_counts)
    
    def _analyze_sum_statistics(self) -> Dict[str, float]:
        """당첨번호 합계의 통계를 분석합니다."""
        sums = []
        for row in self.historical_data:
            numbers = [row[f'번호{i}'] for i in range(1, 7)]
            sums.append(sum(numbers))
        
        return {
            'mean': np.mean(sums),
            'std': np.std(sums),
            'min': min(sums),
            'max': max(sums)
        }
    
    def _analyze_odd_even_patterns(self) -> Dict[str, int]:
        """홀수/짝수 패턴의 빈도를 분석합니다."""
        patterns = Counter()
        for row in self.historical_data:
            numbers = [row[f'번호{i}'] for i in range(1, 7)]
            odd_count = sum(1 for n in numbers if n % 2 == 1)
            patterns[f'{odd_count}:{6-odd_count}'] += 1
        return dict(patterns)
    
    def _analyze_high_low_patterns(self) -> Dict[str, int]:
        """고번호/저번호 패턴의 빈도를 분석합니다."""
        patterns = Counter()
        for row in self.historical_data:
            numbers = [row[f'번호{i}'] for i in range(1, 7)]
            high_count = sum(1 for n in numbers if n > 22)  # 22를 기준으로 고/저 구분
            patterns[f'{high_count}:{6-high_count}'] += 1
        return dict(patterns)
    
    def _analyze_consecutive_patterns(self) -> Dict[int, int]:
        """연속된 번호의 개수 패턴을 분석합니다."""
        patterns = Counter()
        for row in self.historical_data:
            numbers = sorted([row[f'번호{i}'] for i in range(1, 7)])
            consecutive_count = 0
            for i in range(len(numbers)-1):
                if numbers[i+1] - numbers[i] == 1:
                    consecutive_count += 1
            patterns[consecutive_count] += 1
        return dict(patterns)
    
    def get_most_common_numbers(self, n: int = 10) -> List[Tuple[int, int]]:
        """가장 자주 나온 번호 n개를 반환합니다."""
        return self.number_frequencies.most_common(n)
    
    def get_least_common_numbers(self, n: int = 10) -> List[Tuple[int, int]]:
        """가장 적게 나온 번호 n개를 반환합니다."""
        return sorted(self.number_frequencies.items(), key=lambda x: x[1])[:n]
    
    def get_most_common_pairs(self, n: int = 10) -> List[Tuple[Tuple[int, int], int]]:
        """가장 자주 함께 나온 번호 쌍 n개를 반환합니다."""
        return sorted(self.pair_frequencies.items(), key=lambda x: x[1], reverse=True)[:n]
    
    def get_sum_statistics(self) -> Dict[str, float]:
        """당첨번호 합계의 통계를 반환합니다."""
        return self.sum_statistics
    
    def get_odd_even_patterns(self) -> Dict[str, int]:
        """홀수/짝수 패턴의 빈도를 반환합니다."""
        return self.odd_even_patterns
    
    def get_high_low_patterns(self) -> Dict[str, int]:
        """고번호/저번호 패턴의 빈도를 반환합니다."""
        return self.high_low_patterns
    
    def get_consecutive_patterns(self) -> Dict[int, int]:
        """연속된 번호의 개수 패턴을 반환합니다."""
        return self.consecutive_patterns
    
    def calculate_pattern_score(self, numbers: List[int]) -> float:
        """주어진 번호 조합의 패턴 점수를 계산합니다."""
        if len(numbers) != 6:
            return 0.0
            
        score = 0.0
        numbers = sorted(numbers)
        
        # 1. 번호 빈도 점수
        freq_score = sum(self.number_frequencies.get(n, 0) for n in numbers)
        score += freq_score * 0.3
        
        # 2. 번호 쌍 점수
        pair_score = sum(self.pair_frequencies.get(pair, 0) 
                        for pair in combinations(numbers, 2))
        score += pair_score * 0.2
        
        # 3. 합계 점수
        sum_value = sum(numbers)
        mean = self.sum_statistics['mean']
        std = self.sum_statistics['std']
        if std > 0:
            sum_score = 1 - abs(sum_value - mean) / (3 * std)  # 3 표준편차 내에 있으면 높은 점수
            score += sum_score * 0.15
        
        # 4. 홀짝 패턴 점수
        odd_count = sum(1 for n in numbers if n % 2 == 1)
        odd_even_pattern = f'{odd_count}:{6-odd_count}'
        odd_even_score = self.odd_even_patterns.get(odd_even_pattern, 0)
        score += odd_even_score * 0.1
        
        # 5. 고저 패턴 점수
        high_count = sum(1 for n in numbers if n > 22)
        high_low_pattern = f'{high_count}:{6-high_count}'
        high_low_score = self.high_low_patterns.get(high_low_pattern, 0)
        score += high_low_score * 0.1
        
        # 6. 연속번호 패턴 점수
        consecutive_count = sum(1 for i in range(len(numbers)-1) 
                              if numbers[i+1] - numbers[i] == 1)
        consecutive_score = self.consecutive_patterns.get(consecutive_count, 0)
        score += consecutive_score * 0.15
        
        return score
    
    def print_pattern_analysis(self):
        """패턴 분석 결과를 출력합니다."""
        print("\n[INFO] 패턴 분석 결과")
        print("=" * 60)
        
        # 1. 번호 빈도
        print("\n1 번호별 출현 빈도")
        print("-" * 40)
        print("가장 많이 나온 번호 TOP 10:")
        for num, count in self.get_most_common_numbers(10):
            print(f"   {num:2d}번: {count:3d}회")
        
        print("\n가장 적게 나온 번호 TOP 10:")
        for num, count in self.get_least_common_numbers(10):
            print(f"   {num:2d}번: {count:3d}회")
        
        # 2. 번호 쌍
        print("\n2 자주 함께 나온 번호 쌍 TOP 10:")
        print("-" * 40)
        for (num1, num2), count in self.get_most_common_pairs(10):
            print(f"   {num1:2d}-{num2:2d}: {count:3d}회")
        
        # 3. 합계 통계
        print("\n3 당첨번호 합계 통계:")
        print("-" * 40)
        stats = self.get_sum_statistics()
        print(f"   평균: {stats['mean']:.1f}")
        print(f"   표준편차: {stats['std']:.1f}")
        print(f"   최소: {stats['min']}")
        print(f"   최대: {stats['max']}")
        
        # 4. 홀짝 패턴
        print("\n4 홀수:짝수 패턴 빈도:")
        print("-" * 40)
        for pattern, count in sorted(self.get_odd_even_patterns().items()):
            print(f"   {pattern}: {count:3d}회")
        
        # 5. 고저 패턴
        print("\n5 고번호:저번호 패턴 빈도:")
        print("-" * 40)
        for pattern, count in sorted(self.get_high_low_patterns().items()):
            print(f"   {pattern}: {count:3d}회")
        
        # 6. 연속번호 패턴
        print("\n6 연속번호 개수 패턴:")
        print("-" * 40)
        for count, freq in sorted(self.get_consecutive_patterns().items()):
            print(f"   {count}개 연속: {freq:3d}회")

def show_lotto_patterns_histories(winning_numbers_list):
    """
    여러 회차의 당첨번호 패턴을 1~45 격자 히트맵으로 시각화합니다.
    winning_numbers_list: List[List[int]]
    """
    freq = np.zeros(45, dtype=int)
    for nums in winning_numbers_list:
        for n in nums:
            if 1 <= n <= 45:
                freq[n-1] += 1

    fig, ax = plt.subplots(figsize=(7, 7))
    vmax = freq.max() if freq.max() > 0 else 1
    for i in range(45):
        num = i + 1
        row, col = divmod(i, 7)
        color = plt.cm.Reds(freq[i] / vmax)  # 출현 빈도에 따라 색상 진하게
        ax.add_patch(plt.Rectangle((col, -row), 1, 1, color=color, ec='red', lw=1.5))
        ax.text(col+0.5, -row+0.5, str(num), ha='center', va='center', fontsize=12, color='black')
        if freq[i] > 0:
            ax.text(col+0.5, -row+0.2, f"{freq[i]}", ha='center', va='center', fontsize=9, color='blue')
    ax.set_xlim(0, 7)
    ax.set_ylim(-7, 0)
    ax.axis('off')
    plt.title("여러 회차의 로또 당첨번호 패턴(출현 빈도)")
    plt.tight_layout()
    plt.show()

def show_lotto_patterns_lines(winning_numbers_list, n=None):
    """
    회차별로 당첨번호를 선으로 연결하여 보여주는 시각화 함수입니다.
    winning_numbers_list: List[List[int]] (가장 오래된 회차부터 최신순)
    n: 최근 n회만 시각화 (None이면 전체)
    """
    import matplotlib.pyplot as plt
    if n is not None:
        winning_numbers_list = winning_numbers_list[-n:]
    num_rounds = len(winning_numbers_list)
    plt.figure(figsize=(12, max(6, num_rounds * 0.2)))
    for i, numbers in enumerate(winning_numbers_list):
        y = num_rounds - i  # 최신 회차가 위로 오도록
        x = sorted(numbers)
        plt.plot(x, [y]*len(x), 'o-', color='tab:red', alpha=0.7)
    plt.yticks(range(1, num_rounds+1), [f"{num_rounds-i}회" for i in range(num_rounds)])
    plt.xticks(range(1, 46))
    plt.xlabel('번호(1~45)')
    plt.ylabel('회차')
    plt.title('회차별 당첨번호 패턴(선 연결)')
    plt.grid(True, axis='x', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()

def recommend_unseen_patterns(winning_numbers_list, num_recommend=5):
    """
    회차별로 한 번도 등장하지 않은 6개 번호 조합(패턴) 중 일부를 추천합니다.
    (실제 전체 조합은 8,145,060개로 매우 많으므로, 등장하지 않은 패턴 중 랜덤/일부만 반환)
    winning_numbers_list: List[List[int]]
    num_recommend: 추천 개수
    """
    from itertools import combinations
    # 등장한 패턴 집합(정렬된 튜플)
    seen_patterns = set(tuple(sorted(nums)) for nums in winning_numbers_list)
    # 전체 번호 pool
    all_numbers = set(range(1, 46))
    # 미출현 패턴 샘플링
    unseen_patterns = []
    tries = 0
    max_tries = num_recommend * 1000  # 너무 오래 걸리지 않게 제한
    while len(unseen_patterns) < num_recommend and tries < max_tries:
        # all_numbers가 시퀀스인지 확인하고 변환
        if isinstance(all_numbers, dict):
            all_numbers = sorted(all_numbers)
        elif isinstance(all_numbers, set):
            all_numbers = list(all_numbers)
        
        candidate = tuple(sorted(random.sample(all_numbers, 6)))
        if candidate not in seen_patterns and candidate not in unseen_patterns:
            unseen_patterns.append(candidate)
        tries += 1
    return unseen_patterns 