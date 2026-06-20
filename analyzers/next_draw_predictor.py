"""다음 회차 예측 분석기 (패턴 기반)

역대 당첨번호의 번호별 발생 패턴을 다각도로 분석하여
다음 회차에 출현할 가능성이 높은 번호를 예측합니다.

분석 항목:
    1. 주기(Cycle) 분석 - 자기상관(ACF) 기반 번호별 출현 주기 탐지
    2. 갭 기반 출현 예측 - 미출현 기간 vs 역사적 평균 간격 비교
    3. 스트릭(Streak) 분석 - 연속 출현/미출현 패턴 기반 추세 예측
    4. 조건부 페어링 - 최근 출현 번호 기반 동반 출현 확률
    5. 모멘텀 웨이브 - 단기/중기/장기 이동평균 기반 추세
    6. 종합 점수 앙상블 - 위 5개 지표를 가중 합산하여 최종 예측
"""
from __future__ import annotations

import numpy as np
from collections import defaultdict, Counter
from typing import Dict, List, Optional, Set, Tuple

from utils.constants import MAX_LOTTO_NUMBER, NUM_LOTTO_NUMBERS_TO_PICK, LOTTO_NUMBER_COLUMNS
from utils.helpers import get_last_draw_numbers, exceeds_prev_draw_overlap

try:
    from utils.logging_config import get_logger
    _log = get_logger(__name__)
except ImportError:
    import logging
    _log = logging.getLogger(__name__)



