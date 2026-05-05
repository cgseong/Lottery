"""analyzers/pattern_matching_analyzer.py 테스트"""

import pytest
from analyzers.pattern_matching_analyzer import PatternMatchingAnalyzer
from utils.helpers import check_consecutive_count


class TestPatternMatchingAnalyzerInit:
    """초기화 및 패턴 추출 테스트"""

    def test_init_creates_patterns_dict(self, sample_data):
        pa = PatternMatchingAnalyzer(sample_data)
        assert isinstance(pa.patterns, dict)
        for key in ('odd_even_ratios', 'sum_ranges', 'consecutive_patterns', 'section_distributions'):
            assert key in pa.patterns, f"'{key}' 키가 없습니다."

    def test_patterns_populated(self, sample_data):
        pa = PatternMatchingAnalyzer(sample_data)
        assert len(pa.patterns['sum_ranges']) > 0
        assert len(pa.patterns['odd_even_ratios']) > 0

    def test_handles_string_csv_values(self):
        """CSV에서 로드한 문자열 값도 올바르게 분석해야 한다."""
        str_data = [
            {
                '회차': str(i), '번호1': '3', '번호2': '14', '번호3': '22',
                '번호4': '31', '번호5': '39', '번호6': '45', '보너스번호': '7',
            }
            for i in range(1, 11)
        ]
        pa = PatternMatchingAnalyzer(str_data)
        # 문자열 변환 버그가 있으면 sum_ranges가 비어 있거나 잘못된 값이 들어간다
        assert len(pa.patterns['sum_ranges']) == 10
        # 합계가 숫자여야 한다
        assert all(isinstance(s, (int, float)) for s in pa.patterns['sum_ranges'])

    def test_sum_ranges_are_numeric(self, sample_data):
        pa = PatternMatchingAnalyzer(sample_data)
        for s in pa.patterns['sum_ranges']:
            assert isinstance(s, (int, float))

    def test_empty_data(self):
        pa = PatternMatchingAnalyzer([])
        for key in ('odd_even_ratios', 'sum_ranges', 'consecutive_patterns', 'section_distributions'):
            assert pa.patterns[key] == []


class TestPatternMatchingScore:
    """점수 계산 테스트"""

    def test_calculate_score_is_numeric(self, sample_data):
        pa = PatternMatchingAnalyzer(sample_data)
        score = pa.calculate_score([3, 14, 22, 31, 39, 45])
        assert isinstance(score, (int, float))

    def test_calculate_score_non_negative(self, sample_data):
        """점수는 음수가 되지 않아야 한다."""
        pa = PatternMatchingAnalyzer(sample_data)
        score = pa.calculate_score([3, 14, 22, 31, 39, 45])
        assert score >= 0

    def test_consecutive_patterns_consistent(self, sample_data):
        """_analyze_patterns와 calculate_score가 같은 연속 쌍 기준을 사용해야 한다."""
        pa = PatternMatchingAnalyzer(sample_data)
        # consecutive_patterns가 총 쌍 수(check_consecutive_count 기준)로 저장되어 있는지 확인
        for val in pa.patterns['consecutive_patterns']:
            assert isinstance(val, int)
            assert 0 <= val <= 5  # 6개 번호의 최대 연속 쌍 수


class TestPatternMatchingConsecutive:
    """연속 번호 위임 테스트"""

    def test_delegates_to_helper(self, sample_data):
        pa = PatternMatchingAnalyzer(sample_data)
        nums = [1, 2, 5, 6, 7]
        assert pa.check_consecutive_numbers(nums) == check_consecutive_count(nums)

    def test_no_consecutive(self, sample_data):
        pa = PatternMatchingAnalyzer(sample_data)
        assert pa.check_consecutive_numbers([3, 7, 12, 33, 40, 45]) == 0

    def test_all_consecutive(self, sample_data):
        pa = PatternMatchingAnalyzer(sample_data)
        assert pa.check_consecutive_numbers([1, 2, 3, 4, 5, 6]) == 5


class TestPatternMatchingGenerate:
    """번호 생성 테스트"""

    def test_generate_numbers_length(self, sample_data):
        pa = PatternMatchingAnalyzer(sample_data)
        result = pa.generate_numbers(set())
        assert result is not None
        assert len(result) == 6

    def test_generate_numbers_no_duplicates(self, sample_data):
        pa = PatternMatchingAnalyzer(sample_data)
        result = pa.generate_numbers(set())
        assert len(set(result)) == 6

    def test_generate_numbers_in_range(self, sample_data):
        pa = PatternMatchingAnalyzer(sample_data)
        result = pa.generate_numbers(set())
        assert all(1 <= n <= 45 for n in result)

    def test_generate_numbers_respects_exclude(self, sample_data):
        pa = PatternMatchingAnalyzer(sample_data)
        exclude = {1, 2, 3, 4, 5}
        result = pa.generate_numbers(exclude)
        assert not (set(result) & exclude)
