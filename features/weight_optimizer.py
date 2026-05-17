from __future__ import annotations

from typing import Dict, List

from analyzers.statistical_analyzer import StatisticalAnalyzer, _DEFAULT_SCORE_WEIGHTS
from utils.logging_config import get_logger

_log = get_logger(__name__)

# scipy 선택적 의존성 (없으면 그리드 서치로 폴백)
try:
    from scipy.optimize import differential_evolution
    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False

# 그리드 서치용 후보 가중치 (scipy 없을 때 폴백)
_WEIGHT_CANDIDATES: List[Dict[str, float]] = [
    {'frequency': 0.45, 'sum': 0.20, 'trend': 0.20, 'distribution': 0.15},
    {'frequency': 0.50, 'sum': 0.20, 'trend': 0.15, 'distribution': 0.15},
    {'frequency': 0.40, 'sum': 0.25, 'trend': 0.20, 'distribution': 0.15},
    {'frequency': 0.45, 'sum': 0.15, 'trend': 0.25, 'distribution': 0.15},
    {'frequency': 0.35, 'sum': 0.25, 'trend': 0.25, 'distribution': 0.15},
    {'frequency': 0.50, 'sum': 0.15, 'trend': 0.20, 'distribution': 0.15},
    {'frequency': 0.40, 'sum': 0.30, 'trend': 0.15, 'distribution': 0.15},
    {'frequency': 0.55, 'sum': 0.15, 'trend': 0.15, 'distribution': 0.15},
    {'frequency': 0.45, 'sum': 0.25, 'trend': 0.15, 'distribution': 0.15},
    {'frequency': 0.40, 'sum': 0.20, 'trend': 0.25, 'distribution': 0.15},
]


