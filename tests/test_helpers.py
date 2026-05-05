"""utils/helpers.py 테스트 — check_consecutive_count, validate_numbers, extract_numbers_from_data"""

import pytest
from utils.helpers import check_consecutive_count, validate_numbers, extract_numbers_from_data, normalize_exclude_numbers


class TestCheckConsecutiveCount:
    """check_consecutive_count: 연속 쌍 총 개수 반환"""

    def test_empty_list(self):
        assert check_consecutive_count([]) == 0

    def test_single_number(self):
        assert check_consecutive_count([7]) == 0

    def test_no_consecutive(self):
        assert check_consecutive_count([3, 7, 12, 33, 40, 44]) == 0

    def test_one_pair(self):
        assert check_consecutive_count([1, 2, 10, 20, 30, 40]) == 1

    def test_two_separate_pairs(self):
        # (1,2), (5,6) → 2쌍
        assert check_consecutive_count([1, 2, 5, 6, 10, 20]) == 2

    def test_three_scattered_pairs(self):
        # (1,2), (5,6), (6,7) → 3쌍
        assert check_consecutive_count([1, 2, 5, 6, 7]) == 3

    def test_all_consecutive(self):
        # (1,2),(2,3),(3,4),(4,5),(5,6) → 5쌍
        assert check_consecutive_count([1, 2, 3, 4, 5, 6]) == 5

    def test_unsorted_input(self):
        """입력 순서와 무관하게 같은 결과를 반환해야 한다."""
        assert check_consecutive_count([6, 1, 3, 2, 5, 4]) == 5

    def test_multiple_runs_sum(self):
        # (1,2),(2,3) + (9,10),(10,11) → 4쌍
        assert check_consecutive_count([1, 2, 3, 9, 10, 11]) == 4

    def test_five_analyzers_agree(self):
        """5개 분석기 클래스가 모두 같은 값을 반환하는지 확인"""
        from analyzers.statistical_analyzer import StatisticalAnalyzer
        from analyzers.ensemble_analyzer import EnsembleAnalyzer
        from analyzers.trend_analyzer import TrendAnalyzer
        from analyzers.pattern_matching_analyzer import PatternMatchingAnalyzer
        from analyzers.mersenne_twister_analyzer import MersenneTwisterAnalyzer

        data = [
            {
                '회차': i, '번호1': 1, '번호2': 10, '번호3': 20,
                '번호4': 30, '번호5': 40, '번호6': 45, '보너스번호': 5,
            }
            for i in range(1, 11)
        ]
        nums = [1, 2, 5, 6, 7]
        expected = check_consecutive_count(nums)  # 3

        sa = StatisticalAnalyzer(data)
        ea = EnsembleAnalyzer(data)
        ta = TrendAnalyzer(data)
        pa = PatternMatchingAnalyzer(data)
        ma = MersenneTwisterAnalyzer(data)

        assert sa.check_consecutive_numbers(nums) == expected
        assert ea.check_consecutive_numbers(nums) == expected
        assert ta.check_consecutive_numbers(nums) == expected
        assert pa.check_consecutive_numbers(nums) == expected
        assert ma.check_consecutive_numbers(nums) == expected


class TestValidateNumbers:
    """validate_numbers: 번호 조합 유효성 검사"""

    def test_valid_combination(self):
        assert validate_numbers([1, 7, 15, 23, 38, 45]) is True

    def test_wrong_count_five(self):
        assert validate_numbers([1, 2, 3, 4, 5]) is False

    def test_wrong_count_seven(self):
        assert validate_numbers([1, 2, 3, 4, 5, 6, 7]) is False

    def test_duplicate_numbers(self):
        assert validate_numbers([1, 1, 2, 3, 4, 5]) is False

    def test_zero_out_of_range(self):
        assert validate_numbers([0, 2, 3, 4, 5, 6]) is False

    def test_46_out_of_range(self):
        assert validate_numbers([1, 2, 3, 4, 5, 46]) is False

    def test_empty_list(self):
        assert validate_numbers([]) is False


class TestExtractNumbersFromData:
    """extract_numbers_from_data: 행 딕셔너리에서 번호 추출"""

    def test_normal_row(self):
        row = {
            '번호1': 3, '번호2': 14, '번호3': 22,
            '번호4': 31, '번호5': 39, '번호6': 45,
        }
        assert extract_numbers_from_data(row) == [3, 14, 22, 31, 39, 45]

    def test_string_values(self):
        """CSV 문자열 값도 처리할 수 있어야 한다."""
        row = {
            '번호1': '5', '번호2': '12', '번호3': '21',
            '번호4': '30', '번호5': '38', '번호6': '44',
        }
        result = extract_numbers_from_data(row)
        assert result == [5, 12, 21, 30, 38, 44]

    def test_result_is_sorted(self):
        row = {
            '번호1': 40, '번호2': 1, '번호3': 25,
            '번호4': 10, '번호5': 33, '번호6': 7,
        }
        result = extract_numbers_from_data(row)
        assert result == sorted(result)

    def test_missing_columns(self):
        """일부 컬럼이 없어도 추출 가능한 번호만 반환한다."""
        row = {'번호1': 5, '번호2': 10}
        result = extract_numbers_from_data(row)
        assert result == [5, 10]


class TestNormalizeExcludeNumbers:
    """normalize_exclude_numbers: dict/list/set/None → set[int] 변환"""

    def test_none_returns_empty_set(self):
        assert normalize_exclude_numbers(None) == set()

    def test_empty_set_returns_empty_set(self):
        assert normalize_exclude_numbers(set()) == set()

    def test_empty_list_returns_empty_set(self):
        assert normalize_exclude_numbers([]) == set()

    def test_empty_dict_returns_empty_set(self):
        assert normalize_exclude_numbers({}) == set()

    def test_set_passthrough(self):
        assert normalize_exclude_numbers({1, 2, 3}) == {1, 2, 3}

    def test_list_to_set(self):
        assert normalize_exclude_numbers([3, 7, 12]) == {3, 7, 12}

    def test_dict_extracts_keys(self):
        assert normalize_exclude_numbers({1: 'a', 5: 'b'}) == {1, 5}

    def test_returns_set_type(self):
        for value in [None, set(), [], {}, {1, 2}, [3, 4], {5: 'x'}]:
            result = normalize_exclude_numbers(value)
            assert isinstance(result, set)

    def test_set_input_returns_set(self):
        result = normalize_exclude_numbers({10, 20, 30})
        assert isinstance(result, set)
        assert result == {10, 20, 30}

    def test_list_with_duplicates(self):
        assert normalize_exclude_numbers([1, 1, 2, 2, 3]) == {1, 2, 3}
