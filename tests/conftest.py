"""공통 테스트 픽스처"""

import random
import pytest


def _make_draw(round_num: int) -> dict:
    nums = sorted(random.sample(range(1, 46), 6))
    return {
        'round': round_num,
        'num1': nums[0], 'num2': nums[1], 'num3': nums[2],
        'num4': nums[3], 'num5': nums[4], 'num6': nums[5],
        'bonus': random.randint(1, 45),
    }


@pytest.fixture
def sample_data():
    """100회차 무작위 당첨 데이터"""
    random.seed(42)
    return [_make_draw(i) for i in range(1, 101)]


@pytest.fixture
def small_data():
    """10회차 무작위 당첨 데이터 (경계 테스트용)"""
    random.seed(7)
    return [_make_draw(i) for i in range(1, 11)]
