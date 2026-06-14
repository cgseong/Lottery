"""검증 및 피드백 루프 강화 모듈

롤링 백테스트, A/B 테스트 프레임워크, 전략 성능 대시보드를 구현합니다.
다양한 전략의 성능을 정량적으로 평가하고 최적의 방안을 선택합니다.
"""
from __future__ import annotations

import time
import numpy as np
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from utils.constants import MAX_LOTTO_NUMBER, NUM_LOTTO_NUMBERS_TO_PICK

try:
    from utils.logging_config import get_logger
    _log = get_logger(__name__)
except ImportError:
    import logging
    _log = logging.getLogger(__name__)



# ═══════════════════════════════════════════════════════════════════════
# 데이터 구조
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class BacktestResult:
    """단일 백테스트 실행 결과."""
    strategy_name: str
    total_rounds: int = 0
    total_predictions: int = 0
    hit_distribution: Dict[int, int] = field(default_factory=lambda: {i: 0 for i in range(7)})
    avg_hits: float = 0.0
    hit_rate_3plus: float = 0.0
    hit_rate_4plus: float = 0.0
    hit_rate_5plus: float = 0.0
    execution_time_sec: float = 0.0
    details: List[Dict] = field(default_factory=list)

    @property
    def summary(self) -> Dict:
        return {
            'strategy': self.strategy_name,
            'rounds': self.total_rounds,
            'predictions': self.total_predictions,
            'avg_hits': round(self.avg_hits, 4),
            'hit_rate_3+': round(self.hit_rate_3plus, 4),
            'hit_rate_4+': round(self.hit_rate_4plus, 4),
            'hit_rate_5+': round(self.hit_rate_5plus, 4),
            'hit_distribution': self.hit_distribution,
            'time_sec': round(self.execution_time_sec, 2),
        }


@dataclass
class ABTestResult:
    """A/B 테스트 결과."""
    strategy_a: str
    strategy_b: str
    result_a: BacktestResult
    result_b: BacktestResult
    winner: str = ''
    improvement_pct: float = 0.0
    statistical_significance: float = 0.0

    def __post_init__(self):
        rate_a = self.result_a.hit_rate_3plus
        rate_b = self.result_b.hit_rate_3plus
        if rate_a >= rate_b:
            self.winner = self.strategy_a
            self.improvement_pct = ((rate_a - rate_b) / max(rate_b, 1e-10)) * 100
        else:
            self.winner = self.strategy_b
            self.improvement_pct = ((rate_b - rate_a) / max(rate_a, 1e-10)) * 100
        # 간이 유의성 (표본 비율 차이 z-검정)
        n = max(self.result_a.total_predictions, 1)
        p_pool = (rate_a + rate_b) / 2
        if p_pool > 0 and p_pool < 1:
            se = (2 * p_pool * (1 - p_pool) / n) ** 0.5
            z = abs(rate_a - rate_b) / max(se, 1e-10)
            self.statistical_significance = min(1.0, z / 3.0)  # 대략적 정규화



# ═══════════════════════════════════════════════════════════════════════
# 1. 롤링 백테스터
# ═══════════════════════════════════════════════════════════════════════

