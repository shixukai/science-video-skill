---
name: science-video-topic-selection
description: Research, compare, and select science-video topics, titles, cover concepts, and 0-5 s hook candidates for a general adult audience before scripting. Use for topic pitches, shortlists, originality/overlap checks, angle framing, and Hook Lab planning. Do not use for writing full scripts, synthesizing voice, generating footage, or publishing.
---

# Science Video Topic Selection

Return a research-backed editorial decision and package handoff — not a brainstorming list of clickbait titles. Familiar topics are welcome if this episode makes visible or resolves something the closest existing work leaves unexplained. Novelty and audience appeal are separate; neither substitutes for the other.

**If the user has already commissioned a specific topic or question:** preserve it. Apply only the science, feasibility, angle, and Hook Lab checks below — do NOT reject a user-commissioned topic for channel lane or novelty.

## 1. Anchor to channel positioning (unassigned topics)

Follow [topic-positioning.json](config/topic-positioning.json):
- **Primary lane (~80%) — everyday objects & visible mechanisms:** everyday items, packaging, household/daily devices, kitchen/food physics, common materials, and daily mechanical/safety structures immediately recognizable at frame 0 with zero preamble.
- **Secondary lane (~20%) — observable physical or scale paradoxes:** recognizable natural/physical phenomena anchored to a stark visible contradiction or physical limit (mass, height, pressure, force, phase, scale).
- **Deprioritized for default editorial picks** (use only when user-commissioned or tied directly to an everyday mechanism transfer): standalone animal trivia and abstract invisible-instrument/coding/clinical tutorials that cannot show a concrete physical contradiction in the first two seconds.

Category ratios are editorial guidance, not quotas. Frame questions **contradiction-first** ("it looks/behaves like A, yet B happens — why?") rather than flat encyclopedia prompts ("how does X work?") or opening definitions/formulas, choose a concrete **narrative/problem-solving vehicle** (`everyday_problem_solving`, primary-source-`verified_historical_incident`, `what_if_counterfactual`, or tight `direct_mechanism_discovery`) so the episode plays like guided discovery rather than a lecture, and keep standalone feed episodes scoped tightly to **one core visible contradiction and primary mechanism** (let explanation clarity set runtime; no duration floor or ceiling).

### Audience pull check (plain language, no scorecards)

Novelty and accuracy do not make people watch. Before selecting, answer each in one honest sentence; a topic that cannot answer most of them needs a sharper angle, not a louder title:
- **Relevance radius:** Does an ordinary adult touch, see, or hear this object or phenomenon this week? The closer to daily hands, kitchens, commutes, and weather, the stronger the pull.
- **Timing window:** Is there a real seasonal or calendar moment (winter pipes freezing, summer AC dripping, rainy-season smell, holiday travel, exam season) or a verified current event that makes this question feel live right now? Use timing only when the link is real and verified; it never overrides primary evidence or the editorial lane, and never chase rumors, disasters, or tragedies for traffic.
- **Dominant emotional payoff:** Which single emotion can the film honestly deliver: `awe` (scale or limit reveal), `surprise` (expectation reversal proven by a visible test), `satisfaction` (a precise mechanism clicking into place), or `relief_or_usefulness` (a daily snag finally makes sense)? Never manufacture fear or danger.
- **Aha frame:** Which one visible image makes the hidden mechanism readable at a single glance? If you cannot name it, the topic is not yet visual enough.
- **Retell line:** What one-sentence insight would a viewer pass on to a friend (`原来加油枪是靠一股被油面封住的小气流自己跳停的`)? If it needs jargon or three clauses, the angle is too complex for a feed episode.
- **Search words:** Which everyday words do people actually type for this (`加油枪 跳枪`, `不粘锅 涂层`)? These feed the title, description, and tags.

## 2. Check closest existing works & primary science

1. **Form genuinely rival questions** (re-titling the same question and demonstration is not a rival).
2. **Search beyond exact phrasing:** check everyday phrasings, mechanism names, key demonstrations, and prior series episodes by what they actually answered and showed.
3. **Inspect the closest competing works substantively** (link/ID, timestamp/passage checked, what they actually asked, answered, and showed). A title or unread search hit never proves omission; mark uninspected comparisons pending.
4. **Verify primary scientific evidence:** open original papers, engineering standards, or authoritative technical explanations; record the exact claim supported, operating conditions/units, and limits. A paper supports science only — never third-party footage rights.
5. **Confirm visual-demonstration fit (picture replaces prose):** specify what visible state change, animated mechanism, cutaway, controlled side-by-side experiment, slow-motion failure, force/flow path, or scale contrast proves the answer visually within the planned self-created route (`google_flow` cloud realism, `controlled_3d`, or `local_realistic`) — never rely on spoken monologue or text overlays to explain an abstract concept that can be demonstrated visually. Do not promise an unproducible defining shot or graphic/body-horror visuals (zero peeled/carved human skin).

