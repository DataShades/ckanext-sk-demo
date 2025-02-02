"""Template helpers of the sk_demo plugin.

All non-private functions defined here are registered inside `tk.h` collection.
"""

from __future__ import annotations


def sk_demo_hello() -> str:
    """Greet the user.

    Returns:
        greeting with the plugin name.
    """
    return "Hello, sk_demo!"
