#!/usr/bin/env python3
import argparse
import json
from typing import Dict, List


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


def _bucket_for_drop(drop_rate: float) -> str:
    if drop_rate >= 0.7:
        return "tracking"
    if drop_rate >= 0.5:
        return "ops_integration"
    return "lead_quality"


def analyze(stages: List[Dict[str, int]]) -> Dict[str, object]:
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Troubleshoot sales funnel drop-offs.")
    parser.add_argument("--input", required=True, help="Absolute path to a JSON input file.")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        payload = json.load(f)

    funnel_name = payload.get("funnel_name", "Sales Funnel")
    stages = payload.get("stages", [])
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
