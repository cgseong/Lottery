"""필터링 전략 정교화 모듈

역사적 패턴 기반 필터, 총합 분포 필터, 연관규칙 필터, 엔트로피 필터 등을 통해
낮은 가능성의 조합을 배제하여 추천 번호의 질을 향상시킵니다.
"""
from __future__ import annotations

import math
import numpy as np
from collections import Counter, defaultdict
from itertools import combinations
from typing import Dict, List, Optional, Set, Tuple

from utils.constants import MAX_LOTTO_NUMBER, NUM_LOTTO_NUMBERS_TO_PICK

try:
    from utils.logging_config import get_logger
    _log = get_logger(__name__)
except ImportError:
    import logging
    _log = logging.getLogger(__name__)



# ═══════════════════════════════════════════════════════════════════════
# 1. 역사적 패턴 기반 필터
# ═══════════════════════════════════════════════════════════════════════

class HistoricalPatternFilter:
    """역사적 당첨 데이터의 통계적 분포에 부합하지 않는 조합을 배제합니다.

    필터 항목:
        - 합계 범위: 역사적 합계 분포의 90% 신뢰구간
        - 홀짝 비율: 역사적으로 5% 이상 출현한 홀수 개수만 허용
        - 구간 분포: 특정 구간에 4개 이상 집중 배제
        - 연속번호: 3쌍 이상 연속 배제
        - AC값: 최소 7 이상 (Arithmetic Complexity)
        - 끝수 분포: 동일 끝수 3개 이상 배제
        - 소수 비율: 0개 또는 5개 이상이면 배제
        - 이전 당첨번호 재출현: 직전 회차와 4개 이상 겹치면 배제
    """

    def __init__(self, historical_data: List[Dict]):
        self.historical_data = historical_data
        self._sum_stats: Dict = {}
        self._odd_dist: Dict[int, float] = {}
        self._consec_dist: Dict[int, float] = {}
        self._section_limits: Dict[str, int] = {}
        self._prev_numbers: Set[int] = set()
        self._build_profiles()

    def _extract_numbers(self, row: Dict) -> List[int]:
        nums = []
        for i in range(1, 7):
            try:
                n = int(row.get(f'num{i}', 0))
                if 1 <= n <= MAX_LOTTO_NUMBER:
                    nums.append(n)
            except (ValueError, TypeError):
                continue
        return sorted(nums)

    def _build_profiles(self) -> None:
        """역사적 데이터에서 통계 프로파일을 구축합니다."""
        sums = []
        odd_counts = []
        consec_counts = []

        rows = sorted(self.historical_data,
                      key=lambda x: int(x.get('round', 0) or 0))

        for row in rows:
            nums = self._extract_numbers(row)
            if len(nums) != 6:
                continue
            sums.append(sum(nums))
            odd_counts.append(sum(1 for n in nums if n % 2 != 0))
            consec = sum(1 for a, b in zip(nums, nums[1:]) if b - a == 1)
            consec_counts.append(consec)

        if sums:
            arr = np.array(sums)
            self._sum_stats = {
                'mean': float(arr.mean()),
                'std': float(arr.std()),
                'low': float(np.percentile(arr, 5)),
                'high': float(np.percentile(arr, 95)),
            }

        # 홀수 개수별 출현 비율
        if odd_counts:
            counter = Counter(odd_counts)
            total = sum(counter.values())
            self._odd_dist = {k: v / total for k, v in counter.items()}

        # 연속번호 쌍 수별 출현 비율
        if consec_counts:
            counter = Counter(consec_counts)
            total = sum(counter.values())
            self._consec_dist = {k: v / total for k, v in counter.items()}

        # 직전 회차 번호
        if rows:
            self._prev_numbers = set(self._extract_numbers(rows[-1]))


    def check_sum_range(self, numbers: List[int]) -> bool:
        """합계가 역사적 90% 신뢰구간 내인지 확인합니다."""
        if not self._sum_stats:
            return True
        total = sum(numbers)
        return self._sum_stats['low'] <= total <= self._sum_stats['high']

    def check_odd_even(self, numbers: List[int]) -> bool:
        """홀수 개수가 역사적으로 5% 이상 출현한 비율인지 확인합니다."""
        if not self._odd_dist:
            return True
        odd_count = sum(1 for n in numbers if n % 2 != 0)
        return self._odd_dist.get(odd_count, 0) >= 0.05

    def check_consecutive(self, numbers: List[int]) -> bool:
        """연속 쌍이 3개 이상이면 배제합니다."""
        sorted_nums = sorted(numbers)
        consec = sum(1 for a, b in zip(sorted_nums, sorted_nums[1:]) if b - a == 1)
        return consec <= 2

    def check_section_balance(self, numbers: List[int]) -> bool:
        """특정 구간에 4개 이상 집중되면 배제합니다."""
        low = sum(1 for n in numbers if 1 <= n <= 15)
        mid = sum(1 for n in numbers if 16 <= n <= 30)
        high = sum(1 for n in numbers if 31 <= n <= 45)
        return max(low, mid, high) <= 4

    def check_ac_value(self, numbers: List[int]) -> bool:
        """AC값이 7 미만이면 배제합니다."""
        sorted_nums = sorted(numbers)
        diffs = set()
        for i in range(len(sorted_nums)):
            for j in range(i + 1, len(sorted_nums)):
                diffs.add(sorted_nums[j] - sorted_nums[i])
        return len(diffs) >= 7

    def check_last_digit(self, numbers: List[int]) -> bool:
        """동일 끝수(일의 자리) 3개 이상이면 배제합니다."""
        last_digits = [n % 10 for n in numbers]
        counter = Counter(last_digits)
        return counter.most_common(1)[0][1] <= 2

    def check_prime_ratio(self, numbers: List[int]) -> bool:
        """소수 번호가 0개 또는 5개 이상이면 배제합니다."""
        primes = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43}
        prime_count = sum(1 for n in numbers if n in primes)
        return 1 <= prime_count <= 4

    def check_prev_overlap(self, numbers: List[int]) -> bool:
        """직전 회차와 4개 이상 겹치면 배제합니다."""
        if not self._prev_numbers:
            return True
        overlap = len(set(numbers) & self._prev_numbers)
        return overlap <= 3


    def passes_all(self, numbers: List[int]) -> bool:
        """모든 역사적 패턴 필터를 통과하는지 확인합니다."""
        return (
            self.check_sum_range(numbers)
            and self.check_odd_even(numbers)
            and self.check_consecutive(numbers)
            and self.check_section_balance(numbers)
            and self.check_ac_value(numbers)
            and self.check_last_digit(numbers)
            and self.check_prime_ratio(numbers)
            and self.check_prev_overlap(numbers)
        )

    def get_failure_reasons(self, numbers: List[int]) -> List[str]:
        """조합이 실패한 필터 항목명을 반환합니다."""
        reasons = []
        if not self.check_sum_range(numbers):
            reasons.append('합계 범위 이탈')
        if not self.check_odd_even(numbers):
            reasons.append('홀짝 비율 이상')
        if not self.check_consecutive(numbers):
            reasons.append('연속번호 과다')
        if not self.check_section_balance(numbers):
            reasons.append('구간 편중')
        if not self.check_ac_value(numbers):
            reasons.append('AC값 부족')
        if not self.check_last_digit(numbers):
            reasons.append('끝수 중복')
        if not self.check_prime_ratio(numbers):
            reasons.append('소수 비율 이상')
        if not self.check_prev_overlap(numbers):
            reasons.append('직전 회차 과다 겹침')
        return reasons



