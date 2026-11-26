---
name: science-video-production
description: Plan, produce, review or repair science videos, covers and 3D assets about nature, daily life and engineering — prioritizing silent visual causality, authentic real-world scenes, true high-poly industrial CAD silhouettes, conversational narration, vertical-feed packaging, and route-isolated execution (Google Flow, local realistic, or controlled 3D).
---

# Science Video Production (v2.0)

**We make visual science videos — NOT illustrated audiobooks.** Start from a concrete physical question and prove its answer through **continuous, real-world visible causality** that a muted viewer can follow at `1.0×` speed.

## Five Non-Negotiable Visual-First Laws (Read Before Anything Else)

1. **Silent Visual Causality First (`先用画面讲懂原理，绝不做配图小说`):** Design the 4–6 continuous visual cause-and-effect beats BEFORE locking narration. If muting the audio makes the mechanism unreadable, fix the visuals — never write prose to explain what the picture fails to show.
2. **Real-World Scene Persistence (`真实场景全程在场，严禁灰墙/黑棚虚空`):** Every episode lives inside a complete, bright, believable real-world environment and true physical host (real vehicle, room, workshop, or machine). **NEVER hide the real environment (`env.hide_render = True`) and substitute a flat gray/black backdrop (`Stage_MacroBackdrop`) during body cutaways.** Keep the cutaway **in-situ** with the real host and space softly visible in depth of field.
3. **True High-Poly Industrial Silhouettes (`真高面工业风，严禁方块积木冒充`):** On 3D routes, check local/open-licensed high-poly CAD/glTF host models (`CarConcept.glb`, Poly Haven CC0, real teardown references) FIRST. **NEVER fake curved, cast, or sculpted industrial hardware with rectangular boxes or plain cylinders** (e.g., a disc brake caliper is a ~65° curved cast body hugging the rotor, never a red brick). Pass `scripts/colab_cli.py audit-blend --strict` across **Frame 0 + body frames** before Colab GPU rendering.
4. **Causal Context-Preserving Framing (`因果同框，严禁盲人摸象局部切片`):** Keep **driver/actuator + active mechanism + physical result + recognizable host anchor** readable together in frame (`28–60 mm` storytelling lenses or in-situ translucent/cutaway shells). **NEVER crop into a blind `85–105 mm` 2 cm corner sliver** where the viewer loses where the part sits or what is driving it.
5. **Zero Legacy Template Reuse (`严禁复刻旧视频烂模板`):** Never copy old episode scene builders, dark-void `camera_strength <= 0.4` lighting presets, flat backdrop cardboard cards, or primitive `create_box` hero builders from earlier batches.

## Three-skill workflow suite

Maintained in one Git tree via `scripts/sync_companion_skills.py`:
1. **`science-video-topic-selection`** ([source](skills/science-video-topic-selection/SKILL.src.md)) — topic discovery, overlap checks, titles, cover concepts, 0–5 s Hook Lab → **Topic Decision Card**.
2. **`science-video-production`** *(this skill)* — visual-first storyboarding, route-isolated 3D/video production, conversational narration, covers (`compose_cover.py`), G1–G5 QA, and moving accepted finals to `release-candidate/`.
3. **`science-video-publishing`** ([source](skills/science-video-publishing/SKILL.src.md)) — 9:16 vertical feed packaging (`feed_package.py`), Douyin/Xiaohongshu/YouTube submission & standing collections, post-confirmation archive moves, and platform retrospectives.

## Route isolation (load only the active route)

**Lock ONE production route first and load ONLY that route's references.** Never mix toolchains or guides across routes.

