"""System registry. The harness drives adapters by name; this is the map."""
from __future__ import annotations

import importlib

from systems.base import MemoryAdapter

_REGISTRY: dict[str, type[MemoryAdapter]] = {}


def register(cls: type[MemoryAdapter]) -> type[MemoryAdapter]:
    _REGISTRY[cls.name] = cls
    return cls


def build(name: str, **kwargs) -> MemoryAdapter:
    if name not in _REGISTRY:
        # lazy-import known adapters so users can pick a subset
        mapping = {
            "mnemosyne": "systems.mnemosyne",
            "mem0": "systems.mem0",
            "zep": "systems.zep",
            "naive": "systems.naive",
        }
        mod = mapping.get(name)
        if mod is None:
            raise KeyError(f"unknown system: {name!r}; known: {sorted(list(_REGISTRY) + list(mapping))}")
        m = importlib.import_module(mod)
        cls = getattr(m, f"{name.capitalize()}Adapter", None) or getattr(m, f"{name}Adapter", None)
        if cls is None:
            # fall back to scanning module for a MemoryAdapter subclass
            for attr in dir(m):
                obj = getattr(m, attr)
                if isinstance(obj, type) and issubclass(obj, MemoryAdapter) and obj is not MemoryAdapter:
                    cls = obj
                    break
        if cls is None:
            raise KeyError(f"could not locate adapter class in {mod}")
        _REGISTRY[cls.name] = cls
    return _REGISTRY[name](**kwargs)


def available() -> list[str]:
    return sorted(set(list(_REGISTRY) + ["mnemosyne", "mem0", "zep", "naive"]))


# register the built-in naive baseline so it is always present
import systems.naive  # noqa: E402,F401

register(__import__("systems.naive", fromlist=["NaiveBaselineAdapter"]).NaiveBaselineAdapter)
