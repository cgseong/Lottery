"""고급 통계 모델링 모듈

마르코프 체인 전이확률, K-Means 군집분석, 동적 핫/콜드 가중치를 구현합니다.
"""
from __future__ import annotations

import numpy as np
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple, Set
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from utils.constants import MAX_LOTTO_NUMBER, NUM_LOTTO_NUMBERS_TO_PICK

try:
    from utils.logging_config import get_logger
    _log = get_logger(__name__)
except ImportError:
    import logging
    _log = logging.getLogger(__name__)



# ═══════════════════════════════════════════════════════════════════════
# 1. 마르코프 체인 분석기
# ═══════════════════════════════════════════════════════════════════════

class MarkovChainAnalyzer:
    """마르코프 체인을 이용한 번호 간 전이 확률 분석.

    각 회차의 당첨번호를 상태(state)로 보고, 이전 회차에서
    다음 회차로의 번호 전이 확률을 계산합니다.

    - 1차 전이: 이전 회차 번호 → 다음 회차 번호 전이 확률
    - 2차 전이: 이전 2회차 패턴 기반 전이 확률
    - 구간 전이: 구간(1-15, 16-30, 31-45) 간 전이 패턴
    """

    def __init__(self, historical_data: List[Dict], order: int = 1):
        """
        Args:
            historical_data: 회차순 정렬된 당첨번호 데이터
            order: 마르코프 체인 차수 (1 또는 2)
        """
        self.historical_data = historical_data
        self.order = min(order, 2)
        self._transition_matrix = np.zeros((MAX_LOTTO_NUMBER + 1, MAX_LOTTO_NUMBER + 1))
        self._section_transition = np.zeros((3, 3))
        self._gap_transition: Dict[int, List[int]] = defaultdict(list)
        self._is_fitted = False
        self._build()


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

    def _get_section(self, num: int) -> int:
        if num <= 15:
            return 0
        elif num <= 30:
            return 1
        return 2

    def _build(self) -> None:
        """전이 행렬을 구축합니다."""
        if len(self.historical_data) < 2:
            return

        rows = sorted(self.historical_data,
                      key=lambda x: int(x.get('round', 0) or 0))
        prev_nums = None

        for row in rows:
            curr_nums = self._extract_numbers(row)
            if not curr_nums:
                continue

            if prev_nums is not None:
                # 1차 전이 행렬: prev → curr
                for p in prev_nums:
                    for c in curr_nums:
                        self._transition_matrix[p][c] += 1
                # 구간 전이
                for p in prev_nums:
                    for c in curr_nums:
                        self._section_transition[self._get_section(p)][self._get_section(c)] += 1
                # 간격(gap) 전이: 이전 번호와 현재 번호의 차이 패턴
                for p in prev_nums:
                    for c in curr_nums:
                        self._gap_transition[p].append(c - p)

            prev_nums = curr_nums

        # 행별 정규화 → 확률 행렬
        for i in range(1, MAX_LOTTO_NUMBER + 1):
            row_sum = self._transition_matrix[i].sum()
            if row_sum > 0:
                self._transition_matrix[i] /= row_sum

        sec_sums = self._section_transition.sum(axis=1, keepdims=True)
        sec_sums[sec_sums == 0] = 1
        self._section_transition /= sec_sums

        self._is_fitted = True


    def get_transition_probabilities(self, current_numbers: List[int]) -> np.ndarray:
        """현재 당첨번호 기반으로 다음 회차 각 번호의 전이 확률 벡터를 반환합니다.

        Args:
            current_numbers: 최근 회차 당첨번호 6개

        Returns:
            shape=(45,) 확률 벡터 (인덱스 i = 번호 i+1)
        """
        if not self._is_fitted:
            return np.ones(MAX_LOTTO_NUMBER) / MAX_LOTTO_NUMBER

        probs = np.zeros(MAX_LOTTO_NUMBER)
        for num in current_numbers:
            if 1 <= num <= MAX_LOTTO_NUMBER:
                probs += self._transition_matrix[num][1:MAX_LOTTO_NUMBER + 1]

        total = probs.sum()
        if total > 0:
            probs /= total
        else:
            probs = np.ones(MAX_LOTTO_NUMBER) / MAX_LOTTO_NUMBER
        return probs

    def get_section_forecast(self, current_numbers: List[int]) -> Dict[str, float]:
        """다음 회차 구간별 예상 분포를 반환합니다."""
        if not self._is_fitted:
            return {'1-15': 0.33, '16-30': 0.33, '31-45': 0.34}

        section_counts = np.zeros(3)
        for n in current_numbers:
            section_counts[self._get_section(n)] += 1
        section_counts /= max(section_counts.sum(), 1)

        forecast = section_counts @ self._section_transition
        total = forecast.sum()
        if total > 0:
            forecast /= total

        return {
            '1-15': float(forecast[0]),
            '16-30': float(forecast[1]),
            '31-45': float(forecast[2]),
        }

    def predict_next_numbers(self, current_numbers: List[int],
                             top_n: int = 15) -> List[Tuple[int, float]]:
        """전이 확률 기반 다음 회차 유력 번호 상위 N개를 반환합니다."""
        probs = self.get_transition_probabilities(current_numbers)
        indices = np.argsort(probs)[::-1][:top_n]
        return [(int(idx + 1), float(probs[idx])) for idx in indices]



