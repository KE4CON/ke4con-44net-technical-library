# AROC Dashboard — shared HTTP client helper.  GPLv3, see dashboard/__init__.py.
from __future__ import annotations

from typing import Any

import httpx


def make_client(cfg: dict[str, Any], timeout: float, **kwargs: Any) -> httpx.AsyncClient:
    """Build an ``httpx.AsyncClient`` honouring the common ``verify_tls`` option.

    Most home-lab management interfaces use self-signed certificates, so
    ``verify_tls: false`` is allowed per service.  Default is to verify.
    """
    verify: bool | str = cfg.get("verify_tls", True)
    if isinstance(verify, str) and verify.lower() in {"false", "no", "0"}:
        verify = False
    return httpx.AsyncClient(timeout=timeout, verify=verify, **kwargs)