class RollingBacktester:
    """롤링 윈도우 기반 시계열 백테스트.

    과거 데이터를 시간순으로 슬라이딩하며, 각 시점에서
    '미래를 모르는 상태'로 전략을 실행하고 실제 결과와 비교합니다.

    특징:
        - Walk-forward: 학습 데이터와 검증 데이터의 시간적 분리 보장
        - 롤링 윈도우: 고정 크기 학습 윈도우를 슬라이딩
        - 다중 예측: 각 시점에서 여러 조합을 예측하여 최고 매치 기록
        - 상세 로그: 각 회차별 예측/실제 비교 기록
    """

    def __init__(self, historical_data: List[Dict],
                 train_window: int = 200,
                 step: int = 1,
                 predictions_per_round: int = 5):
        """
        Args:
            historical_data: 전체 역사 데이터 (회차순)
            train_window: 학습에 사용할 회차 수
            step: 슬라이딩 간격
            predictions_per_round: 각 시점에서 생성할 예측 조합 수
        """
        self.historical_data = sorted(
            historical_data, key=lambda x: int(x.get('round', 0) or 0))
        self.train_window = train_window
        self.step = step
        self.predictions_per_round = predictions_per_round

    def _extract_numbers(self, row: Dict) -> set:
        nums = set()
        for i in range(1, 7):
            try:
                n = int(row.get(f'num{i}', 0))
                if 1 <= n <= MAX_LOTTO_NUMBER:
                    nums.add(n)
            except (ValueError, TypeError):
                continue
        return nums


    def run(self, strategy_fn: Callable[[List[Dict]], List[List[int]]],
            strategy_name: str = 'unknown',
            max_rounds: Optional[int] = None) -> BacktestResult:
        """백테스트를 실행합니다.

        Args:
            strategy_fn: 학습 데이터를 받아 추천 조합 리스트를 반환하는 함수.
                         시그니처: (train_data: List[Dict]) -> List[List[int]]
            strategy_name: 전략 이름
            max_rounds: 최대 테스트 회차 (None이면 전체)

        Returns:
            BacktestResult 객체
        """
        start_time = time.time()
        data = self.historical_data
        n = len(data)

        if n <= self.train_window + 1:
            _log.warning("데이터 부족: %d회차 (최소 %d 필요)", n, self.train_window + 2)
            return BacktestResult(strategy_name=strategy_name)

        result = BacktestResult(strategy_name=strategy_name)
        test_start = self.train_window
        test_end = min(n - 1, test_start + max_rounds * self.step) if max_rounds else n - 1

        for idx in range(test_start, test_end, self.step):
            train_data = data[max(0, idx - self.train_window):idx]
            actual_row = data[idx]
            actual = self._extract_numbers(actual_row)

            if len(actual) != 6:
                continue

            try:
                predictions = strategy_fn(train_data)
                if not predictions:
                    continue
            except Exception as e:
                _log.debug("전략 실행 오류 (회차 %d): %s", idx, e)
                continue

            # 각 예측 조합의 매치 수 기록
            best_hit = 0
            for pred_nums in predictions[:self.predictions_per_round]:
                hits = len(set(pred_nums) & actual)
                best_hit = max(best_hit, hits)
                result.hit_distribution[hits] = result.hit_distribution.get(hits, 0) + 1
                result.total_predictions += 1

            result.total_rounds += 1
            result.details.append({
                'round_idx': idx,
                'round_no': actual_row.get('round', '?'),
                'actual': sorted(actual),
                'best_hit': best_hit,
            })

        # 통계 계산
        if result.total_predictions > 0:
            total_hits = sum(k * v for k, v in result.hit_distribution.items())
            result.avg_hits = total_hits / result.total_predictions
            result.hit_rate_3plus = sum(
                v for k, v in result.hit_distribution.items() if k >= 3
            ) / result.total_predictions
            result.hit_rate_4plus = sum(
                v for k, v in result.hit_distribution.items() if k >= 4
            ) / result.total_predictions
            result.hit_rate_5plus = sum(
                v for k, v in result.hit_distribution.items() if k >= 5
            ) / result.total_predictions

        result.execution_time_sec = time.time() - start_time
        _log.info("[%s] 백테스트 완료: %d회차, 3+적중률=%.4f, 소요시간=%.1fs",
                  strategy_name, result.total_rounds,
                  result.hit_rate_3plus, result.execution_time_sec)
        return result



# ═══════════════════════════════════════════════════════════════════════
# 2. A/B 테스트 프레임워크
# ═══════════════════════════════════════════════════════════════════════

