"""Template helpers of the sk_demo plugin.

All non-private functions defined here are registered inside `tk.h` collection.
"""

from __future__ import annotations
from typing import Any


from ckanext.sk_demo.shared import enrich_mapping


def sk_demo_hello() -> str:
    """Greet the user.

    Returns:
        greeting with the plugin name.
    """
    return "Hello, sk_demo!"


def sk_demo_enrich_mapping(id: str) -> dict[str, dict[str, Any]]:
    return enrich_mapping(id)
