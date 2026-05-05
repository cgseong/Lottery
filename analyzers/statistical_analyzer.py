#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""통계 기반 로또 번호 분석기."""

import random
from collections import Counter
from typing import List, Dict, Optional, Set, Tuple

from utils.helpers import check_consecutive_count
from utils.logging_config import get_logger

_log = get_logger(__name__)

# 상수 정의
MAX_LOTTO_NUMBER = 45
NUM_LOTTO_NUMBERS_TO_PICK = 6
DEFAULT_RECENT_COUNT = 10

# 상금 분배 최적화: 생일 편향(1-31)을 피하고 32-45를 선호하여 공동 수령자 수를 줄임
# 연구에 따르면 1-31 구간은 생일 선택 패턴으로 과다 선택되고, 32-45는 과소 선택됨
_PRIZE_SHARING_MULTIPLIERS: Dict[int, float] = {
    **{n: 0.75 for n in range(1, 32)},   # 생일 범위: 과다 선택됨
    **{n: 1.40 for n in range(32, 46)},   # 비생일 범위: 과소 선택됨
}
# 5의 배수(라운드 넘버)는 사람들이 더 많이 선택하므로 추가 감소
for _n in [5, 10, 15, 20, 25, 30, 35, 40, 45]:
    _PRIZE_SHARING_MULTIPLIERS[_n] = round(_PRIZE_SHARING_MULTIPLIERS[_n] * 0.85, 3)

# 점수 계산 기본 가중치
_DEFAULT_SCORE_WEIGHTS: Dict[str, float] = {
    'frequency': 0.45,
    'sum': 0.20,
    'trend': 0.20,
    'distribution': 0.15,
}