class ABTestFramework:
    """두 전략을 동일 조건에서 비교하는 A/B 테스트 프레임워크.

    동일한 학습/테스트 분할에서 두 전략을 실행하여
    통계적으로 유의미한 차이가 있는지 평가합니다.
    """

    def __init__(self, historical_data: List[Dict],
                 train_window: int = 200,
                 predictions_per_round: int = 5):
        self.historical_data = historical_data
        self.train_window = train_window
        self.predictions_per_round = predictions_per_round

    def compare(self,
                strategy_a: Callable[[List[Dict]], List[List[int]]],
                strategy_b: Callable[[List[Dict]], List[List[int]]],
                name_a: str = 'Strategy A',
                name_b: str = 'Strategy B',
                max_rounds: Optional[int] = None) -> ABTestResult:
        """두 전략을 비교합니다.

        Args:
            strategy_a, strategy_b: 전략 함수
            name_a, name_b: 전략 이름
            max_rounds: 최대 테스트 회차

        Returns:
            ABTestResult 객체
        """
        _log.info("A/B 테스트 시작: [%s] vs [%s]", name_a, name_b)

        backtester = RollingBacktester(
            self.historical_data,
            train_window=self.train_window,
            predictions_per_round=self.predictions_per_round,
        )

        result_a = backtester.run(strategy_a, name_a, max_rounds)
        result_b = backtester.run(strategy_b, name_b, max_rounds)

        ab_result = ABTestResult(
            strategy_a=name_a,
            strategy_b=name_b,
            result_a=result_a,
            result_b=result_b,
        )

        _log.info("A/B 테스트 결과: 승자=%s (개선율=%.1f%%, 유의성=%.2f)",
                  ab_result.winner, ab_result.improvement_pct,
                  ab_result.statistical_significance)

        return ab_result

    def tournament(self,
                   strategies: Dict[str, Callable[[List[Dict]], List[List[int]]]],
                   max_rounds: Optional[int] = None) -> Dict:
        """여러 전략을 라운드 로빈으로 비교하는 토너먼트.

        Args:
            strategies: {이름: 전략함수} 딕셔너리

        Returns:
            {'rankings': [...], 'results': [...], 'best': str}
        """
        _log.info("토너먼트 시작: %d개 전략 참가", len(strategies))

        backtester = RollingBacktester(
            self.historical_data,
            train_window=self.train_window,
            predictions_per_round=self.predictions_per_round,
        )

        all_results: Dict[str, BacktestResult] = {}
        for name, fn in strategies.items():
            result = backtester.run(fn, name, max_rounds)
            all_results[name] = result

        # 순위 결정 (3+ 적중률 기준)
        rankings = sorted(
            all_results.items(),
            key=lambda x: x[1].hit_rate_3plus,
            reverse=True
        )

        return {
            'rankings': [(name, r.hit_rate_3plus) for name, r in rankings],
            'results': {name: r.summary for name, r in all_results.items()},
            'best': rankings[0][0] if rankings else '',
        }



# ═══════════════════════════════════════════════════════════════════════
# 3. 전략 성능 대시보드
# ═══════════════════════════════════════════════════════════════════════

class PerformanceDashboard:
    """전략 성능을 시각화하고 리포트하는 대시보드.

    기록된 백테스트 결과를 누적하여 전략 간 비교,
    시계열 성능 추이, 최적 전략 추천을 제공합니다.
    """

    def __init__(self):
        self._history: List[BacktestResult] = []
        self._strategy_scores: Dict[str, List[float]] = defaultdict(list)

    def record(self, result: BacktestResult) -> None:
        """백테스트 결과를 기록합니다."""
        self._history.append(result)
        self._strategy_scores[result.strategy_name].append(result.hit_rate_3plus)

    def get_rankings(self) -> List[Dict]:
        """전략별 평균 성능 순위를 반환합니다."""
        rankings = []
        for name, scores in self._strategy_scores.items():
            rankings.append({
                'strategy': name,
                'avg_hit_rate_3plus': float(np.mean(scores)),
                'std_hit_rate_3plus': float(np.std(scores)),
                'runs': len(scores),
                'best': float(max(scores)),
                'worst': float(min(scores)),
            })
        rankings.sort(key=lambda x: x['avg_hit_rate_3plus'], reverse=True)
        return rankings

    def get_best_strategy(self) -> str:
        """평균 성능이 가장 높은 전략명을 반환합니다."""
        rankings = self.get_rankings()
        return rankings[0]['strategy'] if rankings else 'unknown'

    def get_trend(self, strategy_name: str) -> List[float]:
        """특정 전략의 성능 추이를 반환합니다."""
        return self._strategy_scores.get(strategy_name, [])

    def generate_report(self) -> str:
        """텍스트 기반 성능 리포트를 생성합니다."""
        rankings = self.get_rankings()
        if not rankings:
            return "기록된 백테스트 결과가 없습니다."

        lines = []
        lines.append("=" * 70)
        lines.append(" 전략 성능 대시보드")
        lines.append("=" * 70)
        lines.append(f"{'순위':<4} {'전략':<25} {'평균3+적중률':<12} {'최고':<8} {'최저':<8} {'실행횟수':<6}")
        lines.append("-" * 70)

        for i, r in enumerate(rankings, 1):
            lines.append(
                f" {i:<3} {r['strategy']:<25} "
                f"{r['avg_hit_rate_3plus']:.4f}      "
                f"{r['best']:.4f}  {r['worst']:.4f}  "
                f"{r['runs']}"
            )

        lines.append("=" * 70)
        lines.append(f" 최적 전략: {self.get_best_strategy()}")
        lines.append("=" * 70)
        return "\n".join(lines)



