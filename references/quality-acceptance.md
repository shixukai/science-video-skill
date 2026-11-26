# Quality Acceptance: References, Behavior, Evidence, and Return Conditions

Check project and execution records against the single active route under [SKILL.md's Route Isolation gate](../SKILL.md#route-isolation-load-only-the-active-route), then review applicable items below. Conclusions must point to current media/evidence; record technical checks and actual perceptual reviews separately.

## Establish Traceable References First

Pick structural, appearance, and motion references actually opened for this film's medium (recording source/version, purpose, and viewed intervals; keep rights separate and never impose legacy 2D painting on realistic/3D work). Compare exports side by side at comparable shot sizes for contours, proportions, contacts, and function; research unsupported details rather than shipping placeholders.

With an approved style, verify the [actual complete composite against the design board](visual-system.md#actual-implementation-of-approved-designs) and [layer separation](visual-system.md#three-scale-form-and-production-detail) where applicable, plus [G2 delivery scope](production-checkpoints.md#actual-g1g7-progression-records). On Controlled 3D Blender routes, also check [scene background and spatial finish](engineering-blender.md#blender-backgrounds-and-spatial-completion).

## User-Viewing Versions and Internal Proxies

Internal rough cuts and stills locate issues only; user-facing samples for judging opening, rhythm, detail, and motion must run at target frame rate with genuinely continuous subject states. Check frame rate, dimensions, and unique motion frames separately — never disguise repeated stills as continuous animation. Fix known opening defocus, crude assets, or obvious stutter before asking the user to judge open choices, and report any missing viewing/listening capability honestly.

## HD Video Output

Formal renders, G3 samples, G4 candidates, and G5 deliveries require an HD target matching `design.output` (default `1920×1080` landscape, `1080×1920` when portrait is commissioned; short edge `>= 1080` on every route including Google Flow; honor higher explicit targets). Never silently downscale for speed or treat `native_720p_scene` as an exemption — 720p outputs remain internal proxies or export blockers only. Enlarging low-res pixels does not restore HD detail; verify native stream dimensions, SAR, rotation, and cadence via `ffprobe`, inspect master vs final encoding under [detail retention](visual-system.md#detail-retention-in-the-final-encoding), and deliver user-review files via [verified local links](../SKILL.md#local-review-links-and-bandwidth-conservation).

## Inspectable Items

Apply the medium's standards ([realistic](realistic-production.md#observable-standards-for-realistic-imagery), [Blender](engineering-blender.md), or [authorized 2D/covers](visual-system.md#visual-anchors-of-the-approved-style)). Independent reviewers inspect actual new media; unchanged in-scope assets may be reused.

| Item | Required check & evidence | Return conditions |
| --- | --- | --- |
| Real-video anchor (`real_footage` only) | Continuously watch source interval & export; verify user capture, authorization, phenomenon visibility, and rights | Still photo, AI clip, or third-party footage passed off as live action |
| Form & key structure | Compare sourced contours, proportions, connections, and detail across overview + close-up | Missing/wrong structure or placeholders in final picture |
| Orientation & structural logic | Map object left/right to frame left/right across front/side/back/section views | Flipped/mirrored/confused views that alter function or causal direction |
| Arrows & leader lines | Check sharp tip, continuous head/shaft, target, scaling, and motion extremes under [precision annotations](annotation-style.md) | Protruding shaft, cropped/blunt tip, tracking drift, or misread leader |
| Scene space & function | Check scale, support/contact, occlusion, and [audiovisual correspondence](production-checkpoints.md#match-each-sections-picture-sound-and-in-picture-text) | Floating/unsupported objects, occluded key event, or lost location |
| Lines & edges | Inspect hierarchy, joins, masks, and curves at native, zoomed, and phone scale | Ragged edges, broken seams, or abrupt line-weight jumps |
| Brightness & material finish | Check subject illumination, readable dark structure, light hierarchy, and material separation under [art direction](art-direction.md); on 3D routes enforce [general material standard](material-rendering.md) (`purpose=appearance`, never Workbench proxies, grouped lookdev) and [industrial studio standard](visual-system.md#industrial-product-studio-material-standard) | Underlit subject, lost dark detail, uniform plastic look, clipped highlights, stuck reflections, shimmer, or encode graying |
| Color & layers | Check value contrast, scientific color semantics, transparency, and cross-shot consistency | Subject/background confusion, lighting distorting variable meaning |
| Composition & hierarchy | Check full frame and phone scale for focus, framing, host anchors, and readable text under [non-text visual pointing and widescreen framing](animation-scene-design.md#non-text-visual-pointing-grammar-and-widescreen-aspect-ratio-framing) | Purposeless dead zones, `< 25%`-wide vertical "telephone-pole" framing in empty void, cropped actuator/key parts, repeated identical cutaway angles, or whole-frame shrink hacks |
| 3D spatial text (**3D routes only**) | Permit ONLY necessary single-letter spatial markers under [spatial typography](spatial-typography.md); verify non-text visual pointing carries identification cleanly; keep synchronized captions 2D | Any Chinese/English words, units, plaques, split-word letters, second caption strip, or unidentified same-metal CAD clutter where spoken parts cannot be pointed to |
| Text necessity & duration | Apply deletion test & readable hold under [body text rules](visual-system.md#body-auxiliary-text-use-and-hold); check attribution/disclosure placement separately | Corner scene headings, unreadable flashes, production excuses, or unfulfilled obligations |
| Cross-shot continuity | Watch with continuous sound for question/answer handoffs, anchors, and scale bridges | Broken orientation, reversed causal order, unintroduced visual teleports/mystery props, or premature results |
| Animation finish & boundaries | Watch normal-speed playback against narration: real state development, clean contacts, visible flow/gate action, outgoing layer cleanup, scientific limits | Stills/Ken Burns replacing process, invisible gas fog, occluded valve gates, decorative floating glowing rings/halos, ghosting, intersections, floating, or simulation sold as data |
| Narration explanatory role | Watch/listen end-to-end without script notes (and inspect the pre-render captioned beat board on 3D routes); restate answer and run the 1-second layperson pointing test per spoken beat | Self-talk over unidentified visuals, missing fixed-vs-moving reference frame, physics-subject mismatch (camera on stationary part while speech describes moving part), local details clear while main question/premises fail; ASR/tone/clean automated flags cannot excuse broken comprehension |

Static backgrounds and purposeful holds are valid; never add random filler motion to inflate movement.

## Subject Motion and Long Static Holds

The video must visibly advance the observation or mechanism over real playback time. Caption swaps, particles, Ken Burns pans/zooms, and hard cuts between stills are NOT subject progression.

Check the full timeline at G2 (voiced rough cut), G3 (representative sample), and G5 (final export): watch/listen at 1.0× speed, then isolate the subject ROI to confirm required changes happen. `config/production-policy.json subject_motion` thresholds (`3.0 s` no-progress, `1.6 s` reading) are review triggers, not rigid motion-every-second quotas — scientifically needed observation/comparison holds may run longer with explicit `hold_review`, while missing promised processes always fail.

Bind `qa.shotbook.subject_motion` (G2), `qa.visual_frames.animation.subject_motion` (G3), and `qa.visual_frames.subject_motion` (G5) with `status`, `context_sha256`, `media_sha256`, `roi_review`, `excluded_motion_review`, `screen {file,sha256}`, continuous `spans` (`subject_change` / `authentic_motion` / `purposeful_read` / `no_progress`), continuous `semantic_units`, and `longest_no_progress_seconds`. Viewing records (`qa.*.viewing`) bind `method=continuous_playback`, `playback_speed=1`, full `ranges`, and optional `frame_scope=full_frame` / `visual_review_capable=true` belonging strictly to that reviewer.

Screen with `python scripts/subject_motion.py <media> --regions <regions.json> --report <new-screen.json>` (binding the report in `qa.gates.<stage>.evidence`), then replay every low-change candidate at normal speed (`effective_subject_progression` or `purposeful_observation` with `hold_review`). Automatic frame diffs only screen; they never certify causality or reject Ken Burns.

For `workflow_version=3`, also record `subject_motion.object_result_review` (`status`, `media_sha256`, `units` aligned with `semantic_units`, `mode=visible_result|diagram_only`, `overlay_isolation`, `observation`, `scientific_boundary`, `evidence`, plus `diagram_only_reason` when `diagram_only`): temporarily hide overlays diagnostically to confirm whether the promised subject change actually happens (invisible quantities may legitimately use `diagram_only`; a static sticker promising a visible physical change cannot). Legacy `workflow_version=2` packages keep compatibility without forced migration, but version 3 cannot omit or null this item.

### Moving animatics and user review

Distinguish internal narrated storyboards from user-facing moving rough cuts. A rough cut sent for rhythm, motion, or viewing feedback must represent required subject actions and joins across the timeline (simplifying geometry/materials is fine; prolonged still boards or loop hacks are not). Inspect actual source coverage (native frames vs held frames/loops) before handoff; keep intentional comparison freezes purposeful and return known missing action to its owner before asking the user again.

## Orientation Mapping and Graphic Reuse

Fix object identity, viewpoint, and left/right mapping first; recheck after mirroring, sectioning, or pose reuse. Reuse versioned annotation components under [tips and head–shaft joins](annotation-style.md#arrow-tips-and-headshaft-joins), verifying scale, occlusion, and extremes.

## Reviewers and Viewing Safety

Record reviewer/role, actual viewing/listening capabilities, files/intervals covered, and uncovered parts honestly. Match observation method to claim scope (stills/crops never establish continuous full-frame playback; author self-review is not cold first-viewing). Keep outbound review media minimal under [local links & bandwidth conservation](../SKILL.md#local-review-links-and-bandwidth-conservation).

- **Flash / luminance safety:** Eliminate unnecessary rapid high-contrast flashes and inspect the full composited timeline; leave unverified if continuous inspection is unavailable (never make medical safety guarantees).
- **Potentially disturbing imagery:** Review affected intervals, adjoining cuts, hook, covers, and thumbnails at normal speed + frame-step at cuts/masks under [disturbing-imagery rules](visual-system.md#handle-potentially-disturbing-imagery) to ensure zero unintended exposure (including zero peeled/carved human skin) and readable scientific cues.
- **User review evidence:** Genuine user review on exact current media/ranges counts for its reviewed scope; never fabricate assistant listening when audio perception is unavailable.

## Risk-Based Rechecks and Evidence Reuse

Keep checks proportionate to the commissioned explanation, stage, shot scale, and concrete risks. **Do NOT invent engineering-simulation tolerances, microscopic gap/zero-intersection demands, arbitrary part-count rules, or per-shot manual frame quotas.** Judge scientific accuracy and visible readability at intended display scale; use tolerances only when explicitly commissioned or tied to a sourced quantitative claim.

- Maintain ONE canonical timeline and observation set per responsibility/version: one genuine normal-speed viewing can satisfy multiple QA items within that responsibility/version, and derived views (`spans`, `semantic_units`, `object_result_review.units`) do not require rewatching the film per form field. Consolidate defects into one prioritized repair packet.
- Use pausing, magnification, and frame-stepping selectively on real risk areas (new mechanisms, contacts/occlusion, fast actions/flashes, dense captions, encode artifacts, known failures). After targeted fixes, recheck the repaired cycle and adjacent joins; keep valid unaffected evidence. For any repaired motion, workpiece transport, or destructive-physics interval (e.g., shatter, collapse, cut, or roll-through), extract and visually inspect a **2×2 chronological 4-panel motion-transition contact strip** directly from the **final encoded MP4** (`onset → mid-action → state-swap/peak → settled aftermath`) before handing the new version to the user, verifying real displacement, disappearance of intact solids after breakup, bare empty supports, and clean subtitles.
- Run technical checks at the deepest applicable entry (`delivery` for local delivery; `publish_ready` only for release) and avoid redundant silent intermediate encodes or repeated probes of unchanged verified files. Separate G5 explanation and expression passes still require independent actual viewing.

## Evidence from Samples to the Whole Film

Standalone 3D asset tasks follow [asset-task scope](engineering-blender.md#scope-of-asset-only-tasks) (no forced narration or G3). For video commissions, G3 representative samples cover whole-object orientation, key detail, a complete high-risk relationship (`selection_mode=risk_relation` binding full `expression_card_ids` + `step_ids` + `scope_note`, or legacy `full_chain`), and neighboring continuity with real narration/captions. Full films still require complete normal-speed watching/listening and risk-based detail checks (minimum record: export version, shot/time, item, reference, observed gap, repair/recheck). Fix known defects before handing to the user; if the user says the whole film is incomprehensible, retain the failure and repair the full script/premises first.

## Records and Technical Checks

Applicability follows task scope (`video_only` skips covers; local `delivery` skips platform checks). Keep `qa.visual_frames`, `qa.audio`/`narration` (`final_export` vs `short_sample` vs `pending`), `qa.comprehension` (`editor_reviewed` vs genuine `audience_checked`), `qa.topic_alignment`, `qa.shotbook`, `qa.mobile_preview`, and `qa.reviewed_sha256` honest and current; never refresh hashes to fake re-review.

- `scripts/check_episode.py` (`--stage plan|G1..G7|covers|delivery|publish_ready --report <new.json>`) validates structure, stream decode, dimensions, copy limits, and digests offline (exit `0` pass / `1` blocked / `2` error) without certifying science, art, or voice quality.
- `scripts/check_reference_system.py` checks Skill structure/config/links only.

## Handling Failures

When defects appear, return to the responsible stage, revoke stale passes on that version, and preserve pre/post-repair evidence. Whole-film expression failures return to storyboarding + representative verification; whole-batch user rejections freeze deliverability until root causes are repaired across dimensions.

Work through defects cleanly:
1. **Locate:** Bind exact feedback, version, and interval; check whether the same flaw repeats elsewhere in the film.
2. **Repair:** Fix execution when rules are clear; update normative text only for genuine rule gaps. Follow [current commission scope](production-checkpoints.md#3-stage-progression-and-representative-samples) and retain still-valid assets/tracks.
3. **Recheck:** View repaired cycle, dependent shots, and joins (complete new exports need full watching/listening); close only on real recheck of the repaired file.
4. **Retain lesson:** Promote generalizable rules + regression tests to the Skill while keeping private feedback/media in the project.

### Register User Feedback Item by Item and Keep Dimensions Separate

Register every received user comment (positive, negative, corrections) in `qa.feedback` and list expected IDs in `qa.feedback_expected_ids`. Judge understanding, science, art, animation, sound, and layout **independently**: local understanding approval never cancels an art failure or grants a whole-film pass. Preserve original failed states in `dimensions` and record closures strictly in new-version `retest_evidence`.

- Use `contract_version=1`, `origin=user`: bind `source_ref`, `original_feedback`, `media_version/media_sha256`, `scope`, `scope_kind` (`segment`/`whole_episode`/`series_style`/`static_direction`), `time_range_s`, `applies_to_gates`, itemized `dimensions`, `what_changes`, `repair_time_range_s`, `repair_artifacts`, `retest_evidence`, and `skill_update` (`rule_change`/`execution_fix`/`pending` + regression receipt when rules changed).
- `retest_evidence` binds `feedback_id`, `media_sha256`, `feedback_context_sha256` (`scripts/feedback_guard.py`), `scope_mapping`, actual covered `ranges` (`whole_episode`/`series_style` requires full-media continuous review; only `static_direction` may close with a decodable repaired still covering static visual dimensions `art/static_art/layout/composition/color/lighting/material/detail/style` and `ranges=[]`), `reviewer`, `actual_viewed`, and per-dimension `dimension_results`.
- Migrating legacy `visual_frames.failures` rows uses `resolution.binding_version=2`, matching `feedback_id`, and `stage_checks.legacy_failure_sha256(original_failure)`. G3 repair rechecks (`representative_repair`) lift expansion blocks only; G5 still requires full-episode review. Keep Skill commits, sync, and media validation reported separately.

## Full-Quality Diagnostic Scores and Internal Explanation Review

Optional 0–5 five-dimensional diagnostic scoring (`production-policy.json`: Understanding 30, Art 25, Action/Camera 25, Sound 15, Captions/Packaging 5) helps locate gaps only — no minimum score threshold exists and empty scorecards never block stages.

Internal explanation review separates two responsibilities under [autonomous explanation and expression review](#autonomous-explanation-and-expression-review):
- **Explanation review:** `qa.explanation_logic` (G1 paper logic) and `qa.explanation_review` (G5 final export — question, premises, reasoning, boundaries, integration).
- **Expression review:** `qa.expression_plan` (G2 rough cut) and `qa.expression_review` (G5 final export — whether those relations actually appear in picture, action, and sound).

At G5 both bind `actual_information_only=true`, `independent_of_generation_context=true`, `media_sha256`, reviewer capabilities, `understanding_goals` (`answer`, `relationships`, `transfer`, `boundaries`), per-step `steps[]` evidence across all mandatory scope, and empty `unpresented_assumptions` on pass. The two G5 reviewers must NOT inherit each other's viewing or first impressions. Record first confusion during 1.0× first viewing; classify severity honestly (`P0` stop publish: core science/rights/wrong version/ignored rejection/safety; `P1` block publish: broken causality, slideshow mechanism, occluded mechanism, masked audio, mixed styles, or any Human Comprehension P1 Blocker below; `P2` local polish). Never downgrade critical art, framing, or comprehension failures or user rejections to P2.

### Anti-Metric-Gaming Principle and Human Comprehension P1 Blockers

**Automated screening passes carry ZERO weight toward human watchability, comprehension, or cinematography.** Passing `colab_cli.py audit-blend` (high triangle counts, clean bevels, zero blocking issues), `opening_hook.py` (`flags=[]`), `retention_timeline.py` (`flags=[]`), `check_episode.py`, or noise-free Cycles lighting checks ONLY confirms minimum technical hygiene—never that a real human viewer can understand the story or follow what is happening on screen. Never rationalize shipping an incomprehensible or poorly framed film because technical flags are empty.

Treat each of the following eight failures as a **hard `P1` blocking return condition** (both during muted preflight / captioned beat-board review and during G2/G3/G5 review; return to scene/staging before expanding or delivering):

1. **Self-talk / unidentified CAD clutter:** Voiceover names components, passages, or state changes while the picture shows a crowded same-metal cutaway (e.g., brass-on-brass or steel-on-steel) with no active-part spotlighting, ghosting, or role color/finish contrast—failing the [1-Second Layperson Pointing Test](viewer-retention-design.md#explain-like-a-human-two-part-mental-model-and-strict-referent-lock).
2. **Frame-of-reference or physics-subject mismatch:** The film dives into internal forces/pressures without establishing *what stays fixed vs. what moves*, OR the camera focuses on a stationary component while narration describes a different moving surface.
3. **Telephone-pole / empty-void 16:9 framing:** A slender vertical mechanism occupies `< 25%` of a 16:9 widescreen frame stranded in empty blank void across consecutive shots without recognizable host anchors, diagonal framing, horizontal comparisons, or genuine shot-scale variety ([widescreen aspect-ratio framing](animation-scene-design.md#non-text-visual-pointing-grammar-and-widescreen-aspect-ratio-framing)).
4. **Cropped actuator, occluded port gap, or invisible flow direction:** Narration describes pulling a lever, pressing a pedal, turning a dial, shutting a port, or gas/liquid rushing through a passage, while the driver is cropped off-screen, transparent walls blur out the gap, or flow is invisible faint fog instead of discrete directional motion.
5. **Decorative sci-fi crutch or unintroduced mystery prop:** Arbitrary floating glowing toruses/rings, neon energy halos, or sudden teleported white/abstract comparison blocks appear without physical motivation or visual introduction.
6. **Deleted Real-World Scene / Flat Void Backdrop (`场景哪里去了`):** Hiding the real-world room, garage, or host vehicle during body cutaways (`env.hide_render = True`) and pasting a flat gray/slate/black backdrop card (`Stage_MacroBackdrop`) behind floating components.
7. **Blind Contextless Macro Sliver (`局部画面谁看得懂`):** Zooming so tightly (`> 75 mm` extreme corner crop) onto a 2 cm polygon or metal edge that the viewer cannot tell where on the real machine it sits, what drives it, or what physical outcome occurs — violating muted visual-first comprehension.
8. **Crude Primitive Substitution (`卡钳是方的吗`):** Faking curved, cast, ribbed, or sculpted real-world industrial hardware with rectangular boxes (`create_box`) or plain cylinders instead of true high-poly CAD silhouettes or verified open-licensed 3D host models.

## Using Stage-Evidence Checks and Their Limits

`check_episode.py` stages: `plan` (structure only), `G1`–`G7` (gate + prerequisite digests), `delivery` (local completion through G5 + full decode), `publish_ready` (adds G6 previews/declarations/authorization). Every continuous viewing/listening record uses seconds (`ms / 1000`), exact file/hash, and separate records if watched vs heard ranges differ. Dual listening (headphones + phone speaker) follows [voice reference](voice-reference.md#listen-separately-to-source-audio-and-the-final-mix) without forcing picture re-viewing per audio device. Real-footage anchors apply only to shots using `real_footage`; human audience feedback is strictly optional (`not_run` by default, zero synthetic participants).

## Levels of Fine Finish and Itemized Evidence

Target finish is `L3` (`production-policy.json quality.finesse`): `L0` broken, `L1` crude, `L2` solid with reference gaps, `L3` matches approved reference finish across static (`A01`–`A10`), motion (`D01`–`D08`), and integration (`I01`–`I05`) under [positive standards](visual-system.md#positive-completion-standards-for-finely-finished-2d). All three dimensions must independently reach `L3` (no averaging); mark `not_applicable` only with genuine reason (`A07`, `D06`, `I05` depend on film needs). Unverified items stay `pending`. Benchmark qualification requires L3 + repeatability under [benchmark completion](production-checkpoints.md#completion-definition-for-a-benchmark-and-repeatability).

## Stage Evidence for Art Methods

Connect visual checks to existing stages without new gates or duplicate approvals (record notes in [art record](../assets/art-direction-template.md) and bind every referenced image/strip/manifest individually as `{file, sha256}` in `qa.gates.<stage>.evidence`):

| Stage | Evidence & scope | Existing QA binding |
| --- | --- | --- |
| G2 | Whole-film color/composition thumbnail strip + complete voiced rough cut | `qa.expression_plan.evidence`, `qa.shotbook.note`, `qa.gates.G2.evidence` |
| G3 | High-risk representative sample + three-scale stills (`whole_scene`/`object_midshot`/`mechanism_closeup`) + continuous action | `design.keyframe_scales`, `qa.visual_frames.animation.scope_note`, G3 evidence |
| G5 | Complete final encode vs master & covers (at full size + phone scale), itemized A/D/I evidence | `qa.visual_frames.finesse`, G5 evidence |
| G6 | Authorized target-platform prerelease preview (occlusion + detail) | `qa.mobile_preview.note`, G6 evidence |

Save new per-stage snapshots (`art-G2-v1.md`, `art-G3-v1.md`, `art-G5-v1.md`) rather than mutating earlier passed snapshots.

## Autonomous Explanation and Expression Review

Both G5 reviewers inspect the final export independently of generation context, judging only what the work actually shows/says up to each timestamp and noting the first breakdown:

| Check | What to verify | Repair on failure |
| --- | --- | --- |
| E01 Goal & E06 closure | Restate question + answer from the film alone under [whole-film direction](viewer-retention-design.md#direct-the-whole-film-before-polishing-its-parts) | Repair full script/edit if context, promise, or closure disconnects |
| Opening hook (0–5 s) | Frame 0 moving & recognizable, 2 s object + tension, payload within [canonical timing](viral-appeal-and-packaging.md#the-opening-beat-sheet), natural entry | Return to [hook lab](viral-appeal-and-packaging.md#run-the-hook-lab-at-g1); fix shot/line, never speed speech |
| Opening→body bridge | Normal-speed watch through first body payoff: why looking here, scale/object link, advancing rather than restarting | Repair adjacent shots/bridge; dissolves/music cannot fix broken logic |
| E02–E05 Premises & reasoning | Prerequisites precede use; no leaps; continuous progress toward answer | Add missing link/premise; remove dead branches rather than adding “所以” |
| E07–E09 Key picture & path | Core picture carries the visible change/comparison; viewpoint/scale changes preserve orientation | Show real state change and anchors; teaching scans must not fake event order |
| E10–E12 Channels & limits | Narration guides, picture proves, captions match accurately; analogies/models state boundaries and avoid core misconceptions | Align timing, state limits clearly, resolve ambiguity visually |

Complete new films also run the [scroll-viewer appeal check](viral-appeal-and-packaging.md#scroll-viewer-appeal-check) (frame 0/1 s/2 s muted & voiced, ~8 s promise, swipe-risk timestamps, late answer + clean fast ending, promise honesty) with the bound cold 2 s test in `qa.opening_hook` (G3 sample, G5 final). Text purposes follow [visual system](visual-system.md#visible-text-purposes-and-production-excuses); whole-episode voice tone and continuity follow [voice reference](voice-reference.md#whole-episode-narration-continuity).

## Probe understanding without inventing an audience test

When a conclusion could be parroted without understanding, apply a brief nearby-condition diagnostic inside `understanding_goals.transfer` / `boundaries` using only premises the film presented (e.g., larger shoe area alone cannot establish lower pressure without knowing load). Optional when unhelpful; never an audience test, quiz, or extra gate.

## Declared independent-review identity checks

For agent-based G5 explanation and expression passes, record distinct actual reviewer identities in `reviewer` (and `review_task_id` when locating host tasks). The validator rejects identical agent identities or identical task IDs across the two responsibilities; preserve historical receipts without relabeling reviewers to force a pass.
