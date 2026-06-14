"""utils.constants 임포트 및 값 검증 테스트"""

from utils.constants import (
    MAX_LOTTO_NUMBER,
    NUM_LOTTO_NUMBERS_TO_PICK,
    DEFAULT_RECENT_COUNT,
    LOTTO_NUMBER_COLUMNS,
    BONUS_COLUMN,
    ROUND_COLUMN,
    DEFAULT_CSV_FILE,
    DEFAULT_EXCLUDE_FILE,
    DEFAULT_AI_MODELS_PATH,
    DEFAULT_SCORE_WEIGHTS,
    PRIZE_SHARING_HIGH_MULT,
    PRIZE_SHARING_LOW_MULT,
    PRIZE_SHARING_BIRTHDAY_MAX,
)


def test_lotto_number_range():
    assert MAX_LOTTO_NUMBER == 45
    assert NUM_LOTTO_NUMBERS_TO_PICK == 6


def test_column_names():
    assert BONUS_COLUMN == 'bonus'
    assert ROUND_COLUMN == 'round'
    assert len(LOTTO_NUMBER_COLUMNS) == 6
    assert LOTTO_NUMBER_COLUMNS == ['num1', 'num2', 'num3', 'num4', 'num5', 'num6']


def test_file_paths_are_strings():
    assert isinstance(DEFAULT_CSV_FILE, str)
    assert isinstance(DEFAULT_EXCLUDE_FILE, str)
    assert isinstance(DEFAULT_AI_MODELS_PATH, str)


def test_score_weights_sum_to_one():
    total = sum(DEFAULT_SCORE_WEIGHTS.values())
    assert abs(total - 1.0) < 1e-9, f"가중치 합계가 1.0이 아닙니다: {total}"


def test_prize_sharing_multipliers_logical():
    assert PRIZE_SHARING_HIGH_MULT > PRIZE_SHARING_LOW_MULT
    assert 1 <= PRIZE_SHARING_BIRTHDAY_MAX <= 45
