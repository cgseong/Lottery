"""Tests for WeightOptimizer and AutoUpdateScheduler."""

from __future__ import annotations

import random
from unittest.mock import MagicMock

import pytest

from analyzers.statistical_analyzer import _DEFAULT_SCORE_WEIGHTS
from features.auto_update_scheduler import AutoUpdateScheduler
from features.weight_optimizer import WeightOptimizer

REQUIRED_KEYS = {'frequency', 'sum', 'trend', 'distribution'}


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def large_data():
    """200 synthetic draw rows — enough to trigger actual optimization."""
    random.seed(99)
    rows = []
    for i in range(1, 201):
        nums = sorted(random.sample(range(1, 46), 6))
        rows.append({
            '회차': i,
            '번호1': nums[0], '번호2': nums[1], '번호3': nums[2],
            '번호4': nums[3], '번호5': nums[4], '번호6': nums[5],
            '보너스번호': 7,
        })
    return rows


@pytest.fixture
def small_data_10():
    """10 draw rows — intentionally below the min_required threshold."""
    random.seed(7)
    rows = []
    for i in range(1, 11):
        nums = sorted(random.sample(range(1, 46), 6))
        rows.append({
            '회차': i,
            '번호1': nums[0], '번호2': nums[1], '번호3': nums[2],
            '번호4': nums[3], '번호5': nums[4], '번호6': nums[5],
            '보너스번호': random.randint(1, 45),
        })
    return rows


# ---------------------------------------------------------------------------
# Part 1 — WeightOptimizer
# ---------------------------------------------------------------------------

class TestWeightOptimizer:

    # --- basic shape / type tests (use sample_data which has 100 rows;
    #     test_rounds=40 → min_required=90, so 100 rows is enough) ---

    def test_optimize_returns_dict(self, sample_data):
        result = WeightOptimizer(sample_data, test_rounds=40).optimize()
        assert isinstance(result, dict)

    def test_result_has_required_keys(self, sample_data):
        result = WeightOptimizer(sample_data, test_rounds=40).optimize()
        assert REQUIRED_KEYS.issubset(result.keys())

    def test_weights_are_floats(self, sample_data):
        result = WeightOptimizer(sample_data, test_rounds=40).optimize()
        for key in REQUIRED_KEYS:
            assert isinstance(result[key], (int, float)), (
                f"Weight '{key}' is {type(result[key])}, expected int or float"
            )

    def test_weights_sum_to_one(self, sample_data):
        result = WeightOptimizer(sample_data, test_rounds=40).optimize()
        total = sum(result[k] for k in REQUIRED_KEYS)
        assert abs(total - 1.0) < 0.01, f"Weights sum to {total}, expected ~1.0"

    # --- fallback behaviour ---

    def test_fallback_on_insufficient_data(self, small_data_10):
        """With only 10 rows (< test_rounds+50 = 90) must return default weights."""
        result = WeightOptimizer(small_data_10, test_rounds=40).optimize()
        assert result == dict(_DEFAULT_SCORE_WEIGHTS)

    def test_fallback_returns_valid_dict(self):
        """Empty list must still return a non-empty dict (the defaults)."""
        result = WeightOptimizer([], test_rounds=40).optimize()
        assert isinstance(result, dict)
        assert len(result) > 0

    # --- full optimization path ---

    def test_optimize_with_enough_data(self, large_data):
        """200-row fixture triggers real optimization; result must be well-formed."""
        result = WeightOptimizer(large_data, test_rounds=40).optimize()
        assert isinstance(result, dict)
        assert REQUIRED_KEYS.issubset(result.keys())
        total = sum(result[k] for k in REQUIRED_KEYS)
        assert abs(total - 1.0) < 0.01, f"Weights sum to {total}, expected ~1.0"


# ---------------------------------------------------------------------------
# Part 2 — AutoUpdateScheduler
# ---------------------------------------------------------------------------

@pytest.fixture
def scheduler_no_updates():
    mock_collector = MagicMock()
    mock_collector.update_latest_data.return_value = []
    return AutoUpdateScheduler(collector=mock_collector)


@pytest.fixture
def scheduler_with_updates():
    mock_collector = MagicMock()
    mock_collector.update_latest_data.return_value = [{'회차': 1200}]
    return AutoUpdateScheduler(collector=mock_collector)


class TestAutoUpdateScheduler:

    # --- return shape ---

    def test_run_once_returns_dict(self, scheduler_no_updates):
        result = scheduler_no_updates.run_once()
        assert isinstance(result, dict)

    def test_result_has_started_at(self, scheduler_no_updates):
        result = scheduler_no_updates.run_once()
        assert 'started_at' in result

    def test_result_has_updated_count(self, scheduler_no_updates):
        result = scheduler_no_updates.run_once()
        assert 'updated_count' in result

    def test_result_has_updated_flag(self, scheduler_no_updates):
        result = scheduler_no_updates.run_once()
        assert 'updated' in result

    # --- no-updates branch ---

    def test_no_updates_count_zero(self, scheduler_no_updates):
        result = scheduler_no_updates.run_once()
        assert result['updated_count'] == 0

    def test_no_updates_flag_false(self, scheduler_no_updates):
        result = scheduler_no_updates.run_once()
        assert result['updated'] is False

    # --- with-updates branch ---

    def test_with_updates_count_one(self, scheduler_with_updates):
        result = scheduler_with_updates.run_once()
        assert result['updated_count'] == 1

    def test_with_updates_flag_true(self, scheduler_with_updates):
        result = scheduler_with_updates.run_once()
        assert result['updated'] is True

    # --- ISO timestamp ---

    def test_started_at_is_iso_string(self, scheduler_no_updates):
        result = scheduler_no_updates.run_once()
        started_at = result['started_at']
        assert isinstance(started_at, str)
        assert 'T' in started_at, (
            f"'started_at' value '{started_at}' does not contain 'T' (not ISO format)"
        )