# ═══════════════════════════════════════════════════════════════════════
# 2. 군집 분석 (K-Means 기반 번호 조합 패턴 탐색)
# ═══════════════════════════════════════════════════════════════════════

class ClusterPatternAnalyzer:
    """K-Means 군집분석을 통한 당첨번호 조합 패턴 탐색.

    각 회차의 당첨번호를 45차원 이진 벡터 + 파생 피처로 변환하여
    군집화합니다. 최근 회차가 속한 군집의 중심에 가까운 조합을
    우선 추천합니다.
    """

    def __init__(self, historical_data: List[Dict], n_clusters: int = 8):
        self.historical_data = historical_data
        self.n_clusters = n_clusters
        self._kmeans: Optional[KMeans] = None
        self._scaler: Optional[StandardScaler] = None
        self._features: Optional[np.ndarray] = None
        self._labels: Optional[np.ndarray] = None
        self._cluster_centers: Optional[np.ndarray] = None
        self._is_fitted = False
        self._fit()

    def _row_to_features(self, row: Dict) -> Optional[np.ndarray]:
        """회차 데이터를 피처 벡터로 변환 (45차원 이진 + 파생 6차원 = 51차원)."""
        nums = []
        for i in range(1, 7):
            try:
                n = int(row.get(f'num{i}', 0))
                if 1 <= n <= MAX_LOTTO_NUMBER:
                    nums.append(n)
            except (ValueError, TypeError):
                continue
        if len(nums) != 6:
            return None

        # 45차원 이진 벡터
        binary = np.zeros(MAX_LOTTO_NUMBER)
        for n in nums:
            binary[n - 1] = 1.0

        # 파생 피처
        total_sum = sum(nums)
        odd_count = sum(1 for n in nums if n % 2 != 0)
        low_count = sum(1 for n in nums if n <= 15)
        mid_count = sum(1 for n in nums if 16 <= n <= 30)
        high_count = sum(1 for n in nums if n >= 31)
        consec = sum(1 for a, b in zip(sorted(nums), sorted(nums)[1:]) if b - a == 1)

        derived = np.array([total_sum / 270.0, odd_count / 6.0,
                            low_count / 6.0, mid_count / 6.0,
                            high_count / 6.0, consec / 5.0])
        return np.concatenate([binary, derived])


    def _fit(self) -> None:
        """K-Means 군집화를 수행합니다."""
        if len(self.historical_data) < self.n_clusters * 3:
            _log.warning("군집분석에 필요한 데이터가 부족합니다.")
            return

        features = []
        for row in self.historical_data:
            feat = self._row_to_features(row)
            if feat is not None:
                features.append(feat)

        if len(features) < self.n_clusters * 3:
            return

        self._features = np.array(features)
        self._scaler = StandardScaler()
        scaled = self._scaler.fit_transform(self._features)

        self._kmeans = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
        self._labels = self._kmeans.fit_predict(scaled)
        self._cluster_centers = self._kmeans.cluster_centers_
        self._is_fitted = True
        _log.info("군집분석 완료: %d개 클러스터, %d개 샘플", self.n_clusters, len(features))

    def get_recent_cluster(self, recent_n: int = 5) -> int:
        """최근 N회차가 가장 많이 속한 군집 ID를 반환합니다."""
        if not self._is_fitted or self._labels is None:
            return 0
        recent_labels = self._labels[-recent_n:]
        counter = Counter(recent_labels)
        return counter.most_common(1)[0][0]

    def get_cluster_profile(self, cluster_id: int) -> Dict:
        """특정 군집의 프로파일(번호 빈도, 특성)을 반환합니다."""
        if not self._is_fitted:
            return {}

        mask = self._labels == cluster_id
        cluster_features = self._features[mask]

        if len(cluster_features) == 0:
            return {}

        # 45차원 이진 평균 → 번호별 출현 확률
        binary_mean = cluster_features[:, :MAX_LOTTO_NUMBER].mean(axis=0)
        top_numbers = np.argsort(binary_mean)[::-1][:10]

        return {
            'cluster_id': cluster_id,
            'sample_count': int(mask.sum()),
            'top_numbers': [(int(idx + 1), float(binary_mean[idx])) for idx in top_numbers],
            'avg_sum': float(cluster_features[:, 45].mean() * 270),
            'avg_odd_ratio': float(cluster_features[:, 46].mean()),
            'avg_consec': float(cluster_features[:, 50].mean() * 5),
        }


    def score_combination(self, numbers: List[int]) -> float:
        """조합이 최근 군집 중심에 얼마나 가까운지 점수화합니다 (0~1)."""
        if not self._is_fitted or self._scaler is None:
            return 0.5

        # 조합을 피처 벡터로 변환
        binary = np.zeros(MAX_LOTTO_NUMBER)
        for n in numbers:
            binary[n - 1] = 1.0
        total_sum = sum(numbers)
        odd_count = sum(1 for n in numbers if n % 2 != 0)
        low_count = sum(1 for n in numbers if n <= 15)
        mid_count = sum(1 for n in numbers if 16 <= n <= 30)
        high_count = sum(1 for n in numbers if n >= 31)
        consec = sum(1 for a, b in zip(sorted(numbers), sorted(numbers)[1:]) if b - a == 1)
        derived = np.array([total_sum / 270.0, odd_count / 6.0,
                            low_count / 6.0, mid_count / 6.0,
                            high_count / 6.0, consec / 5.0])
        feat = np.concatenate([binary, derived]).reshape(1, -1)
        scaled = self._scaler.transform(feat)

        # 최근 군집 중심과의 유클리드 거리 → 점수 변환
        recent_cluster = self.get_recent_cluster()
        center = self._cluster_centers[recent_cluster].reshape(1, -1)
        dist = float(np.linalg.norm(scaled - center))

        # 거리를 0~1 점수로 변환 (가우시안 커널)
        score = float(np.exp(-0.5 * (dist / 5.0) ** 2))
        return score

    def get_cluster_recommended_numbers(self, top_n: int = 15) -> List[Tuple[int, float]]:
        """최근 군집에서 출현 확률 높은 번호 상위 N개를 반환합니다."""
        if not self._is_fitted:
            return [(i, 1.0 / MAX_LOTTO_NUMBER) for i in range(1, top_n + 1)]

        cluster_id = self.get_recent_cluster()
        profile = self.get_cluster_profile(cluster_id)
        return profile.get('top_numbers', [])[:top_n]



