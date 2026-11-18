# Episode Production Brief

Status: actual G1–G7 stage; version, current task scope, pause/cancellation and reason:
Production class R/N/B; key difficulty and explanation type; actual owners (publication owner only at publication stages); authorized production/publication scope:
Delivery scope `delivery_scope=release_package/video_only` and request reference; requested cover ratios; whether platform actions are commissioned:
Complete the six [topic groups](../references/production-checkpoints.md#1-decide-the-one-thing-viewers-should-understand): main question and necessary subquestions, hierarchy and necessity (no fixed count); audience/starting knowledge; one-sentence answer and understanding target; relations/changes that must be visible; required/excluded scope; prohibited depictions and likely misconceptions:

## Topic card before production
Record `episode.brief.topic_selection` under [adult-audience topic selection](../references/topic-contract.md#topic-selection-for-adult-audiences). Reuse the existing audience starting point, original question/answer and viewing payoff; do not duplicate the form.
- What the audience knows; why to investigate further; relevance to an actual situation/phenomenon; new mechanism, condition, trade-off or discovery:
- Verified primary factual sources and applicable conditions; visualization of the key relation; what viewers can additionally explain or judge:
- Asset/rights plan, method, constraints and blocking gaps (lack of an existing asset alone does not establish infeasibility):
- Topic origin `editorial/user_requested` and original request; explicit rejection reasons (editorial taste cannot veto a user-requested foundational topic); editorial `selected/revise/rejected/pending`, reviewer/reason and current `selection_context_sha256`:
- Interest rationale defaults to an editorial hypothesis; claim observed audience interest only with actual evidence, never fabricated research/popularity:
- Cite authorized platform evidence in private ledgers under [data verification](../references/production-checkpoints.md#platform-topic-selection-and-data-review), recording updates/window/sample/denominator and gaps; identify verification/adoption scope for AI or trend suggestions:

## Appeal and package before the script
Apply [viral appeal and packaging](../references/viral-appeal-and-packaging.md) to complete new films; reuse the topic card fields above rather than a new form.
- Angles considered and the appeal drivers each has (broad entry plus real surprise, visible spectacle, extreme scale, personal stakes, social currency or timeliness); which driver is visible in the picture; strongest losing angle:
- Three to five title candidates and the selected title; cover concept with one large subject, a [realistic background](../references/visual-system.md#realistic-backgrounds-for-every-cover) specific to the topic, an upper-left 1-line topic-noun main title and a 2-line question subtitle; sources for every number or surprising claim:
- First two seconds ([hook lab](../references/viral-appeal-and-packaging.md#run-the-hook-lab-at-g1), recorded in `topic_alignment.opening.hook`): hook inventory of the film's strongest visible moments; at least three candidates across two or more patterns and why each loser lost; `host_relation` (`standalone` or `part_of_host`, plus `host_system` and `whole_to_part_bridge` when explaining a mechanism/part inside a larger host so 0–5 s establishes macro host-to-part orientation from the complete host or recognizable functional cabin/bay); selected first picture already moving at frame 0, first sound, first line with its payload clause and timed read-aloud; muted and phone-feed reading; what the viewer learns next about why it matters:
- Hook sample and test: 0–5 s sample file/version, `opening_hook.py` report and flags/repairs, cold two-second test result (muted and with sound), recheck; final-export report bound in `qa.opening_hook.final`:
- Payoff map through the body (where each new visible payoff or concrete re-hook lands), the strongest reveal, the shareable moment and the ending interaction, if any:
- Scroll-viewer check results with swipe-risk times, repairs and recheck (internal diagnostic only):

## Original topic and science
For engineering/industrial/advanced manufacturing, record [full-chain scope](../references/topic-contract.md#complete-chains-and-duration-for-engineering-and-manufacturing-topics), chapter order, each stage's input/principle/operation/output/handoff, key difficulties/quality verification and research gaps. Estimate duration from explanation needs, then update after actual narration/demonstration:
Use the [topic contract](../references/topic-contract.md) for original topic, question type, required scope, first-picture/narration/ending mapping and each local section's scope. Copy the topic-anchor template and bind source/hash.
Use [science and assets](../references/science-and-rights.md) for claims, evidence, self-produced visuals and verified authorized user capture/rights, actual selected ranges and gaps:

## Original visual provenance (blank, not approval)
Under the [original-visual contract](../references/science-and-rights.md#original-visual-provenance-contract), record `origin_contract.mode=self_created_visuals`, each shot's planned method, pre-production design, actual entrypoint version/hash, and actual asset inputs/outputs, extracted frames and review evidence. User-capture facts and current authorization must be verifiable; missing evidence stays missing. Third-party public, CC/Commons and paper imagery remain research references, not filler or finished backgrounds. Do not rewrite historical provenance or acceptance.

## Finished style and main production project
Record the [production route](../references/tool-routing.md#lock-the-primary-tool-by-final-film-style). Use `design.production_route=google_flow` (with `design.output.fps=24` CFR unless explicitly converted) for commissioned Google Flow work. Map each necessary causal step to shots, spoken explanation and observation time in both languages. Derive shot count and duration from that plan.
- Current style, commissioned tool, and project/version. Record the engine rationale for controlled 3D and the scope of any mixed styles.
- Asset provenance, actual generation and assembly evidence. For Google Flow, record the disk-backed prompt ledger, `1080p Upscaled` staged clip probes, Flow video/voiceover/ambience/caption sources and exports (zero local media resources), and native `48 kHz` audio disposition (`keep foley` vs `mute`).
- For a complete Google Flow film, identify the paired `episode.zh.json` and `episode.en.json` records budgeted across `max(span_zh, span_en)`, common picture sources, clean text-free cover base art with separate `zh`/`en` typography, and each edition's own voice, captions, export, `google_flow_audit.py` report and independent review evidence.

## Global entry and early sample
- Actual global Skill path/version/rule lock; differences from the current global installation, migration record and required renewed actual reviews (no Skill copy):
- Current voice sample, problem times/repair and actual listening scope; opening design follows below:
- Target/actual frame rate of a playable continuous sample; subject detail/motion observations; known failure repair/recheck:

## Fixed references
- Skill commit/version:
- Series configuration ID/version and file SHA-256:
- Visual token ID/version/SHA-256; actual deviations and reasons:
- Current [annotation standard](../references/annotation-style.md) and separate parameter revision; purpose of labels/locators/direction/ranges and existing style-approval scope. Cite actual design/viewing in art records; no prefilled pass:
- Private project design-board ID/version/hash; reviewer, approved scope and date remain private:
- Art-reference index version and actually viewed intervals for this film; not asset-use authorization:
- Available asset/component index version and used IDs/versions/hashes/rights; missing items:
- Caption layout baseline, canvas and actual positions. For an existing layout migration/revision, retain revision ID, old/new baselines, applied state, cumulative offset, resolution-rounding and extra local avoidance:
- Current voice setup, acceptance scope and actual audio hash. Default across all routes: Microsoft Edge cloud neural TTS (`edge-tts`, `zh-CN-YunxiNeural`, `rate="+4%"` via `scripts/synthesize_edge_tts.py`, preserving continuous whole-script synthesis, room-tone observation holds, and `cloud_evidence` hashes; record designated location only if optional local Qwen is explicitly requested).

## Opening context and viewing reason
Apply [opening design](../references/viewer-retention-design.md#establish-context-and-a-reason-to-watch-before-explaining) to full new films; chapter/local repairs follow actual scope. Reuse `opening` and action cards, without another approval.
- First-picture subject/situation and purpose; corresponding main picture and narration:
- Real point of interest, scientific basis and producible visuals; original question/viewing payoff and first useful information, citing `curiosity_gap / viewer_payoff`:
- Write opening's last sentence and body's first sentence together; why the first observation/explanation is necessary; preceding object/state, next observation target and recognition anchor; explanation of scale/time/object changes; selected picture/sound handoff and actual tool feasibility. Cite `opening.visual_handoff` and action cards without another table; actual narration and `shot_ids`, no fabricated timestamps before audio:
- Normal-speed viewing/listening range from first frame through the first body observation, first break/repair and recheck, citing existing G2 QA:

## Complete rough cut and shotbook
Under [production order](../references/production-checkpoints.md), write the short answer, prerequisites, each new concept's purpose/visible counterpart and first break in the initial editorial retelling; record logic, expression-plan and actual-work review.
Use the [shotbook](../references/shotbook.md) for shot IDs, time ranges/semantic beats, subject/state change, adjacent handoffs, spatial anchors/viewpoint/scale bridges, actual candidate viewing/source in/out points and key frames:
Expression cards: difficulty, prerequisites, concrete hold/change/compare/enlarge actions, inferable conclusion, misconception and limits. Compare low-cost alternatives for uncertain key approaches. Action cards follow the actual type: anchors, initial state, necessary trigger/process, final state, trajectory/speed/pauses, comprehension purpose, scientific limits and version. Key states alone do not establish continuous animation.
Representative sequence: covered shots/question, actual sound-picture file/hash, continuous observations, return/recheck and local approval version/range/dimension:
Text inventory: use the [deletion test](../references/visual-system.md#audience-picture-and-delivery-records) for each item/text/range, current viewer task, meaning lost if removed, keep/remove/revise decision and companion placement. Credits/disclosures separately record obligation basis, required presentation location and actual implementation:

Use [retention design](../references/viewer-retention-design.md) through `payoff_steps / handoff` to cite each section's new understanding, next observation, key observation window and result recognized again at the ending:

## Cover production only when commissioned
Apply the [finished-cover standard](../references/visual-system.md#finished-cover-standards-for-engineering-and-manufacturing-topics). This is design information; actual review binds through `qa.covers`, without prefilled approval.
- Current film version, main question and actual coverage; short topic/question on the cover and its fulfillment in the body:
- Subject identity, structural/material basis, defining features, permitted cutaway/illustration and prohibited depictions; series reference and actual inspection scope:
- Requested ratios; title region, primary/secondary objects and negative space per version; text-free image provenance and edition-language font/type layer:
- Finished files, phone thumbnails, side-by-side comparisons and editable sources; actual observations, defects and revised versions (unviewed stays unreviewed):

## Actual acceptance and feedback
Use the [episode art/quality record](art-direction-template.md) when useful, citing representative samples, same-shot comparisons, the full-film thumbnail strip and encoded comparisons in the existing records below; do not create duplicate approval states.

For each [quality requirement](../references/quality-acceptance.md), record artifact/version, evidence file/time, result and gaps. This template does not duplicate the responsibility body:
- Science/rights:
- Topic/explanation/expression: actual opening-to-body, section progression and ending payoff; first break and repair, citing existing G1/G2/G3/G5 records:
- Static art/full canvas/text/orientation/structure and gap against L3 reference:
- Continuous action/full-film integration and their respective L3 evidence:
- Complete voice/mix/captions and actual listening coverage:
- Technical checks/current delivered-media hash:
- Current account/full copy/actual platform UI and device scope:
- Withdrawn older conclusions, concrete gap, repair and recheck:
- Actual application of this feedback to later applicable films (unproduced/unperceived stays pending):

## Delivery and publication
Under [delivery scope](../references/production-checkpoints.md#delivery-package-and-publication-receipts), supply the requested video/covers/copy, source/production statement, acceptance and pending work. Local `delivery` ends at G5; `publish_ready` additionally checks G6:
Record the recipient, destination, version, authorization, pre-submission settings and actual submission action or user handoff. The user checks all publication outcomes. Use existing local records or user evidence for duplicate checks. Record an outcome, work ID or URL only when the user supplies the evidence and asks for it to be recorded. Follow the [publication handoff](../references/production-checkpoints.md#manual-clicks-and-publication-review-handoff).

## Standards execution and operational records
Cite applicable standards, actual reviews and command receipts through `episode.qa`; cite hours, costs, inventory, publication and retrospectives through the project ledger. Missing platform data remains unknown.

## Explanation-design references

Reference the existing topic anchor, `required_scope`, `brief.audience_start`, `brief.understanding_targets`, `topic_alignment.coverage[].explanation_steps` and `topic_alignment.expression_cards`; reviews cite `qa.explanation_logic / expression_plan / explanation_review / expression_review`. From G2, update timing against actual audio.