class StatisticalAnalyzer:
    """Statistical analyzer for lotto numbers."""

    def __init__(self, historical_data: List[Dict], score_weights: Optional[Dict[str, float]] = None):
        """
        Args:
            historical_data: historical winning number rows.
            score_weights: optional override for scoring weights.
        """
        self.historical_data = historical_data
        self.score_weights: Dict[str, float] = score_weights or dict(_DEFAULT_SCORE_WEIGHTS)
        self.frequency_analysis = None
        self.gap_analysis = None
        self.sum_analysis = None
        self.recent_trends = None
        self._distribution_profile = None

    def analyze_recent_trends(self, recent_count: int = 10) -> Dict:
        """최근 N회차의 Hot/Cold 번호를 분석합니다.

        Hot Number: 최근 n회차 내 가장 많이 출현한 번호
        Cold Number: 최근 n회차 내 미출현 번호 중 전체 빈도가 낮은 번호
        """
        if not self.historical_data:
            return {}

        # 최근 N개 데이터 추출 (최신 회차 기준 내림차순)
        sorted_data = sorted(self.historical_data, key=self._get_round_value, reverse=True)
        recent_data = sorted_data[:recent_count]

        recent_numbers = []
        for data in recent_data:
            recent_numbers.extend(self._extract_numbers(data))

        recent_counter = Counter(recent_numbers)

        # Hot Numbers: 최근 출현 빈도 상위
        hot_numbers = recent_counter.most_common(5)

        # Cold Numbers: 최근 N회 내 미출현 번호
        all_numbers = set(range(1, MAX_LOTTO_NUMBER + 1))
        appeared_numbers = set(recent_numbers)
        cold_candidates = list(all_numbers - appeared_numbers)

        # 전체 빈도 기준으로 cold 후보 중 빈도가 낮은 번호 선택
        if not self.frequency_analysis:
            self.analyze_frequency()

        total_freq = self.frequency_analysis.get('frequency', {})
        cold_numbers = sorted(cold_candidates, key=lambda x: total_freq.get(x, 0), reverse=True)[:5]

        self.recent_trends = {
            'recent_count': recent_count,
            'hot_numbers': hot_numbers,   # [(num, count), ...]
            'cold_numbers': cold_numbers, # [num, ...]
            'recent_frequency': dict(recent_counter)
        }

        return self.recent_trends

    def analyze_frequency(self) -> Dict:
        """번호별 출현 빈도를 분석합니다."""
        if not self.historical_data:
            return {}

        all_numbers = []
        for data in self.historical_data:
            numbers = self._extract_numbers(data)
            all_numbers.extend(numbers)

        frequency = Counter(all_numbers)
        self.frequency_analysis = {
            'frequency': dict(frequency),
            'most_common': frequency.most_common(10),
            'least_common': frequency.most_common()[:-11:-1]
        }

        return self.frequency_analysis

    def analyze_gap_patterns(self) -> Dict:
        """번호 간격 패턴을 분석합니다."""
        if not self.historical_data:
            return {}

        gaps = []
        for data in self.historical_data:
            numbers = sorted(self._extract_numbers(data))
            for i in range(len(numbers) - 1):
                gaps.append(numbers[i+1] - numbers[i])

        gap_counter = Counter(gaps)
        self.gap_analysis = {
            'gaps': gaps,
            'gap_frequency': dict(gap_counter),
            'most_common_gaps': gap_counter.most_common(5)
        }

        return self.gap_analysis

    def analyze_sum_range(self) -> Dict:
        """번호 합계 범위를 분석합니다."""
        if not self.historical_data:
            return {}

        sums = []
        for data in self.historical_data:
            numbers = self._extract_numbers(data)
            if numbers:
                sums.append(sum(numbers))

        if not sums:
            return {}

        self.sum_analysis = {
            'sums': sums,
            'min_sum': min(sums),
            'max_sum': max(sums),
            'avg_sum': sum(sums) / len(sums),
            'sum_range': (min(sums), max(sums))
        }

        return self.sum_analysis

    def analyze_odd_even(self) -> Dict:
        """홀짝 비율을 분석합니다."""
        default_result = {
            'avg_odd': 0.0,
            'avg_even': 0.0,
            'odd_counts': [],
            'even_counts': []
        }

        if not self.historical_data:
            return default_result

        odd_counts = []
        even_counts = []

        for data in self.historical_data:
            numbers = self._extract_numbers(data)
            if not numbers:
                continue
            odd = sum(1 for n in numbers if n % 2 == 1)
            even = 6 - odd
            odd_counts.append(odd)
            even_counts.append(even)

        if not odd_counts:
            return default_result

        avg_odd = sum(odd_counts) / len(odd_counts)
        avg_even = sum(even_counts) / len(even_counts)

        return {
            'avg_odd': avg_odd,
            'avg_even': avg_even,
            'odd_counts': odd_counts,
            'even_counts': even_counts
        }

    def analyze_section_distribution(self) -> Dict:
        """구간별 분포를 분석합니다. (1-15, 16-30, 31-45)."""
        default_result = {
            'counts': {'1-15': 0, '16-30': 0, '31-45': 0},
            'percentages': {'1-15': 0.0, '16-30': 0.0, '31-45': 0.0}
        }

        if not self.historical_data:
            return default_result

        sections = {'1-15': 0, '16-30': 0, '31-45': 0}
        total_numbers = 0

        for data in self.historical_data:
            numbers = self._extract_numbers(data)
            for num in numbers:
                if 1 <= num <= 15:
                    sections['1-15'] += 1
                elif 16 <= num <= 30:
                    sections['16-30'] += 1
                elif 31 <= num <= 45:
                    sections['31-45'] += 1
                total_numbers += 1

        if total_numbers == 0:
            return default_result

        # 비율 계산
        percentages = {k: (v / total_numbers) * 100 for k, v in sections.items()}

        return {
            'counts': sections,
            'percentages': percentages
        }

    def analyze_consecutive_patterns(self) -> Dict:
        """연속번호 패턴을 분석합니다."""
        default_result = {
            'counts': {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            'percentages': {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}
        }

        if not self.historical_data:
            return default_result

        consecutive_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        total_draws = 0

        for data in self.historical_data:
            numbers = self._extract_numbers(data)
            if not numbers:
                continue

            count = self.check_consecutive_numbers(numbers)
            if count in consecutive_counts:
                consecutive_counts[count] += 1
            else:
                # 5개 이상인 경우
                consecutive_counts[5] += 1
            total_draws += 1

        if total_draws == 0:
            return default_result

        percentages = {k: (v / total_draws) * 100 for k, v in consecutive_counts.items()}

        return {
            'counts': consecutive_counts,
            'percentages': percentages
        }

    def _build_distribution_profile(self) -> Dict:
        """Build cached distribution profile for filtering."""
        if self._distribution_profile:
            return self._distribution_profile

        sum_stats = self.analyze_sum_range()
        odd_even_stats = self.analyze_odd_even()
        section_stats = self.analyze_section_distribution()
        consecutive_stats = self.analyze_consecutive_patterns()

        sums = sum_stats.get('sums', []) if sum_stats else []
        if sums:
            avg_sum = sum_stats.get('avg_sum', 0)
            variance = sum((s - avg_sum) ** 2 for s in sums) / max(1, len(sums))
            std_sum = variance ** 0.5
        else:
            avg_sum = 0
            std_sum = 0

        odd_counts = odd_even_stats.get('odd_counts', [])
        odd_freq = Counter(odd_counts) if odd_counts else Counter()
        # Allow odd counts that appear frequently (>= 12% of draws)
        min_ratio = 0.12
        total_odd_samples = sum(odd_freq.values())
        if total_odd_samples:
            allowed_odd = {
                odd for odd, cnt in odd_freq.items()
                if (cnt / total_odd_samples) >= min_ratio
            }
        else:
            allowed_odd = {2, 3, 4}

        percentages = section_stats.get('percentages', {}) if section_stats else {}
        if not percentages or sum(percentages.values()) == 0:
            expected_sections = {}
        else:
            expected_sections = {}
            for key, pct in percentages.items():
                expected = (pct / 100.0) * NUM_LOTTO_NUMBERS_TO_PICK
                expected_sections[key] = expected

        # Allow consecutive count that is not extremely rare
        cons_percent = consecutive_stats.get('percentages', {}) if consecutive_stats else {}
        allowed_consecutive = {k for k, v in cons_percent.items() if v >= 5.0}
        if not allowed_consecutive:
            allowed_consecutive = {0, 1, 2}

        self._distribution_profile = {
            'avg_sum': avg_sum,
            'std_sum': std_sum,
            'allowed_odd': allowed_odd,
            'expected_sections': expected_sections,
            'allowed_consecutive': allowed_consecutive,
        }
        return self._distribution_profile

    def _passes_distribution_filters(self, numbers: List[int]) -> bool:
        """Check if numbers fit historical distribution."""
        profile = self._build_distribution_profile()

        # Sum range filter: within avg +/- 1.2 * std (if std exists)
        if profile['std_sum'] > 0:
            total = sum(numbers)
            if abs(total - profile['avg_sum']) > (1.2 * profile['std_sum']):
                return False

        # Odd/even filter
        odd = sum(1 for n in numbers if n % 2 == 1)
        if profile['allowed_odd'] and odd not in profile['allowed_odd']:
            return False

        # Section distribution filter (allow +-1 from expected)
        if profile['expected_sections']:
            sec_counts = {'1-15': 0, '16-30': 0, '31-45': 0}
            for n in numbers:
                if 1 <= n <= 15:
                    sec_counts['1-15'] += 1
                elif 16 <= n <= 30:
                    sec_counts['16-30'] += 1
                elif 31 <= n <= 45:
                    sec_counts['31-45'] += 1

            for key, expected in profile['expected_sections'].items():
                if abs(sec_counts.get(key, 0) - expected) > 1.0:
                    return False

        # Consecutive filter
        consecutive_count = self.check_consecutive_numbers(numbers)
        if profile['allowed_consecutive'] and consecutive_count not in profile['allowed_consecutive']:
            return False

        return True

    def calculate_score(self, numbers: List[int], weights: Optional[Dict[str, float]] = None) -> float:
        """번호 조합의 점수를 계산합니다.

        Args:
            weights: 가중치 오버라이드 (없으면 인스턴스 가중치 사용)
        """
        if not self.frequency_analysis:
            self.analyze_frequency()

        if not self.sum_analysis:
            self.analyze_sum_range()

        score = 0.0

        # 빈도 기반 점수
        frequency = self.frequency_analysis.get('frequency', {})
        total_draws = len(self.historical_data)

        if total_draws == 0:
            return 0.0

        for num in numbers:
            freq = frequency.get(num, 0)
            score += freq / total_draws
        frequency_score = score / max(1, len(numbers))

        # 합계 기반 점수
        sum_score = 0.0
        if self.sum_analysis:
            number_sum = sum(numbers)
            avg_sum = self.sum_analysis.get('avg_sum', 0)
            if avg_sum > 0:
                sum_diff = abs(number_sum - avg_sum)
                sum_score = max(0, 1 - (sum_diff / avg_sum))

        if not self.recent_trends:
            self.analyze_recent_trends()
        hot_numbers = set(num for num, _ in self.recent_trends.get('hot_numbers', [])) if self.recent_trends else set()
        cold_numbers = set(self.recent_trends.get('cold_numbers', [])) if self.recent_trends else set()
        hot_overlap = len(set(numbers) & hot_numbers)
        cold_overlap = len(set(numbers) & cold_numbers)
        trend_score = min(1.0, (hot_overlap * 0.7 + cold_overlap * 0.3) / 3.0)

        distribution_score = 1.0 if self._passes_distribution_filters(numbers) else 0.0

        w = weights if weights is not None else self.score_weights
        return (
            frequency_score * w['frequency'] +
            sum_score * w['sum'] +
            trend_score * w['trend'] +
            distribution_score * w['distribution']
        )

    def check_consecutive_numbers(self, numbers: List[int]) -> int:
        """연속된 번호 쌍의 총 개수를 반환합니다.

        utils.helpers.check_consecutive_count에 위임 — 단일 구현 유지.
        """
        return check_consecutive_count(numbers)

    def generate_recommendations(self, exclude_numbers: Optional[Set[int]] = None,
                                 fixed_numbers: Optional[Set[int]] = None,
                                 num_recommendations: int = 5,
                                 verbose: bool = True) -> List[Dict]:
        """통계 기반 번호 추천 조합을 생성합니다.

        Args:
            exclude_numbers: 제외할 번호 집합
            fixed_numbers: 반드시 포함할 번호 집합
        """
        if not self.historical_data:
            return []

        # 분석 수행
        if not self.frequency_analysis:
            self.analyze_frequency()

        if not self.sum_analysis:
            self.analyze_sum_range()

        exclude_numbers = exclude_numbers or set()
        fixed_numbers = fixed_numbers or set()

        # 고정수와 제외수가 겹치면 고정수 우선
        if fixed_numbers & exclude_numbers:
            if verbose:
                _log.warning("고정수와 제외수에 중복된 번호가 있어, 고정수를 우선 적용합니다.")
            exclude_numbers = exclude_numbers - fixed_numbers

        if len(fixed_numbers) > NUM_LOTTO_NUMBERS_TO_PICK:
            if verbose:
                _log.warning("고정수가 6개를 초과합니다. 6개까지만 사용합니다.")
            fixed_numbers = set(list(fixed_numbers)[:NUM_LOTTO_NUMBERS_TO_PICK])

        if verbose:
            _log.info("통계 기반 분석 실행 중..")

        recommendations = []
        attempts = 0
        max_attempts = num_recommendations * 400
        candidate_limit = num_recommendations * 25

        while len(recommendations) < num_recommendations and attempts < max_attempts:
            attempts += 1

            # 통계 기반 번호 생성 (고정수 포함)
            numbers = self._generate_statistical_numbers(exclude_numbers, fixed_numbers)

            if not numbers:
                continue

            # 중복 검사
            numbers_tuple = tuple(sorted(numbers))
            if any(tuple(sorted(rec['numbers'])) == numbers_tuple for rec in recommendations):
                continue

            # 점수 계산
            score = self.calculate_score(numbers)
            consecutive_count = self.check_consecutive_numbers(numbers)

            recommendation = {
                'numbers': sorted(numbers),
                'score': score,
                'method': '통계 분석',
                'consecutive_count': consecutive_count,
                'sum': sum(numbers)
            }

            recommendations.append(recommendation)
            if len(recommendations) >= candidate_limit:
                break

        # 점수순으로 정렬
        recommendations.sort(key=lambda x: x['score'], reverse=True)

        return recommendations[:num_recommendations]

    def generate_unique_recommendations(self, exclude_numbers: Optional[Set[int]] = None,
                                        num_recommendations: int = 5) -> List[Dict]:
        """과거 당첨 이력에 없는 새로운 패턴(조합)을 추천합니다."""
        if not self.historical_data:
            return []

        exclude_numbers = exclude_numbers or set()

        # 1. 과거 당첨 번호 세트 생성 (정렬된 튜플 형태)
        historical_combinations = set()
        for data in self.historical_data:
            nums = self._extract_numbers(data)
            if nums:
                historical_combinations.add(tuple(sorted(nums)))

        _log.info("과거 %d개의 당첨 패턴과 비교합니다..", len(historical_combinations))

        recommendations = []
        attempts = 0
        max_attempts = num_recommendations * 1200
        # 사용 가능한 번호 풀
        available_numbers = [n for n in range(1, MAX_LOTTO_NUMBER + 1) if n not in exclude_numbers]

        if len(available_numbers) < NUM_LOTTO_NUMBERS_TO_PICK:
            _log.warning("사용 가능한 번호가 부족합니다.")
            return []

        while len(recommendations) < num_recommendations and attempts < max_attempts:
            attempts += 1

            if not self.frequency_analysis:
                self.analyze_frequency()
            if not self.recent_trends:
                self.analyze_recent_trends()

            frequency = self.frequency_analysis.get('frequency', {})
            hot_set = set(num for num, _ in self.recent_trends.get('hot_numbers', [])) if self.recent_trends else set()
            cold_set = set(self.recent_trends.get('cold_numbers', [])) if self.recent_trends else set()
            weights = []
            for num in available_numbers:
                base = max(1.0, float(frequency.get(num, 1)))
                if num in hot_set:
                    base *= 1.25
                elif num in cold_set:
                    base *= 1.12
                # [A] 상금 분배 최적화: 과소 선택된 번호에 가중치 부스트
                base *= _PRIZE_SHARING_MULTIPLIERS.get(num, 1.0)
                weights.append(base)

            selected_nums = sorted(self._weighted_sample_without_replacement(
                available_numbers,
                weights,
                NUM_LOTTO_NUMBERS_TO_PICK
            ))

            if not selected_nums:
                continue

            if not self._passes_distribution_filters(selected_nums):
                continue

            combo_tuple = tuple(selected_nums)

            # 2. 필터링: 과거 당첨 이력 확인
            if combo_tuple in historical_combinations:
                continue

            # 3. 필터링: 이미 추천 목록 중복 확인
            if any(tuple(sorted(rec['numbers'])) == combo_tuple for rec in recommendations):
                continue

            # 4. 점수 계산 및 추가
            score = self.calculate_score(selected_nums)
            consecutive_count = self.check_consecutive_numbers(selected_nums)

            recommendation = {
                'numbers': selected_nums,
                'score': score,
                'method': '미출현 패턴',
                'consecutive_count': consecutive_count,
                'sum': sum(selected_nums)
            }

            recommendations.append(recommendation)

        return recommendations

    def generate_numbers(self, exclude_numbers: Optional[List[int]] = None) -> Optional[List[int]]:
        """가중치 기반 번호를 생성합니다."""
        exclude_numbers = exclude_numbers or []
        available_numbers = [n for n in range(1, MAX_LOTTO_NUMBER + 1) if n not in exclude_numbers]

        if len(available_numbers) < NUM_LOTTO_NUMBERS_TO_PICK:
            return None

        # 빈도 및 트렌드 기반 가중치 적용
        if not self.frequency_analysis:
            self.analyze_frequency()

        if not self.recent_trends:
            self.analyze_recent_trends()

        frequency = self.frequency_analysis.get('frequency', {})
        hot_set = set(num for num, _ in self.recent_trends.get('hot_numbers', [])) if self.recent_trends else set()
        cold_set = set(self.recent_trends.get('cold_numbers', [])) if self.recent_trends else set()

        weights = []
        for num in available_numbers:
            w = float(frequency.get(num, 1))
            if num in hot_set:
                w *= 1.2
            elif num in cold_set:
                w *= 1.1
            # [A] 상금 분배 최적화
            w *= _PRIZE_SHARING_MULTIPLIERS.get(num, 1.0)
            weights.append(w)

        try:
            # 6개 가중치 샘플링 (비복원 추출)
            if sum(weights) > 0:
                selected = self._weighted_sample_without_replacement(
                    available_numbers,
                    weights,
                    NUM_LOTTO_NUMBERS_TO_PICK
                )
            else:
                selected = random.sample(available_numbers, NUM_LOTTO_NUMBERS_TO_PICK)

            if len(selected) != NUM_LOTTO_NUMBERS_TO_PICK:
                return None
            return sorted(selected)
        except (ValueError, IndexError):
            # 예외 발생 시 무작위 추출
            return sorted(random.sample(available_numbers, NUM_LOTTO_NUMBERS_TO_PICK))

    def _extract_numbers(self, data: Dict) -> List[int]:
        """Extract numbers from a row with flexible key matching."""
        numbers = []
        key_map = {k.replace(' ', ''): k for k in data.keys()}
        for i in range(1, 7):
            candidates = [
                f'번호{i}', f'번호 {i}', f'num{i}', f'num{i}'.upper(), f'No{i}', f'No {i}'
            ]
            key = None
            for cand in candidates:
                if cand in data:
                    key = cand
                    break
                if cand.replace(' ', '') in key_map:
                    key = key_map[cand.replace(' ', '')]
                    break
            if key and data.get(key) not in (None, ''):
                try:
                    numbers.append(int(data[key]))
                except (ValueError, TypeError):
                    continue
        return numbers

    def _get_round_value(self, data: Dict) -> int:
        """Return round number for sorting; fallback to 0 if missing."""
        key_map = {k.replace(' ', ''): k for k in data.keys()}
        candidates = ['회차', '회 차', 'round', 'Round']
        key = None
        for cand in candidates:
            if cand in data:
                key = cand
                break
            if cand.replace(' ', '') in key_map:
                key = key_map[cand.replace(' ', '')]
                break
        if not key:
            return 0
        try:
            return int(data.get(key, 0))
        except (ValueError, TypeError):
            return 0

    def _generate_statistical_numbers(self, exclude_numbers: Set[int], fixed_numbers: Optional[Set[int]] = None) -> Optional[List[int]]:
        """통계 기반으로 번호를 생성합니다 (고정수 포함)."""
        fixed_numbers = fixed_numbers or set()

        # 고정수가 이미 6개면 그대로 반환 (추가 생성 불필요)
        if len(fixed_numbers) == NUM_LOTTO_NUMBERS_TO_PICK:
            return sorted(list(fixed_numbers))

        # 추가로 뽑아야 할 번호 수
        num_to_pick = NUM_LOTTO_NUMBERS_TO_PICK - len(fixed_numbers)

        # 후보 번호: 전체 - 제외수 - 고정수
        available_numbers = [
            n for n in range(1, MAX_LOTTO_NUMBER + 1)
            if n not in exclude_numbers and n not in fixed_numbers
        ]

        if len(available_numbers) < num_to_pick:
            return None

        # 빈도 기반 가중치 + 상금 분배 최적화 적용
        frequency = self.frequency_analysis.get('frequency', {})
        weights = [
            frequency.get(num, 1) * _PRIZE_SHARING_MULTIPLIERS.get(num, 1.0)
            for num in available_numbers
        ]

        try:
            # 가중치 합이 0이면 균등 가중치로 대체
            if sum(weights) <= 0:
                weights = [1.0] * len(available_numbers)

            selected = self._weighted_sample_without_replacement(
                available_numbers,
                weights,
                num_to_pick
            )
            if len(selected) != num_to_pick:
                return None

            final_numbers = sorted(list(fixed_numbers) + selected)
            if len(set(final_numbers)) != NUM_LOTTO_NUMBERS_TO_PICK:
                return None
            return final_numbers
        except (ValueError, IndexError):
            return None

    def _weighted_sample_without_replacement(
        self,
        population: List[int],
        weights: List[float],
        k: int
    ) -> List[int]:
        """가중치 기반 비복원 추출로 k개의 번호를 선택합니다."""
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
