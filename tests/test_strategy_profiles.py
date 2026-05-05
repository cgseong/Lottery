"""features/strategy_profiles.py 테스트"""

import pytest
from analyzers.statistical_analyzer import StatisticalAnalyzer
from features.strategy_profiles import StrategyProfileEngine, STRATEGY_PROFILES


class TestStrategyProfileEngine:
    """StrategyProfileEngine: 전략별 번호 추천 테스트"""

    @pytest.fixture
    def engine(self, sample_data):
        analyzer = StatisticalAnalyzer(sample_data)
        return StrategyProfileEngine(analyzer)

    # ── 기본 동작 ──────────────────────────────────────────────────

    def test_generate_returns_list(self, engine):
        results = engine.generate("균형형", exclude_numbers=set(), count=3)
        assert isinstance(results, list)

    def test_generate_requested_count(self, engine):
        results = engine.generate("균형형", exclude_numbers=set(), count=3)
        assert len(results) == 3

    def test_generate_each_has_six_numbers(self, engine):
        results = engine.generate("균형형", exclude_numbers=set(), count=2)
        for rec in results:
            assert len(rec['numbers']) == 6

    def test_generate_numbers_no_duplicates(self, engine):
        results = engine.generate("균형형", exclude_numbers=set(), count=2)
        for rec in results:
            assert len(set(rec['numbers'])) == 6

    def test_generate_numbers_in_range(self, engine):
        results = engine.generate("균형형", exclude_numbers=set(), count=2)
        for rec in results:
            assert all(1 <= n <= 45 for n in rec['numbers'])

    # ── 전략별 합계 범위 검증 ──────────────────────────────────────

    def test_보수형_sum_within_range(self, engine):
        profile = STRATEGY_PROFILES["보수형"]
        results = engine.generate("보수형", exclude_numbers=set(), count=3)
        for rec in results:
            rec_sum = sum(rec['numbers'])
            assert profile['sum_min'] <= rec_sum <= profile['sum_max'], (
                f"보수형 합계 {rec_sum}이 범위 [{profile['sum_min']}, {profile['sum_max']}]를 벗어났습니다."
            )

    def test_균형형_sum_within_range(self, engine):
        profile = STRATEGY_PROFILES["균형형"]
        results = engine.generate("균형형", exclude_numbers=set(), count=3)
        for rec in results:
            rec_sum = sum(rec['numbers'])
            assert profile['sum_min'] <= rec_sum <= profile['sum_max']

    def test_고변동형_sum_within_range(self, engine):
        profile = STRATEGY_PROFILES["고변동형"]
        results = engine.generate("고변동형", exclude_numbers=set(), count=3)
        for rec in results:
            rec_sum = sum(rec['numbers'])
            assert profile['sum_min'] <= rec_sum <= profile['sum_max']

    # ── 알 수 없는 프로파일 ────────────────────────────────────────

    def test_unknown_profile_falls_back_to_균형형(self, engine):
        """정의되지 않은 프로파일은 균형형으로 대체되어야 한다."""
        profile = STRATEGY_PROFILES["균형형"]
        results = engine.generate("없는전략", exclude_numbers=set(), count=2)
        for rec in results:
            rec_sum = sum(rec['numbers'])
            assert profile['sum_min'] <= rec_sum <= profile['sum_max']

    # ── 제외 번호 ──────────────────────────────────────────────────

    def test_generate_respects_exclude_numbers(self, engine):
        """제외번호가 결과에 포함되지 않아야 한다."""
        exclude = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
        results = engine.generate("균형형", exclude_numbers=exclude, count=2)
        for rec in results:
            assert not (set(rec['numbers']) & exclude), (
                f"제외번호 {exclude & set(rec['numbers'])}가 결과에 포함되었습니다."
            )

    # ── 프로파일 메타데이터 ────────────────────────────────────────

    def test_profile_name_attached_to_result(self, engine):
        """결과에 프로파일 이름이 첨부되어야 한다."""
        results = engine.generate("보수형", exclude_numbers=set(), count=1)
        assert results[0].get('profile') == "보수형"

    def test_strategy_profiles_constant_has_required_keys(self):
        for name, profile in STRATEGY_PROFILES.items():
            assert 'sum_min' in profile, f"{name}: sum_min 없음"
            assert 'sum_max' in profile, f"{name}: sum_max 없음"
            assert 'max_consecutive' in profile, f"{name}: max_consecutive 없음"
            assert profile['sum_min'] < profile['sum_max'], f"{name}: sum_min >= sum_max"
