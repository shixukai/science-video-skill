<a id="从成品音轨到可复核的逐镜记录"></a>
# From finished audio to verifiable per-shot records

Write per-shot records in `shots[].shotbook`. Actual gaps are permitted during planning; complete the current version before requesting finished-film delivery.

<a id="音频先行但不牺牲画面"></a>
## Audio first without sacrificing the picture

Use the complete continuous explanation saved in `narration.script_file` as narration text. First divide it into complete semantic sections by understanding task, then arrange shots and semantic beats. Each shot's `narration_exact_text` matches an original passage from that script; do not write separate mini-scripts and stitch them into narration. Determine times from the current actual track, without inferring them from estimated character counts or fixed 4–6-second cuts. Each beat states its attention task and priority without a mechanical object-count limit, as well as the narration trigger, actual track time, relevant object action/state or relationship to observe. Introduce objects before referring to them. Stationary observation can be a legitimate action; do not add floating, shaking or forced pushes/zooms merely to look lively.

At G2, concatenating `narration_exact_text` in shot order must reconstruct the full script, ignoring only formatting whitespace. Use an empty string for shots without narration. This checks text-structure consistency only, not explanation logic.

`start`, `end` and `beats[].at` are seconds on the finished-film timeline. Shots are ordered and nonoverlapping; dissolves are composited within a shot. For a pure observation shot without narration, use `beats: []` and explain the pause's purpose with `silence_reason`. Semantic beats cover actual narration events; do not invent words to fill silence. Every shot records `subject` (object), `action`, `framing` (shot size/framing), `claim_support` (how it supports the listed claims, or its narrative role if no claim) and `motion_purpose` (how change aids understanding or why it remains still).

Write the current narration file's SHA-256 to `narration.audio_sha256`. After recording changes, cropping, speed changes or reordering, listen again and realign all affected semantic beats. Updating a checksum cannot replace listening.

<a id="先设计状态再精绘关键态与分层动作"></a>
## Design states before refining key states and layered motion