# ═══════════════════════════════════════════════════════════════════════
# 2. 총합 분포 기반 정밀 필터
# ═══════════════════════════════════════════════════════════════════════

class SumDistributionFilter:
    """총합의 정규분포 적합도를 기반으로 필터링합니다.

    역사적 합계 분포를 커널 밀도 추정(KDE)으로 모델링하고,
    해당 조합의 합계가 분포상 하위 5%에 해당하면 배제합니다.
    """

    def __init__(self, historical_data: List[Dict]):
        self.historical_data = historical_data
        self._sums: np.ndarray = np.array([])
        self._mean: float = 138.0
        self._std: float = 30.0
        self._kde_bandwidth: float = 5.0
        self._build()

    def _build(self) -> None:
        sums = []
        for row in self.historical_data:
            total = 0
            valid = True
            for i in range(1, 7):
                try:
                    n = int(row.get(f'num{i}', 0))
                    if 1 <= n <= MAX_LOTTO_NUMBER:
                        total += n
                    else:
                        valid = False
                except (ValueError, TypeError):
                    valid = False
            if valid:
                sums.append(total)

        if sums:
            self._sums = np.array(sums)
            self._mean = float(self._sums.mean())
            self._std = float(self._sums.std()) or 1.0
            self._kde_bandwidth = max(3.0, self._std * 0.2)

    def kde_score(self, total_sum: int) -> float:
        """KDE 기반 합계 밀도 점수를 반환합니다 (0~1)."""
        if len(self._sums) == 0:
            return 0.5
        # 간이 KDE: 가우시안 커널
        diffs = (self._sums - total_sum) / self._kde_bandwidth
        density = float(np.exp(-0.5 * diffs ** 2).mean())
        # 최대 밀도(평균값)로 정규화
        max_diffs = (self._sums - self._mean) / self._kde_bandwidth
        max_density = float(np.exp(-0.5 * max_diffs ** 2).mean())
        if max_density > 0:
            return min(1.0, density / max_density)
        return 0.5

    def passes(self, numbers: List[int], threshold: float = 0.15) -> bool:
        """조합의 합계 KDE 점수가 threshold 이상인지 확인합니다."""
        return self.kde_score(sum(numbers)) >= threshold

    def get_optimal_sum_range(self, confidence: float = 0.80) -> Tuple[int, int]:
        """지정 신뢰도의 합계 범위를 반환합니다."""
        if len(self._sums) == 0:
            return (100, 180)
        low_pct = (1 - confidence) / 2 * 100
        high_pct = (1 + confidence) / 2 * 100
        return (int(np.percentile(self._sums, low_pct)),
                int(np.percentile(self._sums, high_pct)))



