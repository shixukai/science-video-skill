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

Category ratios are editorial guidance, not quotas. Frame questions **contradiction-first** ("it looks/behaves like A, yet B happens — why?") rather than flat encyclopedia prompts ("how does X work?"), and keep standalone feed episodes scoped tightly to **one core visible contradiction and primary mechanism** (let explanation clarity set runtime; no duration floor or ceiling).

## 2. Check closest existing works & primary science

1. **Form genuinely rival questions** (re-titling the same question and demonstration is not a rival).
2. **Search beyond exact phrasing:** check everyday phrasings, mechanism names, key demonstrations, and prior series episodes by what they actually answered and showed.
3. **Inspect the closest competing works substantively** (link/ID, timestamp/passage checked, what they actually asked, answered, and showed). A title or unread search hit never proves omission; mark uninspected comparisons pending.
4. **Verify primary scientific evidence:** open original papers, engineering standards, or authoritative technical explanations; record the exact claim supported, operating conditions/units, and limits. A paper supports science only — never third-party footage rights.
5. **Confirm visual-demonstration fit:** specify what visible state change, cutaway, slow-motion failure, force/flow path, or scale contrast proves the answer within the planned self-created route (`google_flow` cloud realism, `controlled_3d`, or `local_realistic`). Do not promise an unproducible defining shot or graphic/body-horror visuals (zero peeled/carved human skin).

## 3. Design the package & 0–5 s Hook Lab (before scripting)

For the winning or commissioned topic, deliver the pre-script package:
- **3–5 sourced titles** (in each commissioned language; Chinese `<= 30` codepoints) in direct, single-breath everyday speech — keep familiar verbs viewers actually say (e.g., `加油枪怎么知道油加满了而跳枪？`) without stacked pre-noun modifiers, clickbait, invented danger, or confrontational phrasing (`凭什么`/`凭啥`/`偏要`).
- **Cover concept:** one large recognizable subject in a **realistic topic-matched setting** (never a bare studio wall or stylized backdrop) + upper-left 1-line topic noun (3–6 CJK chars) + 2-line question answered by the film.
- **0–5 s Hook Lab:**
  - Identify 3–5 strongest honest visible moments from the film; compare **at least 3 hook candidates across >= 2 patterns** (e.g., striking visible consequence, physical scale/expectation contradiction, everyday object anomaly, process-in-motion reveal) and state why each loser lost.
  - Classify `host_relation`: `standalone` or `part_of_host` (when inside a larger machine/body/appliance, specify `host_system` + `whole_to_part_bridge` showing recognizable host/working bay → real mounting site within 0–5 s).
  - Lock **Frame 0** (subject already moving, readable inside phone-feed width), **first sound**, **first spoken line** (warm conversational tone, payload front-loaded naturally within `<= 20` spoken units / `<= 3.5 s`, orienting newcomers without relying on the title/cover), and the **~8 s concrete viewing promise**.

## 4. Decide and hand off to production

Use plain-language decisions without numerical scorecards:
- **Select:** concrete audience reason to care + clear difference vs closest work + verified primary evidence + producible visible payoff; explain why it beats the strongest rival.
- **Revise / pending:** sharper angle needed, closest comparison unread, or science/feasibility unresolved.
- **Reject:** closest work already delivers the same question, answer, and visible evidence, or no concrete payoff (never reject an explicit user-commissioned topic — improve treatment and flag factual/feasibility gaps instead).

Deliver a compact **[Topic Decision Card](assets/topic-decision-template.md)** ready to hand straight into `science-video-production` (`topic-anchor.json` / `episode.json` G1). Selection does not authorize synthesis, rendering, or publishing.
