#!/usr/bin/env python3
"""Behavioral regression tests for the reference/config/catalog contract."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1] / "skills/science-video-production"
spec = importlib.util.spec_from_file_location("reference_checks", ROOT / "scripts/check_reference_system.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ReferenceSystemTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "skill"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns("__pycache__"))
    def tearDown(self):
        self.temp.cleanup()
    def edit(self, path, f):
        p = self.root / path
        d = json.loads(p.read_text())
        f(d)
        p.write_text(json.dumps(d, ensure_ascii=False))
    def errors(self, text):
        self.assertTrue(any(text in e for e in m.check(self.root)), m.check(self.root))
    def test_clean_system(self):
        self.assertEqual(m.check(self.root), [])
    def test_duplicate_responsibility(self):
        self.edit("indexes/rule-owners.json", lambda d: d["owners"][1]["owns"].append(d["owners"][0]["owns"][0]))
        self.errors("multiple owners")
    def test_missing_owner(self):
        self.edit("indexes/rule-owners.json", lambda d: d["owners"].pop())
        self.errors("seven")
    def test_missing_reference_file(self):
        (self.root / "references/shotbook.md").unlink()
        self.errors("owner file")
    def test_caption_idempotence_and_scaling(self):
        p = json.loads((self.root / "config/series-profile.json").read_text())
        self.assertEqual(m.caption_baselines(p, 1080, 1920), {"narration": 1615, "real_footage": 1690})
        self.assertEqual(m.caption_baselines(p, 1080, 1920), m.caption_baselines(copy.deepcopy(p), 1080, 1920))
        self.assertEqual(m.caption_baselines(p, 540, 960), {"narration": 808, "real_footage": 845})
        with self.assertRaises(ValueError):
            m.caption_baselines(p, 1920, 1080)
    def test_repeated_caption_increment_rejected(self):
        self.edit("config/series-profile.json", lambda d: d["captions"]["baselines"]["narration"].update(target=1515))
        self.errors("increment inconsistent")
    def test_real_video_required(self):
        self.edit("config/series-profile.json", lambda d: d["medium"].update(real_anchor="photo"))
        self.errors("real video")
    def test_reference_not_media_license(self):
        self.edit("indexes/aesthetic-references.json", lambda d: d["entries"][0].update(production_use="granted"))
        self.errors("does not grant")
    def test_changed_component_needs_new_hash(self):
        p = self.root / "assets/style/leader-and-arrow.svg"
        p.write_text(p.read_text().replace("#243840", "#000000"))
        self.errors("hash mismatch")
    def test_external_svg_dependency(self):
        p = self.root / "assets/style/leader-and-arrow.svg"
        p.write_text(p.read_text().replace("</svg>", '<image href="https://example.test/private.png"/></svg>'))
        self.errors("embeds media")
    def test_path_escape_rejected(self):
        self.edit("indexes/reusable-assets.json", lambda d: d["entries"][0].update(file="../../outside.svg"))
        self.errors("escapes")
    def test_duplicate_asset_id(self):
        self.edit("indexes/reusable-assets.json", lambda d: d["entries"].append(copy.deepcopy(d["entries"][0])))
        self.errors("duplicate asset")
    def test_science_color_priority(self):
        self.edit("assets/style/bright-nature.tokens.json", lambda d: d.update(science_color_priority=False))
        self.errors("science colors")
    def test_ratio_not_universal_gate(self):
        self.edit("assets/style/bright-nature.tokens.json", lambda d: d["suggested_scene_ratio"].update(status="mandatory"))
        self.errors("adjustable")
    def test_invalid_hex_rejected(self):
        self.edit("assets/style/bright-nature.tokens.json", lambda d: d["colors"]["sky"].update(hex="blue"))
        self.errors("palette")
    def test_private_id_rejected(self):
        (self.root / "leak.md").write_text("libfile_" + "a" * 32)
        self.errors("private identity")
    def test_broken_anchor_rejected(self):
        p = self.root / "SKILL.md"
        p.write_text(p.read_text() + "\n[broken](references/visual-system.md#not-a-section)\n")
        self.errors("broken heading")
    def test_malformed_config_rejected(self):
        (self.root / "config/series-profile.json").write_text("{")
        self.errors("malformed")


    def test_failure_clause_text_stale(self):
        self.edit("indexes/standard-coverage.json", lambda d: d["failure_contracts"][0]["clauses"][0].update(quote="invented reference text"))
        self.errors("failure clause text missing/stale")
    def test_failure_clause_digest_stale(self):
        self.edit("indexes/standard-coverage.json", lambda d: d["failure_contracts"][0]["clauses"][0].update(quote_sha256="0" * 64))
        self.errors("failure clause digest inconsistent")
    def test_failure_contract_unresolved(self):
        self.edit("indexes/standard-coverage.json", lambda d: d["rules"][0].update(failure_condition_ref={"contract_id":"unknown"}))
        self.errors("rule precise failure reference missing")
    def test_unreviewed_mapping_cannot_claim_complete(self):
        self.edit("indexes/standard-coverage.json", lambda d: d["rules"][0].update(mapping_status="pending"))
        self.errors("rule semantic mapping unresolved")

    def test_art_handoff_rule_removal_breaks_reference_integrity(self):
        """Deleting an execution boundary must fail structurally, not judge art."""
        contracts = {c["id"]: c for c in json.loads(
            (self.root / "indexes/standard-coverage.json").read_text())["failure_contracts"]}
        cases = [
            ("field-gates", "G2的低精细度指尚未精修", "references/production-checkpoints.md"),
            ("field-style_approval", "把当前生产资产经实际渲染", "references/visual-system.md"),
            ("field-style_approval", "若实际资产已变成另一种造型语言", "references/visual-system.md"),
            ("V-natural_editable_shapes", "对本镜需要独立显隐", "references/visual-system.md"),
            ("field-art", "已有批准画风时，美术审查须核", "references/quality-acceptance.md"),
        ]
        for ident, prefix, owner in cases:
            with self.subTest(contract=ident, clause=prefix):
                matches = [c for c in contracts[ident]["clauses"] if c["quote"].startswith(prefix)]
                self.assertEqual(len(matches), 1, "Execution rule must have a precise existing-contract reference")
                clause = matches[0]
                self.assertEqual(clause["file"], owner)
                p = self.root / owner
                original = p.read_text()
                try:
                    p.write_text(original.replace(clause["quote"], ""))
                    self.errors("failure clause text missing/stale")
                finally:
                    p.write_text(original)
        self.assertEqual(m.check(self.root), [])

if __name__ == "__main__":
    unittest.main()
