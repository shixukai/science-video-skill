"""Synthetic cover records and colored pixels only; no actual visual approval."""
import hashlib
import json
from pathlib import Path
import struct
import zlib

from cover_guard import OBSERVATIONS, VARIANTS


def png(path, width, height, rgb=(24, 98, 165)):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    raw = b"".join(b"\0" + bytes(rgb) * width for _ in range(height))
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def ref(root, name):
    return {"file": name, "sha256": hashlib.sha256((root / name).read_bytes()).hexdigest()}


def attach_cover_fixture(data, root):
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    qa = data.setdefault("qa", {}); exports = data.setdefault("deliverables", {})
    hashes = qa.setdefault("reviewed_sha256", {})
    png(root / "synthetic-approved-cover.png", 12, 16)
    (root / "synthetic-cover-approval.txt").write_text("Synthetic fixture; no actual user, review, or authorization.")
    baseline = ref(root, "synthetic-approved-cover.png")
    record = {"schema_version": 1, "status": "pass", "producer": "synthetic producer",
              "reviewer": "synthetic independent reviewer", "reviewed_at": "2026-01-01T00:00:00Z",
              "independent_review": True, "method": "actual_images_and_mobile_comparison",
              "baseline": {"kind": "approved_cover", "scope": "cover_appearance", "image": baseline,
                           "approval_evidence": ref(root, "synthetic-cover-approval.txt"),
                           "approval_reference": "synthetic fixture only, not real approval",
                           "approved_image_sha256": baseline["sha256"], "actually_opened": True,
                           "observation": "Synthetic observation fixture; no actual perception."}, "variants": {}}
    for name, ratio in VARIANTS.items():
        if not exports.get(name) or Path(exports[name]).suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
            exports[name] = name + ".png"
            png(root / exports[name], ratio[0] * 16, ratio[1] * 16)
        export = ref(root, exports[name]); hashes[name] = export["sha256"]
        preview_name = name + "-phone.png"; comparison_name = name + "-comparison.png"
        png(root / preview_name, ratio[0] * 2, ratio[1] * 2)
        png(root / comparison_name, 24, 16, (18, 133, 144))
        preview = dict(ref(root, preview_name), source_sha256=export["sha256"], display_width_px=270 if name == "cover_3_4" else 360,
                       display_context="phone_thumbnail", actually_opened=True)
        record["variants"][name] = {
            "export": export, "actual_export_opened": True, "baseline_compared": True,
            "layout_kind": "independent_cover_scene", "style": "detailed_2d_nature", "title_position": "upper_left",
            "subject": "Synthetic natural subject", "title": "Synthetic title", "question": "Synthetic question?",
            "prohibited_elements": [], "mobile_preview": preview,
            "comparison": dict(ref(root, comparison_name), actually_opened=True, baseline_sha256=baseline["sha256"],
                               export_sha256=export["sha256"], preview_sha256=preview["sha256"]),
            "observations": {key: {"status": "pass", "observation": "Synthetic record check only; no actual visual review."} for key in OBSERVATIONS}}
    qa.setdefault("covers", {}).update(status="pass", reviewer=record["reviewer"], note="Synthetic declared cover review only", evidence="synthetic-cover-review.json")
    save_cover_fixture(data, root, record)
    return record


def save_cover_fixture(data, root, record):
    root = Path(root); name = "synthetic-cover-review.json"
    (root / name).write_text(json.dumps(record, ensure_ascii=False))
    data["qa"]["covers"]["visual_review"] = ref(root, name)
