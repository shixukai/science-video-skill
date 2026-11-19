# science-video-skill

A science-video production Skill for nature, daily life, engineering and industrial manufacturing. The current version is 1.6.36. The Git commit identifies the exact revision.

- **Realistic → MoneyPrinterTurbo; 3D animation → Blender or `vork` (agent-selected).** Finished visual style selects the route, and the agent automatically decides whether to use `vork` for full 3D episodes, 3D shots or supporting field/simulation/VFX passes based on mechanism and hardware fit.
- **Default voice across all routes → Microsoft Edge `edge-tts` (`zh-CN-YunxiNeural`, `+4%`).** Synthesize whole-script continuous narration via `scripts/synthesize_edge_tts.py` (`zh-CN-YunxiNeural` at `+4%`, paired with `en-US-AndrewMultilingualNeural` at `+4%` for English editions) and master linearly via `prepare_voice_master.py`.
- **Google Flow cloud production.** Generate video visuals and physical foley in Google Flow (`>= 1440×900` desktop viewport, `1080p Upscaled` staging, `24 fps` CFR cadence, serial queue ledger, full `3–5` chapter depth), synthesize continuous bilingual voiceovers with default `edge-tts` (`zh-CN-YunxiNeural` `+4%` / `en-US-AndrewMultilingualNeural` `+4%`), and composite cleanly into `1920×1080` `24 fps` bilingual editions. See [Google Flow production](references/google-flow-production.md).
- **Realistic direction craft and audit.** Assign each shot a truth register and verified time scale, write physical shot cards before prompts, layer event-accurate sound, and screen exports with `realistic_audit.py` and `google_flow_audit.py`. See [realistic direction](references/realistic-direction.md).
- **Final video handoff.** Move accepted videos to the configured NAS release queue and archive each confirmed publication. See [accepted and published video storage](references/production-checkpoints.md#move-accepted-and-published-videos).
- **Potentially disturbing footage.** Use proportional treatment for blood, exposed organs and injuries while preserving explanatory structure, and review the actual opening, covers and exports. See [visual treatment](references/visual-system.md#handle-potentially-disturbing-imagery).
- **One global production installation.** Projects retain data and rule-hash locks, without Skill copies. The installed Skill is also the Git working tree; maintenance happens directly in that directory. On continuation, read global changes, migrate explicitly and retain old execution records.
- **Open with context and a reason to watch.** Work backward from the first body observation; design the opening's final sentence/frame together with the body's first sentence/frame and continuously review through that observation. Topic and route may flow naturally in one sentence; do not split them merely for time fields.
- **Carry viewers to the end.** Follow the hook with a concrete viewing promise by about 8 s, keep the main question open through the `payoff_steps` open-loop ledger until a late final answer, and end within a few seconds of it. `retention_timeline.py` locates payoff gaps, empty-question intervals and long tails on actual cuts without adding a gate. See [keep a reason to stay](references/viral-appeal-and-packaging.md#keep-a-reason-to-stay).
- **Vertical feed package.** Keep the 1920×1080 master; `feed_package.py` derives a 1080×1920 upload for the Douyin composer group and Xiaohongshu with a persistent topic/question header in the top band and larger re-wrapped captions below the picture. See [vertical feeds](references/viral-appeal-and-packaging.md#package-the-landscape-master-for-vertical-feeds).
- **Explain the full requested engineering/manufacturing chain.** Organize input, principle, key processes, result and verification by topic scope. Actual explanation and observation determine duration.
- **Sample before expanding.** Verify subject, action, voice and joins at actual playback rhythm. Low-frame-rate layout proxies remain internal; the complete film still needs full viewing/listening.
- **Precision annotation and independent covers.** Distinguish location, direction and range. Arrow heads/shafts are continuous, tips sharp, with no shaft overshoot. Compose each commissioned cover ratio independently with a [realistic background](references/visual-system.md#realistic-backgrounds-for-every-cover) showing the topic's actual setting, and inspect the phone thumbnails.
- **Repairable, verifiable sound.** Reuse accepted voice, audition opening/difficult phrases, and repair misreads, sluggishness, phrasing and joins by cause. Listen separately to source and final mix.
- **Current-series original visual provenance.** Use self-generation, scene/animation rendering, self-design or verified authorized user capture. Suitable open-licensed 3D models may be used directly, retaining external authorship/license and actual adaptation records. Third-party finished footage/stills and paper imagery remain research only.
- **English maintenance language.** Skill instructions, normative references, templates and role definitions use English. Actual Chinese narration/captions/copy examples, language-sensitive fixtures and approved model-input payloads retain their intended language.

The production bodies unify executable opening, transition, picture and sound actions and return conditions, removing repetition, tool encyclopedias and unusable prose. They correct legacy 2D/frozen-version/topic biases. Written and executable contracts remain aligned; actual media outcomes still require corresponding viewing/listening records.

<a id="使用入口"></a>
## Entry

Start at [SKILL.md](SKILL.md) and read responsibility bodies for the actual commission. New work defaults to 1920×1080; historical 2D/portrait parameters apply only within their explicit scope. Local video delivery ends at G5; platform preparation/publication enters G6/G7 only when commissioned.

| Need | Body |
| --- | --- |
| Original topic, complete chain and opening | [Topic contract](references/topic-contract.md), [opening/transitions](references/viewer-retention-design.md) |
| Actual tools and execution stages | [Tool routing](references/tool-routing.md), [production checkpoints](references/production-checkpoints.md) |
| Realistic craft & Google Flow | [Realistic direction](references/realistic-direction.md), [Google Flow production](references/google-flow-production.md) |
| Picture, annotations and covers | [Visual system](references/visual-system.md), [precision annotation](references/annotation-style.md) |
| Sound | [Voice and actual listening](references/voice-reference.md) |
| Failures and acceptance | [Quality acceptance](references/quality-acceptance.md) |
| 3D asset reuse | [Blender and asset library](references/engineering-blender.md) |
| Subagent ownership, installation and invocation | [Six roles and parent direction](references/subagent-orchestration.md), [installable TOML definitions](agents) |

Run scripts from the global installation. `render_gate.py lock/run` rejects non-global production entry; `roughcut` serves G2, `sample` produces the review-pending representative sequence, and `full` requires G3. Use new receipt filenames; do not refresh old hashes to pretend an earlier approval covers a new version. Keep private media, accounts and review records out of this repository.

<a id="子代理"></a>
## Subagents

The parent retains direction/integration and invokes research, visual art, animation, audio/editing, local execution and independent review roles as needed. Six definitions do not require six concurrent workers. Roles read standards from the unique global Skill and inherit the host's model/permissions. See [orchestration](references/subagent-orchestration.md#installation-and-invocation) for installation and natural-language invocation examples.

<a id="维护检查"></a>
## Maintenance checks

From the installed Skill/repository root, use Python 3.11+. Media-related tests require FFmpeg/ffprobe and Pillow. Select regressions appropriate to the change.

```bash
python -X utf8 scripts/rebuild_standard_index.py
python -X utf8 scripts/check_reference_system.py .
python -X utf8 -m unittest discover -s tests -t .
python -X utf8 -m unittest discover -s scripts/tests
```

Edit and validate in the installed `science-video-production` directory. Fetch and reconcile `origin/main` there before changing files, then commit and push when authorized. Do not create temporary editing directories, candidate trees, separate maintenance clones or worktrees. See [in-place maintenance](references/global-skill-installation.md#maintain-the-installed-git-working-tree) and [repository instructions](AGENTS.md).

The section index maintains body links, hashes and anchors only. READMEs for `scripts/bounded_blender` and `scripts/bounded_i2v` define their bounded execution/recovery scope. `third-party` retains original licenses and pinned provenance. Historical paper examples and `references/learning-candidates` are unverified research records, not current production permission or passing evidence. Git history retains prior revisions.