## 3. Design the package & 0–5 s Hook Lab (before scripting)

For the winning or commissioned topic, deliver the pre-script package:
- **3–5 sourced titles** (in each commissioned language; Chinese `<= 30` codepoints) in direct, single-breath everyday speech — keep familiar verbs viewers actually say (e.g., `加油枪怎么知道油加满了而跳枪？`) without stacked pre-noun modifiers, clickbait percentages (`90%/99%的人都不知道/被误导`), invented danger, confrontational phrasing (`凭什么`/`凭啥`/`偏要`), or repetitive "no-power/no-sensor" cliché templates (`里面既没插电也没装传感器`, `既没插电也没装电机/芯片/电路`, `没插电也没装传感器`).
- **Title–cover division of labor:** cover and title promise the **same question** but do different jobs. The cover *shows* the visible contradiction or aha state, legible at phone-thumbnail size. The title *names* the everyday object in the words people search, placed early in the title. Never copy the cover text verbatim into the title.
- **Cover concept:** one large recognizable subject in a **realistic topic-matched setting** (never a bare studio wall or stylized backdrop) + upper-left 1-line topic noun (3–6 CJK chars) + 2-line question answered by the film.
- **Narrative frame (`narrative_frame`):** lock how the body turns knowledge into concrete story or problem-solving instead of a lecture — **everyday user/engineering problem**, **verified historical incident entered at the point of conflict** (never slow chronological preamble or fabricated archival proof), or **"what-if" counterfactual boundary test** (`如果XX会怎样`) — plus planned **breathing-point micro-climaxes** (visual reveal, mini controlled experiment, or curiosity-turning micro-prediction) every ~15–25 s (never exceeding 30 s).
- **0–5 s Hook Lab:**
  - Identify 3–5 strongest honest visible moments from the film; compare **at least 3 hook candidates across >= 2 patterns** covering honest high-retention entry doors — **counter-intuitive / expectancy violation** (`strange_phenomenon`, `extreme_contrast`), **everyday relatable pain-point / friction** (`everyday_pain_point` — real physical annoyance without scolding or fake medical claims), **overlooked-detail suspense** (`overlooked_detail` — a tiny ignored physical feature silently deciding the outcome), or visible consequence/process (`result_first`, `stakes_in_action`, `failure_or_breakage`, `question_with_evidence`, `satisfying_process`, `extreme_scale`) — and state why each loser lost. Never open with a textbook definition, formula, or lecture preamble.
  - Classify `host_relation`: `standalone` or `part_of_host` (when inside a larger machine/body/appliance, specify `host_system` + `whole_to_part_bridge` showing recognizable host/working bay → real mounting site within 0–5 s).
  - Lock **Frame 0** (subject already moving, readable inside phone-feed width), **first sound**, **first spoken line** (warm conversational tone using visual-verbal counterpoint — adding why/tension rather than narrating visible pixels — priming shared everyday intuition + sensory touchpoint against a visible contradiction, payload front-loaded naturally within `<= 20` spoken units / `<= 3.5 s`, orienting newcomers without relying on the title/cover; **hard ban** on clickbait percentages, combative `你以为……其实……`, `"里面既没插电也没装传感器"`, and any `"既没插电也没装传感器/电机/芯片/电路"` cliché), and the **~8 s concrete non-spoiling viewing promise** (kept in one continuous opening paragraph and flowing straight into the first visible action/test at 8–15 s with zero static structure inventory).
- **Post-publish engagement seed (for `science-video-publishing`, NOT the video tail):** draft 1 natural extension question (`你平时有没有遇到过……？`) or same-collection next-episode teaser (`下一条拆解……`) to place in the **pinned comment / post copy**, keeping the video itself clean (`<= 3.5 s` after the final mechanism answer).

## 4. Decide and hand off to production

Use plain-language decisions without numerical scorecards:
- **Select:** concrete audience reason to care + clear difference vs closest work + verified primary evidence + producible visible payoff; explain why it beats the strongest rival.
- **Revise / pending:** sharper angle needed, closest comparison unread, or science/feasibility unresolved.
- **Reject:** closest work already delivers the same question, answer, and visible evidence, or no concrete payoff (never reject an explicit user-commissioned topic — improve treatment and flag factual/feasibility gaps instead).

Deliver a compact **[Topic Decision Card](assets/topic-decision-template.md)** ready to hand straight into `science-video-production` (`topic-anchor.json` / `episode.json` G1). Selection does not authorize synthesis, rendering, or publishing.
