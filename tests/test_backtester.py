"""Backtester 단위 테스트"""

import pytest
from features.backtester import Backtester


def test_not_enough_data():
    result = Backtester([]).run(window=200)
    assert not result['ok']


def test_run_returns_hit_distribution(sample_data):
    bt = Backtester(sample_data)
    result = bt.run(window=20, trials=1)
    if result.get('ok'):
        dist = result['hit_distribution']
        assert set(dist.keys()) == {0, 1, 2, 3, 4, 5, 6}
        assert result['samples'] > 0
        assert 0.0 <= result['hit_rate_3_plus'] <= 1.0


def test_tune_trials(sample_data):
    bt = Backtester(sample_data)
    result = bt.tune_trials(window=20, trial_candidates=[1, 2])
    assert isinstance(result, dict)
    assert 'ok' in result