class NextDrawPredictor:
    """역대 당첨번호의 번호 발생 패턴을 분석하여 다음 회차 번호를 예측합니다.

    Args:
        historical_data: CSV에서 로드한 당첨번호 dict 리스트
        weights: 각 분석 지표의 가중치 (합 = 1.0)
    """

    DEFAULT_WEIGHTS = {
        'cycle': 0.20,       # 주기 분석
        'gap': 0.25,         # 갭 기반 예측
        'streak': 0.15,      # 스트릭 분석
        'pairing': 0.20,     # 조건부 페어링
        'momentum': 0.20,    # 모멘텀 웨이브
    }

    def __init__(self, historical_data: List[Dict],
                 weights: Optional[Dict[str, float]] = None):
        self.historical_data = historical_data
        self.weights = weights or dict(self.DEFAULT_WEIGHTS)

        # 내부 상태
        self._draws: List[List[int]] = []  # 회차순 정렬된 당첨번호 리스트
        self._num_draws: int = 0
        self._appearance_matrix: Optional[np.ndarray] = None  # (num_draws, 45) 이진행렬

        # 분석 결과 캐시
        self._cycle_scores: Optional[np.ndarray] = None
        self._gap_scores: Optional[np.ndarray] = None
        self._streak_scores: Optional[np.ndarray] = None
        self._pairing_scores: Optional[np.ndarray] = None
        self._momentum_scores: Optional[np.ndarray] = None
        self._final_scores: Optional[np.ndarray] = None
        self._analysis_details: Dict = {}

        self._is_analyzed = False
        self._prepare_data()


    # ─── 데이터 준비 ───────────────────────────────────────────────

    def _prepare_data(self) -> None:
        """역사 데이터를 정렬하고 출현 행렬을 구성합니다."""
        rows = sorted(self.historical_data,
                      key=lambda x: int(x.get('round', 0) or 0))

        self._draws = []
        for row in rows:
            nums = []
            for col in LOTTO_NUMBER_COLUMNS:
                try:
                    n = int(row.get(col, 0))
                    if 1 <= n <= MAX_LOTTO_NUMBER:
                        nums.append(n)
                except (ValueError, TypeError):
                    continue
            if len(nums) == NUM_LOTTO_NUMBERS_TO_PICK:
                self._draws.append(sorted(nums))

        self._num_draws = len(self._draws)

        # 출현 행렬: (회차 수, 45) - 해당 회차에 번호가 나왔으면 1
        if self._num_draws > 0:
            self._appearance_matrix = np.zeros(
                (self._num_draws, MAX_LOTTO_NUMBER), dtype=np.float64)
            for i, draw in enumerate(self._draws):
                for n in draw:
                    self._appearance_matrix[i, n - 1] = 1.0

        _log.info("NextDrawPredictor: %d회차 데이터 준비 완료", self._num_draws)


    # ─── 1. 주기(Cycle) 분석 ──────────────────────────────────────

    def _analyze_cycles(self) -> np.ndarray:
        """각 번호의 출현 주기를 자기상관(ACF) 기반으로 분석합니다.

        번호별 출현 시계열에서 자기상관이 높은 주기(lag)를 탐지하고,
        현재 시점에서 해당 주기에 맞춰 출현이 예상되는 번호에 높은 점수를 부여합니다.
        """
        scores = np.zeros(MAX_LOTTO_NUMBER, dtype=np.float64)

        if self._num_draws < 20:
            return scores

        max_lag = min(50, self._num_draws // 3)

        for num_idx in range(MAX_LOTTO_NUMBER):
            series = self._appearance_matrix[:, num_idx]
            mean_val = series.mean()

            if mean_val == 0 or mean_val == 1:
                continue

            # 자기상관 계산
            centered = series - mean_val
            var = np.sum(centered ** 2)
            if var == 0:
                continue

            best_lag = 0
            best_acf = 0.0

            for lag in range(2, max_lag + 1):
                acf = np.sum(centered[:-lag] * centered[lag:]) / var
                if acf > best_acf:
                    best_acf = acf
                    best_lag = lag

            # 현재 시점에서 주기에 맞는지 확인
            if best_lag > 0 and best_acf > 0.05:
                # 마지막 출현 이후 경과 회차
                last_appearances = np.where(series == 1.0)[0]
                if len(last_appearances) > 0:
                    gap_since_last = self._num_draws - 1 - last_appearances[-1]
                    # 주기에 얼마나 가까운지 (0~1, 1이면 정확히 주기 도달)
                    cycle_proximity = 1.0 - abs((gap_since_last % best_lag) - best_lag) / best_lag
                    scores[num_idx] = best_acf * cycle_proximity

        # 정규화
        max_score = scores.max()
        if max_score > 0:
            scores /= max_score

        self._analysis_details['cycle'] = {
            'description': '자기상관(ACF) 기반 출현 주기 분석',
            'max_lag_searched': max_lag,
        }
        return scores


    # ─── 2. 갭 기반 출현 예측 ─────────────────────────────────────

    def _analyze_gaps(self) -> np.ndarray:
        """번호별 미출현 기간을 역사적 평균 간격과 비교하여 출현 예정 번호를 예측합니다.

        평균 간격 대비 현재 미출현 기간이 길수록 "출현 예정"으로 판단합니다.
        단, 극단적으로 오래 미출현된 번호는 약간의 감소를 적용합니다.
        """
        scores = np.zeros(MAX_LOTTO_NUMBER, dtype=np.float64)

        if self._num_draws < 10:
            return scores

        gap_details = {}

        for num_idx in range(MAX_LOTTO_NUMBER):
            appearances = np.where(self._appearance_matrix[:, num_idx] == 1.0)[0]

            if len(appearances) < 2:
                # 거의 나오지 않은 번호 - 낮은 점수
                scores[num_idx] = 0.1
                continue

            # 역사적 출현 간격 계산
            intervals = np.diff(appearances)
            avg_interval = intervals.mean()
            std_interval = intervals.std() if len(intervals) > 1 else avg_interval * 0.3

            # 현재 미출현 기간
            current_gap = self._num_draws - 1 - appearances[-1]

            # 갭 비율: current_gap / avg_interval
            # 1.0이면 평균 도달, 1.0 초과면 "과대 미출현"
            if avg_interval > 0:
                gap_ratio = current_gap / avg_interval
            else:
                gap_ratio = 0.0

            # 점수 계산: 시그모이드 형태 (1.0 근처에서 급격히 증가)
            if gap_ratio <= 0.3:
                score = 0.1  # 최근 나온 번호는 낮은 점수
            elif gap_ratio <= 0.7:
                score = 0.3
            elif gap_ratio <= 1.0:
                score = 0.6 + (gap_ratio - 0.7) * 1.3  # 0.6 ~ 1.0
            elif gap_ratio <= 1.5:
                score = 1.0  # 평균 초과 - 최고 점수
            else:
                # 너무 오래 미출현 - 약간 감소 (비활성 번호 가능성)
                score = max(0.5, 1.0 - (gap_ratio - 1.5) * 0.2)

            scores[num_idx] = score

            gap_details[num_idx + 1] = {
                'current_gap': int(current_gap),
                'avg_interval': round(float(avg_interval), 1),
                'std_interval': round(float(std_interval), 1),
                'gap_ratio': round(float(gap_ratio), 2),
            }

        # 정규화
        max_score = scores.max()
        if max_score > 0:
            scores /= max_score

        self._analysis_details['gap'] = {
            'description': '미출현 기간 vs 역사적 평균 간격 비교',
            'top_due_numbers': sorted(
                gap_details.items(),
                key=lambda x: x[1]['gap_ratio'], reverse=True
            )[:10],
        }
        return scores


    # ─── 3. 스트릭(Streak) 분석 ──────────────────────────────────

    def _analyze_streaks(self) -> np.ndarray:
        """연속 출현/미출현 패턴을 분석하여 추세를 예측합니다.

        - 핫 스트릭: 최근 연속 출현 중인 번호 (관성 효과)
        - 콜드 스트릭 종료 임박: 오래 미출현 후 출현 가능성 높아지는 패턴
        - 역사적 스트릭 길이 분포를 참조하여 현재 스트릭의 지속/종료 확률 계산
        """
        scores = np.zeros(MAX_LOTTO_NUMBER, dtype=np.float64)

        if self._num_draws < 10:
            return scores

        recent_window = min(30, self._num_draws)
        recent_matrix = self._appearance_matrix[-recent_window:]

        for num_idx in range(MAX_LOTTO_NUMBER):
            full_series = self._appearance_matrix[:, num_idx]

            # 현재 스트릭 상태 확인 (최근에서 역순으로)
            current_streak_type = None  # 'hot' or 'cold'
            current_streak_len = 0

            for i in range(self._num_draws - 1, -1, -1):
                if current_streak_type is None:
                    current_streak_type = 'hot' if full_series[i] == 1.0 else 'cold'
                    current_streak_len = 1
                elif (current_streak_type == 'hot' and full_series[i] == 1.0):
                    current_streak_len += 1
                elif (current_streak_type == 'cold' and full_series[i] == 0.0):
                    current_streak_len += 1
                else:
                    break

            # 역사적 스트릭 길이 분포 계산
            hot_streak_lengths = []
            cold_streak_lengths = []
            streak_len = 0
            streak_type = None

            for val in full_series:
                if streak_type is None:
                    streak_type = 'hot' if val == 1.0 else 'cold'
                    streak_len = 1
                elif (streak_type == 'hot' and val == 1.0) or \
                     (streak_type == 'cold' and val == 0.0):
                    streak_len += 1
                else:
                    if streak_type == 'hot':
                        hot_streak_lengths.append(streak_len)
                    else:
                        cold_streak_lengths.append(streak_len)
                    streak_type = 'hot' if val == 1.0 else 'cold'
                    streak_len = 1

            # 점수 계산
            if current_streak_type == 'hot':
                # 핫 스트릭 - 관성 vs 종료 확률
                if hot_streak_lengths:
                    avg_hot = np.mean(hot_streak_lengths)
                    # 평균 이하면 계속될 가능성, 평균 초과면 종료 임박
                    if current_streak_len <= avg_hot:
                        scores[num_idx] = 0.7 + 0.3 * (current_streak_len / max(1, avg_hot))
                    else:
                        scores[num_idx] = max(0.3, 0.7 - 0.2 * (current_streak_len - avg_hot))
                else:
                    scores[num_idx] = 0.6
            else:
                # 콜드 스트릭 - 종료 임박 여부
                if cold_streak_lengths:
                    avg_cold = np.mean(cold_streak_lengths)
                    # 평균에 가까울수록 종료(출현) 가능성 높음
                    if current_streak_len >= avg_cold * 0.8:
                        proximity = min(1.0, current_streak_len / max(1, avg_cold))
                        scores[num_idx] = 0.5 + 0.5 * proximity
                    else:
                        scores[num_idx] = 0.2 + 0.3 * (current_streak_len / max(1, avg_cold))
                else:
                    scores[num_idx] = 0.3

        # 정규화
        max_score = scores.max()
        if max_score > 0:
            scores /= max_score

        self._analysis_details['streak'] = {
            'description': '연속 출현/미출현 패턴 기반 추세 예측',
        }
        return scores


    # ─── 4. 조건부 페어링 분석 ────────────────────────────────────

    def _analyze_pairing(self) -> np.ndarray:
        """최근 출현 번호를 조건으로, 동반 출현 확률이 높은 번호를 예측합니다.

        최근 3회차 당첨번호를 기반으로 역사적 동반 출현 확률을 계산합니다.
        """
        scores = np.zeros(MAX_LOTTO_NUMBER, dtype=np.float64)

        if self._num_draws < 20:
            return scores

        # 동반 출현 행렬 구성: co_matrix[a][b] = a가 나온 회차 중 b도 나온 횟수
        co_matrix = np.zeros((MAX_LOTTO_NUMBER, MAX_LOTTO_NUMBER), dtype=np.float64)
        appearance_counts = np.zeros(MAX_LOTTO_NUMBER, dtype=np.float64)

        for draw in self._draws:
            for n in draw:
                appearance_counts[n - 1] += 1
                for m in draw:
                    if m != n:
                        co_matrix[n - 1, m - 1] += 1

        # 조건부 확률: P(b|a) = co_matrix[a][b] / appearance_counts[a]
        cond_prob = np.zeros_like(co_matrix)
        for a in range(MAX_LOTTO_NUMBER):
            if appearance_counts[a] > 0:
                cond_prob[a] = co_matrix[a] / appearance_counts[a]

        # 최근 3회차 번호를 조건으로 사용
        recent_window = min(3, self._num_draws)
        recent_numbers = set()
        for draw in self._draws[-recent_window:]:
            recent_numbers.update(draw)

        # 각 번호에 대해 최근 번호들과의 조건부 확률 합산
        for num_idx in range(MAX_LOTTO_NUMBER):
            if (num_idx + 1) in recent_numbers:
                # 최근에 나온 번호는 약간 감소 (연속 출현은 드묾)
                scores[num_idx] = 0.3
                continue

            pair_score = 0.0
            count = 0
            for cond_num in recent_numbers:
                pair_score += cond_prob[cond_num - 1, num_idx]
                count += 1

            if count > 0:
                scores[num_idx] = pair_score / count

        # 정규화
        max_score = scores.max()
        if max_score > 0:
            scores /= max_score

        self._analysis_details['pairing'] = {
            'description': '최근 3회차 번호 기반 조건부 동반 출현 확률',
            'condition_numbers': sorted(recent_numbers),
        }
        return scores


    # ─── 5. 모멘텀 웨이브 분석 ────────────────────────────────────

    def _analyze_momentum(self) -> np.ndarray:
        """단기/중기/장기 이동평균(MA) 기반 모멘텀 분석.

        - 단기 MA(5회차): 직전 트렌드 반영
        - 중기 MA(15회차): 중기 추세
        - 장기 MA(50회차): 기저 빈도

        단기 > 중기 > 장기이면 상승 모멘텀(출현 가능성 증가),
        반대면 하강 모멘텀으로 판단합니다.
        """
        scores = np.zeros(MAX_LOTTO_NUMBER, dtype=np.float64)

        if self._num_draws < 15:
            return scores

        short_window = min(5, self._num_draws)
        mid_window = min(15, self._num_draws)
        long_window = min(50, self._num_draws)

        for num_idx in range(MAX_LOTTO_NUMBER):
            series = self._appearance_matrix[:, num_idx]

            short_ma = series[-short_window:].mean()
            mid_ma = series[-mid_window:].mean()
            long_ma = series[-long_window:].mean()

            # 모멘텀 점수: 단기가 장기보다 높으면 상승 추세
            # 골든크로스 형태: short > mid > long
            if short_ma > mid_ma > long_ma and long_ma > 0:
                # 강한 상승 모멘텀
                momentum = (short_ma / long_ma) * 0.8
            elif short_ma > long_ma:
                # 약한 상승 모멘텀
                momentum = (short_ma / max(0.01, long_ma)) * 0.5
            elif short_ma < mid_ma < long_ma and short_ma > 0:
                # 하강 모멘텀 (데드크로스) - 하지만 반등 가능성
                momentum = 0.3
            else:
                # 중립
                momentum = 0.4 + short_ma * 2.0

            scores[num_idx] = min(1.0, max(0.0, momentum))

        # 정규화
        max_score = scores.max()
        if max_score > 0:
            scores /= max_score

        self._analysis_details['momentum'] = {
            'description': '단기(5)/중기(15)/장기(50) 이동평균 기반 모멘텀',
            'windows': {'short': short_window, 'mid': mid_window, 'long': long_window},
        }
        return scores


    # ─── 종합 분석 실행 ───────────────────────────────────────────

    def analyze(self) -> None:
        """모든 분석을 실행하고 종합 점수를 계산합니다."""
        if self._num_draws < 10:
            _log.warning("데이터가 10회차 미만입니다. 분석 불가.")
            return

        _log.info("다음 회차 패턴 분석 시작 (%d회차 데이터)", self._num_draws)

        self._cycle_scores = self._analyze_cycles()
        self._gap_scores = self._analyze_gaps()
        self._streak_scores = self._analyze_streaks()
        self._pairing_scores = self._analyze_pairing()
        self._momentum_scores = self._analyze_momentum()

        # 가중 앙상블 합산
        w = self.weights
        self._final_scores = (
            self._cycle_scores * w.get('cycle', 0.20) +
            self._gap_scores * w.get('gap', 0.25) +
            self._streak_scores * w.get('streak', 0.15) +
            self._pairing_scores * w.get('pairing', 0.20) +
            self._momentum_scores * w.get('momentum', 0.20)
        )

        self._is_analyzed = True
        _log.info("다음 회차 패턴 분석 완료")

    def get_top_numbers(self, top_n: int = 15) -> List[Tuple[int, float]]:
        """종합 점수 상위 N개 번호를 반환합니다.

        Returns:
            [(번호, 점수), ...] 점수 내림차순
        """
        if not self._is_analyzed:
            self.analyze()

        if self._final_scores is None:
            return []

        indices = np.argsort(self._final_scores)[::-1][:top_n]
        return [(int(idx) + 1, float(self._final_scores[idx])) for idx in indices]


    def get_indicator_scores(self) -> Dict[str, List[Tuple[int, float]]]:
        """각 지표별 상위 10개 번호를 반환합니다."""
        if not self._is_analyzed:
            self.analyze()

        result = {}
        indicators = {
            'cycle': ('주기 분석', self._cycle_scores),
            'gap': ('갭 예측', self._gap_scores),
            'streak': ('스트릭 분석', self._streak_scores),
            'pairing': ('페어링 분석', self._pairing_scores),
            'momentum': ('모멘텀 분석', self._momentum_scores),
        }

        for key, (name, scores) in indicators.items():
            if scores is not None:
                indices = np.argsort(scores)[::-1][:10]
                result[key] = {
                    'name': name,
                    'top_numbers': [(int(idx) + 1, float(scores[idx])) for idx in indices],
                }

        return result

    def predict_next_draw(self, num_sets: int = 5,
                          exclude_numbers: Optional[Set[int]] = None
                          ) -> List[Dict]:
        """다음 회차 예측 번호 조합을 생성합니다.

        Args:
            num_sets: 생성할 조합 수
            exclude_numbers: 제외할 번호 집합

        Returns:
            [{'numbers': [...], 'score': float, 'method': str,
              'indicator_breakdown': {...}}, ...]
        """
        if not self._is_analyzed:
            self.analyze()

        if self._final_scores is None:
            return []

        exclude = exclude_numbers or set()
        scores = self._final_scores.copy()

        # 제외 번호 처리
        for n in exclude:
            if 1 <= n <= MAX_LOTTO_NUMBER:
                scores[n - 1] = 0.0

        # 확률 벡터로 변환
        total = scores.sum()
        if total <= 0:
            return []
        probs = scores / total

        rng = np.random.default_rng()
        results = []
        seen = set()
        max_attempts = num_sets * 500

        prev_draw = get_last_draw_numbers(self.historical_data)

        for _ in range(max_attempts):
            if len(results) >= num_sets:
                break

            # 확률 기반 샘플링 (상위 번호에 편향)
            chosen = rng.choice(MAX_LOTTO_NUMBER, size=6, replace=False, p=probs)
            nums = sorted((chosen + 1).tolist())
            key = tuple(nums)

            if key in seen:
                continue
            seen.add(key)

            # 직전 회차 당첨번호 2개 이상 포함 시 제외
            if exceeds_prev_draw_overlap(nums, prev_draw):
                continue

            # 기본 필터: 합계 범위
            total_sum = sum(nums)
            if not (100 <= total_sum <= 180):
                continue

            # 연속번호 3쌍 이상 배제
            consec = sum(1 for i in range(len(nums) - 1)
                         if nums[i + 1] - nums[i] == 1)
            if consec >= 3:
                continue

            # 조합 점수 계산
            combo_score = sum(self._final_scores[n - 1] for n in nums)

            # 지표별 분해
            breakdown = {}
            if self._cycle_scores is not None:
                breakdown['cycle'] = round(
                    sum(self._cycle_scores[n - 1] for n in nums), 3)
            if self._gap_scores is not None:
                breakdown['gap'] = round(
                    sum(self._gap_scores[n - 1] for n in nums), 3)
            if self._streak_scores is not None:
                breakdown['streak'] = round(
                    sum(self._streak_scores[n - 1] for n in nums), 3)
            if self._pairing_scores is not None:
                breakdown['pairing'] = round(
                    sum(self._pairing_scores[n - 1] for n in nums), 3)
            if self._momentum_scores is not None:
                breakdown['momentum'] = round(
                    sum(self._momentum_scores[n - 1] for n in nums), 3)

            results.append({
                'numbers': nums,
                'score': round(float(combo_score), 4),
                'method': '패턴 예측 (주기+갭+스트릭+페어링+모멘텀)',
                'indicator_breakdown': breakdown,
            })

        # 점수 내림차순 정렬
        results.sort(key=lambda x: x['score'], reverse=True)

        # 다양성 필터: 상위 결과에서 너무 유사한 조합 제거
        filtered = []
        for r in results:
            if len(filtered) >= num_sets:
                break
            ns = set(r['numbers'])
            if all(len(ns & set(f['numbers'])) <= 3 for f in filtered):
                filtered.append(r)

        _log.info("패턴 예측 완료: %d개 조합 생성", len(filtered))
        return filtered


    def get_analysis_report(self) -> Dict:
        """분석 결과 요약 리포트를 반환합니다."""
        if not self._is_analyzed:
            self.analyze()

        report = {
            'total_draws': self._num_draws,
            'latest_draw': self._draws[-1] if self._draws else [],
            'latest_round': int(self.historical_data[-1].get('round', 0))
                if self.historical_data else 0,
            'weights': self.weights,
            'top_15_numbers': self.get_top_numbers(15),
            'indicator_details': self.get_indicator_scores(),
            'analysis_info': self._analysis_details,
        }

        # 최근 당첨번호와의 관계 분석
        if self._draws:
            last_draw = self._draws[-1]
            report['last_draw_analysis'] = {
                'numbers': last_draw,
                'total_sum': sum(last_draw),
                'odd_count': sum(1 for n in last_draw if n % 2 == 1),
            }

        return report

    def get_number_detail(self, number: int) -> Dict:
        """특정 번호의 상세 분석 결과를 반환합니다."""
        if not self._is_analyzed:
            self.analyze()

        if not (1 <= number <= MAX_LOTTO_NUMBER):
            return {}

        idx = number - 1
        appearances = np.where(self._appearance_matrix[:, idx] == 1.0)[0]
        intervals = np.diff(appearances) if len(appearances) > 1 else np.array([])

        detail = {
            'number': number,
            'total_appearances': int(len(appearances)),
            'appearance_rate': round(len(appearances) / max(1, self._num_draws), 4),
            'avg_interval': round(float(intervals.mean()), 1) if len(intervals) > 0 else 0,
            'current_gap': int(self._num_draws - 1 - appearances[-1]) if len(appearances) > 0 else self._num_draws,
            'scores': {
                'cycle': round(float(self._cycle_scores[idx]), 4) if self._cycle_scores is not None else 0,
                'gap': round(float(self._gap_scores[idx]), 4) if self._gap_scores is not None else 0,
                'streak': round(float(self._streak_scores[idx]), 4) if self._streak_scores is not None else 0,
                'pairing': round(float(self._pairing_scores[idx]), 4) if self._pairing_scores is not None else 0,
                'momentum': round(float(self._momentum_scores[idx]), 4) if self._momentum_scores is not None else 0,
                'final': round(float(self._final_scores[idx]), 4) if self._final_scores is not None else 0,
            },
        }
        return detail
