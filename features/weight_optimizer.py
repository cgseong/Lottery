from __future__ import annotations

from typing import Dict, List

from analyzers.statistical_analyzer import StatisticalAnalyzer, _DEFAULT_SCORE_WEIGHTS

# 탐색할 가중치 조합 후보
_WEIGHT_CANDIDATES: List[Dict[str, float]] = [
    {'frequency': 0.45, 'sum': 0.20, 'trend': 0.20, 'distribution': 0.15},  # 기본값
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

    동작 방식:
    1. 학습 데이터(전체 - 검증 구간)로 후보 조합 200개 생성
    2. 검증 구간(마지막 N 회차)의 실제 당첨번호와 비교
    3. 각 가중치 조합으로 후보를 재점수화하여 3매치 이상 비율이 가장 높은 가중치 반환
    """

    def __init__(self, historical_data: List[Dict], test_rounds: int = 40):
        self.historical_data = historical_data
        self.test_rounds = test_rounds

    def optimize(self) -> Dict[str, float]:
        """최적 가중치를 탐색하여 반환합니다."""
        min_required = self.test_rounds + 50
        if len(self.historical_data) < min_required:
            print(f"[WARN] 데이터가 부족합니다 (최소 {min_required}회차 필요). 기본 가중치 사용.")
            return dict(_DEFAULT_SCORE_WEIGHTS)

        # 학습 / 검증 분리
        train_data = self.historical_data[:-self.test_rounds]
        test_data = self.historical_data[-self.test_rounds:]

        print(f"   학습 데이터: {len(train_data)}회차 / 검증 데이터: {len(test_data)}회차")

        # 기본 분석기로 후보 조합 생성 (가중치 탐색에 공통 사용)
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
            print("[WARN] 후보 조합 생성 실패. 기본 가중치 사용.")
            return dict(_DEFAULT_SCORE_WEIGHTS)

        print(f"   후보 조합 {len(candidate_numbers)}개 생성 완료")
        print(f"   {len(_WEIGHT_CANDIDATES)}개 가중치 조합 평가 중...")

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

                # 해당 가중치로 모든 후보 재점수화 후 상위 3개 추출
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
            print(f"   [{label}] f={w_combo['frequency']:.2f} s={w_combo['sum']:.2f} "
                  f"t={w_combo['trend']:.2f} d={w_combo['distribution']:.2f} "
                  f"→ 3매치율 {rate:.4f}")

        print(f"\n   최적 가중치: frequency={best_weights['frequency']:.2f}, "
              f"sum={best_weights['sum']:.2f}, "
              f"trend={best_weights['trend']:.2f}, "
              f"distribution={best_weights['distribution']:.2f}")
        print(f"   최적 3매치율: {best_rate:.4f}")

        return best_weights
