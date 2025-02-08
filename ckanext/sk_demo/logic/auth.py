from __future__ import annotations

from typing import Any

import ckan.plugins.toolkit as tk
from ckan import authz
from ckan.types import Context


@tk.auth_allow_anonymous_access
def sk_demo_get_sum(context: Context, data_dict: dict[str, Any]):
    """Any user can compute sum."""
    return {"success": True}


def sk_demo_td_file_create(context: Context, data_dict: dict[str, Any]):
    """Authenticated user can create something."""
    return authz.is_authorized("resource_update", {"id": data_dict["resource_id"]})


def sk_demo_update_resource(context: Context, data_dict: dict[str, Any]):
    """Authenticated user can create something."""
    return authz.is_authorized("resource_update", {"id": data_dict["resource_id"]})
