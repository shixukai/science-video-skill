# From finished audio to verifiable per-shot records

Record per-shot structure in `shots[].shotbook`. Gaps are fine during G1 planning; complete and bind actual media before delivery.

## Audio first without sacrificing the picture

Start from the continuous explanation in `narration.script_file`, split by comprehension task, and time shots from actual recorded narration (never guesses or fixed 4–6 s cuts). Each shot's `narration_exact_text` must concatenate in shot order to reconstruct the full script (ignoring whitespace; `""` for wordless observation shots with `silence_reason` and `beats: []`). Record `start`/`end`/`beats[].at` in finished-timeline seconds, `subject`, `action`, `framing`, `claim_support`, `motion_purpose`, and current `narration.audio_sha256` (realigning beats and re-listening after any audio edit).

## Design states before refining key states and layered motion

Establish state changes and anchors under [animation scene design](animation-scene-design.md#work-order-action-intent-before-detailed-art) before polishing frames, following the single commissioned route under [SKILL.md's Route Isolation gate](../SKILL.md#route-isolation-load-only-the-active-route) and [visual system](visual-system.md). Pair each cut's preceding `final_state` with the next `initial_state` (`transition_reason`, `object_ids`, `spatial_anchor`), bind `keyframe_review {file, sha256}`, and update `qa.shotbook` (`reviewed_sha256 = shotbook_sha256(data)`).

## Full-film frame extraction helper

When static inspection helps and `shotbook.start/end` match exported media, optionally run [build_visual_review.py](../scripts/build_visual_review.py):

    python -X utf8 scripts/build_visual_review.py <episode.json> --media renders/candidate.mp4 --output reviews/G5-v1

Outputs `index.html`, shot sample PNGs, `manifest.json` (`timeline_sha256`), and `gate-evidence.json` into a new episode-local folder (optional technical aid — never a per-shot manual quota or substitute for continuous playback). Bind only files actually used for review individually in `qa.gates.<stage>.evidence` under [stage evidence](quality-acceptance.md#stage-evidence-for-art-methods).

## Bind design and asset references

Fill `design.visual_intent` and `shots[].shotbook.realism` truthfully for realistic work, bind `design.board_reference/board_sha256`, register used assets with SHA-256 in `assets[]`, and reference them via `shots[].asset_ids`, `design.render_asset_ids`, `design.font_asset_id`, and `deliverable_asset_ids`. First-sample and render receipts follow [start lock and rendering entry](production-checkpoints.md#start-lock-and-actual-rendering-entry).

## Per-shot structure and directional-graphics records

Record actual-export checks in `shotbook.visual_logic` (`review_scope=final_export` only after viewing the final export):
- `orientation`: Boolean `applicable` (`status`, `reference`, `frame_mapping`, `structures`, `transforms`, `evidence`; or honest `reason` when `false`).
- `graphics`: register every exported arrow or leader (`id`, `kind=arrow|leader`, `asset_id`, `component_reference`, `license_evidence`, and `checks`: arrows check `tip`, `shaft_join`, `visibility`, `direction`, `endpoints`, `motion_extrema`; leaders check `visibility`, `endpoints`, `motion_extrema`). Use `[]` + `no_graphics_reason` when none exist.
- Per-shot provenance binds through `shotbook.origin` and `assets[].origin` under [per-shot provenance](science-and-rights.md#per-shot-provenance-evidence).

## Make asset selection verifiable

Inspect actual candidate intervals (never thumbnails alone) and record `candidates` (`asset_id`, `source_interval`, `viewing_note`, selection reason; `alternatives_note` if only one lawful candidate exists). Only static originals use `still/full`; panned photos never count as live footage.

## Optional working methods

Claim editable project delivery only after opening/verifying the real project. Assign clear per-reference roles for generated inputs and consult [external skills curation](video-skills-curation.md) only within the locked route.

## Motion cards, shot recipes and event review

For process shots, fill core motion-card details in `shotbook` (anchor, `initial_state`, `trigger`, `key_states`, `final_state`, trajectory, observation pauses, `viewer_takeaway`, physical conditions/simplifications). Semantic audio–visual offsets `> 150 ms` trigger review (anticipatory setups remain valid when observed and motivated). Re-check [affected dependencies](quality-acceptance.md#handling-failures) after edits and read domain guides on demand via [SKILL.md](../SKILL.md#read-responsibility-bodies-on-demand).

### Add information by action class

Fill `shotbook.action_class` and `action_class_details` only for classes used (`localization_and_label`, `scale_transition`, `deformation`, `propagation_and_change`, `observation`). Record `timing_basis.mode` (`real_audio` vs `relative_plan`) and `design.library_reference` / `design.new_asset_ids` accurately.

### G1 paper plan without audio

Before working audio exists, G1/plan may use `timing_basis.mode=relative_plan` (`relative_phases`, `note`, `start/end=null`, `beats[].at=null`, `candidates=[]` + `alternatives_note`, planned `assets[]` with `file=""` and `rights.status=pending`). Convert to real audio timings before G2; `relative_plan` never passes G2+.

## Bind explanation design to actual shots

Bind `topic_alignment.coverage[].explanation_steps` (`relation_type` across the 8 types in [episode-template.json](../assets/episode-template.json), plus `prerequisites` with `audience_prior` or prior `step` IDs) to shot IDs under [E02–E07](production-checkpoints.md#e02e07-explanation-design-before-refinement). Map G1 logic (`qa.explanation_logic`) and G5 independent reviews (`qa.explanation_review` / `qa.expression_review`) to the same step IDs, linking motion checks to [subject motion](quality-acceptance.md#subject-motion-and-long-static-holds), text checks to [text purposes](visual-system.md#visible-text-purposes-and-production-excuses), and voice continuity to [voice reference](voice-reference.md#whole-episode-narration-continuity).
