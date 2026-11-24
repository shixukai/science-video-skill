# Preserve the original topic, question type and delivery scope during local revisions

Recover the original topic, intent, and required answer scope from the original commission at startup, resume, and revision. Local feedback locates repairs only; never silently turn a manufacturing process into a usage overview or narrow/replace a user-commissioned topic without an explicit request.

## Preserve the original anchor

Copy `assets/topic-anchor-template.json` to `topic-anchor.json` (`version`, `title`, `question`, `intent`, `required_scope: [{id, answer_requirement}]`). Bind `topic.origin_reference`, `topic.anchor_sha256 = canonical_sha256(anchor)`, and `topic.current / current_sha256`. On an explicit user topic change, record `change_approval` (`status=explicit_user_request`, request ref, `from_sha256`, `to_sha256`) while keeping the original anchor intact.

## Complete chains and duration for engineering and manufacturing topics

- **No mandatory minimum or maximum duration or word count:** Tell the story clearly; let explanation clarity, visible proof, and natural observation time determine runtime. Never pad narration to hit a length floor, and never skip steps or speed up speech to squeeze a fixed duration.
- **Scope tightness for standalone everyday feed episodes:** Anchor unassigned standalone feed videos to **one concrete physical/structural contradiction and its primary causal mechanism**, cutting tangents and side-mechanisms. Reserve multi-chapter chains for explicitly commissioned full-chain engineering/manufacturing topics.
- **Full-chain engineering/manufacturing (when commissioned):** Trace actual input → material/feedstock → forming/machining → assembly → inspection/QC → operating output & boundaries (linking each stage's output to the next stage's purpose, real bottlenecks, and defects). Chain consecutive shots via `Extend`/`Frames` whenever a beat needs more time than one generated clip.

## Separate episodes, chapters and local samples

Set `scope.kind` to `episode`, `chapter`, or `local_sample`. Local/chapter deliverables bind `parent_episode_id`, `chapter_id`, `purpose`, `delivery_context`, `placement=chapter_only`, and `publication_ready=false` (never masquerading as a publishable episode).

For narrow sample repairs (`scope.kind=local_sample`, `qa.visual_frames.animation.next_action=repair_sample`), `opening`/`ending` inherit only original intent, covered `scope_ids`, and real boundary `shot_ids` (no fabricated episode titles or closing answers); `omitted_scope_ids` lists the exact complement of uncovered required scope. `delivery` still applies only to complete episodes.

## Topic selection for adult audiences

Pre-script editorial discovery, channel positioning (~80% everyday objects & visible physical mechanisms, ~20% observable physical/scale paradoxes), closest-comparison novelty checks, and Hook Lab selection live in the standalone **[Science Video Topic Selection Skill](../skills/science-video-topic-selection/SKILL.src.md)** (`science-video-topic-selection`).

Map its Topic Decision Card into `brief.topic_selection` (no duplicate form):
- `audience_category` (default `ordinary_adults`), `conflict_or_question`, `adult_relevance`, `knowledge_increment`, primary `source_ids`, `causal_visualization`, `feasibility` (`materials_and_rights_plan`, `method`, `constraints`, `blocking_gaps`), `interest_basis` (`editorial_hypothesis` by default; `observed_audience_evidence` only with real evidence), `disqualifiers` (`common_knowledge_only`, `definition_only`, `title_only_change`, `asset_led`, `unsupported_hook`, `no_explanatory_payoff`, `unvisualizable`, `unfeasible`), and `review` (`status=selected|revise|rejected|pending`, `reviewer`, `reason`, `selection_context_sha256(data)`).
- **User-commissioned topics (`selection_origin=user_requested`):** Bind `user_request_reference`, `user_request_evidence {file, sha256}`, and `scope_reason`. Preserve the user's question regardless of editorial lane (`common_knowledge_only`/`definition_only`/`title_only_change` stay editorial risks rather than vetoes; real science/rights/feasibility gaps still require resolution).
- For editorial picks, record the strongest rival in `alternatives` (`question`, `not_selected_reason`). Platform trends supplement judgment only — never replace primary sources or explanatory payoff.

## Opening and audience scope

