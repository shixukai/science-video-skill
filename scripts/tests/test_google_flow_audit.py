#!/usr/bin/env python3
"""Unit tests for scripts/google_flow_audit.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT_PATH = SKILL_ROOT / "scripts" / "google_flow_audit.py"
PYTHON = sys.executable


def make_clip(path: Path, width: int = 1920, height: int = 1080, fps: int = 24, duration_s: float = 7.833) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c=black:s={width}x{height}:r={fps}:d={duration_s}",
        "-f",
        "lavfi",
        "-i",
        f"anullsrc=r=48000:cl=stereo:d={duration_s}",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-pix_fmt",
        "yuv420p",
        "-r",
        str(fps),
        "-c:a",
        "aac",
        "-shortest",
        str(path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed creating fixture {path}: {proc.stderr}")


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def run_audit(args: list[str]) -> tuple[int, dict | None, str]:
    proc = subprocess.run([PYTHON, "-X", "utf8", str(SCRIPT_PATH), "measure", *args], capture_output=True, text=True, encoding="utf-8")
    report_idx = args.index("--report") + 1
    rpath = Path(args[report_idx])
    data = json.loads(rpath.read_text(encoding="utf-8")) if rpath.is_file() else None
    return proc.returncode, data, proc.stderr


class GoogleFlowAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.clips_dir = self.root / "clips"
        self.clips_dir.mkdir(parents=True, exist_ok=True)
        for sid in ("SH01", "SH02", "SH03"):
            make_clip(self.clips_dir / f"{sid}.mp4", 1920, 1080, 24, 7.833)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _build_clean_project(self) -> tuple[Path, Path, Path, Path, Path, Path]:
        zh_vid = self.root / "export_zh.mp4"
        en_vid = self.root / "export_en.mp4"
        make_clip(zh_vid, 1920, 1080, 24, 18.0)
        make_clip(en_vid, 1920, 1080, 24, 18.0)

        zh_srt = self.root / "captions.zh.srt"
        zh_srt.write_text(
            "1\n00:00:00,000 --> 00:00:05,200\n玻璃假体里的液体在稳定流动。\n\n"
            "2\n00:00:06,200 --> 00:00:11,500\n加热后压力把阀门顶开了一毫米。\n\n"
            "3\n00:00:12,500 --> 00:00:17,600\n冷却收缩后阀门重新回落闭合。\n",
            encoding="utf-8",
            newline="\n",
        )
        en_srt = self.root / "captions.en.srt"
        en_srt.write_text(
            "1\n00:00:00,000 --> 00:00:05,100\nFluid inside the clear glass phantom\nmoves steadily upward.\n\n"
            "2\n00:00:06,100 --> 00:00:11,400\nHeating pushes the inner valve open\nby one millimeter.\n\n"
            "3\n00:00:12,400 --> 00:00:17,500\nWhen the vessel cools down again,\nthe valve closes shut.\n",
            encoding="utf-8",
            newline="\n",
        )

        # ~54 CJK chars over ~15.5s active cue span = ~209 chars/min; ~36 EN words over ~15.4s active cue span = ~140 wpm.
        zh_text = "玻璃假体里的液体在稳定流动，随着底部持续升温，压力稳步上升并顶开内部阀门，随后冷却使阀门重新完全闭合。"
        en_text = (
            "Fluid inside the clear phantom moves steadily forward through the channel. "
            "As heat rises from below, internal pressure pushes the valve smoothly open. "
            "Once the vessel cools back down, the valve settles shut cleanly."
        )
        ep_zh = self.root / "episode.zh.json"
        ep_en = self.root / "episode.en.json"
        common_design = {"production_route": "google_flow", "output": {"width": 1920, "height": 1080, "fps": 24}}
        shots_zh = [
            {"id": "SH01", "duration_s": 6.0, "observation_hold_s": 0.9},
            {"id": "SH02", "duration_s": 6.0, "observation_hold_s": 0.9},
            {"id": "SH03", "duration_s": 6.0, "observation_hold_s": 0.9},
        ]
        shots_en = [
            {"id": "SH01", "duration_s": 6.0, "observation_hold_s": 0.9},
            {"id": "SH02", "duration_s": 6.0, "observation_hold_s": 0.9},
            {"id": "SH03", "duration_s": 6.0, "observation_hold_s": 0.9},
        ]
        write_json(ep_zh, {"design": common_design, "narration": {"language": "zh", "text": zh_text}, "shots": shots_zh, "captions": {"file": "captions.zh.srt", "wrap_style": 2, "font_size": 22}})
        write_json(ep_en, {"design": common_design, "narration": {"language": "en", "text": en_text}, "shots": shots_en, "captions": {"file": "captions.en.srt", "wrap_style": 0}})
        return zh_vid, en_vid, ep_zh, ep_en, zh_srt, en_srt

    def test_clean_bilingual_pass(self) -> None:
        zh_vid, en_vid, ep_zh, ep_en, _, _ = self._build_clean_project()
        report = self.root / "report_clean.json"
        code, data, err = run_audit([
            str(zh_vid),
            "--en-video",
            str(en_vid),
            "--episode-zh",
            str(ep_zh),
            "--episode-en",
            str(ep_en),
            "--clips-dir",
            str(self.clips_dir),
            "--report",
            str(report),
        ])
        self.assertEqual(code, 0, f"Unexpected stderr/flags: {err} {data}")
        self.assertEqual(data["status"], "clean")
        self.assertEqual(data["flags"], [])

    def test_clips_only_catches_720p(self) -> None:
        make_clip(self.clips_dir / "SH04.mp4", 1280, 720, 24, 7.917)
        report = self.root / "report_720.json"
        code, data, _ = run_audit(["--clips-only", "--clips-dir", str(self.clips_dir), "--report", str(report)])
        self.assertEqual(code, 1)
        self.assertIn("low_res_source_clip", data["summary"]["flag_codes"])

    def test_catches_clip_duration_overrun_and_fps_cadence_and_mismatch(self) -> None:
        zh_vid, en_vid, ep_zh, ep_en, _, _ = self._build_clean_project()
        make_clip(en_vid, 1920, 1080, 30, 12.0)
        ep_zh_data = json.loads(ep_zh.read_text(encoding="utf-8"))
        ep_zh_data["shots"][1]["duration_s"] = 10.5  # > 7.833 s native clip
        ep_zh_data["narration"]["text"] = "高" * 110  # ~366 chars/min
        for s in ep_zh_data["shots"]:
            s["observation_hold_s"] = 0.0
        write_json(ep_zh, ep_zh_data)

        ep_en_data = json.loads(ep_en.read_text(encoding="utf-8"))
        ep_en_data["shots"] = ep_en_data["shots"][:2]  # mismatched shot count/order
        write_json(ep_en, ep_en_data)

        report = self.root / "report_bad.json"
        code, data, _ = run_audit([
            str(zh_vid),
            "--en-video",
            str(en_vid),
            "--episode-zh",
            str(ep_zh),
            "--episode-en",
            str(ep_en),
            "--clips-dir",
            str(self.clips_dir),
            "--report",
            str(report),
        ])
        self.assertEqual(code, 1)
        codes = set(data["summary"]["flag_codes"])
        self.assertIn("clip_duration_overrun", codes)
        self.assertIn("fps_cadence_mismatch", codes)
        self.assertIn("speech_rate_out_of_range", codes)
        self.assertIn("missing_observation_holds", codes)
        self.assertIn("shot_sequence_mismatch", codes)
        self.assertIn("edition_duration_divergence", codes)

    def test_refuses_overwrite_existing_report(self) -> None:
        report = self.root / "existing.json"
        report.write_text("{\"keep\": true}\n", encoding="utf-8")
        code, data, err = run_audit(["--clips-only", "--clips-dir", str(self.clips_dir), "--report", str(report)])
        self.assertEqual(code, 2)
        self.assertIn("Refusing to overwrite", err)
        self.assertEqual(data, {"keep": True})

    def test_missing_bilingual_and_caption_wrap_and_allow_fps(self) -> None:
        zh_vid, en_vid, ep_zh, ep_en, zh_srt, _ = self._build_clean_project()
        report_single = self.root / "report_single.json"
        code1, data1, _ = run_audit([str(zh_vid), "--episode-zh", str(ep_zh), "--clips-dir", str(self.clips_dir), "--report", str(report_single)])
        self.assertEqual(code1, 1)
        self.assertIn("missing_bilingual_edition", data1["summary"]["flag_codes"])

        # Bad WrapStyle on zh episode + caption past end
        zh_srt.write_text(zh_srt.read_text(encoding="utf-8") + "\n4\n00:00:18,200 --> 00:00:22,500\n超时字幕。\n", encoding="utf-8")
        ep_zh_data = json.loads(ep_zh.read_text(encoding="utf-8"))
        ep_zh_data["captions"]["wrap_style"] = 0
        write_json(ep_zh, ep_zh_data)

        report_cap = self.root / "report_cap.json"
        code2, data2, _ = run_audit([
            str(zh_vid),
            "--en-video",
            str(en_vid),
            "--episode-zh",
            str(ep_zh),
            "--episode-en",
            str(ep_en),
            "--clips-dir",
            str(self.clips_dir),
            "--report",
            str(report_cap),
        ])
        self.assertEqual(code2, 1)
        self.assertIn("caption_sync_or_wrap_issue", data2["summary"]["flag_codes"])

        # Test --allow-fps-conversion permits 30fps without emitting fps_cadence_mismatch
        zh_30 = self.root / "zh_30.mp4"
        en_30 = self.root / "en_30.mp4"
        make_clip(zh_30, 1920, 1080, 30, 18.0)
        make_clip(en_30, 1920, 1080, 30, 18.0)
        ep_zh_clean, ep_en_clean = self._build_clean_project()[2:4]
        report_30 = self.root / "report_30.json"
        code3, data3, _ = run_audit([
            str(zh_30),
            "--en-video",
            str(en_30),
            "--episode-zh",
            str(ep_zh_clean),
            "--episode-en",
            str(ep_en_clean),
            "--clips-dir",
            str(self.clips_dir),
            "--allow-fps-conversion",
            "--report",
            str(report_30),
        ])
        self.assertEqual(code3, 0, f"Expected clean with --allow-fps-conversion, got {data3}")

    def test_calm_vs_rushed_speech_pacing(self) -> None:
        zh_vid, en_vid, ep_zh, ep_en, _, _ = self._build_clean_project()
        # Calm: ~49 CJK chars over ~15.5s active cues (~189.7 CJK/min), ~32 EN words over ~15.4s (~124.7 WPM), >=30% holds >=0.8s
        ep_zh_data = json.loads(ep_zh.read_text(encoding="utf-8"))
        ep_en_data = json.loads(ep_en.read_text(encoding="utf-8"))
        ep_zh_data["narration"]["text"] = "玻璃假体里面的液体正在慢慢流过，底部持续温和加热后压力顶开内部阀门，等到冷却下来时阀门又稳稳闭合起来了。"
        ep_en_data["narration"]["text"] = (
            "Clear liquid inside the glass phantom moves calmly along the channel. "
            "Rising heat slowly builds internal pressure and pushes the inner valve open. "
            "Once the vessel cools back down again, the valve settles shut."
        )
        # Verify 1 of 3 shots >=0.8s (33.3% >= 30%) passes holds check alongside calm speech rate
        ep_zh_data["shots"][0]["observation_hold_s"] = 0.4
        ep_zh_data["shots"][1]["observation_hold_s"] = 0.85
        ep_zh_data["shots"][2]["observation_hold_s"] = 0.4
        ep_en_data["shots"][0]["observation_hold_s"] = 0.4
        ep_en_data["shots"][1]["observation_hold_s"] = 0.85
        ep_en_data["shots"][2]["observation_hold_s"] = 0.4
        write_json(ep_zh, ep_zh_data)
        write_json(ep_en, ep_en_data)

        report_calm = self.root / "report_calm.json"
        code_calm, data_calm, err_calm = run_audit([
            str(zh_vid), "--en-video", str(en_vid),
            "--episode-zh", str(ep_zh), "--episode-en", str(ep_en),
            "--clips-dir", str(self.clips_dir), "--report", str(report_calm),
        ])
        self.assertEqual(code_calm, 0, f"Calm documentary pace should pass cleanly: {err_calm} {data_calm}")
        self.assertEqual(data_calm["flags"], [])

        # Rushed: ~85 CJK chars (~329 CJK/min > 290) and ~52 EN words (~202 WPM > 175) -> both flagged
        ep_zh_data["narration"]["text"] = "高" * 85
        ep_en_data["narration"]["text"] = " ".join(["word"] * 52)
        write_json(ep_zh, ep_zh_data)
        write_json(ep_en, ep_en_data)
        report_rush = self.root / "report_rush.json"
        code_rush, data_rush, _ = run_audit([
            str(zh_vid), "--en-video", str(en_vid),
            "--episode-zh", str(ep_zh), "--episode-en", str(ep_en),
            "--clips-dir", str(self.clips_dir), "--report", str(report_rush),
        ])
        self.assertEqual(code_rush, 1)
        rate_flags = [f for f in data_rush["flags"] if f.get("code") == "speech_rate_out_of_range"]
        self.assertEqual({f["edition"] for f in rate_flags}, {"zh", "en"})

    def test_anti_ai_voice_warping_chopped_pauses_and_script_markers(self) -> None:
        zh_vid, en_vid, ep_zh, ep_en, _, _ = self._build_clean_project()
        ep_zh_data = json.loads(ep_zh.read_text(encoding="utf-8"))
        # Write clean 3-paragraph script for EN and bad script + warped rate + 5/6 long holds for ZH
        bad_script = self.root / "bad_zh.txt"
        bad_script.write_text(
            "第一步靠慢消化：袋熊啃干草。\n\n" + "\n\n".join(f"第{i}镜头只有短短一句话。" for i in range(2, 11)),
            encoding="utf-8",
        )
        gen_rec = self.root / "bad_gen.json"
        write_json(gen_rec, {"voice": {"rate": "-14%"}})
        ep_zh_data["narration"]["script_file"] = "bad_zh.txt"
        ep_zh_data["narration"]["generation_record"] = {"file": "bad_gen.json"}
        ep_zh_data["shots"] = [
            {"id": f"SH0{i}", "duration_s": 5.5, "observation_hold_s": 1.7 if i <= 5 else 0.3}
            for i in range(1, 7)
        ]
        write_json(ep_zh, ep_zh_data)

        ep_en_data = json.loads(ep_en.read_text(encoding="utf-8"))
        ep_en_data["shots"] = [
            {"id": f"SH0{i}", "duration_s": 5.5, "observation_hold_s": 0.9 if i == 1 else 0.3}
            for i in range(1, 7)
        ]
        write_json(ep_en, ep_en_data)

        rep = self.root / "report_ai_tone.json"
        code, data, _ = run_audit([
            str(zh_vid), "--en-video", str(en_vid),
            "--episode-zh", str(ep_zh), "--episode-en", str(ep_en),
            "--clips-dir", str(self.clips_dir), "--report", str(rep),
        ])
        self.assertEqual(code, 1)
        codes = set(data["summary"]["flag_codes"])
        self.assertIn("tts_rate_warping", codes)
        self.assertIn("mechanical_chopped_pauses", codes)
        self.assertIn("script_ai_tone_markers", codes)

    def test_flags_non_flow_voice_or_local_resource(self) -> None:
        zh_vid, en_vid, ep_zh, ep_en, _, _ = self._build_clean_project()
        ep_zh_data = json.loads(ep_zh.read_text(encoding="utf-8"))
        ep_en_data = json.loads(ep_en.read_text(encoding="utf-8"))

        # Default Microsoft Edge edge-tts (zh-CN-YunxiNeural +4%) continuous ZH + EN + linear mastering/compositing should pass
        clean_gen_zh = self.root / "edge_gen_zh.json"
        write_json(
            clean_gen_zh,
            {
                "provider": "Microsoft Edge",
                "backend": "edge-tts",
                "model_id": "edge-tts",
                "voice": {"speaker": "zh-CN-YunxiNeural", "language": "Chinese", "rate": "+4%"},
            },
        )
        clean_post_zh = self.root / "master_post_zh.json"
        write_json(clean_post_zh, {"steps": [{"tool": "synthesize_edge_tts.py"}, {"tool": "prepare_voice_master.py"}, {"tool": "ffmpeg"}]})
        ep_zh_data["narration"]["execution"] = {
            "status": "confirmed",
            "mode": "service",
            "location": "https://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1",
        }
        ep_zh_data["narration"]["generation_record"] = {"file": "edge_gen_zh.json"}
        ep_zh_data["narration"]["postprocess_record"] = {"file": "master_post_zh.json"}
        write_json(ep_zh, ep_zh_data)

        clean_gen_en = self.root / "edge_gen_en.json"
        write_json(
            clean_gen_en,
            {
                "provider": "Microsoft Edge",
                "backend": "edge-tts",
                "model_id": "edge-tts",
                "voice": {"speaker": "en-US-AndrewMultilingualNeural", "language": "English", "rate": "+4%"},
            },
        )
        clean_post_en = self.root / "flow_post_en.json"
        write_json(clean_post_en, {"steps": [{"tool": "edge-tts"}, {"tool": "ffmpeg"}]})
        ep_en_data["narration"]["execution"] = {
            "status": "confirmed",
            "mode": "service",
            "location": "https://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1",
        }
        ep_en_data["narration"]["generation_record"] = {"file": "edge_gen_en.json"}
        ep_en_data["narration"]["postprocess_record"] = {"file": "flow_post_en.json"}
        write_json(ep_en, ep_en_data)

        rep_ok = self.root / "report_flow_ok.json"
        code_ok, data_ok, err_ok = run_audit([
            str(zh_vid), "--en-video", str(en_vid),
            "--episode-zh", str(ep_zh), "--episode-en", str(ep_en),
            "--clips-dir", str(self.clips_dir), "--report", str(rep_ok),
        ])
        self.assertEqual(code_ok, 0, f"Default edge-tts Yunxi +4% + Flow metadata should pass: {err_ok} {data_ok}")
        self.assertEqual(data_ok["flags"], [])

        # Local Qwen / OS TTS resources on ZH (local_project + local_qwen + flow_postproduction_gaps + synthesize_voice.py) must flag
        bad_gen_zh = self.root / "bad_gen_zh.json"
        write_json(bad_gen_zh, {"provider": "Qwen", "backend": "local_qwen"})
        bad_post_zh = self.root / "bad_post_zh.json"
        write_json(bad_post_zh, {"steps": [{"tool": "synthesize_voice.py"}]})
        ep_zh_data["design"]["flow_postproduction_gaps"] = ["loudnorm"]
        ep_zh_data["narration"]["execution"] = {
            "status": "confirmed",
            "mode": "local_project",
            "location": "https://unapproved-local-tts.example/v1",
        }
        ep_zh_data["narration"]["generation_record"] = {"file": "bad_gen_zh.json"}
        ep_zh_data["narration"]["postprocess_record"] = {"file": "bad_post_zh.json"}
        write_json(ep_zh, ep_zh_data)

        rep_bad = self.root / "report_non_flow.json"
        code_bad, data_bad, _ = run_audit([
            str(zh_vid), "--en-video", str(en_vid),
            "--episode-zh", str(ep_zh), "--episode-en", str(ep_en),
            "--clips-dir", str(self.clips_dir), "--report", str(rep_bad),
        ])
        self.assertEqual(code_bad, 1)
        non_flow = [f for f in data_bad["flags"] if f.get("code") == "non_flow_voice_or_local_resource"]
        self.assertEqual(len(non_flow), 1)
        self.assertEqual(non_flow[0]["edition"], "zh")
        reasons = set(non_flow[0]["reasons"])
        self.assertIn("flow_postproduction_gaps_forbidden", reasons)
        self.assertIn("execution_mode:local_project", reasons)
        self.assertIn("non_flow_execution_location", reasons)
        self.assertIn("non_flow_provider:Qwen", reasons)
        self.assertIn("non_flow_backend:local_qwen", reasons)
        self.assertIn("local_postprocess_tool:synthesize_voice.py", reasons)

    def test_allows_indextts2_zh_clone_paired_with_edge_en(self) -> None:
        zh_vid, en_vid, ep_zh, ep_en, _, _ = self._build_clean_project()
        ep_zh_data = json.loads(ep_zh.read_text(encoding="utf-8"))
        ep_en_data = json.loads(ep_en.read_text(encoding="utf-8"))

        idx_gen_zh = self.root / "indextts2_gen_zh.json"
        write_json(
            idx_gen_zh,
            {
                "provider": "IndexTTS",
                "backend": "local_indextts2",
                "model_id": "IndexTeam/IndexTTS-2.5",
                "voice": {"speaker": "user_clone", "language": "Chinese", "reference_prompt_sha256": "a" * 64},
            },
        )
        idx_post_zh = self.root / "indextts2_polish_zh.json"
        write_json(
            idx_post_zh,
            {"steps": [{"tool": "synthesize_indextts2.py"}, {"tool": "prepare_voice_master.py"}, {"tool": "ffmpeg"}]},
        )
        ep_zh_data["narration"]["execution"] = {
            "status": "confirmed",
            "mode": "local_project",
            "location": "/fixture-only/indextts2",
            "confirmation_reference": "audition #5",
        }
        ep_zh_data["narration"]["generation_record"] = {"file": "indextts2_gen_zh.json"}
        ep_zh_data["narration"]["postprocess_record"] = {"file": "indextts2_polish_zh.json"}
        write_json(ep_zh, ep_zh_data)

        edge_gen_en = self.root / "edge_gen_en.json"
        write_json(
            edge_gen_en,
            {
                "provider": "Microsoft Edge",
                "backend": "edge-tts",
                "model_id": "edge-tts",
                "voice": {"speaker": "en-US-AndrewMultilingualNeural", "language": "English", "rate": "+4%"},
            },
        )
        edge_post_en = self.root / "edge_post_en.json"
        write_json(edge_post_en, {"steps": [{"tool": "synthesize_edge_tts.py"}, {"tool": "prepare_voice_master.py"}]})
        ep_en_data["narration"]["execution"] = {
            "status": "confirmed",
            "mode": "service",
            "location": "https://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1",
        }
        ep_en_data["narration"]["generation_record"] = {"file": "edge_gen_en.json"}
        ep_en_data["narration"]["postprocess_record"] = {"file": "edge_post_en.json"}
        write_json(ep_en, ep_en_data)

        rep_ok = self.root / "report_indextts2_ok.json"
        code_ok, data_ok, err_ok = run_audit([
            str(zh_vid), "--en-video", str(en_vid),
            "--episode-zh", str(ep_zh), "--episode-en", str(ep_en),
            "--clips-dir", str(self.clips_dir), "--report", str(rep_ok),
        ])
        self.assertEqual(code_ok, 0, f"Default IndexTTS-2.5 #5 zh + edge-tts en should pass: {err_ok} {data_ok}")
        self.assertEqual(data_ok["flags"], [])

    def test_catches_clickbait_telegraphese_and_ping_pong_cuts_without_duration_floor(self) -> None:
        zh_vid, en_vid, ep_zh, ep_en, _, _ = self._build_clean_project()
        make_clip(zh_vid, 1920, 1080, 24, 80.0)
        make_clip(en_vid, 1920, 1080, 24, 80.0)
        ep_zh_data = json.loads(ep_zh.read_text(encoding="utf-8"))
        ep_en_data = json.loads(ep_en.read_text(encoding="utf-8"))

        bad_zh_script = self.root / "bad_telegraphic_zh.txt"
        bad_zh_script.write_text(
            "圆出口竟能拉出方便便，袋熊是怎么做到的？不是方形模具，而是软硬肠壁。袋熊啃食干草。肠道慢慢脱水。"
            "硬带压平粪面。软沟折出棱角。并非出口定型，而是末端挤压。圆环弹性撑开。"
            "斜坡圆粒滚走，方块稳停；喂太湿会变圆。只有干纤维配软硬肠壁，才留得住路标。\n",
            encoding="utf-8",
        )
        ep_zh_data["narration"]["script_file"] = "bad_telegraphic_zh.txt"
        scopes = [{"id": f"R{i}"} for i in range(1, 6)]
        ep_zh_data["topic"] = {"current": {"required_scope": scopes}}
        ep_en_data["topic"] = {"current": {"required_scope": scopes}}
        ping_pong_shots = [
            {"id": "SH01", "duration_s": 6.0, "observation_hold_s": 0.9, "shotbook": {"realism": {"observation_level": "naked_eye"}}},
            {"id": "SH02", "duration_s": 6.0, "observation_hold_s": 0.3, "shotbook": {"realism": {"observation_level": "not_observable"}}},
            {"id": "SH03", "duration_s": 6.0, "observation_hold_s": 0.9, "shotbook": {"realism": {"observation_level": "naked_eye"}}},
            {"id": "SH04", "duration_s": 6.0, "observation_hold_s": 0.3, "shotbook": {"realism": {"observation_level": "not_observable"}}},
        ]
        make_clip(self.clips_dir / "SH04.mp4", 1920, 1080, 24, 7.833)
        ep_zh_data["shots"] = ping_pong_shots
        ep_en_data["shots"] = ping_pong_shots
        write_json(ep_zh, ep_zh_data)
        write_json(ep_en, ep_en_data)

        rep = self.root / "report_patchwork.json"
        code, data, _ = run_audit([
            str(zh_vid), "--en-video", str(en_vid),
            "--episode-zh", str(ep_zh), "--episode-en", str(ep_en),
            "--clips-dir", str(self.clips_dir), "--report", str(rep),
        ])
        self.assertEqual(code, 1)
        codes = set(data["summary"]["flag_codes"])
        self.assertIn("script_ai_tone_markers", codes)
        self.assertNotIn("compressed_checklist_episode", codes)
        self.assertIn("world_ping_pong_cuts", codes)
        zh_ai = next(f for f in data["flags"] if f["code"] == "script_ai_tone_markers" and f["edition"] == "zh")
        ai_reasons = set(zh_ai["reasons"])
        self.assertIn("clickbait_contrast_hook", ai_reasons)
        self.assertIn("strawman_reversal_density", ai_reasons)
        self.assertIn("semicolon_tail_stuffing", ai_reasons)
        self.assertIn("slogan_closing_formula", ai_reasons)
        self.assertTrue(any(r.startswith("telegraphic_short_sentences:") for r in ai_reasons), ai_reasons)

    def test_short_clear_multi_scope_episode_has_no_duration_floor(self) -> None:
        zh_vid, en_vid, ep_zh, ep_en, _, _ = self._build_clean_project()
        scopes = [{"id": f"R{i}"} for i in range(1, 6)]
        for p in (ep_zh, ep_en):
            d = json.loads(p.read_text(encoding="utf-8"))
            d["topic"] = {"current": {"required_scope": scopes}}
            write_json(p, d)
        rep = self.root / "report_short_clear.json"
        code, data, err = run_audit([
            str(zh_vid), "--en-video", str(en_vid),
            "--episode-zh", str(ep_zh), "--episode-en", str(ep_en),
            "--clips-dir", str(self.clips_dir), "--report", str(rep),
        ])
        self.assertEqual(code, 0, f"Concise clear multi-scope episode should pass without duration floor: {err} {data}")
        self.assertEqual(data["status"], "clean")
        self.assertEqual(data["flags"], [])

    def test_native_720p_flow_scene_export_rejected_even_with_1080p_staged_clips(self) -> None:
        _, _, ep_zh, ep_en, _, _ = self._build_clean_project()
        zh_720 = self.root / "scene_zh_720.mp4"
        en_720 = self.root / "scene_en_720.mp4"
        make_clip(zh_720, 1280, 720, 24, 18.0)
        make_clip(en_720, 1280, 720, 24, 18.0)
        for p in (ep_zh, ep_en):
            d = json.loads(p.read_text(encoding="utf-8"))
            d["design"]["flow_scene_export"] = "native_720p_scene"
            d["design"]["output"] = {"width": 1280, "height": 720, "fps": 24}
            write_json(p, d)
        rep = self.root / "report_native_720_scene.json"
        code, data, err = run_audit([
            str(zh_720), "--en-video", str(en_720),
            "--episode-zh", str(ep_zh), "--episode-en", str(ep_en),
            "--clips-dir", str(self.clips_dir), "--report", str(rep),
        ])
        self.assertEqual(code, 1, (err, data))
        mismatches = [f for f in data["flags"] if f["code"] == "export_stream_mismatch"]
        self.assertEqual({f["edition"] for f in mismatches}, {"zh", "en"})

    def test_catches_curiosity_killing_spoilers_hype_and_flat_lists_in_zh_and_en(self) -> None:
        zh_vid, en_vid, ep_zh, ep_en, _, _ = self._build_clean_project()
        ep_zh_data = json.loads(ep_zh.read_text(encoding="utf-8"))
        ep_en_data = json.loads(ep_en.read_text(encoding="utf-8"))

        bad_zh = self.root / "curiosity_bad_zh.txt"
        bad_zh.write_text(
            "冰块浮在水上，其实原理很简单，下面我们一起来看它的内部结构。"
            "先来了解一下它的基本结构，它主要由氧原子和氢键组成。"
            "此外，水分子会重新排列成六边形网格。另外，网格中间留出了大量空隙。"
            "与此同时，同等质量下冰的体积随之变大。总结一下，这就是冰为什么会浮在水上的原因。\n",
            encoding="utf-8",
        )
        ep_zh_data["narration"]["script_file"] = "curiosity_bad_zh.txt"
        write_json(ep_zh, ep_zh_data)

        bad_en = self.root / "curiosity_bad_en.txt"
        bad_en.write_text(
            "Welcome back to the channel, the short answer is density drop. "
            "Furthermore, water molecules line up in rings. Moreover, those rings hold open space. "
            "In conclusion, stay until the end to see why ice floats.\n",
            encoding="utf-8",
        )
        ep_en_data["narration"]["script_file"] = "curiosity_bad_en.txt"
        write_json(ep_en, ep_en_data)

        rep = self.root / "report_curiosity_killers.json"
        code, data, err = run_audit([
            str(zh_vid), "--en-video", str(en_vid),
            "--episode-zh", str(ep_zh), "--episode-en", str(ep_en),
            "--clips-dir", str(self.clips_dir), "--report", str(rep),
        ])
        self.assertEqual(code, 1, (err, data))
        zh_flag = next(f for f in data["flags"] if f["code"] == "script_ai_tone_markers" and f["edition"] == "zh")
        en_flag = next(f for f in data["flags"] if f["code"] == "script_ai_tone_markers" and f["edition"] == "en")
        self.assertIn("premature_answer_spoiler", zh_flag["reasons"])
        self.assertIn("empty_suspense_filler", zh_flag["reasons"])
        self.assertIn("additive_list_transition_density", zh_flag["reasons"])
        self.assertIn("early_structure_dump", zh_flag["reasons"])
        self.assertIn("premature_ending_signal", zh_flag["reasons"])
        self.assertIn("empty_suspense_or_preamble_en", en_flag["reasons"])
        self.assertIn("premature_ending_signal_en", en_flag["reasons"])
        self.assertIn("additive_list_transition_density_en", en_flag["reasons"])


if __name__ == "__main__":
    unittest.main()