# ═══════════════════════════════════════════════════════════════════════
# 3. 연관규칙 기반 필터 (Apriori-like)
# ═══════════════════════════════════════════════════════════════════════

class AssociationRuleFilter:
    """번호 쌍/트리플의 공동 출현 연관규칙을 분석합니다.

    - Support: 해당 번호 조합이 전체 회차 중 출현한 비율
    - Confidence: A가 나왔을 때 B도 나올 조건부 확률
    - Lift: 기대값 대비 실제 공동출현 비율

    높은 Lift를 가진 번호 쌍을 포함한 조합을 우대하고,
    극히 낮은 Support의 트리플을 포함한 조합을 배제합니다.
    """

    def __init__(self, historical_data: List[Dict], min_support: float = 0.01):
        self.historical_data = historical_data
        self.min_support = min_support
        self._pair_support: Dict[Tuple[int, int], float] = {}
        self._pair_lift: Dict[Tuple[int, int], float] = {}
        self._single_support: Dict[int, float] = {}
        self._triple_support: Dict[Tuple[int, int, int], float] = {}
        self._n_rounds = 0
        self._build()

    def _build(self) -> None:
        if not self.historical_data:
            return

        self._n_rounds = len(self.historical_data)
        single_count: Counter = Counter()
        pair_count: Counter = Counter()
        triple_count: Counter = Counter()

        for row in self.historical_data:
            nums = []
            for i in range(1, 7):
                try:
                    n = int(row.get(f'num{i}', 0))
                    if 1 <= n <= MAX_LOTTO_NUMBER:
                        nums.append(n)
                except (ValueError, TypeError):
                    continue

            for n in nums:
                single_count[n] += 1
            for pair in combinations(sorted(nums), 2):
                pair_count[pair] += 1
            # 트리플은 상위 빈도만 저장 (메모리 절약)
            for triple in combinations(sorted(nums), 3):
                triple_count[triple] += 1

        n = self._n_rounds
        for num, cnt in single_count.items():
            self._single_support[num] = cnt / n

        for pair, cnt in pair_count.items():
            sup = cnt / n
            self._pair_support[pair] = sup
            # Lift = P(A∩B) / (P(A) * P(B))
            pa = self._single_support.get(pair[0], 1/45)
            pb = self._single_support.get(pair[1], 1/45)
            self._pair_lift[pair] = sup / max(pa * pb, 1e-10)

        # 상위 support 트리플만 유지
        for triple, cnt in triple_count.items():
            sup = cnt / n
            if sup >= self.min_support:
                self._triple_support[triple] = sup


    def get_top_pairs(self, top_n: int = 20) -> List[Tuple[Tuple[int, int], float]]:
        """Lift가 높은 상위 번호 쌍을 반환합니다."""
        sorted_pairs = sorted(self._pair_lift.items(), key=lambda x: x[1], reverse=True)
        return sorted_pairs[:top_n]

    def score_combination(self, numbers: List[int]) -> float:
        """조합 내 번호 쌍들의 평균 Lift를 점수화합니다 (0~1)."""
        pairs = list(combinations(sorted(numbers), 2))
        if not pairs:
            return 0.5

        lifts = []
        for pair in pairs:
            lift = self._pair_lift.get(pair, 1.0)
            lifts.append(lift)

        avg_lift = np.mean(lifts)
        # Lift > 1 이면 기대 이상의 연관, < 1 이면 기대 이하
        # 정규화: lift=1 → 0.5, lift=2 → 1.0, lift=0.5 → 0.25
        return float(min(1.0, avg_lift / 2.0))

    def has_anti_pattern(self, numbers: List[int]) -> bool:
        """조합 내에 극히 낮은 연관도(Lift < 0.3)의 쌍이 2개 이상이면 True."""
        pairs = list(combinations(sorted(numbers), 2))
        low_lift_count = sum(
            1 for pair in pairs
            if self._pair_lift.get(pair, 1.0) < 0.3
        )
        return low_lift_count >= 2

    def passes(self, numbers: List[int]) -> bool:
        """연관규칙 필터를 통과하는지 확인합니다."""
        return not self.has_anti_pattern(numbers)



