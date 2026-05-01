"""Structured observability helpers.

Cloud Run captures stdout/stderr into Cloud Logging. These JSON lines give the
demo a traceable record of agent decisions and MCP tool actions without adding
a hard dependency on google-cloud-logging for local tests.
"""

from __future__ import annotations

import json
import os

from shipwright.contracts import utc_now_iso


def record_event(event: str, **fields: object) -> None:
    if os.environ.get("SHIPWRIGHT_QUIET_LOGS") == "1":
        return
    payload = {"event": event, "timestamp": utc_now_iso(), **fields}
    print(json.dumps(payload, default=str, sort_keys=True))
