"""Small Cloud Run-compatible HTTP surface for the demo."""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from shipwright.evaluation import build_seeded_coordinator, run_evaluations


class ShipwrightHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/healthz":
            self._json({"ok": True})
            return
        if self.path == "/demo":
            coordinator = build_seeded_coordinator(missing_dependency=True)
            result = coordinator.run_demo()
            self._json(
                {
                    "dependency_findings": [finding.summary for finding in result["dependency_findings"]],
                    "memory_summary_id": result["memory_summary_id"],
                    "slack_messages": coordinator.mcp.slack_messages,  # type: ignore[attr-defined]
                    "jira_comments": coordinator.mcp.issues["SHIP-100"].comments,  # type: ignore[attr-defined]
                }
            )
            return
        if self.path == "/eval":
            self._json(
                {
                    "results": [
                        {"name": result.name, "passed": result.passed, "detail": result.detail}
                        for result in run_evaluations()
                    ]
                }
            )
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        print(f"shipwright_http {self.address_string()} {format % args}")

    def _json(self, payload: object) -> None:
        body = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), ShipwrightHandler)
    print(f"Shipwright demo server listening on :{port}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