# ═══════════════════════════════════════════════════════════════════════
# 4. 엔트로피 기반 필터
# ═══════════════════════════════════════════════════════════════════════

class EntropyFilter:
    """정보 엔트로피를 기반으로 조합의 '무작위성'을 평가합니다.

    너무 규칙적(낮은 엔트로피)이거나 너무 무질서(높은 엔트로피)한
    조합을 배제하고, 역사적 당첨번호의 엔트로피 분포 중심에 가까운
    조합을 우대합니다.
    """

    def __init__(self, historical_data: List[Dict]):
        self.historical_data = historical_data
        self._entropy_mean: float = 0.0
        self._entropy_std: float = 1.0
        self._build()

    @staticmethod
    def _calc_entropy(numbers: List[int]) -> float:
        """조합의 간격 엔트로피를 계산합니다.

        번호 간 간격(gap)의 분포를 확률로 변환하여 Shannon 엔트로피를 계산합니다.
        """
        sorted_nums = sorted(numbers)
        gaps = [sorted_nums[0]] + [
            sorted_nums[i+1] - sorted_nums[i] for i in range(len(sorted_nums)-1)
        ] + [MAX_LOTTO_NUMBER - sorted_nums[-1]]

        total = sum(gaps)
        if total == 0:
            return 0.0

        entropy = 0.0
        for g in gaps:
            if g > 0:
                p = g / total
                entropy -= p * math.log2(p)
        return entropy

    def _build(self) -> None:
        entropies = []
        for row in self.historical_data:
            nums = []
            for i in range(1, 7):
                try:
                    n = int(row.get(f'num{i}', 0))
                    if 1 <= n <= MAX_LOTTO_NUMBER:
                        nums.append(n)
                except (ValueError, TypeError):
                    continue
            if len(nums) == 6:
                entropies.append(self._calc_entropy(nums))

        if entropies:
            arr = np.array(entropies)
            self._entropy_mean = float(arr.mean())
            self._entropy_std = float(arr.std()) or 1.0

    def score(self, numbers: List[int]) -> float:
        """조합의 엔트로피 적합도 점수 (0~1). 평균에 가까울수록 높음."""
        ent = self._calc_entropy(numbers)
        z = abs(ent - self._entropy_mean) / self._entropy_std
        return float(np.exp(-0.5 * z ** 2))

    def passes(self, numbers: List[int], max_z: float = 2.0) -> bool:
        """엔트로피가 평균 ± max_z*std 이내인지 확인합니다."""
        ent = self._calc_entropy(numbers)
        z = abs(ent - self._entropy_mean) / self._entropy_std
        return z <= max_z



# ═══════════════════════════════════════════════════════════════════════
# 5. 통합 필터 파이프라인
# ═══════════════════════════════════════════════════════════════════════

