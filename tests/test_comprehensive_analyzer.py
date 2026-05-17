"""ComprehensiveAnalyzer 단위 테스트"""

import pytest
from analyzers.comprehensive_analyzer import ComprehensiveAnalyzer


def test_summary_stats_keys(sample_data):
    ca = ComprehensiveAnalyzer(sample_data)
    stats = ca.summary_stats()
    assert 'total_rounds' in stats
    assert stats['total_rounds'] == len(sample_data)
    assert 'sum_mean' in stats
    assert 'top5_freq' in stats


def test_compute_score_range(sample_data):
    ca = ComprehensiveAnalyzer(sample_data)
    score = ca.compute_score([1, 7, 14, 21, 33, 42])
    assert 0.0 <= score <= 1.0


def test_generate_recommendations_structure(sample_data):
    ca = ComprehensiveAnalyzer(sample_data)
    recs = ca.generate_recommendations(num_recommendations=3, sample_size=500, seed=42)
    assert isinstance(recs, list)
    for rec in recs:
        assert 'numbers' in rec
        assert 'score' in rec
        assert len(rec['numbers']) == 6
        assert all(1 <= n <= 45 for n in rec['numbers'])


def test_exclude_numbers_respected(sample_data):
    exclude = {1, 2, 3}
    ca = ComprehensiveAnalyzer(sample_data)
    recs = ca.generate_recommendations(
        num_recommendations=5, sample_size=2000, exclude_numbers=exclude, seed=42
    )
    for rec in recs:
        assert not (set(rec['numbers']) & exclude)


def test_indicator_report_has_ten_keys(sample_data):
    ca = ComprehensiveAnalyzer(sample_data)
    report = ca.indicator_report([5, 12, 22, 30, 38, 44])
    assert len(report) == 10
    for val in report.values():
        assert 0.0 <= val <= 1.0


def test_empty_data():
    ca = ComprehensiveAnalyzer([])
    assert ca.summary_stats() == {}
    assert ca.generate_recommendations() == []
