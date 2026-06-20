from __future__ import annotations

from itertools import combinations
from typing import Dict, List, Optional

import numpy as np

from utils.helpers import passes_advanced_filters, get_last_draw_numbers, exceeds_prev_draw_overlap

# 로또 기본 상수
_NUM_BALLS = 45
_PICK = 6
_RECENT_WINDOW = 30          # 최근 트렌드 분석 회차 수
_EXPECTED_GAP = _NUM_BALLS / _PICK  # ≈ 7.5 — 각 번호의 기대 출현 간격
_COLD_PERIOD_MULTIPLIER = 4  # 냉각 번호 기준: 기대 간격의 N배
_BIRTHDAY_MAX = 31           # 생일 편향 상한 (1~31)
_PRIZE_HIGH_SCORE = 1.0      # 비생일 구간 (32~45) 상금 배분 점수
_PRIZE_LOW_SCORE = 0.45      # 생일 구간 상금 배분 점수
_PRIZE_ROUND_MULT = 0.75     # 5의 배수 심리적 인기 번호 감소 계수
_PRIZE_LUCKY7_MULT = 0.80    # 행운의 7 배수(≤28) 감소 계수

# 10개 지표별 기본 가중치 (합계 = 1.0)
_DEFAULT_WEIGHTS: Dict[str, float] = {
    'frequency':            0.10,  # 지표 1: 전체 출현 빈도
    'recent_trend':         0.12,  # 지표 2: 최근 트렌드
    'cold_period':          0.08,  # 지표 3: 냉각(미출현) 번호
    'sum_fitness':          0.12,  # 지표 4: 합계 범위 적합도
    'odd_even_balance':     0.10,  # 지표 5: 홀짝 균형
    'section_spread':       0.12,  # 지표 6: 구간 분산
    'consecutive_pattern':  0.08,  # 지표 7: 연속번호 패턴
    'cooccurrence':         0.12,  # 지표 8: 번호 쌍 공동 출현
    'last_digit_diversity': 0.08,  # 지표 9: 끝수(일의 자리) 다양성
    'prize_sharing':        0.08,  # 지표 10: 상금 배분 최적화
}

# 지표 5: 홀수 개수별 역사적 등장 비율 기반 가중치
_ODD_EVEN_SCORES: Dict[int, float] = {
    3: 1.00, 4: 0.84, 2: 0.84, 5: 0.35, 1: 0.28, 0: 0.05, 6: 0.05,
}

# 지표 7: 연속 쌍 수별 역사적 등장 비율 기반 가중치
_CONSEC_SCORES: Dict[int, float] = {
    0: 0.85, 1: 1.00, 2: 0.70, 3: 0.35, 4: 0.15, 5: 0.05,
}