class AdvancedFilterPipeline:
    """모든 고급 필터를 파이프라인으로 통합하여 일괄 적용합니다.

    각 필터는 독립적으로 on/off 가능하며, 조합별 상세 리포트를 제공합니다.
    """

    def __init__(self, historical_data: List[Dict], config: Optional[Dict] = None):
        """
        Args:
            config: 필터별 활성화 여부 및 파라미터 설정
                {
                    'historical_pattern': True,
                    'sum_distribution': True,
                    'association_rule': True,
                    'entropy': True,
                    'sum_threshold': 0.15,
                    'entropy_max_z': 2.0,
                }
        """
        self.config = config or {
            'historical_pattern': True,
            'sum_distribution': True,
            'association_rule': True,
            'entropy': True,
            'sum_threshold': 0.15,
            'entropy_max_z': 2.0,
        }

        self._filters: Dict[str, object] = {}

        if self.config.get('historical_pattern', True):
            self._filters['historical_pattern'] = HistoricalPatternFilter(historical_data)
        if self.config.get('sum_distribution', True):
            self._filters['sum_distribution'] = SumDistributionFilter(historical_data)
        if self.config.get('association_rule', True):
            self._filters['association_rule'] = AssociationRuleFilter(historical_data)
        if self.config.get('entropy', True):
            self._filters['entropy'] = EntropyFilter(historical_data)

        _log.info("고급 필터 파이프라인 초기화: %d개 필터 활성",
                  len(self._filters))


    def passes(self, numbers: List[int]) -> bool:
        """모든 활성 필터를 통과하는지 확인합니다."""
        if 'historical_pattern' in self._filters:
            if not self._filters['historical_pattern'].passes_all(numbers):
                return False

        if 'sum_distribution' in self._filters:
            threshold = self.config.get('sum_threshold', 0.15)
            if not self._filters['sum_distribution'].passes(numbers, threshold):
                return False

        if 'association_rule' in self._filters:
            if not self._filters['association_rule'].passes(numbers):
                return False

        if 'entropy' in self._filters:
            max_z = self.config.get('entropy_max_z', 2.0)
            if not self._filters['entropy'].passes(numbers, max_z):
                return False

        return True

    def score(self, numbers: List[int]) -> float:
        """각 필터의 개별 점수를 가중 평균하여 종합 필터 점수를 반환합니다 (0~1)."""
        scores = []
        weights = []

        if 'sum_distribution' in self._filters:
            scores.append(self._filters['sum_distribution'].kde_score(sum(numbers)))
            weights.append(0.30)

        if 'association_rule' in self._filters:
            scores.append(self._filters['association_rule'].score_combination(numbers))
            weights.append(0.30)

        if 'entropy' in self._filters:
            scores.append(self._filters['entropy'].score(numbers))
            weights.append(0.20)

        if 'historical_pattern' in self._filters:
            # 역사적 패턴: 통과=1.0, 실패=0.0
            passes = 1.0 if self._filters['historical_pattern'].passes_all(numbers) else 0.0
            scores.append(passes)
            weights.append(0.20)

        if not scores:
            return 0.5

        total_w = sum(weights)
        return float(sum(s * w for s, w in zip(scores, weights)) / total_w)

    def get_detailed_report(self, numbers: List[int]) -> Dict:
        """조합에 대한 상세 필터 리포트를 반환합니다."""
        report = {
            'numbers': numbers,
            'passes_all': self.passes(numbers),
            'total_score': self.score(numbers),
            'filters': {}
        }

        if 'historical_pattern' in self._filters:
            hf = self._filters['historical_pattern']
            report['filters']['historical_pattern'] = {
                'passes': hf.passes_all(numbers),
                'failures': hf.get_failure_reasons(numbers),
            }

        if 'sum_distribution' in self._filters:
            sf = self._filters['sum_distribution']
            report['filters']['sum_distribution'] = {
                'sum': sum(numbers),
                'kde_score': sf.kde_score(sum(numbers)),
                'optimal_range': sf.get_optimal_sum_range(),
            }

        if 'association_rule' in self._filters:
            af = self._filters['association_rule']
            report['filters']['association_rule'] = {
                'lift_score': af.score_combination(numbers),
                'has_anti_pattern': af.has_anti_pattern(numbers),
            }

        if 'entropy' in self._filters:
            ef = self._filters['entropy']
            report['filters']['entropy'] = {
                'entropy_score': ef.score(numbers),
                'entropy_value': ef._calc_entropy(numbers),
                'expected_mean': ef._entropy_mean,
            }

        return report

    def filter_combinations(self, combinations_list: List[List[int]]) -> List[List[int]]:
        """조합 리스트에서 모든 필터를 통과하는 것만 반환합니다."""
        return [nums for nums in combinations_list if self.passes(nums)]

    def rank_combinations(self, combinations_list: List[List[int]]) -> List[Tuple[List[int], float]]:
        """조합 리스트를 필터 점수 기준으로 내림차순 정렬합니다."""
        scored = [(nums, self.score(nums)) for nums in combinations_list]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored
