"""HTTP capture service for honeypot-med decoy endpoints."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .decoys import DecoyRoute
from .errors import ValidationError
from .events import events_to_payload, normalize_event
from .models import InputPayload
from .redaction import redact_event
from .service import analyze_prompts
from .store import JSONLStore

LOGGER = logging.getLogger("honeypot_med.server")


@dataclass(frozen=True)
class ServerConfig:
    store_path: Path
    min_high_risk: int
    proof_required: bool
    api_key: str | None
    decoy_routes: tuple[DecoyRoute, ...] = ()
    max_body_bytes: int = 1_000_000


class HoneypotHTTPServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], config: ServerConfig):
        super().__init__(address, HoneypotRequestHandler)
        self.config = config
        self.store = JSONLStore(config.store_path)


class HoneypotRequestHandler(BaseHTTPRequestHandler):
    server: HoneypotHTTPServer

    def _send_json(self, status: HTTPStatus, payload: dict) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _error(self, status: HTTPStatus, message: str) -> None:
        self._send_json(status, {"error": message})

    def _authorized(self) -> bool:
        api_key = self.server.config.api_key
        if not api_key:
            return True
        auth_header = self.headers.get("Authorization", "")
        expected = f"Bearer {api_key}"
        return auth_header == expected

    def _read_json_body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            raise ValidationError("request body is required")
        if content_length > self.server.config.max_body_bytes:
            raise ValidationError(
                f"request body too large: {content_length} bytes exceeds max {self.server.config.max_body_bytes}"
            )
        data = self.rfile.read(content_length)
        try:
            payload = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValidationError(f"invalid JSON body: {exc}") from exc
        if not isinstance(payload, dict):
            raise ValidationError("request body must be a JSON object")
        return payload

    def _analyze_event(self, event: dict) -> dict:
        payload = InputPayload.from_dict(events_to_payload([event]))
        report = analyze_prompts(
            payload,
            min_high_risk=self.server.config.min_high_risk,
            proof_required=self.server.config.proof_required,
        )
        return report["events"][0]

    def _capture_event(self, raw_event: dict, *, source: str, metadata: dict | None = None) -> dict:
        if metadata:
            raw_metadata = raw_event.get("metadata", {})
            if not isinstance(raw_metadata, dict):
                raw_metadata = {}
            raw_event = dict(raw_event)
            merged = dict(raw_metadata)
            merged.update(metadata)
            raw_event["metadata"] = merged

        redacted_event, _ = redact_event(raw_event)
        event = normalize_event(redacted_event, default_source=source)
        self.server.store.append(event)
        event_report = self._analyze_event(event)

        return {
            "event_id": event["event_id"],
            "trace_id": event["trace_id"],
            "source": event["source"],
            "severity": event_report["severity"],
            "risk_score": event_report["risk_score"],
            "finding_count": event_report["finding_count"],
            "proven_count": event_report["proven_count"],
            "findings": event_report["findings"],
        }

    def _plugin_decoy_for_path(self, path: str) -> DecoyRoute | None:
        for route in self.server.config.decoy_routes:
            if route.path == path:
                return route
        return None

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "ok",
                    "event_count": self.server.store.count(),
                    "store_path": str(self.server.config.store_path),
                },
            )
            return

        self._error(HTTPStatus.NOT_FOUND, "not found")

    def do_POST(self) -> None:  # noqa: N802
        if not self._authorized():
            self._error(HTTPStatus.UNAUTHORIZED, "unauthorized")
            return

        parsed = urlparse(self.path)

        try:
            body = self._read_json_body()

            if parsed.path == "/capture":
                raw_event = body.get("event", body)
                result = self._capture_event(raw_event, source="api.capture")
                self._send_json(HTTPStatus.OK, {"status": "captured", **result})
                return

            if parsed.path == "/decoy/fhir/query":
                prompt = body.get("prompt")
                query = body.get("query")
                if not isinstance(prompt, str) or not prompt.strip():
                    if isinstance(query, str) and query.strip():
                        prompt = f"FHIR query request: {query.strip()}"
                    else:
                        prompt = "FHIR query request"

                decoy_raw_event = {
                    "prompt": prompt,
                    "tool_calls": [
                        {
                            "name": "fhir.decoy.search",
                            "args": json.dumps(body, sort_keys=True),
                        }
                    ],
                    "model_output": "Decoy FHIR endpoint invoked for honeypot telemetry.",
                    "response": "No records found.",
                }

                result = self._capture_event(
                    decoy_raw_event,
                    source="decoy.fhir.query",
                    metadata={"endpoint": parsed.path, "client": self.client_address[0]},
                )
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "status": "decoy_response",
                        "decoy": {"resourceType": "Bundle", "total": 0, "entry": []},
                        **result,
                    },
                )
                return

            plugin_route = self._plugin_decoy_for_path(parsed.path)
            if plugin_route:
                prompt = body.get("prompt")
                if not isinstance(prompt, str) or not prompt.strip():
                    prompt = plugin_route.default_prompt
                decoy_raw_event = {
                    "prompt": prompt,
                    "tool_calls": [
                        {
                            "name": plugin_route.tool_name,
                            "args": json.dumps(body, sort_keys=True),
                        }
                    ],
                    "model_output": f"Decoy endpoint {plugin_route.path} invoked.",
                    "response": "Plugin decoy response returned.",
                }
                result = self._capture_event(
                    decoy_raw_event,
                    source=plugin_route.source,
                    metadata={"endpoint": parsed.path, "client": self.client_address[0]},
                )
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "status": "decoy_response",
                        "decoy": plugin_route.response_body,
                        **result,
                    },
                )
                return

            self._error(HTTPStatus.NOT_FOUND, "not found")

        except ValidationError as exc:
            LOGGER.warning("request validation error: %s", exc)
            self._error(HTTPStatus.BAD_REQUEST, str(exc))
        except Exception as exc:  # pragma: no cover
            LOGGER.exception("unhandled request error: %s", exc)
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR, "internal server error")

    def log_message(self, fmt: str, *args) -> None:  # noqa: A003
        LOGGER.info("%s - %s", self.address_string(), fmt % args)



def run_server(
    host: str,
    port: int,
    *,
    store_path: Path,
    min_high_risk: int,
    proof_required: bool,
    api_key: str | None,
    decoy_routes: tuple[DecoyRoute, ...] = (),
    max_body_bytes: int = 1_000_000,
) -> None:
    config = ServerConfig(
        store_path=store_path,
        min_high_risk=min_high_risk,
        proof_required=proof_required,
        api_key=api_key,
        decoy_routes=decoy_routes,
        max_body_bytes=max_body_bytes,
    )

    server = HoneypotHTTPServer((host, port), config=config)
    LOGGER.info("honeypot-med server listening on http://%s:%s", host, port)
    LOGGER.info("store path: %s", store_path)

    try:
        server.serve_forever()
    except KeyboardInterrupt:  # pragma: no cover
        LOGGER.info("shutdown requested")
    finally:
        server.server_close()
