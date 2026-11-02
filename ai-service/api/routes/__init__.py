"""Route package without eager cross-feature imports.

Importing ``api.routes.voice`` must not initialize TRACE-CAG, MongoDB chat, or
other unrelated stacks. Legacy ``*_router`` exports remain available lazily.
"""

from importlib import import_module
from typing import Any

_ROUTER_MODULES = {
    "ai_router": "ai",
    "chat_router": "chat",
    "stt_router": "stt",
    "tts_router": "tts",
    "topic_chat_router": "topic_chat",
}

__all__ = list(_ROUTER_MODULES)


def __getattr__(name: str) -> Any:
    module_name = _ROUTER_MODULES.get(name)
    if module_name is None:
        raise AttributeError(name)
    return import_module(f"{__name__}.{module_name}").router
