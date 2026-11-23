# Google Flow cloud production

> **Route isolation:** When `design.production_route=google_flow`, use this handbook with [voice-reference.md](voice-reference.md), [viral-appeal-and-packaging.md](viral-appeal-and-packaging.md), [realistic-direction.md](realistic-direction.md), and only needed cover/QA/release sections. **Do not load `tool-routing.md`, `ai-generated-video.md`, `engineering-blender.md`, `blender-execution.md`, `material-rendering.md`, or `spatial-typography.md`, and do not activate local realistic or 3D rendering toolchains.**

## Select the route and budget bilingual chains at G1

Set `design.production_route=google_flow` for Google Flow commissions:
- **Visuals & physical foley:** Generate all video imagery and physical foley (`1080p Upscaled`, `24/1 fps` CFR) in [Google Flow](https://flow.google.com/). OS TTS, local 3D renderers, local video-assembly pipelines, screen capture, and stock footage/music cannot supply delivered media on this route.
- **Narration & muxing:** Synthesize continuous **Chinese (`zh`)** narration via local IndexTTS-2.5 `#5` voice clone ([synthesize_indextts2.py](../scripts/synthesize_indextts2.py)) + `#5` speech polish ([prepare_voice_master.py --polish](../scripts/prepare_voice_master.py), `mandarin-clone-polish-v1`, zero echo) — or `edge-tts` (`zh-CN-YunxiNeural`, `+4%`) as cloud fallback — and paired **English (`en`)** narration via `edge-tts` (`en-US-AndrewMultilingualNeural`, `+4%`, [synthesize_edge_tts.py](../scripts/synthesize_edge_tts.py)) mastered linearly via `prepare_voice_master.py`; composite (`ffmpeg`) with `1080p` Flow visuals, ducked Flow foley/ambience, and synchronized captions.
- **Explanation-led runtime & visual acts:** Plan the full [causal chain](topic-contract.md#complete-chains-and-duration-for-engineering-and-manufacturing-topics) first with **no minimum or maximum runtime or word-count quota**. Group shots into sustained visual acts (`2–4` consecutive shots bridged via `Frames`/`Extend` or a shared scene preamble — never ping-ponging exterior/studio on single shots, and never tacking caveats onto the end with `；`).
- **Paired bilingual budgeting (`24/1 fps` CFR):** Deliver sibling `episode.zh.json` and `episode.en.json` sharing shot order, picture clips, truth registers, and foley stems. Raw `1080p Upscaled` clips run `~7.833 s` (`188` frames at `24/1 fps`); after trimming `0.15–0.40 s` ramp head and holding `0.20–0.40 s` tail margin, each clip yields **`~6.8–7.4 s` usable core**. Budget every shot to `max(span_zh, span_en)` at G1: split longer beats into `SHxxA`/`SHxxB` or tail-frame `Frames` continuations — **never** use `setpts` slow-mo, `tpad` tail freezes, loops, or `atempo` audio warping. Lock `design.output.fps=24` CFR on pure Flow timelines (never duplicate frames to `30 fps`).

## Start with active project controls, pacing and 1080p Upscaled staging

- **Desktop viewport lock (`>= 1440×900`):** Enforce `1440×900+` at the start of every browser step and after navigation (below `~840 px`, Flow switches to mobile layout and hides `Scenes`, `+ Add clip`, and `>> Extend`). Check active models/credits (`Veo 3.1 - Fast` 10 cr/8s, `Veo 3.1 - Quality` 100 cr/8s, `Omni 1.2 Flash` 24 cr/8s; `1080p Upscaled` = 0 cr on single clips). [Flow docs](https://support.google.com/flow/answer/16353333?hl=en&co=GENIE.Platform%3DDesktop), [Models](https://support.google.com/flow/answer/16352836?hl=en), [Credits](https://support.google.com/flow/answer/16526234?hl=en).
- **Disk-backed prompt ledger:** Save a versioned local ledger mapping every `shot_id` → exact prompt, input mode (`Text`/`Frames`/`Ingredients`), expected span, card index, and downloaded filename; re-read from disk after any compaction/resume.
- **Strict 1-by-1 serial submission & anti-bot stop:** Submit and upscale one card serially at calm human pace (never parallel tabs/burst loops). On `"We noticed some unusual activity"`, CAPTCHA, sign-in, region, or credit block: **stop immediately**, save state, and report to the user (never bypass).
- **Asset reuse & `1080p Upscaled` verification:** Reuse clean project cards/`Frames` under [minimal transfer](../SKILL.md#local-review-links-and-bandwidth-conservation). Download every selected single clip via **`1080p Upscaled`** (`720p Original` is screening-only), verify `dl.path() !== null && dl.failure() === null`, probe with `ffprobe` (`>= 1920×1080`, `24/1 fps`, valid video + `48 kHz` audio), and inspect BOTH contact sheets AND **full-resolution `1920×1080` Frame 0 / hero stills** before assembly.

## Prompting, conditioning, clean phantoms and native foley

Draft every prompt from its [shot card](realistic-direction.md#write-a-shot-card-before-the-prompt) (`truth_register`, `time_scale`, scene lighting preamble, camera package, concrete physical transition) and select candidates science-first:
1. **0–5 s hook sample & G3 first:** Produce `SH01` at `1080p Upscaled` first, trim `>= 0.15 s` (`>= 4` frames) of static ramp so motion starts at frame 0 ([two-second hook](viral-appeal-and-packaging.md#win-the-first-two-seconds)), inspect full-res `1920×1080` Frame 0, and pass `opening_hook.py` + cold 2 s test + G3 before generating remaining body shots.
2. **Frameless, text-free staging (`>= 90%` safe zone):** Keep props/instruments blank and unmarked; never prompt counters, labels, split screens, PiP insets, borders, or UI mockups (Flow garbles glyphs).
3. **Zero body horror / clean biological cutaways:** Under [disturbing-imagery rules](visual-system.md#handle-potentially-disturbing-imagery), NEVER prompt or accept peeled/carved/translucent human skin, exposed wet subcutaneous vessels, or needle piercings on human hands/limbs (in video or covers). Open on clean intact exteriors and cut to standalone non-fleshy microscopic optics or clean non-photorealistic schematics; preserve soft-tissue compliance (never metal pistons/blades for soft organs) and check `4–8 s` tails for late morphs.
4. **Physical foley only inside Veo prompts:** Live verification shows Flow has no voiceover upload lane and `Veo 3.1 - Fast` rejects offscreen Mandarin speech prompts (`35%–57%` `Audio generation failed`), whereas literal physical `Audio:` foley prompts succeed cleanly. Prompt pure physical visuals + literal `Audio:` foley in Flow, then mux continuous `#5` IndexTTS-2.5 Mandarin / `edge-tts` English narration in FFmpeg.
5. **`1080p Upscaled` vs `720p` platform limits:** In-editor `>> Extend` (`Omni 1.2 Flash`, `+4 s`) and `/scene/` `Download scene` currently export `1280×720` only (`720p` cannot satisfy the formal `1080p` floor even with `native_720p_scene`). Prefer tail-frame `Frames` conditioning on `1080p`-upscalable single clips, or report verified `720p` platform limits honestly rather than silently lowering targets.

## Build a cloud-generated narration master for each language

Adapt approved Chinese narration into natural spoken English preserving exact causal order, units, and conditions ([claim preservation](science-and-rights.md#preserve-claim-meaning-through-production-handoffs); [spoken craft](voice-reference.md#edit-narration-and-dialogue-for-the-ear)):
- **Warm conversational paragraphs, zero per-shot chopping:** Draft cohesive paragraphs (not per-shot `\n\n` couplets), free of blunt/confrontational wording (`凭什么`/`凭啥`/`偏要`/bossy imperatives/crude verbs), prompt colons, coined shorthand, or slogan closings. Synthesize continuously (`duration_factor=1.0`, `use_emo_text=False` for `#5` IndexTTS-2.5; `|rate| <= 6%`, default `+4%` for `edge-tts`), keeping natural cadence and reserving `>= 0.8 s` wordless observation holds on `2–4` major reveals (`>= 15%` of shots). Snap cuts to natural breath valleys with `0.12–0.30 s` J/L overlaps and `0.20–0.30 s` act-boundary dissolves; keep continuous `150–250 ms` room-tone/foley crossfades (never digital zero) and `-16 LUFS` / `-1.5 dBTP` mix balance. Optional [Flow Music](https://support.google.com/flow/answer/17084348?hl=en) stays on its own ducked stem within verified plan rights.
- **Canonical audio bindings:** Default Chinese `#5` clone binds `voice_type="synthetic"`, `mode="local_project"`, `provider="IndexTTS"`, `backend="local_indextts2"`, `model_id="IndexTeam/IndexTTS-2.5"`, `speaker="user_clone"`, plus `postprocess_record` (`whole_track_speech_polish`); `edge-tts` English / cloud ZH fallback binds `mode="service"`, `provider="Microsoft Edge"`, `backend="edge-tts"`, `model_id="edge-tts"`. Never record `Qwen`, `synthesize_voice.py`, or `os_tts`.

## Edit, mix, caption, export and review in Flow

- Maintain clause-level single-line synchronized subtitles (`.zh.srt` `WrapStyle=2 >= 20 pt`; `.en.srt` `WrapStyle=0` clean breaks, zero SSML/markup leakage).
- Generate clean text-free cover art (`3:4` & `4:3`, plus `16:9` if requested) and render separate `zh` and `en` covers strictly via `scripts/compose_cover.py --lang zh|en` (never reuse Chinese cover text on English editions).
- Enforce `>= 1080` short edge (`1920×1080`, `24/1 fps` CFR) on all formal samples and finals under [HD output](quality-acceptance.md#hd-video-output); report genuine route blockers honestly without bypassing tool boundaries.

## Audit staged clips and paired editions before delivery

Bind Flow clips (`ai_generated`), prompt-ledger proofs, and audio stems into sibling `episode.zh.json` and `episode.en.json`, then run:
1. `python -X utf8 scripts/google_flow_audit.py measure <zh.mp4> --episode-zh <episode.zh.json> --en-video <en.mp4> --episode-en <episode.en.json> --clips-dir <clips-dir> --report <flow-audit.json>`
2. `python -X utf8 scripts/opening_hook.py measure <export.mp4> --captions <srt> --preview-dir <dir> --report <hook.json>` (both editions)
3. `python -X utf8 scripts/realistic_audit.py measure <export.mp4> --shots <shots.json> --delivery-fps 24 --report <realistic-audit.json>` (both editions)
4. `python -X utf8 scripts/check_episode.py <episode.zh.json|episode.en.json> --stage delivery --report <delivery.json>`

Follow checks with independent `1.0×` continuous audiovisual review in BOTH Chinese and English, preserving SynthID provenance and platform AI disclosure ([publication declarations](production-checkpoints.md#declare-ai-generated-content-at-publication)).

### Diagnose by symptom

| Symptom | Root cause | Fix |
| --- | --- | --- |
| `1280×720` clip / scene | Downloaded `720p Original`, `>> Extend`, or `Download scene` | Export single clips via `1080p Upscaled`, chain via tail-frame `Frames`, or report `720p` blocker |
| 4th-frame judder | `24 fps` Flow clips forced onto `30 fps` timeline | Lock `design.output.fps=24` CFR & pass `--delivery-fps 24` |
| Slow-mo / tail freeze / warped foley | Beat exceeded `~7.0 s` usable core | Split into `SHxxA`/`SHxxB` or `Frames` bridge; remove `setpts`/`tpad`/`atempo` |
| Stiff/blunt tone, pitch resets, or dead gaps | Per-shot `\n\n` breaks, `\|rate\| > 6%`, blunt/telegraphic wording, or spliced `1.5–2 s` holes | Rewrite warm paragraphs ([voice-reference.md](voice-reference.md#edit-narration-and-dialogue-for-the-ear)), synthesize continuously, add `0.12–0.30 s` J/L cuts & continuous room tone |
| `Audio generation failed` (`30–57%`) | Offscreen Mandarin speech prompted in Veo 3.1 | Prompt physical foley only in Flow; mux continuous `#5` IndexTTS-2.5 / `edge-tts` narration |
| `"We noticed some unusual activity"` | Parallel tabs or rapid polling | Stop immediately (never bypass); resume 1-by-1 serially |
| Missing `Scenes` / `+ Add clip` | Browser pane `< 840 px` (mobile mode) | Lock viewport `>= 1440×900` on every step |
| Garbled dials, PiP borders, late morphs, or body horror | Asked for labels/insets, unchecked `4–8 s` tails, or carved/translucent skin | Use blank frameless props, intact exteriors + non-fleshy microscopic cuts, full-res `1920×1080` inspection |
| Clashing chatter / `zh` vs `en` cover mixup | Unmuted Veo gibberish audio or reused `zh` cover | Mute gibberish clips, layer clean foley, run `compose_cover.py --lang en` separately |
