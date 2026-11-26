# Production checkpoints from research to execution

Follow the single commissioned route under [SKILL.md's Route Isolation gate](../SKILL.md#route-isolation-load-only-the-active-route). This page owns explanation design, G1–G7 progression, storage moves, and platform release handoffs; [quality acceptance](quality-acceptance.md) owns actual review and rework. Execute only stages covered by the current commission.

## 1. Decide the one thing viewers should understand

Lock the original topic and audience under the [topic contract](topic-contract.md). Put three sentences in the brief: what viewers already encounter, what deserves a question, and what they can explain or judge afterward.

Complete G1's six topic-selection groups inside the existing brief/storyboard (no second form): (1) main question and necessary sub-questions, (2) target audience and starting knowledge, (3) one-sentence answer and takeaway, (4) relations/changes the picture must show, (5) required vs out-of-scope boundaries, and (6) misconceptions and prohibited depictions.

Check every new concept: which step toward the answer it supports, where its prerequisites appear, and what visible object corresponds to it. Remove unused terms and explain necessary ones nearby in everyday speech.

For complete feed films, run the [hook lab](viral-appeal-and-packaging.md#run-the-hook-lab-at-g1) first, then write the opening's final sentence/image together with the body's first observation under [context and bridging](viewer-retention-design.md#connect-the-opening-to-the-first-body-observation). Before full narration synthesis or batch refinement, verify whole-film coherence under [whole-film direction](viewer-retention-design.md#direct-the-whole-film-before-polishing-its-parts): restate the question and answer using only what is in the script and fix any structural break first.

## 2. Make explanatory relationships visible

Choose the topic's relationship types below so every section advances understanding (observe, supply prerequisite, establish relation, rule out misconception, or test prediction). Remove repeated previews and dead branches, and answer promptly once explained.

For every cut or model switch, pair the preceding shot's final state with the following shot's initial state (conclusion carried forward, retained spatial anchor, changed viewpoint/scale/state). Establish location before magnifying and keep the return recognizable; a dissolve alone is not a bridge.

Hold other variables constant in single-variable comparisons. Show necessary intermediate processes before results; do not invent delays or rearrange the whole frame at once. Clear outgoing layers so old objects do not ghost.

Record the explanation storyboard in `topic_alignment.coverage[].explanation_steps` (`causal_steps` is legacy compatibility only): `id`, `relation_type`, `prerequisites` (`{knowledge, source}` where `source` is `audience_prior` or an earlier `step` with `step_id`), `key_relation`, `derivation`, `boundary`, `referent_mappings`, `handoff`, `shot_ids`, `requires_dynamic`, and `key_difficulty` (`still_reason` when static). A prerequisite step must precede or match actual presentation order; later steps or an opening summary cannot fill an earlier gap.

### Expression plan for each key difficulty

Record key difficulties in `topic_alignment.expression_cards`: `difficulty`, `prerequisites`, `visual_action` (exact fixed vs changed elements, display order, states compared, or retained anchor), `inferable_outcome`, `misconception`, `boundary`, `step_ids`, and `uncertain`. For `uncertain=true` difficulties only, compare at least two low-cost visual approaches (`variants` + `selection`) before full refinement.

Use a brief familiar analogy only when it avoids piling up unexplained terms: map parts to real mechanism, state what differs, and return immediately to the real physical process (e.g., building-floor channels introduce multilayer wiring geometry, then return to electrochemical copper deposition and planarization rather than poured molten copper).

| relation_type | Relationship fields to record |
| --- | --- |
| causal | `before`, `change`, `after` (+ necessary intermediate states) |
| spatial | `objects_positions`, `constraints`, `reference_frame`, `spatial_relation` |
| structure_function | `components`, `organization`, `structure`, `function`, `mechanism_link` |
| comparison | `compared_cases`, `controlled_conditions`, `difference`, `inference` |
| quantitative | `quantities`, `relationship`, `conditions`, `common_scale`, `denominator`, `sample_scope`, `uncertainty` |
| probability | `outcomes`, `distribution`, `interpretation`, `uncertainty`, `common_scale`, `denominator`, `sample_scope` |
| evidence | `evidence_basis`, `inference`, `limitations`, `alternative_explanations`, `inference_rule` |
| propagation | `carrier`, `path`, `transfer` |

Frameworks in [explanation recipes](../assets/explanation-recipes.json) may be adapted per topic; they never replace scientific sources or actual art/motion review.

### Match each section's picture, sound and in-picture text

Write each semantic section as: **narration sentence → object/relationship → visible action/state → necessary marker (3D: single-letter only; other media follow their text rules) → actual audio time**.

| Narrated content | Picture implementation | Check & repair |
| --- | --- | --- |
| Object / component / “这里” | Make the referent identifiable first (framing, emphasis, or nearby marker) | Reframe if too small, ambiguous, or occluded; recheck audio timing |
| Change / comparison / evidence | Show actual process, controlled conditions, connections, or common scale | Rebuild states if only captions change or results appear prematurely |
| Position / orientation / viewpoint | Anchor axes and direction to physical objects before switching views | Restore locating cues if viewpoint shift breaks recognition |
| In-picture text | 3D permits single-letter markers only; non-3D uses concise needed labels only ([text purposes](visual-system.md#visible-text-purposes-and-production-excuses), [3D single-letter rule](spatial-typography.md)) | Delete prohibited plaques/excuses while keeping synchronized captions |
| Cross-shot / scale / analogy joins | Keep a trackable anchor or explicit old→new mapping | Reorder adjacent beats together; connective words cannot bridge a visual gap |

Mute first to check visual locating, then review with sound at normal speed. Fix broken explanation in the storyboard rather than patching captions.

## 3. Stage progression and representative samples

Pass the original request, latest delivery scope, permitted changes, and retained items on every delegation or revision. Internal samples never narrow a full-film commission, and local repairs preserve valid assets/audio. Repairs follow [failure handling](quality-acceptance.md#handling-failures).

Advance through [G1–G7](#actual-g1g7-progression-records) strictly to the commissioned depth: local delivery stops at G5; G6/G7 apply only to authorized platform release. Record actual version, status, next action, and unreviewed items honestly; cost or schedule never substitutes for quality.

## 4. Arrange understanding rhythm around actual narration

Under [continuous narration](voice-reference.md#continuous-narration-and-synthesis-units), finish the full script first, split by understanding tasks, and time shots from actual narration audio — never accelerate narration or delete necessary explanations to hit an arbitrary runtime. Keep observation holds clear while trimming dead branches under [viewer retention](viewer-retention-design.md).

### Start lock and actual rendering entry

This entry governs assembled stage media (`roughcut`, `sample`, `full`). Intermediate silent assets (single frames, stems, model checks) keep source/task receipts without requiring narration or prior G3, and cannot masquerade as voiced approvals.

- **Rule lock:** Create a write-once lock per session via `render_gate.py lock` (`execution.skill_lock`) invoking the [single global Skill](global-skill-installation.md); never copy executable Skill snapshots into projects. Explicitly migrate on resume after global rule changes.
- **Style baseline (`design.approved_film_reference`):** Bind either an accepted finished film (`kind=approved_finished_film`, allowing `method=frame_samples` / `purpose=appearance_only` when inspecting appearance stills without claiming continuous playback) OR an inspected first-trial reference (`kind=initial_style_reference` with `actually_opened=true` and observation). Both paths require G3 sample validation before expansion.
- **Adapter & phase receipts (`execution.entrypoint` + `render_gate.py run`):** Accepts `--episode`, `--phase roughcut|sample|full`, `--shot-ids`, `--output`. Nonzero exit blocks bypassing the gate; exit 0 records `rendered_unreviewed` only.
  - `roughcut` (`execution.roughcut_receipt`, `contract_version=2`): full voiced rough cut after G1; apply [moving animatics](quality-acceptance.md#moving-animatics-and-user-review) before user review.
  - `sample` (`execution.sample_receipt`): high-risk representative segment (for feed films, first build the 0–5 s [hook sample](viral-appeal-and-packaging.md#produce-and-test-the-hook-first), measured via `opening_hook.py` and cold-tested before G3 expansion).
  - `full` (`execution.full_receipt`): requires current G3 pass, matching style comparison, and zero blocking failures across all episode shots.
- **Google Flow route:** Follow [Google Flow production](google-flow-production.md) directly (`gemini_api_cli` via `scripts/gemini_api_cli.py` or `google_flow_web`, disk prompt ledger, `>= 1080p` / `1080p Upscaled`, `24 fps` CFR, paired `zh`/`en` records, IndexTTS-2.5 `#5` Mandarin clone / Edge English whole-track mastering, `google_flow_audit.py` + `check_episode.py` on both sibling editions).
- **Failure discipline:** Diagnose concrete causes before rerunning; never blindly repeat identical failing runs or invent unsupported wrapper gates.

## 5. Sole entry for quality judgments

Quality checks, unreviewed gates, and failure closure live solely in [quality acceptance](quality-acceptance.md); visual rules in [visual system](visual-system.md); voice rules in [voice reference](voice-reference.md). An explicit user comprehension failure requires structural rework and cannot be offset by technical checks.

## 6. Check from export through actual platform completion

Enter platform composers only with authorization under [manual-click handoff](#manual-clicks-and-publication-review-handoff). Check final title, complete description, [supported tags](#select-relevant-tags-at-publication), overlay occlusion, dense captions, and motion extremes on the actual target account.

Record preview surface honestly in `qa.mobile_preview` (`actual_device` or `desktop_platform_preview` with `platform`, `account`, `review_scope=target_platform`, `note`, and `reviewed_metadata_sha256` from `check_episode.platform_metadata_sha256(data, preview)` after real inspection). A browser phone frame is not an actual device; recheck whenever video, copy, or destination changes.

## Delivery package and publication receipts

Deliver strictly to `delivery_scope`:
- `release_package` (default): narrated captioned HD video (paired `zh` and `en` for complete Google Flow films), title/description/tags, independently composed 3:4 and 4:3 covers, provenance/rights statement, acceptance & pending list.
- `video_only`: record `delivery_scope_note`, omit covers, still deliver provenance and full-film QA.
- Single cover: set `requested_cover_keys=["cover_3_4"]` or `["cover_4_3"]`.

Keep public copy focused on the episode: strip production credits, render notes, or generic “原理示意” disclaimers at G6; keep provenance internal and use platform AI disclosure controls. For direct publication of an existing finished file, follow SKILL.md's direct-publication route (skipping G1–G6 production records while keeping the handoff rules below).

### Move accepted and published videos

Use `archive_root` in trusted local `config/video-storage.local.json` (`release-candidate` for G5-accepted videos awaiting publish; `archive` for user-confirmed published videos):
- **After G5 acceptance:** Move each G5-bound final video (both `zh` and `en` for complete Google Flow deliveries) to `release-candidate`, placing any checked `-feed916` derivative and `-textless` master alongside with recorded SHA-256 values. Keep project records, covers, captions, and drafts at project paths.
- **After user confirms publication:** Move the confirmed published version/edition to `archive` (user confirmation suffices; no separate G7 request needed). Keep scheduled/moderation-pending works in `release-candidate`.
- **Verify every move:** Never overwrite an existing work/version. Across volumes, copy to a temporary partial file, read back size + SHA-256, rename atomically, and remove source only after verifying destination integrity. Keep original review records intact and pass moved paths explicitly via `--stored-video`:

    python -X utf8 scripts/check_episode.py <episode.json> --stage publish_ready --stored-video <absolute-stored-video> --report <new-receipt.json>

### Manual clicks and publication review handoff

- **YouTube audience:** Apply standing `operations.youtube_made_for_kids` from [series profile](../config/series-profile.json) unless overridden for the video.
- **Xiaohongshu:** Open the official publish page when requested; hand over adapted title, description (with `#科普`), and paste-ready directory + file paths for the accepted 16:9 landscape video master and finished 4:3 cover (`cover_4_3`) in one handoff. Paste plain text only into creator-focused fields; the creator operates navigation, uploads, topic picker, settings, and submission.
- **File chooser handoff:** Provide the verified absolute directory in one standalone code block and exact file path in a second code block using native OS separators (`C:\...`). Hand off checked 9:16 feed packages for the Douyin composer group and accepted 16:9 landscape masters for Xiaohongshu and YouTube.
- **Pacing & release spacing:** Let controls settle before clicking. Follow `operations.publication_spacing` (`recommended_min_gap_hours`, avoiding burst posts) unless explicitly overridden; never alter schedules autonomously.
- **Stop after submission on ALL platforms:** Once submitted/scheduled or handed off in a ready composer, STOP interacting with that destination for the submitted work. Do NOT reload result pages, browse published posts, poll dashboards, screenshot results, or retry uncertain submissions. Record `submitted, creator review pending` or `ready for user submission`; record G7 work IDs/status only from user-supplied evidence when asked.

### Select relevant tags at publication

Select the exact `科普` tag on every publication (via platform picker where available, `#科普` in body copy on hashtag-only/Xiaohongshu platforms), plus a few relevant mechanism/subject tags within platform limits. Record unavailable pickers honestly.

### Assign every public video to its matching Douyin collection

With `operations.douyin_collections` enabled in [series profile](../config/series-profile.json), assign every authorized public science video in Douyin Creator Center (`添加到合集` / `选择合集`) to its single best-matching standing collection and verify selection before submission:

| Order | Standing collection (`合集标题`) | Primary mechanism scope | Typical subjects |
| --- | --- | --- | --- |
| 1 | `透视日常造物` | Everyday objects, packaging, appliances, food/kitchen physics, daily mechanical/safety devices | Fuel nozzles, tamper caps, dry pasta, QR codes, seatbelts, pressure cookers, RCD breakers, pull-tabs, soap bubbles, popcorn |
| 2 | `解码巅峰工程` | Heavy machinery, rail/transit, aviation/aerospace, industrial manufacturing/3D printing, precision scientific/medical instruments | MRI, electron microscopes, elevator safety gears, pantographs/welded rails, SLA 3D printing, turbine blades, neutrino detectors, rockets, spacesuits |
| 3 | `丈量天地寰宇` | Weather, atmospheric optics, natural phase-change physics, geology/volcanology, space/astronomy | Petrichor, clouds, lightning, frost, hurricanes, snowflakes, geysers, supercooled water, rainbows, dew, auroras, coronal rain, lava, tidal locking |
| 4 | `探秘生命法则` | Animal/plant biomechanics, evolutionary limits, biological structures/behaviors, human sensory/perceptual mechanisms | Camouflage, beaver teeth, wombat feces, coconut octopus, sea slugs, capsaicin heat, high-altitude birds, redwoods, hadal fish, owl flight, optical illusions |

- Route strictly by the video's primary physical/scientific mechanism. Exclude private (`私密`) or non-series personal clips. Never create ad-hoc collections or reorder without explicit creator authorization.
- Record the selected collection in release notes; compose any `1:1` collection cover (`1080×1080`, `<= 5 MB`) via `scripts/compose_cover.py --ratio 1:1` under [cover standards](visual-system.md#finished-cover-standards-for-engineering-and-manufacturing-topics).

### Cross-platform association, monetization and download controls

Use one authenticated Douyin Creator Center composer for Douyin plus native cross-posts (`西瓜视频`, `今日头条`, `番茄小说`) according to authorized scope. Verify account, exact video, covers, copy, `科普` tag, [matching standing Douyin collection](#assign-every-public-video-to-its-matching-douyin-collection), optional scheduler timestamp, and settings together before a single submission:
- **Eligible Douyin activities:** When `operations.douyin_join_eligible_activities` is enabled, inspect displayed options/terms against what the video actually teaches, select compatible eligible activities (preferring narrow subject fit if capped), and verify coexistence/tags without enrolling in separate agreements or paid promos.
- **Eligible monetization & originality:** Enable available per-work options (`广告分成`, Xigua revenue) and `原创` declaration where eligible under verified provenance; record unavailable/ineligible controls honestly.
- **No-download preference:** Apply standing no-download/no-save (`不允许` in Douyin; disable download/save on every supporting cross-post destination). Verify actual toggle state rather than assuming propagation; keep unconfirmed switches pending.

### Declare AI-generated content at publication

Apply [generated-content declaration rules](science-and-rights.md#actual-publication-steps-for-generated-content-declarations) before submission: select “内容由 AI 生成” / “AI 创作” (or current equivalent) while keeping separate optional creation categories off per [series profile](../config/series-profile.json). Record observed toggle states and destination coverage; the user verifies displayed labels after submission under [publication handoff](#manual-clicks-and-publication-review-handoff).

## Actual G1–G7 progression records

Hard gates (`H`) and calibratable starting points (`D`) come solely from [production policy](../config/production-policy.json). Optional diagnostic scores never override failed or unknown hard gates. Assign owners in `brief.roles` (one person may hold multiple production roles; independent review requires a separate person or fresh independent context).

| Gate | Required output / check | Unlocks | Return on failure |
| --- | --- | --- | --- |
| G1 | Six topic groups, fact cards, explanation steps for all required scope, prerequisites, expression cards, prohibited depictions, internal science/logic review | Script & storyboard | Narrow topic / research |
| G2 | Checked script, expression-plan review, actual working audio, full-episode shotbook, complete voiced rough cut viewed/heard continuously (checking every adjacent-shot join) | Finished art / sample | Script / shot order |
| G3 | Three-scale art/forms, formal audio/captions, complete high-risk representative segment (binding difficulty cards, prerequisites & joins) + 0–5 s hook sample independently viewed/heard | Same-system expansion within verified scope | Art / action / sample |
| G4 | Full film export, audio stems, captions, editable project, provenance & asset manifest | Formal G5 acceptance | Corresponding process |
| G5 | Independent explanation & expression reviews on final export, L3 finesse, dual listening, captions, technical & viewing-safety checks | Delivery / release queue | Corresponding process |
| G6 | Locked release package, platform preview, [cover consistency](visual-system.md#series-cover-consistency-at-publication), [standing Douyin collection](#assign-every-public-video-to-its-matching-douyin-collection), [associations/monetization/no-download](#cross-platform-association-monetization-and-download-controls), rights, [AI declaration](#declare-ai-generated-content-at-publication), authorization | Authorized submission | Release package / settings |
| G7 | User-supplied offline publication evidence (work IDs/links, times, status, settings, displayed covers/crop) when requested | Verified unique publish count | Leave unclear items with user |

`qa.gates.G1..G7` reference existing QA (`not_reviewed`, `needs_changes`, `passed`, `cancelled`) with reviewer, timestamp, scope, evidence hashes, and context digest. Later gates cannot backfill failed prerequisites; `plan` checks never pass G2.

- **G1→G2 timing:** G1 may use a [relative-stage plan](shotbook.md#g1-paper-plan-without-audio); before G2 acquire real working audio, time shots from it, and watch/listen continuously to verify adjacent-shot joins (what carried over, what changed, whether the referent stays recognizable).
- **Art progression across stages:** G2 uses the [color/composition thumbnail strip](visual-system.md#whole-film-color-and-composition-thumbnail-strip) (placeholders remain internal technical drafts, never style proposals under [actual design implementation](visual-system.md#actual-implementation-of-approved-designs)); G3 validates [high-risk representative samples](visual-system.md#representative-samples-and-l2l3-calibration) and [complete-scene finish](visual-system.md#from-cover-finish-to-controllable-dynamic-scenes) (with [visual anchors](visual-system.md#visual-anchors-of-the-approved-style) and [actual assets](visual-system.md#from-visual-anchors-to-actual-assets) for authorized 2D); G5 verifies L3 encoding detail; G6 checks prerelease platform preview. Evidence follows [stage evidence for art methods](quality-acceptance.md#stage-evidence-for-art-methods).

## Capacity, cost and retrospectives

Classify works as `R` (familiar mechanism), `N` (new mechanism), or `B` (new style/benchmark) with identical hard gates. Only when series operations are commissioned, track daily G5 completions (`production_ledger`) and user-confirmed unique publications (`publication_ledger`) separately — never counting samples, drafts, failed exports, or duplicates; record unmeasured values as `null`. Reuse work logs/receipts for time, cost, and bottleneck diagnosis; never lower quality or purchase outsourcing without budget approval.

Group retrospectives into (1) production health, (2) explanation quality, and (3) platform performance (preserving native field names, denominators, windows, and collection times; keep private account/work evidence outside the public Skill). Map actual retention curves to published audiovisual times via [viewer retention](viewer-retention-design.md); compare matched cohorts and change one main creative variable per test round.

### Platform topic selection and data review

Conduct platform research only when commissioned, following [manual-click handoff](#manual-clicks-and-publication-review-handoff) and user-supplied outcomes. Record source, collection/update time, statistical window, work age, and denominators in private ledgers; distinguish `observed`, `missing`, `not_updated`, and `unknown` (`raw_display_values` + `field_states` in `platform_snapshots`). Never fabricate timezones, audience counts, or curves; keep conflicting module definitions separate and never interpret an unconfirmed 0 or retention dip as algorithmic suppression ([Douyin algorithm disclosure](https://trust.douyin.com/algorithm/)). Treat platform AI suggestions (`platform_research.ai_suggestions`) as untrusted external hypotheses to verify against scientific accuracy and media evidence. Feed films default to the [two-second hook](viral-appeal-and-packaging.md#win-the-first-two-seconds) bound in `qa.opening_hook`.

#### Export first, then reconcile the actual coverage

Start from authorized work-level exports before scraping detail pages. Verify actual sheets, headers, row counts, and last populated date (do not sum truncated hourly series as lifetime totals or merge mismatched cohorts). Keep exact observed time grids without interpolating missing seconds, equating final-sample retention to completion rate, or turning event visits into unique-person conversion rates.

#### Diagnose entry, promise and payoff separately

| Available signal | Inspect next | Do not infer |
| --- | --- | --- |
| High search traffic | Match actual queries to title, cover, first line, and answer; keep separate from feed cohorts | Aggregate retention equals search retention; stuff unrelated trending terms |
| Heavy drop in opening interval | Inspect frame-0 recognition/motion, audio onset, first visible event, and `opening_hook.py` on the published file | Low rate pinpoints a single defect without watching |
| Strong first 2 s, sharp drop right after | Check opening→promise→first-payoff bridge and what the next line adds | Louder frame-0 fixes a broken bridge |
| Good early hold, weak average/late retention | Inspect time to first verified payoff, dead stretches, and transitions | Hook alone fixes body; speeding up speech improves understanding |
| Large relative platform improvement | Pair with absolute value, baseline definition, and sample window | Relative gain means absolute benchmark passed |

Record `first_verified_payoff_s` only after inspecting actual published picture/narration (leave `null` until verified; never trust auto-generated chapters as ground truth).

#### Reconcile platform advice with dimension-level evidence

Log platform diagnoses/AI advice under exact displayed labels alongside supporting metrics, conflicting metrics, and missing definitions — never relabel praise or advice as causal proof. Separate displayed comment totals, unique IDs, root threads, replies, and distinct non-author commenters. Track text corrections separately across publication copy, burned-in captions, and audible narration on the actual observed version/interval (optional `scripts/platform_evidence.py` aligns exact-time samples and comment coverage locally without diagnosing causes). During authorized Skill maintenance, promote only generalizable fixes with synthetic counterexamples, keeping raw account data private.

#### Turn each useful review into a next-production change

Close the private research record with a short `next_production_brief` (`experiment.production_action`, `responsible_role`, `review_segment`, one primary variable, metric/window, alternative explanations). Integrate before the next G1 script and verify actual implementation at G2/G5 (keeping cold-view pass first); media verification and later audience effect remain separate.

## Completion definition for a benchmark and repeatability

Validate repeatability against `adoption_validation` in [production policy](../config/production-policy.json) only when building a series system (single-episode commissions do not require extra replication episodes). Export all derivatives from one master project (never download/re-encode published copies), verify streams with `ffprobe`, keep `source_ids` as referenced ID lists, keep `qa.release.authorization_status` distinct from package readiness, and record `actual_commit` only after a real Git commit.

## Whole-film coverage and expansion boundaries

G2 shotbooks must continuously cover `0` through the full audio track end. Before G3 expansion (`qa.visual_frames.animation.next_action="expand"`), every blocking failure scoped `whole_episode`, `series_style`, or `segment` must be closed by actual recheck — local repairs (`repair_sample`), technical passes, or renaming cannot lift expansion blocks.

## From learning a reference to actual improvement

When closing a concrete gap from a reference: (1) actually watch/listen to the reference interval (checking science and rights separately), (2) map the transferable method to the exact defect without copying media or breaking locked style, (3) test on the affected G2/G3 sample (maintenance-only runs keep methods as unverified candidates), and (4) compare before/after under matched conditions in the [art record](../assets/art-direction-template.md).

## E02–E07: Explanation design before refinement

Complete E02–E07 in the same G1 brief and explanation storyboard (no extra forms):

| Item | Output & check |
| --- | --- |
| E02 Audience starting point | Separate assumed knowledge, newly established knowledge, and out-of-scope; bind prerequisite sources |
| E03 Structure | Order prerequisites, key relations, conclusions, and conditions by actual `relation_type` |
| E04 Reasoning | Verify every “therefore” already presented its required change, constraint, or evidence |
| E05 Segmentation | Segment by comprehension tasks; pair preceding final state with next initial state |
| E06 Integration | Ending reconnects original phenomenon, mechanism, and answer without new concepts |
| E07 Expression | `expression_cards` states fixed vs changed visual actions and outcome; compare 2 low-cost plans only if `uncertain=true` |

G2 checks the voiced rough cut; G5 checks E08–E12 in [quality acceptance](quality-acceptance.md#autonomous-explanation-and-expression-review).

## Precise control and efficient iteration

Applies to authorized prototyping and rendering. Silent intermediates keep versioned inputs/outputs; once assembled into stage media, full voiced review applies.

### Action states and visible success conditions

State initial state, transitions, final state, fixed anchors, contacts, and visible failure criteria per shot before rendering. Use verifiable scientific observations for research and self-created visuals or authorized user capture for production ([original visual provenance](science-and-rights.md#original-visual-provenance-contract)); AI environmental shots are not mechanism evidence.

### Fixed baselines and evidence-based hypotheses

Preserve a traceable baseline and exact inputs each round, changing only design variables stated in advance. List coordinated changes explicitly; evaluate at matched scale against visible criteria rather than guessing from prompt edits. Image-to-video constrains framing/initial state but cannot guarantee contact order, fluid mechanics, or higher quality; panning a still is not generated motion.

### Conditional reuse of static evidence and fresh dynamic checks

Reuse static environment/tool provenance only when original records bind checksums/versions and nothing changed; recheck immediately on any change or frozen-entry requirement. Scope ordinary checks to files actually used (authored scene/helpers, models, textures, caches, executor identity) — do not recursively hash Python/NumPy or OS DLLs on routine previews.

Use a stable verified executor with per-job immutable parameters (on Controlled 3D Blender routes, default to Colab GPU `scripts/colab_cli.py blender-render` with automatic local GPU fallback via [reusable runner](blender-execution.md)). Measured comparison is required before claiming time saved; collect dynamic resource observations afresh each time.

Bind executor identity locally via controlled launch/lock evidence (preserving full fractional-second UTC timestamps without losing precision). Refresh resource headroom, service identity, queue ownership, and execution budget immediately before launch. **GPU utilization is telemetry, not a launch blocker:** never stall, wait for idle, or force CPU from utilization metrics or invented VRAM ceilings; refusals must cite a real requirement/OOM/fault. When no real resource blocker exists, proceed within authorization without inventing another resource approval step.

### Record normalization and incremental review

Normalize declared text-channel coverage once with `scripts/review_delta.py normalize-text` and triage diffs with `scripts/review_delta.py compare` (triage only, never approval). Consolidate paperwork, automate derived fields, and avoid routing silent intermediates through full G1–G3 gates or creating needless silent intermediate encodes.

### Single submission and minimum recovery record

Save a durable minimum recovery record (task/candidate ID, frozen inputs/entrypoint, single-submission marker, executor, timestamp) before submission, then record service task ID promptly. On timeout/disconnect/unknown outcome, inspect queue/history/output read-only first — **Do not blindly resubmit** or switch directories to reset one-time locks. Distinguish proven non-submission (`known noPOST`) from `unknown POST`, persisting raw failure samples before raising errors.

### Segmented timing and controlled service reuse

Time pure inference strictly from inference start/end timestamps (label broader ranges as `service-task duration`). Separately record static verification, queueing, loading, inference, encoding, checks, review, and archiving. Authorized batches may reuse a compliant unchanged service/loaded model under single-submission checks; **Do not stop services outside your authority** or clear others' queues.

### Prioritize output review/feedback and archive

On 3D routes, archive reused editable assets to the designated NAS under [engineering shared asset library](engineering-blender.md). After any render completes, verify stream/file integrity and review continuously at normal speed before archiving. **Applicable voiced stages still require actual listening and independent review.** **Save the minimum recovery record and current media identity first**; lengthy archiving may run asynchronously without blocking review (never claim backup complete while pending).

### Stop hard failures and substantiate optimization claims

State hard-failure stop conditions before each round and halt futile seed/prompt sweeps when hit; propose a next bounded candidate only with new causal evidence. For recurring motion defects, escalate through [complete repair cycle](blender-execution.md#complete-a-repair-cycle-before-expanding) without degrading requested motion into stills. **Without comparative measurements**, never claim speed or quality improvements.

## Choose a comparison that separates explanations

When a question hinges on a misconception or competing explanation, pick an observable difference that actually distinguishes the rivals while holding confounding conditions trackable (e.g., equal starting temperature when contrasting metal vs wood heat-transfer feel). Record in existing `expression_cards` (`misconception`, `boundary`, `visual_action`, `inferable_outcome`) without adding extra stages.
