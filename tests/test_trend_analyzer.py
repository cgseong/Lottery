"""analyzers/trend_analyzer.py 테스트"""

import pytest
from analyzers.trend_analyzer import TrendAnalyzer
from utils.helpers import check_consecutive_count


class TestTrendAnalyzerInit:
    """초기화 및 분석 구조 테스트"""

    def test_init_creates_all_structures(self, sample_data):
        ta = TrendAnalyzer(sample_data)
        assert isinstance(ta.frequency, dict)
        assert isinstance(ta.recent_trends, dict)
        assert isinstance(ta.momentum_scores, dict)
        assert isinstance(ta.volatility_patterns, dict)

    def test_frequency_keys_are_ints(self, sample_data):
        """CSV 문자열 값을 가진 데이터에서도 빈도 키가 int여야 한다."""
        # 문자열 값 데이터 (실제 CSV 로딩 시나리오)
        str_data = [
            {
                'round': str(i), 'num1': '3', 'num2': '14', 'num3': '22',
                'num4': '31', 'num5': '39', 'num6': '45', 'bonus': '7',
            }
            for i in range(1, 11)
        ]
        ta = TrendAnalyzer(str_data)
        assert all(isinstance(k, int) for k in ta.frequency.keys()), (
            "빈도 딕셔너리 키가 int여야 합니다 (CSV 문자열 변환 필요)"
        )

    def test_frequency_int_data(self, sample_data):
        """픽스처(int) 데이터로도 키가 int여야 한다."""
        ta = TrendAnalyzer(sample_data)
        assert all(isinstance(k, int) for k in ta.frequency.keys())

    def test_recent_trends_covers_all_numbers(self, sample_data):
        ta = TrendAnalyzer(sample_data)
        # 1~45 모든 번호에 대한 추세 정보가 있어야 한다
        assert len(ta.recent_trends) == 45
        for num in range(1, 46):
            assert num in ta.recent_trends

    def test_momentum_scores_all_numbers(self, sample_data):
        ta = TrendAnalyzer(sample_data)
        assert len(ta.momentum_scores) == 45

    def test_empty_data(self):
        ta = TrendAnalyzer([])
        assert ta.frequency == {}


class TestTrendAnalyzerScore:
    """점수 계산 테스트"""

    def test_calculate_score_is_numeric(self, sample_data):
        ta = TrendAnalyzer(sample_data)
        score = ta.calculate_score([3, 14, 22, 31, 39, 45])
        assert isinstance(score, (int, float))

    def test_calculate_score_string_data(self):
        """문자열 값 데이터에서도 점수 계산이 정상 동작해야 한다."""
        str_data = [
            {
                'round': str(i), 'num1': '3', 'num2': '14', 'num3': '22',
                'num4': '31', 'num5': '39', 'num6': '45', 'bonus': '7',
            }
            for i in range(1, 21)
        ]
        ta = TrendAnalyzer(str_data)
        score = ta.calculate_score([3, 14, 22, 31, 39, 45])
        assert isinstance(score, (int, float))
        # 빈도 키가 int이므로 get(num, 0)이 제대로 동작해야 → freq_score > 0
        # (적어도 frequency가 공백 dict가 아니어야 한다)
        assert ta.frequency  # 비어있지 않아야 함


class TestTrendAnalyzerConsecutive:
    """연속 번호 위임 테스트"""

    def test_check_consecutive_delegates_to_helper(self, sample_data):
        ta = TrendAnalyzer(sample_data)
        nums = [1, 2, 5, 6, 7]
        assert ta.check_consecutive_numbers(nums) == check_consecutive_count(nums)

    def test_check_consecutive_no_pairs(self, sample_data):
        ta = TrendAnalyzer(sample_data)
        assert ta.check_consecutive_numbers([3, 7, 12, 33, 40, 45]) == 0

    def test_check_consecutive_all_pairs(self, sample_data):
        ta = TrendAnalyzer(sample_data)
        assert ta.check_consecutive_numbers([1, 2, 3, 4, 5, 6]) == 5


class TestTrendAnalyzerGenerate:
    """번호 생성 테스트"""

    def test_generate_numbers_returns_six(self, sample_data):
        ta = TrendAnalyzer(sample_data)
        result = ta.generate_numbers_trend(set())
        assert len(result) == 6

    def test_generate_numbers_no_duplicates(self, sample_data):
        ta = TrendAnalyzer(sample_data)
        result = ta.generate_numbers_trend(set())
        assert len(set(result)) == 6

    def test_generate_numbers_in_range(self, sample_data):
        ta = TrendAnalyzer(sample_data)
        result = ta.generate_numbers_trend(set())
        assert all(1 <= n <= 45 for n in result)

    def test_generate_numbers_respects_exclude(self, sample_data):
        ta = TrendAnalyzer(sample_data)
        exclude = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
        result = ta.generate_numbers_trend(exclude)
        assert not (set(result) & exclude), "제외번호가 결과에 포함되면 안 됩니다."
