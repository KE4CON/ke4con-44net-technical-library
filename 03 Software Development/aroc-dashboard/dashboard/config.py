# AROC Dashboard — configuration loading.  GPLv3, see dashboard/__init__.py.
"""Load ``config.yaml`` and expand ``${ENV_VAR}`` references.

Secrets never need to live in the YAML file: any string value may contain
``${NAME}`` or ``${NAME:-default}``; the value is substituted from the process
environment (or from a ``.env`` file next to the config) at load time.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

_ENV_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")


def load_dotenv(path: Path) -> None:
    """Populate ``os.environ`` from a simple ``KEY=value`` file (existing vars win)."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'\"")
        os.environ.setdefault(key, value)


def _expand(value: Any) -> Any:
    if isinstance(value, str):
        def repl(m: re.Match[str]) -> str:
            name, default = m.group(1), m.group(2)
            if name in os.environ:
                return os.environ[name]
            if default is not None:
                return default
            raise KeyError(f"config references ${{{name}}} but it is not set in the environment")
        return _ENV_RE.sub(repl, value)
    if isinstance(value, list):
        return [_expand(v) for v in value]
    if isinstance(value, dict):
        return {k: _expand(v) for k, v in value.items()}
    return value


def load_config(path: str | os.PathLike[str]) -> dict[str, Any]:
    cfg_path = Path(path)
    load_dotenv(cfg_path.with_name(".env"))
    with cfg_path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    cfg = _expand(raw)
    cfg.setdefault("dashboard", {})
    cfg["dashboard"].setdefault("title", "Operations Center")
    cfg["dashboard"].setdefault("refresh_seconds", 30)
    cfg["dashboard"].setdefault("history_points", 24)
    cfg.setdefault("services", [])
    seen: set[str] = set()
    for svc in cfg["services"]:
        if "id" not in svc or "type" not in svc:
            raise ValueError(f"every service needs an 'id' and a 'type': {svc}")
        if svc["id"] in seen:
            raise ValueError(f"duplicate service id: {svc['id']}")
        seen.add(svc["id"])
    return cfg
