"""Single source of truth for the retail raw-source contract.

This module contains metadata only. It must never contain source records.
"""

from __future__ import annotations

EXPECTED_SOURCE_FILES: tuple[str, ...] = (
    "transaction_data.csv",
    "causal_data.csv",
    "coupon.csv",
    "coupon_redempt.csv",
    "campaign_table.csv",
    "campaign_desc.csv",
    "product.csv",
    "hh_demographic.csv",
)

# Planning expectations from the supplied execution plan. These values are
# review metadata; permitted source versions may have different counts.
EXPECTED_ROW_COUNTS: dict[str, int] = {
    "transaction_data.csv": 2_595_732,
    "causal_data.csv": 36_786_524,
    "coupon.csv": 124_548,
    "coupon_redempt.csv": 2_318,
    "campaign_table.csv": 7_208,
    "campaign_desc.csv": 30,
    "product.csv": 92_353,
    "hh_demographic.csv": 801,
}

SOURCE_NAME_BY_FILE: dict[str, str] = {
    file_name.removesuffix(".csv"): file_name
    for file_name in EXPECTED_SOURCE_FILES
}

MANIFEST_VERSION = "1.0"

if set(EXPECTED_ROW_COUNTS) != set(EXPECTED_SOURCE_FILES):
    raise RuntimeError("Source manifest row-count keys must match the exact file set")
