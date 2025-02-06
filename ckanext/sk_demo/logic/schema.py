from __future__ import annotations

from ckan import types
from ckan.logic.schema import validator_args


@validator_args
def get_sum(
    convert_int: types.Validator,
    not_empty: types.Validator,
) -> types.Schema:
    """Schema for sk_demo_get_sum action."""
    return {
        "left": [not_empty, convert_int],
        "right": [not_empty, convert_int],
    }


@validator_args
def td_file_create(
    not_missing: types.Validator,
    ignore_empty: types.Validator,
) -> types.Schema:
    return {
        "name": [ignore_empty],
        "resource_id": [not_missing],
        "upload": [not_missing],
    }
