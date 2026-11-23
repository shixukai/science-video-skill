---
name: science-video-production
description: Plan, produce, review or repair science videos, covers and 3D assets about nature, daily life and engineering — covering titles, first-two-second hooks, viewing promises, open-loop retention, conversational spoken scripts, vertical-feed packaging, and route-isolated execution (Google Flow bilingual cloud production, local realistic, or controlled 3D).
---

# Science Video Production

Start from a concrete question and make its answer visible. Prioritize the opening before polishing the rest: find an understandable event worth watching, compare genuinely different ways to reveal it, and test the chosen opening in the existing sample review.

## Three-skill workflow suite

This repository maintains **three independent top-level skills** synced via `scripts/sync_companion_skills.py`:
1. **`science-video-topic-selection`** ([source](skills/science-video-topic-selection/SKILL.src.md)) — pre-script topic discovery, originality/overlap checks, titles, cover concepts, and 0–5 s Hook Lab → hands off a **Topic Decision Card**.
2. **`science-video-production`** *(this skill)* — script craft, conversational narration & voice mastering, route-isolated media generation/editing, covers (`compose_cover.py`), G1–G5 quality review, and moving accepted finals to `release-candidate/`.
3. **`science-video-publishing`** ([source](skills/science-video-publishing/SKILL.src.md)) — 9:16 vertical feed packaging (`feed_package.py`), Douyin/Xiaohongshu/YouTube submission & standing collections, post-confirmation archive moves (`release-candidate/` → `archive/`), and platform data retrospectives (`next_production_brief`).

Use the dedicated companion skill directly when a task is purely topic selection or purely publishing/retrospective — do not pull production rules into those tasks.

## Route isolation (load only the active route)

**Select ONE production route from the commission first and load ONLY that route's references.** Never read or pull another route's engine instructions, sub-guides, or toolchains into context.

