# science-video-skill

A science-video production Skill for nature, daily life, engineering and industrial manufacturing. Current version: 1.6.12; the Git commit identifies the exact revision.

- **Realistic → MoneyPrinterTurbo; 3D animation → Blender or `vork` (agent-selected).** Finished visual style selects the route, and the agent automatically decides whether to use `vork` for full 3D episodes, 3D shots or supporting field/simulation/VFX passes based on mechanism and hardware fit.
- **One global production installation.** Projects retain data and rule-hash locks, without Skill copies. Maintenance source is not a production entry. On continuation, read global changes, migrate explicitly and retain old execution records.
- **Open with context and a reason to watch.** Work backward from the first body observation; design the opening's final sentence/frame together with the body's first sentence/frame and continuously review through that observation. Topic and route may flow naturally in one sentence; do not split them merely for time fields.
- **Explain the full requested engineering/manufacturing chain.** Organize input, principle, key processes, result and verification by topic scope. Actual explanation and observation determine duration.
- **Sample before expanding.** Verify subject, action, voice and joins at actual playback rhythm. Low-frame-rate layout proxies remain internal; the complete film still needs full viewing/listening.
- **Precision annotation and independent covers.** Distinguish location, direction and range. Arrow heads/shafts are continuous, tips sharp, with no shaft overshoot. Compose each commissioned cover ratio independently and inspect phone thumbnails.
- **Repairable, verifiable sound.** Reuse accepted voice, audition opening/difficult phrases, and repair misreads, sluggishness, phrasing and joins by cause. Listen separately to source and final mix.
- **Current-series original visual provenance.** Use self-generation, scene/animation rendering, self-design or verified authorized user capture. Suitable open-licensed 3D models may be used directly, retaining external authorship/license and actual adaptation records. Third-party finished footage/stills and paper imagery remain research only.
- **English maintenance language.** Skill instructions, normative references, templates and role definitions use English. Actual Chinese narration/captions/copy examples, language-sensitive fixtures and approved model-input payloads retain their intended language.

The production bodies unify executable opening, transition, picture and sound actions and return conditions, removing repetition, tool encyclopedias and unusable prose. They correct legacy 2D/frozen-version/topic biases. Written and executable contracts remain aligned; actual media outcomes still require corresponding viewing/listening records.

<a id="使用入口"></a>
## Entry

Start at [SKILL.md](skills/science-video-production/SKILL.md) and read responsibility bodies for the actual commission. New work defaults to 1920×1080; historical 2D/portrait parameters apply only within their explicit scope. Local video delivery ends at G5; platform preparation/publication enters G6/G7 only when commissioned.

| Need | Body |
| --- | --- |
| Original topic, complete chain and opening | [Topic contract](skills/science-video-production/references/topic-contract.md), [opening/transitions](skills/science-video-production/references/viewer-retention-design.md) |
| Actual tools and execution stages | [Tool routing](skills/science-video-production/references/tool-routing.md), [production checkpoints](skills/science-video-production/references/production-checkpoints.md) |
| Picture, annotations and covers | [Visual system](skills/science-video-production/references/visual-system.md), [precision annotation](skills/science-video-production/references/annotation-style.md) |
| Sound | [Voice and actual listening](skills/science-video-production/references/voice-reference.md) |
| Failures and acceptance | [Quality acceptance](skills/science-video-production/references/quality-acceptance.md) |
| 3D asset reuse | [Blender and asset library](skills/science-video-production/references/engineering-blender.md) |
| Subagent ownership, installation and invocation | [Six roles and parent direction](skills/science-video-production/references/subagent-orchestration.md), [installable TOML definitions](skills/science-video-production/agents) |

Run scripts from the global installation. `render_gate.py lock/run` rejects non-global production entry; `roughcut` serves G2, `sample` produces the review-pending representative sequence, and `full` requires G3. Use new receipt filenames; do not refresh old hashes to pretend an earlier approval covers a new version. Keep private media, accounts and review records out of this repository.

<a id="子代理"></a>
## Subagents

The parent retains direction/integration and invokes research, visual art, animation, audio/editing, local execution and independent review roles as needed. Six definitions do not require six concurrent workers. Roles read standards from the unique global Skill and inherit the host's model/permissions. See [orchestration](skills/science-video-production/references/subagent-orchestration.md#installation-and-invocation) for installation and natural-language invocation examples.

<a id="维护检查"></a>
## Maintenance checks

From the maintenance repository root, use Python 3.11+. Media-related tests require FFmpeg/ffprobe. Select regressions appropriate to the change.

```bash
python -X utf8 skills/science-video-production/scripts/rebuild_standard_index.py
python -X utf8 skills/science-video-production/scripts/check_reference_system.py skills/science-video-production
python -X utf8 -m unittest discover -s tests -t .
python -X utf8 -m unittest discover -s skills/science-video-production/scripts/tests
```

The section index maintains body links, hashes and anchors only. READMEs for `scripts/bounded_blender` and `scripts/bounded_i2v` define their bounded execution/recovery scope. `third-party` retains original licenses and pinned provenance. Historical paper examples and `references/learning-candidates` are unverified research records, not current production permission or passing evidence. Git history retains prior revisions.