| Active route | Load ONLY these route files (plus shared core as needed) | Do NOT load or invoke |
| --- | --- | --- |
| **Google Flow (`google_flow`)** | [Google Flow production](references/google-flow-production.md) (`scripts/gemini_api_cli.py` or Flow Web), [Voice reference](references/voice-reference.md), [Viral appeal](references/viral-appeal-and-packaging.md), [Realistic direction](references/realistic-direction.md); open [Visual system](references/visual-system.md), [Checkpoints](references/production-checkpoints.md), or [Acceptance](references/quality-acceptance.md) when covers/QA require them | **Never load** `tool-routing.md`, `ai-generated-video.md`, `engineering-blender.md`, `blender-execution.md`, `material-rendering.md`, or `spatial-typography.md`. |
| **Controlled 3D (`controlled_3d`)** | [Blender production](references/engineering-blender.md) (`high_poly_industrial_3d` + in-situ real-world scenes + silent-first preflight), [Animation scene design](references/animation-scene-design.md#non-text-visual-pointing-grammar-and-widescreen-aspect-ratio-framing), [Tool routing](references/tool-routing.md#lock-the-primary-tool-by-final-film-style) (Blender/Colab vs `vork`; **ALL Blender Cycles rendering defaults strictly to Google Colab GPU**; local Blender is headless build/bake + `audit-blend --strict` ONLY), [Material rendering](references/material-rendering.md), [Spatial typography](references/spatial-typography.md) | Do NOT load `google-flow-production.md` or `ai-generated-video.md`. |
| **Local Realistic (`local_realistic`)** | [Tool routing](references/tool-routing.md#lock-the-primary-tool-by-final-film-style), [Realistic workflow](references/ai-generated-video.md) (MoneyPrinterTurbo), [Realistic contract](references/realistic-production.md), [Realistic direction](references/realistic-direction.md) | Do NOT load `google-flow-production.md`, `vork`, or Blender guides. |

- **Shared narration default across ALL routes:** continuous whole-script Mandarin via local IndexTTS-2.5 clone (`scripts/synthesize_indextts2.py` + `scripts/prepare_voice_master.py --polish`, `mandarin-indextts25-clone-polished-v1`, zero echo); `edge-tts` (`scripts/synthesize_edge_tts.py`) for English (`en-US-AndrewMultilingualNeural`, `+4%`) and cloud Mandarin fallback (`zh-CN-YunxiNeural`, `+4%`). Warm, peer-level conversational tone driven by honest curiosity: pair narration with visible causality (never narrate pixels or deliver lecture walls); keep 0–8 s hook + non-spoiling viewing promise in ONE paragraph flowing straight into action; pace with "Therefore / But" obstacles and ~15–25 s breathing points; put visible behavior before jargon; end cleanly within `<= 3.5 s` after the answer on a loop-friendly frame (zero trailing questions, zero `总结一下`/`所以说到底`, zero `凭什么`/`凭啥`/`偏要`, zero `90%/99%`, zero `既没插电也没装传感器/电机/芯片`, zero `顺着截面往里看`/`剖开就能看到`/`放大截面`).

## Visual-first work order

1. **Hook Lab & Silent Visual Storyboard (G1):** Run the [hook lab](references/viral-appeal-and-packaging.md#win-the-first-two-seconds) (3+ candidates across 2+ patterns, moving Frame 0 in an unmistakable real-world host, exact title/feed/opening alignment) AND design the **complete silent visual causal chain** (real host → in-situ cutaway keeping driver + mechanism + result in frame → controlled side-by-side comparison → real-world payoff).
2. **Real Assets, Strict Audit & Muted 1080p Preflight (Controlled 3D):** Lock open-licensed 3D host models + real engineering photo silhouettes first; build the full real-world scene + true sculpted high-poly CAD mechanism (zero box substitutes, zero hidden-scene backdrop cards); pass `scripts/colab_cli.py audit-blend --strict` across Frame 0 + body frames; render `1920×1080` Colab stills across every beat (`scripts/colab_cli.py blender-stills`) and pass a **100% muted `< 1 s` recognition & principle check** BEFORE locking narration or full renders.
3. **Lean Narration, Beat-Board Pointing Test & 0–5 s Hook Sample:** Write lean conversational narration pointing to the verified visuals, synthesize continuous IndexTTS-2.5 `#5` audio + real `captions.srt`, run `scripts/build_visual_review.py beat-board` and pass the **1-Second Layperson Pointing Test** on every beat, then render/assemble the `1920×1080` **0–5 s hook sample** (`scripts/opening_hook.py` + cold 2 s test) before expanding.
4. **Advance only required stages:** G1 visual plan & hook → 0–5 s hook sample → G2 voiced rough cut → G3 representative sample → G4 full candidate → G5 independent full-film audiovisual acceptance. Local `delivery` ends at G5; G6/G7 apply only to authorized platform release.

## Scope, global installation & direct publication

- **Instruction priority:** Host rules → user's current explicit request → responsibility bodies → configuration defaults → episode records. Maintain normative docs/templates/agents in English; keep audience narration, captions, and copy in the edition's language.
- **One global installation:** Edit directly in the single [globally installed Skill Git working tree](references/global-skill-installation.md#maintain-the-installed-git-working-tree); never copy the Skill into projects.

| Commission | Scope & entry |
| --- | --- |
| Maintain this Skill | Edit directly in the global Git tree; reconcile bodies, configs, templates, indexes, agents, companion skills, and tests. Do not invoke models, resume video production, or publish. |
| Planning only | Read [Topic contract](references/topic-contract.md), [Viral appeal](references/viral-appeal-and-packaging.md), [Science and rights](references/science-and-rights.md), and [Checkpoints](references/production-checkpoints.md). |
| New / continued video | Lock ONE route above, then run G1 (visual-first + muted preflight) → 0–5 s hook sample → G2 → G3 → G4 → G5. |
| Local repair | Read current media, original request, and latest feedback; preserve valid assets/audio and recheck [affected dependencies](references/quality-acceptance.md#handling-failures). |
| Video only (`video_only`) | Stop at G5 and move accepted exports to `release-candidate/`. |
| Covers / release package | Independently composed 3:4 and 4:3 covers with realistic topic-matched backgrounds via `scripts/compose_cover.py` (`Noto Sans SC`, locked sizes & closed color presets, zero strokes/shadows). |
| Platform release | Use standalone [`science-video-publishing`](skills/science-video-publishing/SKILL.src.md) directly (`feed_package.py` 9:16, Douyin `#科普` + standing collections, Xiaohongshu handoff, post-confirm `archive/` move). |

## Core production standards (shared summary)

| Area | Essential rule (read linked owner body when acting) |
| --- | --- |
| Topic selection | Unassigned topics follow `editorial_positioning` in [series profile](config/series-profile.json) (~80% everyday mechanisms, ~20% scale/physical paradoxes). Always preserve user-commissioned topics. |
| Duration & depth | **No mandatory minimum or maximum duration or word count.** Let clear visual demonstration set length. |
| HD output | Formal samples and finals require short edge `>= 1080` (`1920×1080` default; `24 fps` CFR on Google Flow). Inspect full-res `1920×1080` Frame 0 and hero stills. |
| Provenance & safety | Self-created visuals, verified user capture, or licensed 3D models only. **Every scene, vehicle, prop, and backdrop comes from real everyday life or real manufacturing — never dark voids, flat gray backdrops, or peeled-skin body-horror cutaways.** |
| Narration & sound | Continuous IndexTTS-2.5 `#5` Mandarin / Edge English master; dual listening (headphones + phone speaker) required at G5; missing listening stays unreviewed. |
| In-picture text | Zero corner scene headings in body shots; on 3D routes, ZERO explanatory words/units/plaques (only necessary single-letter spatial markers under [spatial typography](references/spatial-typography.md)); synchronized captions stay 2D. |
| Covers & feeds | Realistic backgrounds + locked `scripts/compose_cover.py` typography; 9:16 vertical feed via `scripts/feed_package.py` from textless 16:9 master + SRT. |
| Anti-metric-gaming QA | Automated `flags=[]` / `audit-blend` / triangle counts NEVER certify human comprehension or art quality ([8 Human Comprehension & Visual P1 Blockers](references/quality-acceptance.md#anti-metric-gaming-principle-and-human-comprehension-p1-blockers)). Register [user feedback](references/quality-acceptance.md#register-user-feedback-item-by-item-and-keep-dimensions-separate) item by item. |

## Local review links and bandwidth conservation

Binds parent and every subagent across all routes:
- **Verified clickable local links:** Return user-review media as clickable Markdown links with short label and absolute filesystem target (forward slashes on Windows, angle-wrap paths with spaces) — never bare paths, redundant uploads, embeds, or auto-previews.
- **Minimal outbound media:** Verify genuine need, perception capability, deduplication, and smallest sufficient payload before any vision/media submission.

## Read responsibility bodies on demand

Load ONLY the files relevant to your active route and current stage:

| Need | Responsibility body |
| --- | --- |
| **Route: Google Flow** | [Google Flow production](references/google-flow-production.md) |
| **Route: Local Realistic** | [Realistic workflow](references/ai-generated-video.md), [Realistic contract](references/realistic-production.md), [Tool routing](references/tool-routing.md#lock-the-primary-tool-by-final-film-style) |
| **Route: Controlled 3D** | [Blender production](references/engineering-blender.md), [Animation scene design](references/animation-scene-design.md), [Tool routing](references/tool-routing.md#lock-the-primary-tool-by-final-film-style), [Material rendering](references/material-rendering.md), [Spatial typography](references/spatial-typography.md), [Blender execution](references/blender-execution.md) |
| Topic, packaging, hook & retention | [Topic contract](references/topic-contract.md), [Viral appeal](references/viral-appeal-and-packaging.md), [Viewer retention](references/viewer-retention-design.md) |
| Realistic direction & science/rights | [Realistic direction](references/realistic-direction.md), [Science and rights](references/science-and-rights.md) |
| Voice, visuals, art & annotations | [Voice reference](references/voice-reference.md), [Visual system](references/visual-system.md), [Art direction](references/art-direction.md), [Annotation style](references/annotation-style.md) |
| Checkpoints, acceptance & orchestration | [Checkpoints](references/production-checkpoints.md), [Acceptance](references/quality-acceptance.md), [Shotbook](references/shotbook.md), [Render evidence](references/render-evidence.md), [Subagent orchestration](references/subagent-orchestration.md) |

## Records and validation commands

Use [brief-template.md](assets/brief-template.md), [episode-template.json](assets/episode-template.json), and [art-direction-template.md](assets/art-direction-template.md) only to the commissioned depth. Run scripts with a verified working Python interpreter:

    python -X utf8 scripts/check_reference_system.py .
    python -X utf8 scripts/colab_cli.py audit-blend --blend <packed.blend> --shards 2 --strict --report <new-audit.json>
    python -X utf8 scripts/colab_cli.py blender-stills -s <session> --blend <packed.blend> --frames <spec> --out-dir <stills-dir> --receipt <new-stills.json>
    python -X utf8 scripts/build_visual_review.py beat-board --stills-dir <preflight-stills-dir> --captions <captions.srt> --fps 30 --output <new-beat-board-dir>
    python -X utf8 scripts/render_gate.py lock <absolute-episode-directory>/skill-lock.json
    python -X utf8 scripts/render_gate.py run <episode.json> --phase roughcut|sample|full --shot-ids SH1,SH2 --output <out.mp4> --receipt <new-receipt.json>
    python -X utf8 scripts/gemini_api_cli.py preflight --check-auth
    python -X utf8 scripts/google_flow_audit.py measure <zh.mp4> --en-video <en.mp4> --episode-zh <episode.zh.json> --episode-en <episode.en.json> --clips-dir <clips-dir> --report <new-flow-audit.json>
    python -X utf8 scripts/opening_hook.py measure <export.mp4> --captions <captions.srt> --preview-dir <local-preview-dir> --report <new-hook-report.json>
    python -X utf8 scripts/realistic_audit.py measure <export.mp4> --shots <shots.json> [--delivery-fps 24] --report <new-audit-report.json>
    python -X utf8 scripts/retention_timeline.py measure <export.mp4> --episode <episode.json> --preview-dir <local-preview-dir> --report <new-retention-report.json>
    python -X utf8 scripts/feed_package.py compose <textless-master.mp4> --captions <captions.srt> --topic <topic> --question <line1\nline2> --output <feed-916.mp4> --report <new-feed-report.json>
    python -X utf8 scripts/compose_cover.py compose <text-free-cover.png> --ratio <1:1|3:4|4:3|16:9> --title <1-line> --question <line1\nline2> --palette <daylight_terracotta|daylight_navy|dark_terracotta|dark_ocean_gold> --lang <zh|en> --output <cover.png> --report <new-cover-receipt.json>
    python -X utf8 scripts/check_episode.py <episode.json> --stage <G1..G7|covers|delivery|publish_ready> [--stored-video <abs-path>] --report <new-receipt.json>

Exit codes: `0` = passed, `1` = blocking findings, `2` = input/execution error. Always write new receipt filenames and follow structural checks with actual audiovisual review.
