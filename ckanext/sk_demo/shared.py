from __future__ import annotations
from typing import Any
import ckan.plugins.toolkit as tk
from ckanext.toolbelt.decorators import Cache


def enrich_flake_name(id: str):
    return f"sk:enrich_configuration:{id}"


@Cache()
def enrich_mapping(id: str) -> dict[str, dict[str, Any]]:
    """Return field mapping for the dataset."""
    flake_name = enrich_flake_name(id)

    try:
        flake = tk.get_action("flakes_flake_lookup")(
            {"ignore_auth": True}, {"author_id": None, "name": flake_name}
        )
        return flake["data"]

    except tk.ObjectNotFound:
        return {"dataset": {}, "resource": {}}
