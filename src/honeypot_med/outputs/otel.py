"""OpenTelemetry-style log export for report events."""

from __future__ import annotations

from datetime import datetime, timezone


def _now_unix_nano() -> str:
    return str(int(datetime.now(timezone.utc).timestamp() * 1_000_000_000))


def _severity_number(severity: str) -> int:
    return {
        "low": 9,
        "medium": 13,
        "high": 17,
        "critical": 21,
    }.get(severity.lower(), 9)


def _attribute(key: str, value: str | int | bool) -> dict:
    if isinstance(value, bool):
        return {"key": key, "value": {"boolValue": value}}
    if isinstance(value, int):
        return {"key": key, "value": {"intValue": str(value)}}
    return {"key": key, "value": {"stringValue": str(value)}}


def report_to_otel_logs(report: dict, *, source_label: str, service_name: str = "honeypot-med") -> dict:
    """Return a JSON-serializable OTLP log payload."""
    records = []
    timestamp = _now_unix_nano()
    for index, event in enumerate(report.get("events", []), start=1):
        severity = str(event.get("severity", "low"))
        records.append(
            {
                "timeUnixNano": timestamp,
                "observedTimeUnixNano": timestamp,
                "severityText": severity.upper(),
                "severityNumber": _severity_number(severity),
                "body": {
                    "stringValue": (
                        f"Honeypot Med event {index}: {event.get('finding_count', 0)} findings, "
                        f"risk score {event.get('risk_score', 0)}"
                    )
                },
                "attributes": [
                    _attribute("honeypot_med.source", source_label),
                    _attribute("honeypot_med.event_index", index),
                    _attribute("honeypot_med.risk_score", int(event.get("risk_score", 0))),
                    _attribute("honeypot_med.finding_count", int(event.get("finding_count", 0))),
                    _attribute("honeypot_med.proven_count", int(event.get("proven_count", 0))),
                    _attribute("honeypot_med.prompt", str(event.get("prompt", ""))[:300]),
                ],
            }
        )

    return {
        "resourceLogs": [
            {
                "resource": {
                    "attributes": [
                        _attribute("service.name", service_name),
                        _attribute("service.namespace", "byteworthy"),
                        _attribute("telemetry.sdk.language", "python"),
                    ]
                },
                "scopeLogs": [
                    {
                        "scope": {"name": "honeypot_med.report", "version": str(report.get("version", ""))},
                        "logRecords": records,
                    }
                ],
            }
        ]
    }
