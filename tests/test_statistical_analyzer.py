"""StatisticalAnalyzer 단위 테스트"""

import pytest
from analyzers.statistical_analyzer import StatisticalAnalyzer


def test_analyze_frequency_returns_dict(sample_data):
    analyzer = StatisticalAnalyzer(sample_data)
    result = analyzer.analyze_frequency()
    assert isinstance(result, dict)
    assert 'frequency' in result
    assert 'most_common' in result
    assert 'least_common' in result


def test_frequency_covers_all_appeared_numbers(sample_data):
    analyzer = StatisticalAnalyzer(sample_data)
    freq = analyzer.analyze_frequency()['frequency']
    # 모든 빈도값은 양수여야 함
    assert all(v > 0 for v in freq.values())


def test_analyze_sum_range(sample_data):
    analyzer = StatisticalAnalyzer(sample_data)
    result = analyzer.analyze_sum_range()
    assert result['min_sum'] <= result['avg_sum'] <= result['max_sum']


def test_analyze_odd_even(sample_data):
    analyzer = StatisticalAnalyzer(sample_data)
    result = analyzer.analyze_odd_even()
    assert 0.0 <= result['avg_odd'] <= 6.0
    assert abs(result['avg_odd'] + result['avg_even'] - 6.0) < 1e-9


def test_analyze_section_distribution(sample_data):
    analyzer = StatisticalAnalyzer(sample_data)
    result = analyzer.analyze_section_distribution()
    pct = result['percentages']
    total = sum(pct.values())
    assert abs(total - 100.0) < 0.01


def test_generate_recommendations_returns_sorted_unique(sample_data):
    analyzer = StatisticalAnalyzer(sample_data)
    recs = analyzer.generate_recommendations(num_recommendations=3)
    assert len(recs) <= 3
    for rec in recs:
        nums = rec['numbers']
        assert nums == sorted(nums)
        assert len(set(nums)) == 6
        assert all(1 <= n <= 45 for n in nums)


def test_generate_recommendations_respects_exclude(sample_data):
    exclude = {1, 2, 3, 4, 5}
    analyzer = StatisticalAnalyzer(sample_data)
    recs = analyzer.generate_recommendations(
        exclude_numbers=exclude, num_recommendations=5
    )
    for rec in recs:
        assert not (set(rec['numbers']) & exclude)


def test_generate_recommendations_respects_fixed(sample_data):
    fixed = {7, 14}
    analyzer = StatisticalAnalyzer(sample_data)
    recs = analyzer.generate_recommendations(
        fixed_numbers=fixed, num_recommendations=5
    )
    for rec in recs:
        assert fixed.issubset(set(rec['numbers']))


def test_check_consecutive_numbers():
    analyzer = StatisticalAnalyzer([])
    assert analyzer.check_consecutive_numbers([1, 2, 3, 7, 14, 21]) == 2
    assert analyzer.check_consecutive_numbers([1, 3, 5, 7, 9, 11]) == 0
    assert analyzer.check_consecutive_numbers([1, 2, 3, 4, 5, 6]) == 5


def test_empty_data_returns_empty():
    analyzer = StatisticalAnalyzer([])
    assert analyzer.analyze_frequency() == {}
    assert analyzer.generate_recommendations() == []


def test_score_is_between_zero_and_one(sample_data):
    analyzer = StatisticalAnalyzer(sample_data)
    analyzer.analyze_frequency()
    analyzer.analyze_sum_range()
    score = analyzer.calculate_score([1, 7, 14, 21, 33, 42])
    assert 0.0 <= score <= 1.0


def test_small_data_does_not_crash(small_data):
    analyzer = StatisticalAnalyzer(small_data)
    recs = analyzer.generate_recommendations(num_recommendations=2)
    assert isinstance(recs, list)