# ═══════════════════════════════════════════════════════════════════════
# 4. 전략 팩토리 (기본 전략 래퍼)
# ═══════════════════════════════════════════════════════════════════════

class StrategyFactory:
    """기존 분석기들을 백테스트용 전략 함수로 래핑합니다.

    각 전략은 동일한 인터페이스를 가집니다:
        fn(train_data: List[Dict]) -> List[List[int]]
    """

    @staticmethod
    def statistical_strategy(train_data: List[Dict]) -> List[List[int]]:
        """통계 분석 기반 전략."""
        from analyzers.statistical_analyzer import StatisticalAnalyzer
        analyzer = StatisticalAnalyzer(train_data)
        recs = analyzer.generate_recommendations(num_recommendations=5, verbose=False)
        return [r['numbers'] for r in recs]

    @staticmethod
    def comprehensive_strategy(train_data: List[Dict]) -> List[List[int]]:
        """10개 지표 종합 분석 전략."""
        from analyzers.comprehensive_analyzer import ComprehensiveAnalyzer
        analyzer = ComprehensiveAnalyzer(train_data)
        recs = analyzer.generate_recommendations(num_recommendations=5)
        return [r['numbers'] for r in recs]

    @staticmethod
    def markov_strategy(train_data: List[Dict]) -> List[List[int]]:
        """마르코프 체인 전이확률 전략."""
        from analyzers.advanced_statistics import MarkovChainAnalyzer
        analyzer = MarkovChainAnalyzer(train_data)

        # 최근 회차 번호 추출
        last_row = train_data[-1] if train_data else {}
        current_nums = []
        for i in range(1, 7):
            try:
                n = int(last_row.get(f'num{i}', 0))
                if 1 <= n <= MAX_LOTTO_NUMBER:
                    current_nums.append(n)
            except (ValueError, TypeError):
                continue

        if not current_nums:
            return []

        probs = analyzer.get_transition_probabilities(current_nums)
        rng = np.random.default_rng()
        results = []

        for _ in range(5):
            # 확률 가중 샘플링으로 6개 선택
            p = probs.copy()
            p[p < 0] = 0
            total = p.sum()
            if total > 0:
                p /= total
            else:
                p = np.ones(MAX_LOTTO_NUMBER) / MAX_LOTTO_NUMBER
            chosen = rng.choice(MAX_LOTTO_NUMBER, size=6, replace=False, p=p)
            results.append(sorted((chosen + 1).tolist()))

        return results

    @staticmethod
    def deep_learning_strategy(train_data: List[Dict]) -> List[List[int]]:
        """딥러닝 앙상블 전략."""
        from analyzers.deep_learning_predictor import DeepLearningPredictor
        predictor = DeepLearningPredictor(train_data, epochs=30)
        recs = predictor.generate_combinations(n_combinations=5)
        return [r['numbers'] for r in recs]

    @staticmethod
    def cluster_strategy(train_data: List[Dict]) -> List[List[int]]:
        """군집분석 기반 전략."""
        from analyzers.advanced_statistics import ClusterPatternAnalyzer
        analyzer = ClusterPatternAnalyzer(train_data)

        top_nums = analyzer.get_cluster_recommended_numbers(top_n=20)
        if not top_nums:
            return []

        candidates = [n for n, _ in top_nums]
        rng = np.random.default_rng()
        results = []

        weights = np.array([s for _, s in top_nums])
        weights = weights / weights.sum() if weights.sum() > 0 else np.ones(len(weights)) / len(weights)

        for _ in range(5):
            if len(candidates) >= 6:
                chosen_idx = rng.choice(len(candidates), size=6, replace=False, p=weights)
                nums = sorted([candidates[i] for i in chosen_idx])
                results.append(nums)

        return results

    @staticmethod
    def hybrid_strategy(train_data: List[Dict]) -> List[List[int]]:
        """하이브리드: 통계 + 마르코프 + 핫콜드 결합 전략."""
        from analyzers.statistical_analyzer import StatisticalAnalyzer
        from analyzers.advanced_statistics import (
            MarkovChainAnalyzer, DynamicHotColdWeighter
        )

        stat = StatisticalAnalyzer(train_data)
        markov = MarkovChainAnalyzer(train_data)
        hotcold = DynamicHotColdWeighter(train_data)

        # 최근 번호
        last_row = train_data[-1] if train_data else {}
        current_nums = []
        for i in range(1, 7):
            try:
                n = int(last_row.get(f'num{i}', 0))
                if 1 <= n <= MAX_LOTTO_NUMBER:
                    current_nums.append(n)
            except (ValueError, TypeError):
                continue

        # 3개 소스의 확률 합산
        markov_probs = markov.get_transition_probabilities(current_nums) if current_nums else np.ones(45)/45
        hotcold_weights = hotcold.get_sampling_weights('balanced')

        # 통계 빈도 기반 가중치
        stat.analyze_frequency()
        freq = stat.frequency_analysis.get('weighted_frequency', {})
        freq_weights = np.array([freq.get(i, 1.0) for i in range(1, 46)])
        if freq_weights.sum() > 0:
            freq_weights /= freq_weights.sum()
        else:
            freq_weights = np.ones(45) / 45

        # 앙상블 확률
        combined = markov_probs * 0.35 + hotcold_weights * 0.35 + freq_weights * 0.30
        combined[combined < 0] = 0
        total = combined.sum()
        if total > 0:
            combined /= total

        rng = np.random.default_rng()
        results = []
        for _ in range(5):
            chosen = rng.choice(45, size=6, replace=False, p=combined)
            results.append(sorted((chosen + 1).tolist()))

        return results



