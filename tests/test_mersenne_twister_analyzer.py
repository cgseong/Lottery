#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MersenneTwisterAnalyzer 단위 테스트
"""

import pytest
from analyzers.mersenne_twister_analyzer import MersenneTwisterAnalyzer
from utils.helpers import check_consecutive_count


# ---------------------------------------------------------------------------
# TestMersenneTwisterAnalyzerInit
# ---------------------------------------------------------------------------

class TestMersenneTwisterAnalyzerInit:
    """MersenneTwisterAnalyzer.__init__ 및 분석 메서드 초기화 테스트"""

    def test_init_creates_frequency_dict(self, sample_data):
        analyzer = MersenneTwisterAnalyzer(sample_data)
        assert isinstance(analyzer.frequency, dict)

    def test_frequency_keys_are_ints(self, sample_data):
        analyzer = MersenneTwisterAnalyzer(sample_data)
        for key in analyzer.frequency:
            assert isinstance(key, int), f"Expected int key, got {type(key)}: {key!r}"

    def test_frequency_values_positive(self, sample_data):
        analyzer = MersenneTwisterAnalyzer(sample_data)
        for key, val in analyzer.frequency.items():
            assert val > 0, f"frequency[{key}] should be > 0, got {val}"

    def test_recent_numbers_is_set(self, sample_data):
        analyzer = MersenneTwisterAnalyzer(sample_data)
        assert isinstance(analyzer.recent_numbers, set)

    def test_recent_numbers_int_elements(self, sample_data):
        analyzer = MersenneTwisterAnalyzer(sample_data)
        for elem in analyzer.recent_numbers:
            assert isinstance(elem, int), f"Expected int in recent_numbers, got {type(elem)}: {elem!r}"

    def test_handles_string_csv_values(self, sample_data):
        """같은 데이터를 문자열로 변환해도 frequency 키가 int여야 한다."""
        str_data = [
            {k: str(v) for k, v in row.items()}
            for row in sample_data
        ]
        analyzer = MersenneTwisterAnalyzer(str_data)
        for key in analyzer.frequency:
            assert isinstance(key, int), f"Expected int key from str data, got {type(key)}: {key!r}"

    def test_init_with_empty_data(self):
        """빈 데이터로 초기화해도 예외가 발생하지 않아야 한다."""
        analyzer = MersenneTwisterAnalyzer([])
        assert isinstance(analyzer.frequency, dict)
        assert len(analyzer.frequency) == 0


# ---------------------------------------------------------------------------
# TestMersenneTwisterAnalyzerScore
# ---------------------------------------------------------------------------

class TestMersenneTwisterAnalyzerScore:
    """calculate_score 메서드 테스트"""

    def test_calculate_score_is_numeric(self, sample_data):
        analyzer = MersenneTwisterAnalyzer(sample_data)
        score = analyzer.calculate_score([3, 14, 22, 31, 38, 45])
        assert isinstance(score, (int, float))

    def test_consecutive_penalty_reduces_score(self, sample_data):
        """연속번호가 많을수록 점수가 낮아야 한다."""
        analyzer = MersenneTwisterAnalyzer(sample_data)
        score_consecutive = analyzer.calculate_score([1, 2, 3, 4, 5, 6])   # 5쌍 연속
        score_spread = analyzer.calculate_score([3, 14, 22, 31, 38, 45])   # 연속 없음
        assert score_consecutive < score_spread, (
            f"연속번호 점수({score_consecutive}) < 분산번호 점수({score_spread}) 여야 한다."
        )


# ---------------------------------------------------------------------------
# TestMersenneTwisterConsecutive
# ---------------------------------------------------------------------------

class TestMersenneTwisterConsecutive:
    """check_consecutive_numbers 메서드 테스트"""

    def test_delegates_to_helper(self, sample_data):
        """analyzer.check_consecutive_numbers가 check_consecutive_count에 위임해야 한다."""
        analyzer = MersenneTwisterAnalyzer(sample_data)
        numbers = [1, 2, 5, 6, 7]
        assert analyzer.check_consecutive_numbers(numbers) == check_consecutive_count(numbers)

    def test_no_consecutive(self, sample_data):
        analyzer = MersenneTwisterAnalyzer(sample_data)
        assert analyzer.check_consecutive_numbers([3, 7, 12, 33, 40, 45]) == 0

    def test_all_consecutive(self, sample_data):
        analyzer = MersenneTwisterAnalyzer(sample_data)
        assert analyzer.check_consecutive_numbers([1, 2, 3, 4, 5, 6]) == 5


# ---------------------------------------------------------------------------
# TestMersenneTwisterGenerateNumbersMt
# ---------------------------------------------------------------------------

class TestMersenneTwisterGenerateNumbersMt:
    """generate_numbers_mt 메서드 테스트"""

    def test_returns_six_numbers(self, sample_data):
        analyzer = MersenneTwisterAnalyzer(sample_data)
        result = analyzer.generate_numbers_mt(set())
        assert len(result) == 6

    def test_no_duplicates(self, sample_data):
        analyzer = MersenneTwisterAnalyzer(sample_data)
        result = analyzer.generate_numbers_mt(set())
        assert len(result) == len(set(result)), "중복 번호가 있어서는 안 된다."

    def test_in_range(self, sample_data):
        analyzer = MersenneTwisterAnalyzer(sample_data)
        result = analyzer.generate_numbers_mt(set())
        for num in result:
            assert 1 <= num <= 45, f"번호 {num}은 1~45 범위를 벗어났다."

    def test_respects_exclude(self, sample_data):
        analyzer = MersenneTwisterAnalyzer(sample_data)
        exclude = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
        result = analyzer.generate_numbers_mt(exclude)
        for num in result:
            assert num not in exclude, f"제외 번호 {num}이 결과에 포함되었다."

    def test_returns_list_not_none(self, sample_data):
        analyzer = MersenneTwisterAnalyzer(sample_data)
        result = analyzer.generate_numbers_mt(set())
        assert result is not None
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# TestMersenneTwisterGenerateRecommendations
# ---------------------------------------------------------------------------

class TestMersenneTwisterGenerateRecommendations:
    """generate_recommendations 메서드 테스트"""

    def test_returns_list(self, sample_data):
        analyzer = MersenneTwisterAnalyzer(sample_data)
        result = analyzer.generate_recommendations()
        assert isinstance(result, list)

    def test_has_at_least_one_result(self, sample_data):
        analyzer = MersenneTwisterAnalyzer(sample_data)
        result = analyzer.generate_recommendations()
        assert len(result) >= 1

    def test_result_has_numbers_key(self, sample_data):
        analyzer = MersenneTwisterAnalyzer(sample_data)
        result = analyzer.generate_recommendations()
        assert 'numbers' in result[0]

    def test_result_numbers_length_six(self, sample_data):
        analyzer = MersenneTwisterAnalyzer(sample_data)
        result = analyzer.generate_recommendations()
        assert len(result[0]['numbers']) == 6

    def test_result_has_score_key(self, sample_data):
        analyzer = MersenneTwisterAnalyzer(sample_data)
        result = analyzer.generate_recommendations()
        assert 'score' in result[0]

    def test_score_is_numeric(self, sample_data):
        analyzer = MersenneTwisterAnalyzer(sample_data)
        result = analyzer.generate_recommendations()
        assert isinstance(result[0]['score'], (int, float))

    def test_respects_exclude_numbers(self, sample_data):
        analyzer = MersenneTwisterAnalyzer(sample_data)
        exclude = {1, 2, 3, 4, 5}
        result = analyzer.generate_recommendations(exclude_numbers=exclude)
        assert len(result) >= 1
        for num in result[0]['numbers']:
            assert num not in exclude, f"제외 번호 {num}이 추천 결과에 포함되었다."
