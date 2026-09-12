import numpy as np
import pytest

from src.statistical_validation import (
    bootstrap_mean_difference,
    cohens_d,
    normalized_group_label,
    wilson_interval,
)


def test_null_and_blank_groups_are_safe_for_statistics():
    assert normalized_group_label(None) == "Unknown"
    assert normalized_group_label("") == "Unknown"
    assert normalized_group_label("  ") == "Unknown"
    assert normalized_group_label("display_only") == "display_only"


def test_bootstrap_mean_difference_returns_observation_and_interval():
    left = np.array([2.0, 4.0, 6.0])
    right = np.array([1.0, 1.0, 1.0])

    observed, lower, upper = bootstrap_mean_difference(
        left, right, iterations=200, seed=7
    )

    assert observed == pytest.approx(3.0)
    assert lower <= observed <= upper


def test_cohens_d_handles_constant_and_insufficient_samples():
    assert cohens_d(np.array([1.0, 1.0]), np.array([1.0, 1.0])) == 0.0
    assert np.isnan(cohens_d(np.array([1.0]), np.array([1.0, 2.0])))


def test_wilson_interval_is_bounded_and_null_safe():
    lower, upper = wilson_interval(5, 10)
    assert 0.0 <= lower <= 0.5 <= upper <= 1.0
    assert all(np.isnan(value) for value in wilson_interval(0, 0))
