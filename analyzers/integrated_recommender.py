"""통합 추천 엔진

마르코프 체인, 군집분석, 동적 핫/콜드, 딥러닝, 고급 필터링을
모두 결합하여 최적의 번호 조합을 추천합니다.
"""
from __future__ import annotations

import numpy as np
from typing import Dict, List, Optional, Set

from utils.constants import MAX_LOTTO_NUMBER, NUM_LOTTO_NUMBERS_TO_PICK

try:
    from utils.logging_config import get_logger
    _log = get_logger(__name__)
except ImportError:
    import logging
    _log = logging.getLogger(__name__)



class IntegratedRecommender:
    """모든 고급 분석 모듈을 통합한 최종 추천 엔진.

    단계:
        1. 각 분석기에서 번호별 확률/점수를 수집
        2. 가중 앙상블로 합산하여 샘플링 확률 생성
        3. 고급 필터 파이프라인으로 저품질 조합 배제
        4. 최종 조합을 종합 점수 기준으로 정렬하여 반환
    """

    # 각 분석기의 기본 가중치 (합 = 1.0)
    DEFAULT_WEIGHTS = {
        'markov': 0.20,
        'cluster': 0.15,
        'hotcold': 0.20,
        'deep_learning': 0.25,
        'statistical': 0.20,
    }

    def __init__(self, historical_data: List[Dict],
                 weights: Optional[Dict[str, float]] = None,
                 dl_epochs: int = 50):
        self.historical_data = historical_data
        self.weights = weights or dict(self.DEFAULT_WEIGHTS)
        self._dl_epochs = dl_epochs

        # 분석기 초기화
        self._markov = None
        self._cluster = None
        self._hotcold = None
        self._deep_learning = None
        self._stat_analyzer = None
        self._filter_pipeline = None
        self._is_initialized = False

    def initialize(self) -> None:
        """모든 분석기를 초기화합니다. 개별 분석기 실패 시에도 계속 진행합니다."""
        if self._is_initialized:
            return

        _log.info("통합 추천 엔진 초기화 시작...")

        from analyzers.advanced_statistics import (
            MarkovChainAnalyzer, ClusterPatternAnalyzer, DynamicHotColdWeighter
        )
        from analyzers.statistical_analyzer import StatisticalAnalyzer
        from analyzers.advanced_filters import AdvancedFilterPipeline

        # 핵심 분석기 초기화
        try:
            self._markov = MarkovChainAnalyzer(self.historical_data)
        except Exception as e:
            _log.warning("MarkovChainAnalyzer 초기화 실패: %s", e)

        try:
            self._cluster = ClusterPatternAnalyzer(self.historical_data)
        except Exception as e:
            _log.warning("ClusterPatternAnalyzer 초기화 실패: %s", e)

        try:
            self._hotcold = DynamicHotColdWeighter(self.historical_data)
        except Exception as e:
            _log.warning("DynamicHotColdWeighter 초기화 실패: %s", e)

        # 딥러닝 예측기 (numpy/sklearn 비호환 시 실패 가능 — 선택적)
        try:
            from analyzers.deep_learning_predictor import DeepLearningPredictor
            self._deep_learning = DeepLearningPredictor(
                self.historical_data, epochs=self._dl_epochs)
        except Exception as e:
            _log.warning("DeepLearningPredictor 초기화 실패 (선택적): %s", e)
            self._deep_learning = None

        try:
            self._stat_analyzer = StatisticalAnalyzer(self.historical_data)
            self._stat_analyzer.analyze_frequency()
            self._stat_analyzer.analyze_recent_trends()
        except Exception as e:
            _log.warning("StatisticalAnalyzer 초기화 실패: %s", e)

        try:
            self._filter_pipeline = AdvancedFilterPipeline(self.historical_data)
        except Exception as e:
            _log.warning("AdvancedFilterPipeline 초기화 실패: %s", e)

        self._is_initialized = True
        _log.info("통합 추천 엔진 초기화 완료")


    def _get_latest_numbers(self) -> List[int]:
        """최근 회차 당첨번호를 반환합니다."""
        rows = sorted(self.historical_data,
                      key=lambda x: int(x.get('회차', 0) or 0), reverse=True)
        if not rows:
            return []
        nums = []
        for i in range(1, 7):
            try:
                n = int(rows[0].get(f'번호{i}', 0))
                if 1 <= n <= MAX_LOTTO_NUMBER:
                    nums.append(n)
            except (ValueError, TypeError):
                continue
        return nums

    def _compute_ensemble_probabilities(self,
                                        exclude: Optional[Set[int]] = None
                                        ) -> np.ndarray:
        """각 분석기의 확률/가중치를 앙상블 합산합니다.

        Returns:
            shape=(45,) 정규화된 확률 벡터
        """
        exclude = exclude or set()
        probs = np.zeros(MAX_LOTTO_NUMBER, dtype=np.float64)
        w = self.weights

        current_nums = self._get_latest_numbers()

        # 1. 마르코프 체인 전이확률
        if self._markov and w.get('markov', 0) > 0:
            markov_p = self._markov.get_transition_probabilities(current_nums)
            probs += markov_p * w['markov']

        # 2. 군집분석: 최근 군집의 번호별 출현 확률
        if self._cluster and w.get('cluster', 0) > 0:
            cluster_nums = self._cluster.get_cluster_recommended_numbers(top_n=45)
            cluster_p = np.zeros(MAX_LOTTO_NUMBER)
            for num, score in cluster_nums:
                if 1 <= num <= MAX_LOTTO_NUMBER:
                    cluster_p[num - 1] = score
            c_total = cluster_p.sum()
            if c_total > 0:
                cluster_p /= c_total
            probs += cluster_p * w['cluster']

        # 3. 동적 핫/콜드 가중치
        if self._hotcold and w.get('hotcold', 0) > 0:
            hotcold_p = self._hotcold.get_sampling_weights('balanced', exclude)
            probs += hotcold_p * w['hotcold']

        # 4. 딥러닝 예측 확률
        if self._deep_learning and w.get('deep_learning', 0) > 0:
            dl_p = self._deep_learning.predict_probabilities()
            probs += dl_p * w['deep_learning']

        # 5. 통계 빈도 가중치
        if self._stat_analyzer and w.get('statistical', 0) > 0:
            freq = self._stat_analyzer.frequency_analysis.get('weighted_frequency', {})
            stat_p = np.array([freq.get(i, 1.0) for i in range(1, 46)])
            s_total = stat_p.sum()
            if s_total > 0:
                stat_p /= s_total
            probs += stat_p * w['statistical']

        # 제외 번호 처리
        for n in exclude:
            if 1 <= n <= MAX_LOTTO_NUMBER:
                probs[n - 1] = 0.0

        # 정규화
        total = probs.sum()
        if total > 0:
            probs /= total
        else:
            probs = np.ones(MAX_LOTTO_NUMBER) / MAX_LOTTO_NUMBER
            for n in exclude:
                if 1 <= n <= MAX_LOTTO_NUMBER:
                    probs[n - 1] = 0.0
            probs /= probs.sum()

        return probs


    def generate_recommendations(self,
                                 num_recommendations: int = 10,
                                 exclude_numbers: Optional[Set[int]] = None,
                                 sample_size: int = 50000,
                                 diversity_threshold: float = 0.35
                                 ) -> List[Dict]:
        """통합 추천 번호를 생성합니다.

        Args:
            num_recommendations: 추천 조합 수
            exclude_numbers: 제외할 번호 집합
            sample_size: 후보 생성 수
            diversity_threshold: 조합 간 자카드 유사도 최대값

        Returns:
            [{'numbers': [...], 'score': float, 'method': str,
              'filter_score': float, 'details': {...}}, ...]
        """
        self.initialize()

        exclude = exclude_numbers or set()
        probs = self._compute_ensemble_probabilities(exclude)

        rng = np.random.default_rng()
        candidates = []
        seen = set()

        _log.info("후보 조합 %d개 생성 중...", sample_size)

        for _ in range(sample_size):
            chosen = rng.choice(MAX_LOTTO_NUMBER, size=6, replace=False, p=probs)
            nums = sorted((chosen + 1).tolist())
            key = tuple(nums)

            if key in seen:
                continue
            seen.add(key)

            # 고급 필터 파이프라인 적용 (없으면 필터 없이 통과)
            if self._filter_pipeline:
                if not self._filter_pipeline.passes(nums):
                    continue
                filter_score = self._filter_pipeline.score(nums)
            else:
                filter_score = 0.5
            ensemble_score = sum(probs[n - 1] for n in nums)

            # 군집 적합도
            cluster_score = self._cluster.score_combination(nums) if self._cluster else 0.5

            # 핫콜드 적합도
            hotcold_score = self._hotcold.score_combination(nums) if self._hotcold else 0.5

            total_score = (
                ensemble_score * 0.30
                + filter_score * 0.30
                + cluster_score * 0.20
                + hotcold_score * 0.20
            )

            candidates.append({
                'numbers': nums,
                'score': total_score,
                'filter_score': filter_score,
                'cluster_score': cluster_score,
                'hotcold_score': hotcold_score,
                'method': '통합 AI 추천',
            })

        # 점수 내림차순 정렬
        candidates.sort(key=lambda x: x['score'], reverse=True)

        # 다양성 필터: 자카드 유사도 기반
        results = []
        for cand in candidates:
            if len(results) >= num_recommendations:
                break
            ns = set(cand['numbers'])
            if all(
                len(ns & set(r['numbers'])) / len(ns | set(r['numbers'])) < diversity_threshold
                for r in results
            ):
                results.append(cand)

        _log.info("통합 추천 완료: %d개 조합 (필터 통과 %d개 중 선정)",
                  len(results), len(candidates))
        return results


    def get_analysis_report(self) -> Dict:
        """현재 상태의 종합 분석 리포트를 반환합니다."""
        self.initialize()

        current_nums = self._get_latest_numbers()
        report = {'latest_numbers': current_nums}

        # 마르코프 전이 예측
        if self._markov:
            top_markov = self._markov.predict_next_numbers(current_nums, top_n=10)
            report['markov_top10'] = top_markov
            report['section_forecast'] = self._markov.get_section_forecast(current_nums)

        # 군집 프로파일
        if self._cluster:
            cluster_id = self._cluster.get_recent_cluster()
            report['current_cluster'] = self._cluster.get_cluster_profile(cluster_id)

        # 핫/콜드 번호
        if self._hotcold:
            report['hot_numbers'] = self._hotcold.get_hot_numbers(10)
            report['cold_numbers'] = self._hotcold.get_cold_numbers(10)

        # 최적 합계 범위
        if self._filter_pipeline and 'sum_distribution' in self._filter_pipeline._filters:
            sf = self._filter_pipeline._filters['sum_distribution']
            report['optimal_sum_range'] = sf.get_optimal_sum_range(confidence=0.80)

        return report

    def score_existing_combination(self, numbers: List[int]) -> Dict:
        """기존 조합을 통합 점수로 평가합니다."""
        self.initialize()

        probs = self._compute_ensemble_probabilities()
        ensemble_score = sum(probs[n - 1] for n in numbers if 1 <= n <= MAX_LOTTO_NUMBER)

        result = {
            'numbers': numbers,
            'ensemble_score': ensemble_score,
            'filter_report': self._filter_pipeline.get_detailed_report(numbers),
        }

        if self._cluster:
            result['cluster_score'] = self._cluster.score_combination(numbers)
        if self._hotcold:
            result['hotcold_score'] = self._hotcold.score_combination(numbers)
        if self._deep_learning:
            result['dl_score'] = self._deep_learning.score_combination(numbers)

        # 종합 점수
        scores = [ensemble_score]
        if 'cluster_score' in result:
            scores.append(result['cluster_score'])
        if 'hotcold_score' in result:
            scores.append(result['hotcold_score'])
        if 'dl_score' in result:
            scores.append(result['dl_score'])
        result['total_score'] = float(np.mean(scores))

        return result
