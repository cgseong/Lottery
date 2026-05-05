"""analyzers/ensemble_analyzer.py 테스트"""

import pytest
from analyzers.ensemble_analyzer import EnsembleAnalyzer
from utils.helpers import check_consecutive_count


class TestEnsembleAnalyzerInit:
    """초기화 테스트"""

    def test_init_creates_sub_analyzers(self, sample_data):
        ea = EnsembleAnalyzer(sample_data)
        assert ea.statistical_analyzer is not None
        assert ea.pattern_analyzer is not None
        assert ea.trend_analyzer is not None

    def test_init_with_empty_data(self):
        ea = EnsembleAnalyzer([])
        assert ea is not None


class TestEnsembleConsecutive:
    """연속 번호 위임 테스트"""

    def test_delegates_to_helper(self, sample_data):
        ea = EnsembleAnalyzer(sample_data)
        nums = [1, 2, 5, 6, 7]
        assert ea.check_consecutive_numbers(nums) == check_consecutive_count(nums)

    def test_no_consecutive(self, sample_data):
        ea = EnsembleAnalyzer(sample_data)
        assert ea.check_consecutive_numbers([3, 7, 12, 33, 40, 45]) == 0

    def test_all_consecutive(self, sample_data):
        ea = EnsembleAnalyzer(sample_data)
        assert ea.check_consecutive_numbers([1, 2, 3, 4, 5, 6]) == 5


class TestEnsembleGenerate:
    """번호 생성 테스트"""

    def test_generate_numbers_length(self, sample_data):
        ea = EnsembleAnalyzer(sample_data)
        result = ea.generate_numbers(set())
        assert result is not None
        assert len(result) == 6

    def test_generate_numbers_no_duplicates(self, sample_data):
        ea = EnsembleAnalyzer(sample_data)
        result = ea.generate_numbers(set())
        assert len(set(result)) == 6

    def test_generate_numbers_in_range(self, sample_data):
        ea = EnsembleAnalyzer(sample_data)
        result = ea.generate_numbers(set())
        assert all(1 <= n <= 45 for n in result)

    def test_generate_numbers_respects_exclude(self, sample_data):
        ea = EnsembleAnalyzer(sample_data)
        exclude = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
        result = ea.generate_numbers(exclude)
        assert result is not None
        assert not (set(result) & exclude)

    def test_generate_recommendations_returns_list(self, sample_data):
        ea = EnsembleAnalyzer(sample_data)
        recs = ea.generate_recommendations(num_recommendations=3)
        assert isinstance(recs, list)

    def test_generate_recommendations_structure(self, sample_data):
        ea = EnsembleAnalyzer(sample_data)
        recs = ea.generate_recommendations(num_recommendations=2)
        assert len(recs) >= 1
        rec = recs[0]
        assert 'numbers' in rec
        assert 'total_score' in rec
        assert len(rec['numbers']) == 6

    def test_generate_recommendations_sorted_by_score(self, sample_data):
        ea = EnsembleAnalyzer(sample_data)
        recs = ea.generate_recommendations(num_recommendations=3)
        if len(recs) >= 2:
            scores = [r['total_score'] for r in recs]
            assert scores == sorted(scores, reverse=True), "결과가 점수 내림차순으로 정렬되어야 합니다."