# ═══════════════════════════════════════════════════════════════════════
# 5. 편의 함수
# ═══════════════════════════════════════════════════════════════════════

def run_full_evaluation(historical_data: List[Dict],
                        train_window: int = 200,
                        max_rounds: Optional[int] = 50) -> Dict:
    """모든 기본 전략에 대한 전체 평가를 실행합니다.

    Args:
        historical_data: 전체 역사 데이터
        train_window: 학습 윈도우 크기
        max_rounds: 최대 테스트 회차

    Returns:
        토너먼트 결과 딕셔너리
    """
    strategies = {
        '통계분석': StrategyFactory.statistical_strategy,
        '종합분석(10지표)': StrategyFactory.comprehensive_strategy,
        '마르코프체인': StrategyFactory.markov_strategy,
        '군집분석': StrategyFactory.cluster_strategy,
        '하이브리드': StrategyFactory.hybrid_strategy,
    }

    framework = ABTestFramework(
        historical_data,
        train_window=train_window,
        predictions_per_round=5
    )

    result = framework.tournament(strategies, max_rounds=max_rounds)

    # 대시보드 생성
    dashboard = PerformanceDashboard()
    backtester = RollingBacktester(historical_data, train_window=train_window)
    for name, fn in strategies.items():
        bt_result = backtester.run(fn, name, max_rounds)
        dashboard.record(bt_result)

    result['dashboard_report'] = dashboard.generate_report()
    result['dashboard'] = dashboard

    return result
