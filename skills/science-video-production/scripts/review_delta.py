#!/usr/bin/env python3
"""Compare stage contexts or derive text-channel coverage. Never writes approval."""
import argparse
import copy
import json
from pathlib import Path
from stage_checks import context_sha256, GATES


def normalize_channels(data):
    """Only derive inventory membership; no inference about rendered media."""
    result = copy.deepcopy(data)
    inventory = result.get("presentation_text")
    if not isinstance(inventory, dict) or not isinstance(inventory.get("items"), list):
        raise ValueError("A declared presentation_text.items list is required")
    surfaces = {"frame", "caption", "voiceover", "cover"}
    if any(not isinstance(item, dict) or item.get("surface") not in surfaces for item in inventory["items"]):
        raise ValueError("Invalid item surface; fix classification before deriving coverage")
    channels = inventory.setdefault("channels", {})
    if not isinstance(channels, dict) or set(channels) - surfaces:
        raise ValueError("Invalid channel inventory")
    for surface in sorted(surfaces):
        channel = channels.setdefault(surface, {})
        if not isinstance(channel, dict):
            raise ValueError("Channel must be an object")
        channel["status"] = "present" if any(item["surface"] == surface for item in inventory["items"]) else "absent"
        if not isinstance(channel.get("note"), str) or not channel["note"].strip():
            channel["note"] = "Coverage derived from declared items; actual media inspection remains separate."
    return result


def compare(before, after):
    return {"kind": "review_context_delta", "stages": {
        gate: {"before": context_sha256(before, gate), "after": context_sha256(after, gate),
               "changed": context_sha256(before, gate) != context_sha256(after, gate)} for gate in GATES},
        "meaning": "Triage only. Unchanged context is not approval; verify original evidence, actual files, scope and unresolved failures. Old receipts are not rewritten."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    normalize = sub.add_parser("normalize-text"); normalize.add_argument("input"); normalize.add_argument("output")
    delta = sub.add_parser("compare"); delta.add_argument("before"); delta.add_argument("after")
    args = parser.parse_args()
    def read(path): return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if args.command == "compare":
        print(json.dumps(compare(read(args.before), read(args.after)), ensure_ascii=False, indent=2))
    else:
        data = normalize_channels(read(args.input))
        with Path(args.output).open("x", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2); stream.write("\n")


if __name__ == "__main__":
    main()
