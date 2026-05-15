#!/usr/bin/env python3
import argparse
import json
import ssl
from typing import Any, Dict, List
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import urlopen


CHECKLIST: Dict[str, List[str]] = {
    "tracking": [
        "Validate event tracking for both source and destination stages.",
        "Check for recent tag manager, SDK, or schema changes.",
        "Verify timezone alignment in reports.",
    ],
    "lead_quality": [
        "Review lead qualification rules and recent rule updates.",
        "Check source/channel mix for lower-quality traffic spikes.",
        "Confirm deduplication and bot filtering behavior.",
    ],
    "ops_integration": [
        "Check CRM/API sync jobs and queue delays.",
        "Confirm no failed webhook deliveries between funnel systems.",
        "Verify owner assignment and routing rules are active.",
    ],
}
HTTP_REQUEST_TIMEOUT_SECONDS = 30


def _bucket_for_drop(drop_rate: float) -> str:
    """Map drop severity to the most likely troubleshooting area.

    >=70%: severe break often tied to tracking/data integrity gaps.
    >=50%: major operational friction typically in handoff/sync.
    <50%: moderate degradation often caused by lead quality changes.
    """
    if drop_rate >= 0.7:
        return "tracking"
    if drop_rate >= 0.5:
        return "ops_integration"
    return "lead_quality"


def analyze(stages: List[Dict[str, int]]) -> Dict[str, Any]:
    if len(stages) < 2:
        raise ValueError("At least two stages are required.")

    transitions = []
    for current, nxt in zip(stages, stages[1:]):
        current_count = int(current["count"])
        next_count = int(nxt["count"])
        if current_count <= 0:
            raise ValueError(f"Stage '{current['name']}' must have count > 0.")
        conversion = next_count / current_count
        drop_rate = 1 - conversion
        transitions.append(
            {
                "from": current["name"],
                "to": nxt["name"],
                "from_count": current_count,
                "to_count": next_count,
                "conversion_rate": conversion,
                "drop_rate": drop_rate,
            }
        )

    biggest_drop = max(transitions, key=lambda item: item["drop_rate"])
    bucket = _bucket_for_drop(biggest_drop["drop_rate"])
    return {
        "transitions": transitions,
        "biggest_drop": biggest_drop,
        "recommended_checks": CHECKLIST[bucket],
    }


def _is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _is_valid_json_content_type(content_type: str) -> bool:
    return content_type in {"application/json", "text/json"} or content_type.endswith("+json")


def _load_payload(input_source: str) -> Dict[str, Any]:
    if _is_http_url(input_source):
        try:
            ssl_context = ssl.create_default_context()
            with urlopen(
                input_source, timeout=HTTP_REQUEST_TIMEOUT_SECONDS, context=ssl_context
            ) as response:
                raw_content_type = response.headers.get("Content-Type", "")
                content_type = raw_content_type.split(";", 1)[0].strip().lower()
                if not _is_valid_json_content_type(content_type):
                    raise SystemExit(
                        f"URL must return JSON content, got '{content_type}': {input_source}"
                    )
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            raise SystemExit(f"Cannot read URL (HTTP {exc.code}): {input_source}") from exc
        except URLError as exc:
            raise SystemExit(f"Cannot read URL: {input_source} ({exc.reason})") from exc
        except UnicodeDecodeError as exc:
            raise SystemExit(f"URL content is not UTF-8 text: {input_source}") from exc

        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSON from URL: {input_source}") from exc

    try:
        with open(input_source, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as exc:
        raise SystemExit(f"Input file not found: {input_source}") from exc
    except PermissionError as exc:
        raise SystemExit(f"Cannot read input file (permission denied): {input_source}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in input file: {input_source}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Troubleshoot sales funnel drop-offs.")
    parser.add_argument("--input", required=True, help="Path or URL to a JSON input.")
    args = parser.parse_args()

    payload = _load_payload(args.input)

    funnel_name = payload.get("funnel_name", "Sales Funnel")
    stages = payload.get("stages", [])
    if len(stages) < 2:
        raise SystemExit("Invalid input: 'stages' must include at least two stage objects.")
    result = analyze(stages)

    print(f"=== {funnel_name} troubleshooting report ===")
    for t in result["transitions"]:
        print(
            f"{t['from']} -> {t['to']}: "
            f"conversion={t['conversion_rate']:.2%}, drop={t['drop_rate']:.2%} "
            f"({t['from_count']} -> {t['to_count']})"
        )

    largest = result["biggest_drop"]
    print("\nLargest issue point:")
    print(
        f"- {largest['from']} -> {largest['to']} with {largest['drop_rate']:.2%} drop "
        f"({largest['from_count']} -> {largest['to_count']})"
    )
    print("\nRecommended checks:")
    for item in result["recommended_checks"]:
        print(f"- {item}")


if __name__ == "__main__":
    main()
