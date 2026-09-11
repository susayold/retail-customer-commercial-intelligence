import numpy as np

from src.statistical_validation import bootstrap_mean_difference, cohens_d, wilson_interval


def test_wilson_interval_is_bounded():
    lower, upper = wilson_interval(5, 10)
    assert 0 <= lower <= upper <= 1


def test_bootstrap_returns_observed_difference_and_ci():
    left = np.array([2.0, 2.0, 2.0])
    right = np.array([1.0, 1.0, 1.0])
    observed, lower, upper = bootstrap_mean_difference(left, right, iterations=100)
    assert observed == 1.0
    assert lower <= observed <= upper
    assert cohens_d(left, right) == 0.0