class ComprehensiveAnalyzer:
    """전체 회차 데이터를 10개 지표로 종합 분석해 최적 번호를 추천합니다.

    지표 목록:
        1. 전체 출현 빈도     — 전체 회차 기준 번호별 등장 횟수
        2. 최근 트렌드        — 최근 30회차 핫 번호
        3. 냉각 번호          — 예상 간격 대비 장기 미출현 번호
        4. 합계 범위 적합도   — 조합 합계의 역사적 분포 적합성
        5. 홀짝 균형          — 홀수/짝수 비율 vs 역사적 최빈 패턴
        6. 구간 분산          — 1-15 / 16-30 / 31-45 균등 분포
        7. 연속번호 패턴      — 연속 쌍 수 vs 역사적 최빈 패턴
        8. 번호 쌍 공동출현   — 자주 함께 등장하는 번호 쌍
        9. 끝수 다양성        — 일의 자리 숫자 중복 최소화
        10. 상금 배분 최적화  — 비인기 번호 선호로 공동 1등 감소
    """

    def __init__(
        self,
        historical_data: List[Dict],
        weights: Optional[Dict[str, float]] = None,
    ) -> None:
        self.historical_data = historical_data
        self.weights = weights or dict(_DEFAULT_WEIGHTS)

        self._data_matrix: np.ndarray = np.empty((0, 6), dtype=int)
        self._freq: np.ndarray = np.zeros(46, dtype=float)
        self._recent_freq: np.ndarray = np.zeros(46, dtype=float)
        self._last_seen: np.ndarray = np.full(46, -1, dtype=int)
        self._cooccur: np.ndarray = np.zeros((46, 46), dtype=float)
        self._sum_mean: float = 138.0
        self._sum_std: float = 30.0

        self._precompute()

    # ------------------------------------------------------------------
    # 전처리
    # ------------------------------------------------------------------

    def _precompute(self) -> None:
        rows: List[List[int]] = []
        for d in self.historical_data:
            try:
                row = [int(d[f'num{j}']) for j in range(1, 7)]
                if all(1 <= n <= 45 for n in row):
                    rows.append(row)
            except (KeyError, ValueError):
                continue

        if not rows:
            return

        self._data_matrix = np.array(rows, dtype=int)
        n = len(rows)

        for row in rows:
            for num in row:
                self._freq[num] += 1

        recent = min(_RECENT_WINDOW, n)
        for row in rows[-recent:]:
            for num in row:
                self._recent_freq[num] += 1

        for i, row in enumerate(rows):
            for num in row:
                self._last_seen[num] = i

        for row in rows:
            for a, b in combinations(row, 2):
                self._cooccur[a][b] += 1
                self._cooccur[b][a] += 1

        sums = self._data_matrix.sum(axis=1).astype(float)
        self._sum_mean = float(sums.mean())
        self._sum_std = float(sums.std()) or 1.0

    # ------------------------------------------------------------------
    # 개별 번호 지표 (1·2·3·10)
    # ------------------------------------------------------------------

    def _ind_frequency(self, num: int) -> float:
        """지표 1: 전체 출현 빈도 정규화"""
        lo, hi = self._freq[1:46].min(), self._freq[1:46].max()
        if hi == lo:
            return 0.5
        return float((self._freq[num] - lo) / (hi - lo))

    def _ind_recent_trend(self, num: int) -> float:
        """지표 2: 최근 30회 트렌드"""
        hi = self._recent_freq[1:46].max()
        if hi == 0:
            return 0.5
        return float(self._recent_freq[num] / hi)

    def _ind_cold_period(self, num: int) -> float:
        """지표 3: 미출현 기간 — 예상 간격(7.5회)의 4배까지 선형 정규화"""
        n = len(self._data_matrix)
        if n == 0:
            return 0.5
        last = int(self._last_seen[num])
        gap = (n - 1 - last) if last >= 0 else n
        return float(min(1.0, gap / (_EXPECTED_GAP * _COLD_PERIOD_MULTIPLIER)))

    def _ind_prize_sharing(self, num: int) -> float:
        """지표 10: 상금 배분 최적화 — 생일·행운 번호 편향 역보정"""
        score = _PRIZE_HIGH_SCORE if num >= _BIRTHDAY_MAX else _PRIZE_LOW_SCORE
        if num % 5 == 0:
            score *= _PRIZE_ROUND_MULT
        if num % 7 == 0 and num <= 28:
            score *= _PRIZE_LUCKY7_MULT
        return float(min(1.0, score))

    # ------------------------------------------------------------------
    # 조합 지표 (4·5·6·7·8·9)
    # ------------------------------------------------------------------

    def _ind_sum_fitness(self, numbers: List[int]) -> float:
        """지표 4: 합계가 역사적 평균에 가까울수록 높은 점수 (정규분포 커널)"""
        z = abs(sum(numbers) - self._sum_mean) / self._sum_std
        return float(np.exp(-0.5 * z ** 2))

    def _ind_odd_even_balance(self, numbers: List[int]) -> float:
        """지표 5: 홀수 개수별 역사적 등장 빈도 반영"""
        odd_count = sum(1 for n in numbers if n % 2 != 0)
        return float(_ODD_EVEN_SCORES.get(odd_count, 0.5))

    def _ind_section_spread(self, numbers: List[int]) -> float:
        """지표 6: 저(1-15) / 중(16-30) / 고(31-45) 구간 균등 분포"""
        low  = sum(1 for n in numbers if 1  <= n <= 15)
        mid  = sum(1 for n in numbers if 16 <= n <= 30)
        high = sum(1 for n in numbers if 31 <= n <= 45)
        deviation = abs(low - 2) + abs(mid - 2) + abs(high - 2)
        return float(max(0.0, 1.0 - deviation / 6.0))

    def _ind_consecutive_pattern(self, numbers: List[int]) -> float:
        """지표 7: 연속 쌍 수별 역사적 등장 빈도 반영"""
        sorted_nums = sorted(numbers)
        pairs = sum(
            1 for i in range(len(sorted_nums) - 1)
            if sorted_nums[i + 1] - sorted_nums[i] == 1
        )
        return float(_CONSEC_SCORES.get(pairs, 0.05))

    def _ind_cooccurrence(self, numbers: List[int]) -> float:
        """지표 8: 조건부 확률 기반 번호 쌍 공동 출현.

        P(B|A) = count(A∩B) / count(A) 를 활용하여
        단순 공동출현 횟수 대신 조건부 확률로 평가합니다.
        """
        n = len(self._data_matrix)
        if n == 0:
            return 0.5

        total = 0.0
        cnt = 0
        for a, b in combinations(numbers, 2):
            freq_a = float(self._freq[a])
            freq_b = float(self._freq[b])
            co_ab = float(self._cooccur[a][b])
            if freq_a > 0 and freq_b > 0:
                # P(B|A) + P(A|B) 의 평균 → 쌍의 조건부 연관도
                cond_prob = (co_ab / freq_a + co_ab / freq_b) / 2.0
                total += cond_prob
            cnt += 1

        if cnt == 0:
            return 0.5
        # 기대값: 각 번호가 독립이면 P(B|A) ≈ 6/45 ≈ 0.133
        expected = 6.0 / 45.0
        avg_cond = total / cnt
        return float(min(1.0, avg_cond / (expected * 2.5)))

    def _ind_last_digit_diversity(self, numbers: List[int]) -> float:
        """지표 9: 일의 자리 숫자 다양성 (6개 모두 다르면 만점)"""
        unique = len({n % 10 for n in numbers})
        return float((unique - 1) / 5.0)

    # ------------------------------------------------------------------
    # 종합 점수
    # ------------------------------------------------------------------

    def compute_score(self, numbers: List[int]) -> float:
        """10개 지표 가중 합산 종합 점수 반환 (0.0 ~ 1.0)"""
        w = self.weights
        scores = {
            'frequency':            float(np.mean([self._ind_frequency(n)     for n in numbers])),
            'recent_trend':         float(np.mean([self._ind_recent_trend(n)  for n in numbers])),
            'cold_period':          float(np.mean([self._ind_cold_period(n)   for n in numbers])),
            'prize_sharing':        float(np.mean([self._ind_prize_sharing(n) for n in numbers])),
            'sum_fitness':          self._ind_sum_fitness(numbers),
            'odd_even_balance':     self._ind_odd_even_balance(numbers),
            'section_spread':       self._ind_section_spread(numbers),
            'consecutive_pattern':  self._ind_consecutive_pattern(numbers),
            'cooccurrence':         self._ind_cooccurrence(numbers),
            'last_digit_diversity': self._ind_last_digit_diversity(numbers),
        }
        return float(sum(scores[k] * w[k] for k in w))

    # ------------------------------------------------------------------
    # 번호별 샘플링 가중치
    # ------------------------------------------------------------------

    def _number_sampling_weights(self, exclude: set) -> np.ndarray:
        """번호 1~45의 샘플링 확률 벡터 (인덱스 i → 번호 i+1)

        self.weights에서 개별 번호에 적용 가능한 4개 지표
        (frequency, recent_trend, cold_period, prize_sharing)의 가중치를
        추출·정규화하여 사용합니다. 따라서 self.weights를 변경하면
        샘플링 확률도 자동으로 연동됩니다.
        """
        # self.weights에서 개별 번호 수준 지표 가중치를 추출하여 정규화
        _INDIVIDUAL_KEYS = ('frequency', 'recent_trend', 'cold_period', 'prize_sharing')
        raw_w = {k: self.weights.get(k, 0.0) for k in _INDIVIDUAL_KEYS}
        w_total = sum(raw_w.values()) or 1.0
        w_freq  = raw_w['frequency']    / w_total
        w_trend = raw_w['recent_trend'] / w_total
        w_cold  = raw_w['cold_period']  / w_total
        w_prize = raw_w['prize_sharing'] / w_total

        raw = np.zeros(45, dtype=float)
        for n in range(1, _NUM_BALLS + 1):
            if n in exclude:
                continue
            raw[n - 1] = (
                self._ind_frequency(n)    * w_freq
                + self._ind_recent_trend(n)  * w_trend
                + self._ind_cold_period(n)   * w_cold
                + self._ind_prize_sharing(n) * w_prize
            )
        raw = raw - raw[raw > 0].min() + 0.02 if (raw > 0).any() else raw + 0.02
        for n in exclude:
            raw[n - 1] = 0.0
        total = raw.sum()
        return raw / total if total > 0 else np.ones(45) / 45

    # ------------------------------------------------------------------
    # 추천 생성
    # ------------------------------------------------------------------

    def generate_recommendations(
        self,
        num_recommendations: int = 10,
        sample_size: int = 30_000,
        exclude_numbers: Optional[set] = None,
        diversity_threshold: float = 0.40,
        seed: Optional[int] = None,
    ) -> List[Dict]:
        """10개 지표 종합 점수 기준 추천 조합 목록 반환

        Args:
            seed: 난수 시드. None이면 매번 다른 결과, 정수를 주면 재현 가능.
        """
        if not len(self._data_matrix):
            return []

        exclude = exclude_numbers or set()
        if len([n for n in range(1, _NUM_BALLS + 1) if n not in exclude]) < 6:
            return []

        p = self._number_sampling_weights(exclude)
        rng = np.random.default_rng(seed=seed)
        prev_draw = get_last_draw_numbers(self.historical_data)

        seen: set = set()
        scored: List[tuple] = []

        for _ in range(sample_size):
            nums = sorted((rng.choice(45, size=6, replace=False, p=p) + 1).tolist())
            key = tuple(nums)
            if key in seen:
                continue
            seen.add(key)
            # 직전 회차 당첨번호 2개 이상 포함 시 제외
            if exceeds_prev_draw_overlap(nums, prev_draw):
                continue
            # 고급 필터: AC값, 동일 십의자리, 끝수합, 저고비율
            if not passes_advanced_filters(nums):
                continue
            scored.append((self.compute_score(nums), nums))

        scored.sort(key=lambda x: x[0], reverse=True)

        results: List[Dict] = []
        for score, nums in scored:
            if len(results) >= num_recommendations:
                break
            ns = set(nums)
            if all(
                len(ns & set(r['numbers'])) / len(ns | set(r['numbers'])) < diversity_threshold
                for r in results
            ):
                results.append({'numbers': nums, 'score': score})

        return results

    # ------------------------------------------------------------------
    # 지표별 상세 리포트
    # ------------------------------------------------------------------

    def indicator_report(self, numbers: List[int]) -> Dict[str, float]:
        """조합에 대한 10개 지표 점수 딕셔너리 반환"""
        return {
            '① 전체빈도   ': round(float(np.mean([self._ind_frequency(n)     for n in numbers])), 4),
            '② 최근트렌드 ': round(float(np.mean([self._ind_recent_trend(n)  for n in numbers])), 4),
            '③ 냉각번호   ': round(float(np.mean([self._ind_cold_period(n)   for n in numbers])), 4),
            '④ 합계적합도 ': round(self._ind_sum_fitness(numbers),          4),
            '⑤ 홀짝균형   ': round(self._ind_odd_even_balance(numbers),     4),
            '⑥ 구간분산   ': round(self._ind_section_spread(numbers),       4),
            '⑦ 연속패턴   ': round(self._ind_consecutive_pattern(numbers),  4),
            '⑧ 공동출현   ': round(self._ind_cooccurrence(numbers),         4),
            '⑨ 끝수다양성 ': round(self._ind_last_digit_diversity(numbers), 4),
            '⑩ 상금배분   ': round(float(np.mean([self._ind_prize_sharing(n) for n in numbers])), 4),
        }

    def summary_stats(self) -> Dict:
        """전체 데이터 기초 통계 요약"""
        n = len(self._data_matrix)
        if n == 0:
            return {}
        top5 = sorted(
            [(int(i), int(self._freq[i])) for i in range(1, _NUM_BALLS + 1)],
            key=lambda x: x[1], reverse=True
        )[:5]
        cold5 = sorted(
            [(int(i), int(self._last_seen[i])) for i in range(1, _NUM_BALLS + 1)],
            key=lambda x: x[1]
        )[:5]
        return {
            'total_rounds': n,
            'sum_mean':     round(self._sum_mean, 2),
            'sum_std':      round(self._sum_std,  2),
            'top5_freq':    top5,
            'coldest5':     [(num, n - 1 - last if last >= 0 else n) for num, last in cold5],
        }
