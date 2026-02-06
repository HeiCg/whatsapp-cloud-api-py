from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

_CAMEL_RE = re.compile(r"_([a-z0-9])")
_SNAKE_RE = re.compile(r"(?<=[a-z0-9])([A-Z])")


@lru_cache(maxsize=1024)
def to_camel(s: str) -> str:
    return _CAMEL_RE.sub(lambda m: m.group(1).upper(), s)


@lru_cache(maxsize=1024)
def to_snake(s: str) -> str:
    return _SNAKE_RE.sub(r"_\1", s).lower()


def _is_plain_object(v: Any) -> bool:
    return isinstance(v, dict)


def to_camel_deep(obj: Any) -> Any:
    if isinstance(obj, list):
        return [to_camel_deep(item) for item in obj]
    if _is_plain_object(obj):
        return {to_camel(k): to_camel_deep(v) for k, v in obj.items()}
    return obj


def to_snake_deep(obj: Any) -> Any:
    if isinstance(obj, list):
        return [to_snake_deep(item) for item in obj]
    if _is_plain_object(obj):
        return {to_snake(k): to_snake_deep(v) for k, v in obj.items()}
    return obj