| Active route | Load ONLY these route files (plus shared core as needed) | Do NOT load or invoke |
| --- | --- | --- |
| **Google Flow (`google_flow`)** | [Google Flow production](references/google-flow-production.md), [Voice reference](references/voice-reference.md), [Viral appeal and packaging](references/viral-appeal-and-packaging.md), [Realistic direction](references/realistic-direction.md); open [Visual system](references/visual-system.md), [Production checkpoints](references/production-checkpoints.md), or [Quality acceptance](references/quality-acceptance.md) sections only when covers, QA, or release require them | **Never load** `references/tool-routing.md`, `references/ai-generated-video.md` (MoneyPrinterTurbo), `references/engineering-blender.md`, `references/blender-execution.md`, `references/material-rendering.md`, or `references/spatial-typography.md`. Do NOT activate MoneyPrinterTurbo, `vork`, Blender, or Colab toolchains. |
| **Controlled 3D (`controlled_3d`)** | [Tool routing](references/tool-routing.md#lock-the-primary-tool-by-final-film-style) (Blender/Colab vs `vork`), [Blender production](references/engineering-blender.md), [Material rendering](references/material-rendering.md), [Spatial typography](references/spatial-typography.md) | Do NOT load `references/google-flow-production.md` or `references/ai-generated-video.md` (MoneyPrinterTurbo). |
| **Local Realistic (`local_realistic`)** | [Tool routing](references/tool-routing.md#lock-the-primary-tool-by-final-film-style), [Realistic production workflow](references/ai-generated-video.md) (MoneyPrinterTurbo), [Realistic production contract](references/realistic-production.md), [Realistic direction](references/realistic-direction.md) | Do NOT load `references/google-flow-production.md`, `vork`, or Blender 3D references. |

- If the route is unspecified, ask or default to the commissioned project's existing route (series fallback: local realistic). Topic category alone never silently switches routes.
- **Shared narration default across ALL routes:** continuous whole-script Mandarin narration using local IndexTTS-2.5 voice clone (`scripts/synthesize_indextts2.py` + `scripts/prepare_voice_master.py --polish`, `mandarin-indextts25-clone-polished-v1`, zero echo), paired with `edge-tts` (`scripts/synthesize_edge_tts.py`) for English (`en-US-AndrewMultilingualNeural`, `+4%`) and cloud Mandarin fallback (`zh-CN-YunxiNeural`, `+4%`). Write and edit narration in a warm, unhurried, peer-level conversational register — never stiff textbook/telegraphic bullets, confrontational hooks (`凭什么`/`凭啥`/`偏要`), bossy imperatives, crude force verbs, or abrupt narrator camera/cutaway commands (`顺着截面往里看`/`剖开就能看到`/`放大截面`); let the picture cut in while the voice follows the viewer's causal curiosity.

## Opening-first work order

1. **Package & Hook Lab (G1):** Run the [hook lab](references/viral-appeal-and-packaging.md#win-the-first-two-seconds) before scripting: compare 3+ genuinely different opening candidates across 2+ patterns; pair frame-0 moving picture, first sound, and natural first line (payload finishing by the configured deadline, concrete [viewing promise](references/viral-appeal-and-packaging.md#lock-a-concrete-viewing-promise-by-about-8-seconds) by ~8 s).
2. **Test the 0–5 s hook sample first:** Render/assemble the 0–5 s hook at target HD canvas and frame rate, measure with `scripts/opening_hook.py`, and run the cold two-second test before expanding the body.
3. **Carry open loops to a late answer:** Keep the main question open in `payoff_steps` until a late final answer, open the next question before closing the current beat, and [end cleanly right after explaining the mechanism](references/viral-appeal-and-packaging.md#end-fast-after-explaining-the-mechanism) without trailing questions or recap filler.
4. **Advance only required stages:** G1 design → 0–5 s hook sample → G2 complete voiced rough cut → G3 high-risk representative sample → G4 full candidate → G5 independent full-film audiovisual acceptance. Local `delivery` ends at G5; G6/G7 apply only to authorized platform release.

## Scope, global installation & direct publication

- **Instruction priority:** Host rules & permissions → user's current explicit request & still-valid authorization → responsibility bodies → configuration defaults → episode records. Templates and indexes add no extra gates. Maintain normative docs, templates and agent definitions in English; keep audience narration, captions and copy in the edition's language.
- **One global installation:** Work directly in the single [globally installed Skill Git working tree](references/global-skill-installation.md#maintain-the-installed-git-working-tree); never copy the Skill into projects or spawn temporary maintenance clones. Explicitly migrate locks when global rules change; never rewrite historical receipts.

| Commission | Scope & entry |
| --- | --- |
| Maintain this Skill | Edit directly in the global Git tree; reconcile bodies, configs, templates, indexes and tests. Do not invoke models, resume video production, or publish. |
| Planning only | Read [Topic contract](references/topic-contract.md), [Viral appeal](references/viral-appeal-and-packaging.md), [Science and rights](references/science-and-rights.md), and [Production checkpoints](references/production-checkpoints.md). Deliver draft package + hook lab without invented sources or timestamps. |
| New / continued video | Lock ONE route above, then run G1 → 0–5 s hook sample → G2 → G3 → G4 → G5 using lean project records. |
| Local repair | Read current media, original request and latest feedback; preserve valid assets/audio and recheck [affected dependencies](references/quality-acceptance.md#handling-failures). |
| Video only (`video_only`) | Set `delivery_scope=video_only` + `delivery_scope_note`; stop at G5 and [move accepted exports to `release-candidate`](references/production-checkpoints.md#move-accepted-and-published-videos). Complete Google Flow films still deliver paired `zh`/`en` editions. |
| Covers / release package | Default `delivery_scope=release_package` includes independently composed 3:4 and 4:3 covers with realistic topic-matched backgrounds, typeset strictly via `scripts/compose_cover.py` (`Noto Sans SC`, fixed sizes, closed color presets, zero strokes/shadows). |
| Platform release / direct publication | Prefer the standalone [`science-video-publishing`](skills/science-video-publishing/SKILL.src.md) skill directly. It covers checked `feed_package.py` 9:16 derivatives, direct publication without G1–G6 paperwork, Douyin single-composer multi-platform release (`#科普`, standing collections `透视日常造物`/`解码巅峰工程`/`丈量天地寰宇`/`探秘生命法则`, no-download, AI disclosure), Xiaohongshu user handoff, post-submit stop rule, and verified `release-candidate` → `archive` moves. |

## Core production standards (shared summary)

| Area | Essential rule (read linked owner body when acting) |
| --- | --- |
| Topic selection | For unassigned topics, follow `editorial_positioning` in [series profile](config/series-profile.json) (~80% everyday objects & visible physical mechanisms, ~20% observable scale/physical paradoxes) via [Topic Selection Skill](skills/science-video-topic-selection/SKILL.src.md). Always preserve user-commissioned topics. |
| Duration & depth | **No mandatory minimum or maximum duration or word count.** Let clear explanation and observation set runtime naturally; keep standalone feed episodes focused on one core contradiction and causal chain without padding or speeding up speech. |
| HD output | Formal samples and finals on every route require short edge `>= 1080` matching `design.output` (default `1920×1080`, `24 fps` CFR on pure Google Flow timelines). `720p` exports are internal proxies only; verify streams with `ffprobe` and inspect full-res `1920×1080` Frame 0 and hero frames. |
| Provenance & safety | Self-created visuals or verified authorized user capture only (licensed 3D model inputs permitted on 3D routes); third-party finished footage/stills stay research-only. Keep [potentially disturbing imagery](references/visual-system.md#handle-potentially-disturbing-imagery) clean — zero peeled-skin, carved-window, or body-horror cutaways in video or covers. |
| Narration & sound | Warm, natural peer-level conversational speech ([voice craft](references/voice-reference.md#edit-narration-and-dialogue-for-the-ear)); one continuous voice master and shared processing chain per language (`synthesize_indextts2.py` + `prepare_voice_master.py --polish` for Mandarin; `synthesize_edge_tts.py` for English/fallback). Dual listening (headphones + phone speaker) required at G5; missing listening stays unreviewed. |
| In-picture text & markings | No upper-left/upper-right scene headings in body shots; apply the [deletion test](references/visual-system.md#body-auxiliary-text-use-and-hold). Default AI disclosure to platform fields/companion records; in-picture markings/watermarks require [specific consent](references/visual-system.md#in-picture-markings-require-specific-consent). (3D routes additionally restrict picture text to single-letter spatial markers.) |
| Covers & vertical feeds | Realistic topic-matched backgrounds for every cover + locked `scripts/compose_cover.py` typography ([cover standards](references/visual-system.md#finished-cover-standards-for-engineering-and-manufacturing-topics)). For the Douyin composer group vertical feed, compose the 1080×1920 dark-band derivative via `scripts/feed_package.py` from the textless 16:9 master + captions ([vertical feed package](references/viral-appeal-and-packaging.md#package-the-landscape-master-for-vertical-feeds)); Xiaohongshu and YouTube use the accepted 16:9 landscape master directly. |
| Proportionate review | Apply [risk-based rechecks](references/quality-acceptance.md#risk-based-rechecks-and-evidence-reuse): one genuine normal-speed viewing per responsibility/version covers multiple QA items; no per-shot frame quotas or uncommissioned engineering tolerances. Keep technical, static, audiovisual, and platform passes distinct; register [user feedback](references/quality-acceptance.md#register-user-feedback-item-by-item-and-keep-dimensions-separate) by version and dimension. |

## Local review links and bandwidth conservation

Binds parent and every subagent across all routes:
- **Verified clickable local links:** Return user-review media as verified clickable Markdown links with a short material/version label and absolute local target (angle-wrap paths with spaces) — never bare paths, redundant uploads, embeds, or auto-previews. For upload file choosers, provide paste-ready native directory and file paths in separate code blocks.
- **Minimal outbound media:** Before any outbound media/vision submission, verify (1) genuine unresolved question, (2) recipient perception capability, (3) deduplication against already-sent assets, and (4) smallest sufficient payload (targeted stills or contact sheets for static diagnosis; bounded clips for continuous motion — never bulk raw frame uploads).

## Read responsibility bodies on demand

Load ONLY the files relevant to your active route and current stage:

| Need | Responsibility body |
| --- | --- |
| **Route: Google Flow (cloud bilingual)** | [Google Flow production](references/google-flow-production.md) *(stop here for route mechanics — do not open `tool-routing.md`, `ai-generated-video.md`, or 3D guides)* |
| **Route: Local Realistic** | [Realistic production workflow](references/ai-generated-video.md), [Realistic production contract](references/realistic-production.md), [Tool routing](references/tool-routing.md#lock-the-primary-tool-by-final-film-style) |
| **Route: Controlled 3D (Blender/Colab or `vork`)** | [Tool routing](references/tool-routing.md#lock-the-primary-tool-by-final-film-style), [Blender production](references/engineering-blender.md), [Material rendering](references/material-rendering.md), [Spatial typography](references/spatial-typography.md), [Blender execution](references/blender-execution.md) |
| Topic, audience, scope & complete chains | [Topic contract](references/topic-contract.md) |
| Viral packaging, 0–5 s hook, retention & 9:16 feeds | [Viral appeal and packaging](references/viral-appeal-and-packaging.md), [Viewer retention](references/viewer-retention-design.md) |
| Realistic direction (truth registers, shot cards, sound, grade) | [Realistic direction handbook](references/realistic-direction.md) |
| Science claims, original visual provenance & rights | [Science and rights](references/science-and-rights.md) |
| Spoken craft, IndexTTS-2.5 `#5` / Edge mastering & listening | [Voice reference](references/voice-reference.md) |
| Covers, visual system, text rules & disturbing imagery | [Visual system](references/visual-system.md), [Art direction](references/art-direction.md), [Annotation style](references/annotation-style.md), [Animation scene design](references/animation-scene-design.md) |
| G1–G7 checkpoints, storage moves & platform release | [Production checkpoints](references/production-checkpoints.md) |
| Acceptance, subject motion, feedback & failure handling | [Quality acceptance](references/quality-acceptance.md) |
| Shotbook schema / Render evidence / Subagent handoffs | [Shotbook](references/shotbook.md), [Render evidence](references/render-evidence.md), [Subagent orchestration](references/subagent-orchestration.md) |

## Records and validation commands

Use [brief-template.md](assets/brief-template.md), [episode-template.json](assets/episode-template.json), and [art-direction-template.md](assets/art-direction-template.md) only to the commissioned depth; add optional stage fields only when that gate applies. Run scripts from the active global Skill using a verified working Python interpreter (never a broken Windows Store stub):

    python -X utf8 scripts/check_reference_system.py .
    python -X utf8 scripts/render_gate.py lock <absolute-episode-directory>/skill-lock.json
    python -X utf8 scripts/render_gate.py run <episode.json> --phase roughcut|sample|full --shot-ids SH1,SH2 --output <out.mp4> --receipt <new-receipt.json>
    python -X utf8 scripts/google_flow_audit.py measure <zh.mp4> --en-video <en.mp4> --episode-zh <episode.zh.json> --episode-en <episode.en.json> --clips-dir <clips-dir> --report <new-flow-audit.json>
    python -X utf8 scripts/opening_hook.py measure <export.mp4> --captions <captions.srt> --preview-dir <local-preview-dir> --report <new-hook-report.json>
    python -X utf8 scripts/realistic_audit.py measure <export.mp4> --shots <shots.json> [--delivery-fps 24] --report <new-audit-report.json>
    python -X utf8 scripts/retention_timeline.py measure <export.mp4> --episode <episode.json> --preview-dir <local-preview-dir> --report <new-retention-report.json>
    python -X utf8 scripts/feed_package.py compose <textless-master.mp4> --captions <captions.srt> --topic <topic> --question <line1\nline2> --output <feed-916.mp4> --report <new-feed-report.json>
    python -X utf8 scripts/compose_cover.py compose <text-free-cover.png> --ratio <1:1|3:4|4:3|16:9> --title <1-line> --question <line1\nline2> --palette <daylight_terracotta|daylight_navy|dark_terracotta|dark_ocean_gold> --lang <zh|en> --output <cover.png> --report <new-cover-receipt.json>
    python -X utf8 scripts/check_episode.py <episode.json> --stage <G1..G7|covers|delivery|publish_ready> [--stored-video <abs-path>] --report <new-receipt.json>

Exit codes: `0` = passed, `1` = blocking findings, `2` = input/execution error. Always write new receipt filenames and follow structural checks with actual audiovisual review.
