from __future__ import annotations

from typing import Any

import ckan.plugins.toolkit as tk
from ckan import model
from ckan.logic import validate
from ckan.types import Context

from ckanext.sk_demo.model import Something

from . import schema


@tk.side_effect_free
@validate(schema.get_sum)
def sk_demo_get_sum(context: Context, data_dict: dict[str, Any]):
    """Produce a sum of left and right.

    Args:
        left (int): firt argument
        right (int): second argument

    Returns:
        operation details
    """
    tk.check_access("sk_demo_get_sum", context, data_dict)

    return {
        "left": data_dict["left"],
        "right": data_dict["right"],
        "sum": data_dict["left"] + data_dict["right"],
    }


@validate(schema.td_file_create)
def sk_demo_td_file_create(context: Context, data_dict: dict[str, Any]):
    """Upload file for tabledesigner ingestion.

    Args:
        resource_id (str): ID of the owner

    Returns:
        details of the new file
    """
    tk.check_access("sk_demo_td_file_create", context, data_dict)

    internal_context = tk.fresh_context(context)
    internal_context["ignore_auth"] = True

    file = tk.get_action("files_file_create")(
        internal_context,
        {
            "upload": data_dict["upload"],
            "name": data_dict.get("name"),
            "storage": "td",
        },
    )
    return tk.get_action("files_transfer_ownership")(
        internal_context,
        {
            "id": file["id"],
            "owner_id": data_dict["resource_id"],
            "owner_type": "resource",
        },
    )
