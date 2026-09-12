from src.statistical_validation import normalized_group_label


def test_null_and_blank_groups_are_safe_for_statistics():
    assert normalized_group_label(None) == "Unknown"
    assert normalized_group_label("") == "Unknown"
    assert normalized_group_label("  ") == "Unknown"
    assert normalized_group_label("display_only") == "display_only"