class WeightOptimizer:
    """백테스트 결과를 기반으로 최적 점수 가중치를 탐색합니다.

    scipy가 설치되어 있으면 differential_evolution으로 연속 공간 탐색,
    없으면 기존 그리드 서치로 폴백합니다.

    Rolling Optimization: 여러 검증 구간을 슬라이딩하여
    과적합을 방지하고 안정적인 최적 가중치를 도출합니다.
    """

    def __init__(self, historical_data: List[Dict], test_rounds: int = 40):
        self.historical_data = historical_data
        self.test_rounds = test_rounds

    def optimize(self) -> Dict[str, float]:
        """최적 가중치를 탐색하여 반환합니다."""
        min_required = self.test_rounds + 50
        if len(self.historical_data) < min_required:
            _log.warning("데이터가 부족합니다 (최소 %d회차 필요). 기본 가중치 사용.", min_required)
            return dict(_DEFAULT_SCORE_WEIGHTS)

        if _HAS_SCIPY:
            return self._optimize_scipy()
        else:
            _log.info("scipy 미설치 — 그리드 서치로 최적화합니다.")
            return self._optimize_grid()

    def _optimize_scipy(self) -> Dict[str, float]:
        """scipy differential_evolution 기반 연속 공간 최적화.

        Rolling window: 50회차 간격으로 슬라이딩하며 각 구간의
        3매치 비율을 합산 → 전체 구간에 걸쳐 안정적인 가중치 도출.
        """
        _log.info("differential_evolution 기반 롤링 최적화 시작")

        # 학습 데이터 / 검증 데이터 분리 (최소 50회 간격)
        data = self.historical_data
        n = len(data)
        window_size = min(self.test_rounds, 40)
        step = max(20, window_size // 2)

        # 롤링 검증 구간들: [(train_end, test_start, test_end), ...]
        validation_splits = []
        for test_end_offset in range(window_size, min(n - 50, window_size * 4), step):
            test_end = n - (test_end_offset - window_size)
            test_start = test_end - window_size
            if test_start < 50:
                break
            validation_splits.append((test_start, test_start, test_end))

        if not validation_splits:
            validation_splits = [(n - self.test_rounds, n - self.test_rounds, n)]

        _log.info("롤링 검증 구간 %d개 사용", len(validation_splits))

        # 기본 분석기로 후보 조합 사전 생성 (전체 학습 데이터 기반)
        train_cutoff = validation_splits[0][0]
        base_analyzer = StatisticalAnalyzer(data[:train_cutoff])
        base_analyzer.analyze_frequency()
        base_analyzer.analyze_sum_range()
        base_analyzer.analyze_recent_trends()

        candidates = base_analyzer.generate_recommendations(
            num_recommendations=30, verbose=False
        ) + base_analyzer.generate_unique_recommendations(
            num_recommendations=30
        )
        candidate_numbers = [c['numbers'] for c in candidates]

        if not candidate_numbers:
            _log.warning("후보 조합 생성 실패. 기본 가중치 사용.")
            return dict(_DEFAULT_SCORE_WEIGHTS)

        def objective(params):
            """목적함수: -3매치율 (최소화)"""
            raw = params[:4]
            total = sum(raw)
            if total <= 0:
                return 1.0
            w = {
                'frequency': raw[0] / total,
                'sum': raw[1] / total,
                'trend': raw[2] / total,
                'distribution': raw[3] / total,
            }

            hits = 0
            total_evals = 0

            for _, test_start, test_end in validation_splits:
                test_data = data[test_start:test_end]

                for actual_row in test_data:
                    try:
                        actual = {int(actual_row[f'번호{j}']) for j in range(1, 7)}
                    except (KeyError, ValueError):
                        continue

                    scored = sorted(
                        candidate_numbers,
                        key=lambda nums, _w=w: base_analyzer.calculate_score(nums, _w),
                        reverse=True
                    )
                    for nums in scored[:3]:
                        if len(set(nums) & actual) >= 3:
                            hits += 1
                        total_evals += 1

            rate = hits / max(1, total_evals)
            return -rate  # 최소화이므로 음수

        # 탐색 범위: 각 가중치 0.05 ~ 0.70
        bounds = [(0.05, 0.70)] * 4

        result = differential_evolution(
            objective,
            bounds,
            seed=42,
            maxiter=15,
            popsize=5,
            tol=1e-3,
            polish=False,
            init='sobol',
        )

        raw = result.x
        total = sum(raw)
        best_weights = {
            'frequency': round(raw[0] / total, 4),
            'sum': round(raw[1] / total, 4),
            'trend': round(raw[2] / total, 4),
            'distribution': round(raw[3] / total, 4),
        }
        best_rate = -result.fun

        _log.info(
            "최적 가중치 (DE): frequency=%.3f, sum=%.3f, trend=%.3f, distribution=%.3f  3매치율=%.4f",
            best_weights['frequency'], best_weights['sum'],
            best_weights['trend'], best_weights['distribution'], best_rate
        )

        return best_weights

    def _optimize_grid(self) -> Dict[str, float]:
        """그리드 서치 기반 최적화 (scipy 없을 때 폴백)."""
        train_data = self.historical_data[:-self.test_rounds]
        test_data = self.historical_data[-self.test_rounds:]

        _log.info("학습 데이터: %d회차 / 검증 데이터: %d회차", len(train_data), len(test_data))

        base_analyzer = StatisticalAnalyzer(train_data)
        base_analyzer.analyze_frequency()
        base_analyzer.analyze_sum_range()
        base_analyzer.analyze_recent_trends()

        candidates = base_analyzer.generate_recommendations(
            num_recommendations=100, verbose=False
        ) + base_analyzer.generate_unique_recommendations(
            num_recommendations=100
        )
        candidate_numbers = [c['numbers'] for c in candidates]

        if not candidate_numbers:
            _log.warning("후보 조합 생성 실패. 기본 가중치 사용.")
            return dict(_DEFAULT_SCORE_WEIGHTS)

        _log.info("후보 조합 %d개 생성 완료, %d개 가중치 조합 평가 중...",
                  len(candidate_numbers), len(_WEIGHT_CANDIDATES))

        best_weights = dict(_DEFAULT_SCORE_WEIGHTS)
        best_rate = 0.0

        for i, w_combo in enumerate(_WEIGHT_CANDIDATES):
            hits = 0
            total = 0

            for actual_row in test_data:
                try:
                    actual = {int(actual_row[f'번호{j}']) for j in range(1, 7)}
                except (KeyError, ValueError):
                    continue

                scored = sorted(
                    candidate_numbers,
                    key=lambda nums: base_analyzer.calculate_score(nums, w_combo),
                    reverse=True
                )
                for nums in scored[:3]:
                    if len(set(nums) & actual) >= 3:
                        hits += 1
                    total += 1

            rate = hits / max(1, total)

            if rate > best_rate:
                best_rate = rate
                best_weights = dict(w_combo)

            label = "기본값" if i == 0 else f"조합{i:02d}"
            _log.debug("[%s] f=%.2f s=%.2f t=%.2f d=%.2f → 3매치율 %.4f",
                       label, w_combo['frequency'], w_combo['sum'],
                       w_combo['trend'], w_combo['distribution'], rate)

        _log.info("최적 가중치: frequency=%.2f, sum=%.2f, trend=%.2f, distribution=%.2f  3매치율=%.4f",
                  best_weights['frequency'], best_weights['sum'],
                  best_weights['trend'], best_weights['distribution'], best_rate)

        return best_weights
