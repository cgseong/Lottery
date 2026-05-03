"""공통 테스트 픽스처"""

import random
import pytest


def _make_draw(round_num: int) -> dict:
    nums = sorted(random.sample(range(1, 46), 6))
    return {
        '회차': round_num,
        '번호1': nums[0], '번호2': nums[1], '번호3': nums[2],
        '번호4': nums[3], '번호5': nums[4], '번호6': nums[5],
        '보너스번호': random.randint(1, 45),
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
