import numpy as np
import pytest

from src.statistical_validation import (
    bootstrap_mean_difference,
    chi_square_test,
    cohens_d,
    mann_whitney_u,
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

def test_mann_whitney_is_null_safe_and_returns_a_two_sided_result():
    statistic, p_value = mann_whitney_u(
        np.array([1.0, 2.0, 3.0]),
        np.array([3.0, 4.0, 5.0]),
    )

    assert np.isfinite(statistic) and statistic >= 0.0
    assert 0.0 <= p_value <= 1.0
    assert all(np.isnan(value) for value in mann_whitney_u(np.array([]), np.array([1.0])))


def test_chi_square_returns_cramers_v_and_rejects_degenerate_tables():
    statistic, p_value, cramers_v = chi_square_test(
        np.array([[8.0, 2.0], [3.0, 7.0]])
    )

    assert statistic > 0.0
    assert 0.0 <= p_value <= 1.0
    assert 0.0 <= cramers_v <= 1.0
    assert all(np.isnan(value) for value in chi_square_test(np.array([[1.0, 0.0], [2.0, 0.0]])))
