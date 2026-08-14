"""Strict byte-only ingestion into canonical v3 categorical presentations."""

from .runtime import categorical_three_way_from_csv, categorical_three_way_from_jsonl

__all__ = (
    "categorical_three_way_from_csv",
    "categorical_three_way_from_jsonl",
)
