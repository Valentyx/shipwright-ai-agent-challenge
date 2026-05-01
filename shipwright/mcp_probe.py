"""CLI for probing configured live MCP connectors."""

from __future__ import annotations

import json
import os
from dataclasses import asdict

from shipwright.mcp_live import probe_all_from_env


def main() -> int:
    results = probe_all_from_env()
    print(json.dumps([asdict(result) | {"passed": result.passed, "decision": result.decision} for result in results], indent=2))
    strict = os.environ.get("SHIPWRIGHT_MCP_STRICT") == "1"
    return 0 if not strict or all(result.passed for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