Open on a recognizable object in its most interesting honest state, then narrow to the core question and hand off to the first body observation (for feed films, land object + tension within [the first two seconds](viral-appeal-and-packaging.md#win-the-first-two-seconds) under [opening direction](viewer-retention-design.md)). Record `curiosity_gap`, `viewer_payoff`, `voiceover`, `spoken_question`, `answer_route`, `shot_ids`, and `payoff_steps` in `topic_alignment.opening`.

Examples of question-to-evidence openings (follow [SKILL.md's Route Isolation gate](../SKILL.md#route-isolation-load-only-the-active-route) and [science and rights](science-and-rights.md)):

| Topic & warm conversational opening (non-spoiling curiosity gap) | Curiosity gap & payoff | Evidence & boundaries |
| --- | --- | --- |
| Ice floating (frame 0: ice cube dropping into water & bobbing up): “冰明明已经冻成硬块了，放进水里却还能稳稳浮在上面。按理说东西越冷越紧实，同样重的水冻成冰以后，怎么反而胀大了一圈？” | Open ice lattice holds equal mass in larger volume (earned in body, not spoiled at 6 s). | Compare equal-mass liquid vs ordinary ice molecular packing ([USGS](https://www.usgs.gov/water-science-school/science/water-density/)). Molecules don't expand; limit to ordinary water ice at normal pressure. |
| Blue sky (frame 0: sunlit street tilting up to open blue sky): “阳光本身看起来近乎白色，可晴朗的天空为什么会是一整片蓝？一束白光穿过空气时，蓝光究竟在半路上拐了什么弯？” | White source vs blue sky from scattered light entering the eye. | Show sunlight → air → scattering → eye ([NASA](https://spaceplace.nasa.gov/blue-sky/en/)). Distinguish sky scattering from sunset path length. |
| Delayed thunder (frame 0: lightning flash lighting clouds): “同一道闪电亮起来之后，雷声总要晚几秒才传到耳边。明明是同一次放电，画面和声音怎么会被拉开这么远？” | Seeing/hearing delay comes from propagation speed, not delayed thunder creation (earned in body, not spoiled in the hook). | Show heated air at discharge + light vs sound travel ([NOAA](https://www.nesdis.noaa.gov/about/k-12-education/severe-weather/what-causes-lightning-and-thunder)). Don't imply lightning waits to trigger thunder. |

Keep one main question per episode; finish the main answer before optional extensions.

## Recheck the original question in four places without keyword box-ticking

Bind `topic_alignment` to current `topic_sha256` and check semantics (not keywords) in four places:
1. `opening`: first screen, `voiceover`, `spoken_question` (question or accurate conditional topic statement), `answer_route`, `intent`, `scope_ids`, `shot_ids`.
2. `coverage`: shots & answering evidence for every required scope item (local repairs cannot hijack the main backbone).
3. `ending`: real closing answer fulfilling the opening promise without switching to an easier question.
4. `omitted_scope_ids`: honest list of uncovered scope on local samples.

At export, record real observations in `qa.topic_alignment` (`opening_title`, `opening_voiceover` with `review_scope=final_export`, `heard_question`, `heard_answer_route`, `coverage`, `ending`, honest `reviewer_role`, and `topic_review_sha256(data)`). Script-only or ASR-only notes remain pending; topic drift must be repaired before art polish.

## Continuously check the cover's question against the actual opening

Verify natural semantic equivalence across original topic → cover question → spoken opening → first body observation (objects, conditions, and relation must match; no reading cover verbatim required).

- At G1/plan, fill `cover_question`, `question_relation=specific_equivalent` (not `generic_only`/`different_question`/`pending`), `question_comparison`, and `visual_handoff` in `topic_alignment.opening`.
- At G5/delivery, bind `qa.topic_alignment.opening_alignment {status, evidence: {file, sha256}}` using [opening-review-template.json](../assets/opening-review-template.json) and `opening_context_sha256(data)`, binding exact video/cover hashes (`video_only` skips covers), actual `viewed_range_s` (from frame 0 through first body payoff), `question_range_s` (`<=` route time), `visual_handoff` (`continuous_subject` or `motivated_transition`), and item-level `sources` (`editor`, `independent`, or genuine `user` feedback covering `cover_question`, `spoken_question`, `answer_route`, and `visual_handoff`). Refreshing hashes without real re-viewing never passes.

## E01: Explanation promise and question scope

State the concrete question and post-viewing capability separately from the topic noun; bind every promise to its answer section. If scope narrows, update title, opening, and ending together rather than silently dropping hard promises.