Under [animation scene design](animation-scene-design.md#work-order-action-intent-before-detailed-art), determine state changes, persistent/new/separating structures and inter-shot relationships before key states and assets. Review key states for this episode's medium and [visual baseline](visual-system.md), recording file, SHA-256, conclusion and observations in `keyframe_review`. MoneyPrinterTurbo is the main production tool for realism; Blender is the main tool for 3D animation. 2D is restricted to explicitly authorized scope. Panning/zooming or revealing a final-state image cannot replace process animation.

At a cut, design the preceding shot's `final_state` and following shot's `initial_state` as a pair. `transition_reason` states preceding/following shot IDs/times, the conclusion carried forward and next task. Preserve recognizable correspondence with `object_ids/spatial_anchor` and viewpoint. Motion-card fields are below; do not create a duplicate ledger. Record actual audiovisual review in `qa.shotbook`, with `reviewed_sha256=shotbook_sha256(data)`. Recheck affected content after shot, asset or track changes. `assets[].sha256` binds the current file.

<a id="整片视觉抽帧工具"></a>
## Full-film frame extraction helper

When static location/diagnosis is needed and `shotbook.start/end` already align with media, [build_visual_review.py](../scripts/build_visual_review.py) can create local support material. Reuse suitable existing extracted frames; running the tool is not a mandatory operation at every stage. Run from the Skill directory:

```bash
python3 scripts/build_visual_review.py /path/to/episode.json --media renders/candidate-v3.mp4 --output reviews/G5-v3
```

Python3.11+ and local ffmpeg/ffprobe are required. `--media` and relative `--output` are rooted at the episode directory and must both remain inside it. Output goes to a new directory without modifying episode/QA. Only local self-contained videos are accepted; playlists are rejected. For nonsquare pixels or special display transforms, first export a corrected copy in production software. `relative_plan`, empty/nonfinite times, overlapping/unordered shots or out-of-bounds shots fail.

By default, the tool outputs `index.html`, first/middle/last PNGs for each shot, `manifest.json` and `gate-evidence.json`. This is a technical sample count, not a manual-viewing, model-call or upload quota. Choose actually needed times under [risk-based review](quality-acceptance.md#risk-based-rechecks-and-evidence-reuse), and still watch necessary processes continuously. The overview preserves the full frame and lists covered/uncovered ranges; the final sample uses an actual frame before the shot's end boundary. The manifest records requested times and actual frame times. Short shots or low frame rates can yield duplicate frames; add missing key mechanisms, joins or extrema separately.

The manifest preserves the episode snapshot, source video, HTML/PNG digests and tool version. Frame paths are relative to the extraction directory, while media/episode paths are relative to the episode directory. `timeline_sha256` binds only shot IDs and start/end. QA-only changes alter the snapshot hash; media/time/content changes require rebuilding in a new directory and rechecking affected scope.

`gate-evidence.json` is a file list that may be copied into `qa.gates.<stage>.evidence` according to actual review scope. Its paths are rooted at the episode directory and directly list the manifest, HTML and all PNGs with SHA-256, excluding the list itself. Reference only the evidence scope actually adopted. Generating all PNGs does not require viewing every one, copying them into every QA record or sending them outbound. Separately list files actually used for observations, master-reference comparisons or supplementary clips. Referencing only this list or the manifest does not recursively bind images in a stage check; see [stage evidence](quality-acceptance.md#stage-evidence-for-art-methods).

The page supports [whole-film arrangement](visual-system.md#whole-film-color-and-composition-thumbnail-strip) and static diagnosis. Color fidelity, small-screen/platform display, motion and complete audiovisual media require separate actual review.

<a id="设计和资产引用绑定"></a>
## Bind design and asset references

Templates for new realistic work include design.visual_intent and per-shot shotbook.realism; fill them according to actual implementation. Default empty values are not authorization. G1 binds only textual meaning and purpose; later layout/media stages recheck coordinates/timing. A local label movement does not require redoing unchanged topic selection. First-sample baselines and roughcut/sample/full receipts are defined in the [production entry](production-checkpoints.md#start-lock-and-actual-rendering-entry).

The brief fixes the Skill commit, series-profile and tokens versions/hashes, private design-board ID/hash and approval scope. Register actually used design images, components, videos and audio in the existing `assets` with actual kind, provenance/rights, version notes and `sha256`, then link through `shots[].asset_ids`. Do not misreport configuration parameters or indexes as live footage. Record versions and locations of configuration/design evidence copied into the project in the brief and `qa.visual_frames.note`. Do not write latest version or infer design-board approval merely from public tokens.

Actually inspect consistency among the design board, configuration and picture under the quality reference. Public-index validation does not cover private media.

Only when a specific historical 2D style is authorized, register fixed versions/hashes of the Skill's [reference image](../assets/style/accepted-style-reference.png) and [art specification](../assets/style/bright-nature.art-direction.json) in the brief's references. Record actual image viewing and this shot's adopted features in the art record; prose cannot establish that an image was viewed. If generating a project design board from those references, `design.board_reference/board_sha256` still points to the current actual board. Separate reference-appearance approval from the new board's actual review scope; do not fill in the series-reference hash as new-board approval. For stage freezes, separately list used reference copies, specifications and actual comparison files in existing gate evidence. Do not infer old project inputs from a later installed version.

<a id="逐镜结构与方向图形记录"></a>
## Per-shot structure and directional-graphics records

Save checks of the actual export for this shot in `shotbook.visual_logic`, without another ledger detached from the storyboard:

- `review_scope`: use `final_export` only after actually inspecting the current final export. Plans/short samples cannot sign for it.
- `orientation`: `applicable` is Boolean. Use true where object structure or direction is involved, and record `status`, `reference` (factual-reference location), `frame_mapping` (object-left/right, screen-left/right and front/side/back view), `structures` (key structural observations), `transforms` (mirroring/flipping/view changes and consistency across shots), and `evidence` (actual frames/continuous clips and times). Use false only for explicitly absent structural/directional relevance and give a `reason`; nonapplicability cannot bypass known defects.
- `graphics`: for every visible arrow or nondirectional leader, register unique `id`, `kind=arrow/leader`, this shot's `asset_id`, `component_reference` (component source/version) and `license_evidence` (license/original-creation basis matching the asset ledger). If no such graphics exist, use an empty list and explain with `no_graphics_reason`.
- Every graphic's `checks` records per-item `status`, specific `note` and actual-export `evidence`. Arrow items are `tip`, `shaft_join`, `visibility` (scale/crop/occlusion), `direction` (meaning), `endpoints`, and `motion_extrema` (animation extrema/continuity). Leaders require only `visibility`, `endpoints` and `motion_extrema`; endpoints explains the label/object connection and absence of directional meaning. Static graphics also record final dimensions/crop and explicitly state that there is no animation.

Inventory all relevant objects and graphics actually exported in each shot. Repair failures, omissions and unreviewed items first. Do not change applicability or rename an arrow as a leader to hide defects. Review component, mirroring, shot and export changes again, binding current asset, shotbook and export digests.

Per-shot provenance belongs in `shotbook.origin`, and asset provenance in `assets[].origin`. Fields, evidence and the research/delivery closure boundary uniformly follow the [original visual provenance contract](science-and-rights.md#per-shot-provenance-evidence). Preserve existing modality, rights and viewing records. Added provenance fields are neither approval nor permission to rewrite historical results retroactively.

<a id="素材选择要能复核"></a>
## Make asset selection verifiable

First state the object, action, framing, duration and supporting claim. Then actually inspect corresponding candidate intervals and compare object correctness, action coverage, clarity, composition margins and rights. Search thumbnails cannot replace viewing.

`candidates` preserves provenance, `viewing_note` and selection decisions. A main candidate's `asset_id` must belong to this shot; auxiliary layers use separate `asset_ids`. `source_interval` records original-footage in/out points and time basis. Only static references/original images may use `still/full`; panning/zooming a photo is not live footage. If there is only one lawful candidate, explain with `alternatives_note`. Preserve source, creator, rights evidence, scope and attribution through the asset ledger.

<a id="可选工作方式"></a>
## Optional working methods

Editable editing projects may use separate narration, captions, music/effects, picture and in-picture annotation tracks for replacement and verification. Claim delivery of an editable project only after actual export and opening/verification in the target editor. Current rules do not promise compatibility with a particular editor.

For generated references, identify each reference's responsibility for object identity, structural facts, style, action or composition. Describe actions and relationships to preserve by interval, and review outputs per shot.

For external methods' provenance, licenses, fixed versions and actually adopted features, see [external skill selection](video-skills-curation.md).

<a id="动作卡镜头配方与事件复核"></a>
## Motion cards, shot recipes and event review

For actual process shots, implement eight motion-card items in the existing shotbook: object/anchor, initial state, trigger, key change, final state, trajectory, speed/observation pauses and what viewers learn. Add physical conditions, teaching simplifications, key poses, narration events and actual audio hash. Do not impose a universal elastic curve on different mechanisms. Changes in path, direction, constraints, occlusion or observation conditions may be substantive mechanisms; deformation is not mandatory. Key images also state viewpoint, attention center, motion path, caption area and scale changes.

Reusable recipes record question type, conditions, shot structure, assets, motion cards, narration events, scientific risks and positive/negative examples. Whole → detail → whole must return to the same object. Before → trigger → after preserves intermediate change. A same-condition comparison changes only relevant variables. Propagation → response checks cause/direction/delay, without treating a wavefront as matter flying out. A cutaway first establishes external shape and the cutting relationship, then restores the whole. Silent web demos/relative timing are only candidates; they cannot satisfy G3 or prefill absolute timecodes for ungenerated audio.

For D timing such as locating/labels, scale changes and observation pauses, see the production policy and calibrate to the task without mechanical uniformity. An actual semantic audio-versus-picture event difference above 150ms first triggers a review warning. Give reasons for anticipatory setup/reaction shots and actually watch them; do not automatically fail or ignore them.

Preserve recoverable briefs, sources, scripts, storyboards, designs/assets, raw audio/mix stems, timecodes, captions, media versions, reviews and authorization/platform receipts. Filenames distinguish episode/edit/audio/aspect-ratio versions; captions/covers/copy have independent hashes. Recheck [affected dependencies](quality-acceptance.md#handling-failures) after changes without reusing old acceptance.

<a id="按动作类别补充信息"></a>
### Add information by action class

Fill `shotbook.action_class` (deduplicated list) and `action_class_details` (organized by class key) only for classes actually used in this shot. Reuse existing object, anchor, trigger/key_states/trajectory and related fields. Do not require all five classes for every shot:
- localization_and_label: appearance_condition, follow_target, hold_duration.
- scale_transition: original_object, spatial_anchor, local_frame (local framing and coordinate basis), return_location; identify the same object's entry/return relationship.
- deformation: topology_states (corresponding same-topology key states), fixed_boundary, sliding_boundary, trajectory; design by mechanism without making every object bounce or changing science to fit tool limitations.
- propagation_and_change: cause, origin, direction, delay, end_state. Explanatory animation follows the same rule as live footage: if slowed for teaching, clearly disclose time scaling at first use rather than waiting until the end.
- observation: learning_task and duration; actual dwell depends on the understanding task.

`timing_basis.mode` separately states real_audio (actual audio ID/hash and semantic times) or relative_plan (relative stages only when no audio exists). A formal motion plan also records note explaining its semantic basis; this is not the same as speed_and_pause. Record path, speed/pauses and audiovisual events separately; trajectory alone cannot replace full action timing. The main reference's combined locating/label range 160–320ms and tokens' finer attention160–280, label180–320 are different granularities of the same D. Actual readability and semantics take priority; these are not hard physical durations.

Fix library ID/version/hash in `design.library_reference`. Style version remains design.style_version; do not assume they match. `design.new_asset_ids` lists only assets needing new creation this episode. Record actual reuse and changes for other assets rather than treating the entire asset list as new creation.

Read the responsibility references and actual configuration needed for the current stage through the [entry routing](../SKILL.md#read-responsibility-bodies-on-demand). `design.library_reference` records library id/version/manifest hash and adoption (adopted/reference-only), without conflating it with style version.

If adopting the thunder-mechanism recipe, also read the [conditional complete example](../assets/examples/thunder-brief.md), preserving its specific prohibited depictions, first-use slow-motion disclosure and unproduced state. This does not force other topics to explain thunder or revive canceled topics.

Resolve actual dependencies uniformly by asset ID. design.font_asset_id and design.render_asset_ids are shared representative-segment/full-film dependencies; per-shot asset_ids preserve each shot's scope; deliverable_asset_ids records lists by deliverable. The representative segment and actual dependencies of its captions and three-scale design enter rights checks and version binding. Unused later assets do not invalidate the current representative segment. All dependencies must have correct types and resolve; do not silently treat invalid fields as empty lists.
<a id="无音轨的-g1-纸面计划"></a>
### G1 paper plan without audio

`plan` / G1 may use `timing_basis.mode=relative_plan`, with specific `relative_phases` and `note` describing semantic order, observation tasks and actual times awaiting audio. Leave `start` and `end` null or absent. If planned semantic beats exist, leave `beats[].at` null and add a specific `phase`, intended trigger wording, attention object and action; an empty `beats` is also allowed temporarily. Do not mark intended but unsynthesized narration as a silent shot.

Before obtaining media, use `candidates=[]`, with `alternatives_note` stating objects to select and gaps. Remove example candidates not actually viewed. Obtain actual working audio before G2, convert relative stages to actual times, align semantic beats and add actual asset viewing. `relative_plan` cannot pass G2 or later.

The plan package's `assets` may register explicit asset needs still awaiting production/acquisition, referenced by stable IDs in shot `asset_ids`. `source` states planned acquisition method and use, `creator` truthfully remains undetermined, `file` is empty and `rights.status=pending`. These records do not establish asset possession. `candidates` contains only actually viewed candidates; keep the two distinct. Choose `kind` for the planned medium, and truthfully supply required `disclosure` for diagrams/simulations. Add actual original provenance, author, file and rights evidence only after acquisition. If asset needs themselves are still undetermined, deliver a brief first rather than inventing assets or scientific sources to satisfy structural checks.

<a id="解释设计与实际镜头的绑定"></a>
## Bind explanation design to actual shots

Reuse scope and shot references in `topic_alignment.coverage` to bind [explanation types and difficulty solutions](production-checkpoints.md#e02e07-explanation-design-before-refinement) to actual shots and semantic beats. Typed relationship paths use each `explanation_steps` step's `relation_type`; old scope-level `explanation_type` is read for compatibility, and historical causal records may use `causal_steps`. Do not fill two competing structures for the same scope. Each step retains necessary prerequisites, key relationship, derivation, boundaries, mappings from references to depicted objects, shot IDs, handoff and dynamic applicability. Causal steps additionally record before/change/after. `prerequisites` binds specific reused conclusions with `knowledge` and `source=audience_prior/step`, adding `step_id` for step sources. Audience prerequisites, presentation order and old-string migration follow the [prerequisite-source rules](production-checkpoints.md#2-make-explanatory-relationships-visible). If dynamics are unnecessary, explain why the static relationship is sufficient rather than using nonapplicability to hide a missing process.

Connect planned paths and actual evidence through the same step IDs. Actual expression checks record relationships seen/heard and the basis for derivation in the work, rather than copying design intent. Apply [E09–E10](quality-acceptance.md#autonomous-explanation-and-expression-review) to time/scale location and audiovisual semantic coordination during cuts, cutaways, magnification or teaching scans. Muted locating does not mean independently understanding all logic without sound; word-level timing also does not replace timely semantic correspondence.

Fields follow the [episode template](../assets/episode-template.json): `relation_type=causal/spatial/structure_function/comparison/propagation/quantitative/probability/evidence`. Add spatial references, structural connections, propagation paths, common scale/denominator, probability scope or evidence limits according to actual type.

Current qa.explanation_review and qa.expression_review may reference the same detailed observation evidence. Old `qa.comprehension.internal_review` compatibly binds current context and final audiovisual scope, separately preserving explanation/expression responsibilities, the four targets of answer/relationship/small change or distinction/boundary, and actual observation evidence for every step. Capabilities, reviewed files and ranges must be truthful; template text cannot manufacture viewing/listening facts. If the current gate has no actual work yet, keep it unreviewed and continue drafts within stage scope rather than signing a finished-film pass.
Preproduction paper-logic review uses qa.explanation_logic; old `qa.comprehension.logic_review` may be read for compatibility, explicitly using `basis=paper_logic` and binding G1 context. It does not reuse final audiovisual acceptance. Current per-step key_difficulty identifies actual key difficulties, and topic_alignment.expression_cards covers that set. Old `brief.difficult_step_ids` and four-item difficulty cards are read for compatibility rather than requiring a card for every setup step. Give specific reasons if there is genuinely no specialized difficulty. Compatibility reading of old `causal_steps` does not let old packages skip current G1 explanation design or G5 actual review.

For subject-motion definitions, long-still-frame limits, ROI screening, semantic-section records and G2/G3/G5 failure gates, use the [quality responsibility reference](quality-acceptance.md#subject-motion-and-long-static-holds). Per-shot static-direction approval cannot replace corresponding motion evidence.

The per-shot text-purpose inventory references the [text responsibility reference](visual-system.md#visible-text-purposes-and-production-excuses), and storyboard voice-handoff evidence references the [voice responsibility reference](voice-reference.md#whole-episode-narration-continuity). One shot's voice impression cannot establish whole-episode continuity.