# ═══════════════════════════════════════════════════════════════════════
# 3. 동적 핫/콜드 번호 가중치 엔진
# ═══════════════════════════════════════════════════════════════════════

class DynamicHotColdWeighter:
    """핫/콜드 번호의 동적 가중치 적용 엔진.

    단순 빈도가 아닌, 시간 감쇠 + 모멘텀 + 평균회귀를 결합하여
    각 번호의 '현재 온도'를 동적으로 계산합니다.

    - 핫 모멘텀: 최근 연속 출현 시 가속도 부여
    - 콜드 반등: 장기 미출현 번호의 평균회귀 기대값
    - 온도 지수: 핫/콜드를 -1 ~ +1로 정규화
    """

    def __init__(self, historical_data: List[Dict],
                 decay_rate: float = 0.05,
                 momentum_window: int = 10,
                 reversion_strength: float = 0.3):
        """
        Args:
            decay_rate: 시간 감쇠율 (높을수록 최근에 민감)
            momentum_window: 모멘텀 계산 윈도우
            reversion_strength: 평균회귀 강도 (0~1)
        """
        self.historical_data = historical_data
        self.decay_rate = decay_rate
        self.momentum_window = momentum_window
        self.reversion_strength = reversion_strength
        self._temperatures: np.ndarray = np.zeros(MAX_LOTTO_NUMBER)
        self._momentum: np.ndarray = np.zeros(MAX_LOTTO_NUMBER)
        self._last_seen: np.ndarray = np.zeros(MAX_LOTTO_NUMBER)
        self._total_rounds = 0
        self._compute()


    def _compute(self) -> None:
        """전체 데이터를 순차 처리하여 온도·모멘텀을 계산합니다."""
        rows = sorted(self.historical_data,
                      key=lambda x: int(x.get('round', 0) or 0))
        if not rows:
            return

        self._total_rounds = len(rows)
        # 각 번호의 출현 회차 인덱스 기록
        appearances: Dict[int, List[int]] = defaultdict(list)

        for idx, row in enumerate(rows):
            for i in range(1, 7):
                try:
                    n = int(row.get(f'num{i}', 0))
                    if 1 <= n <= MAX_LOTTO_NUMBER:
                        appearances[n].append(idx)
                except (ValueError, TypeError):
                    continue

        n = self._total_rounds
        expected_freq = 6.0 / MAX_LOTTO_NUMBER  # 기대 출현율 ≈ 0.133

        for num in range(1, MAX_LOTTO_NUMBER + 1):
            app = appearances.get(num, [])
            idx = num - 1

            # 시간 가중 빈도 (지수 감쇠)
            weighted_count = sum(
                np.exp(-self.decay_rate * (n - 1 - t)) for t in app
            )

            # 모멘텀: 최근 window 내 출현 횟수 변화율
            recent_app = [t for t in app if t >= n - self.momentum_window]
            older_app = [t for t in app if n - 2 * self.momentum_window <= t < n - self.momentum_window]
            recent_rate = len(recent_app) / max(self.momentum_window, 1)
            older_rate = len(older_app) / max(self.momentum_window, 1)
            self._momentum[idx] = recent_rate - older_rate

            # 마지막 출현 이후 경과
            if app:
                self._last_seen[idx] = n - 1 - app[-1]
            else:
                self._last_seen[idx] = n

            # 평균회귀 보정: 오래 안 나온 번호는 양의 보정
            gap = self._last_seen[idx]
            expected_gap = 1.0 / expected_freq  # ≈ 7.5
            reversion_bonus = self.reversion_strength * max(0, gap - expected_gap) / expected_gap

            # 종합 온도: 가중빈도 정규화 + 모멘텀 + 평균회귀
            max_weighted = n * expected_freq  # 이론적 최대 가중 빈도
            norm_freq = weighted_count / max(max_weighted, 1) - 0.5  # -0.5 ~ +0.5

            self._temperatures[idx] = np.clip(
                norm_freq * 0.5 + self._momentum[idx] * 0.3 + reversion_bonus * 0.2,
                -1.0, 1.0
            )


    def get_temperatures(self) -> Dict[int, float]:
        """모든 번호의 온도 지수를 반환합니다 (-1: 극콜드, +1: 극핫)."""
        return {num: float(self._temperatures[num - 1])
                for num in range(1, MAX_LOTTO_NUMBER + 1)}

    def get_hot_numbers(self, top_n: int = 10) -> List[Tuple[int, float]]:
        """핫 번호 상위 N개 (온도 높은 순)."""
        temps = self.get_temperatures()
        sorted_nums = sorted(temps.items(), key=lambda x: x[1], reverse=True)
        return sorted_nums[:top_n]

    def get_cold_numbers(self, top_n: int = 10) -> List[Tuple[int, float]]:
        """콜드 번호 상위 N개 (온도 낮은 순)."""
        temps = self.get_temperatures()
        sorted_nums = sorted(temps.items(), key=lambda x: x[1])
        return sorted_nums[:top_n]

    def get_sampling_weights(self, strategy: str = 'balanced',
                             exclude: Optional[Set[int]] = None) -> np.ndarray:
        """전략별 샘플링 가중치 벡터를 반환합니다.

        Args:
            strategy: 'hot' | 'cold' | 'balanced' | 'contrarian'
            exclude: 제외할 번호 집합

        Returns:
            shape=(45,) 정규화된 확률 벡터
        """
        exclude = exclude or set()
        weights = np.zeros(MAX_LOTTO_NUMBER)

        for num in range(1, MAX_LOTTO_NUMBER + 1):
            if num in exclude:
                continue
            temp = self._temperatures[num - 1]

            if strategy == 'hot':
                # 핫 번호 선호: 온도가 높을수록 가중치 증가
                weights[num - 1] = max(0.01, 0.5 + temp)
            elif strategy == 'cold':
                # 콜드 번호 선호 (평균회귀 전략)
                weights[num - 1] = max(0.01, 0.5 - temp)
            elif strategy == 'contrarian':
                # 역발상: 극단적 핫/콜드 모두 기피, 중간 온도 선호
                weights[num - 1] = max(0.01, 1.0 - abs(temp))
            else:  # balanced
                # 균형: 핫 60% + 콜드 회귀 40%
                hot_w = max(0, 0.5 + temp)
                cold_w = max(0, self._last_seen[num - 1] / 30.0)
                weights[num - 1] = hot_w * 0.6 + cold_w * 0.4

        total = weights.sum()
        if total > 0:
            weights /= total
        else:
            weights = np.ones(MAX_LOTTO_NUMBER) / MAX_LOTTO_NUMBER
        return weights

    def score_combination(self, numbers: List[int], strategy: str = 'balanced') -> float:
        """조합의 전략 적합도를 0~1로 점수화합니다."""
        weights = self.get_sampling_weights(strategy)
        score = sum(weights[n - 1] for n in numbers if 1 <= n <= MAX_LOTTO_NUMBER)
        # 6개 번호의 가중치 합을 이론적 최대(상위 6개 선택 시)로 정규화
        top6 = np.sort(weights)[-6:].sum()
        if top6 > 0:
            return float(min(1.0, score / top6))
        return 0.5
