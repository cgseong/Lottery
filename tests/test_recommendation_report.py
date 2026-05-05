"""features/recommendation_report.py 테스트"""

import pytest
from analyzers.statistical_analyzer import StatisticalAnalyzer
from features.recommendation_report import RecommendationExplainer
from utils.helpers import check_consecutive_count


REQUIRED_KEYS = {'numbers', 'sum', 'sum_vs_avg', 'odd_even', 'sections', 'consecutive_pairs', 'score'}


@pytest.fixture
def explainer(sample_data):
    analyzer = StatisticalAnalyzer(sample_data)
    return RecommendationExplainer(analyzer)


@pytest.fixture
def sample_numbers():
    return [3, 14, 22, 31, 38, 45]


class TestRecommendationExplainerStructure:
    """build() 반환 구조 테스트"""

    def test_build_returns_dict(self, explainer, sample_numbers):
        result = explainer.build(sample_numbers)
        assert isinstance(result, dict)

    def test_build_has_all_required_keys(self, explainer, sample_numbers):
        result = explainer.build(sample_numbers)
        missing = REQUIRED_KEYS - result.keys()
        assert not missing, f"누락된 키: {missing}"

    def test_numbers_are_sorted(self, explainer):
        """입력 순서와 무관하게 결과가 정렬되어야 한다."""
        result = explainer.build([45, 3, 31, 14, 38, 22])
        assert result['numbers'] == sorted(result['numbers'])

    def test_odd_even_has_required_keys(self, explainer, sample_numbers):
        result = explainer.build(sample_numbers)
        for key in ('odd', 'even', 'avg_odd', 'avg_even'):
            assert key in result['odd_even'], f"odd_even에 '{key}' 없음"

    def test_sections_has_required_keys(self, explainer, sample_numbers):
        result = explainer.build(sample_numbers)
        assert 'counts' in result['sections']
        assert 'historical_pct' in result['sections']


class TestRecommendationExplainerValues:
    """build() 반환값 정확성 테스트"""

    def test_sum_equals_sum_of_numbers(self, explainer, sample_numbers):
        result = explainer.build(sample_numbers)
        assert result['sum'] == sum(sample_numbers)

    def test_odd_even_totals_six(self, explainer, sample_numbers):
        result = explainer.build(sample_numbers)
        assert result['odd_even']['odd'] + result['odd_even']['even'] == 6

    def test_odd_count_correct(self, explainer):
        # [3,7,11,22,34,44] → 홀수: 3, 7, 11 → 3개
        nums = [3, 7, 11, 22, 34, 44]
        result = explainer.build(nums)
        assert result['odd_even']['odd'] == 3
        assert result['odd_even']['even'] == 3

    def test_section_counts_sum_to_six(self, explainer, sample_numbers):
        result = explainer.build(sample_numbers)
        total = sum(result['sections']['counts'].values())
        assert total == 6

    def test_consecutive_pairs_matches_helper(self, explainer, sample_numbers):
        result = explainer.build(sample_numbers)
        expected = check_consecutive_count(sample_numbers)
        assert result['consecutive_pairs'] == expected

    def test_score_is_numeric(self, explainer, sample_numbers):
        result = explainer.build(sample_numbers)
        assert isinstance(result['score'], (int, float))

    def test_sum_vs_avg_is_numeric(self, explainer, sample_numbers):
        result = explainer.build(sample_numbers)
        assert isinstance(result['sum_vs_avg'], (int, float))

    def test_all_consecutive_numbers(self, explainer):
        """모두 연속인 번호 조합: consecutive_pairs == 5"""
        result = explainer.build([1, 2, 3, 4, 5, 6])
        assert result['consecutive_pairs'] == 5

    def test_no_consecutive_numbers(self, explainer):
        """연속 쌍이 없는 조합: consecutive_pairs == 0"""
        result = explainer.build([3, 7, 12, 20, 33, 44])
        assert result['consecutive_pairs'] == 0
