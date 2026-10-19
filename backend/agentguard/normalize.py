import posixpath
import re
import unicodedata
from urllib.parse import unquote
from typing import Any


def decode_repeated(value: str) -> str:
    for _ in range(3):
        decoded = unquote(value)
        if decoded == value:
            break
        value = decoded
    return value


def normalize_string(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).replace("\x00", "")
    value = decode_repeated(value)
    value = re.sub(r"[ \t\r\n\f\v]+", " ", value).strip()
    return value


def normalize_path(value: str, workspace_root: str = "/workspace") -> str:
    value = normalize_string(value).replace("\\", "/")
    if value == "~" or value.startswith("~/"):
        value = "/~" + value[1:]
    if not value.startswith("/"):
        value = "/" + value
    return posixpath.normpath(value)


def normalize_arguments(value: Any, workspace_root: str = "/workspace") -> Any:
    if isinstance(value, dict):
        return {str(k): normalize_arguments(v, workspace_root) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize_arguments(v, workspace_root) for v in value]
    if isinstance(value, str):
        return normalize_string(value)
    return value
