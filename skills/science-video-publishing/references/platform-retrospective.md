# Platform Data Retrospective & Next-Production Feedback

Load this file ONLY when the user commissions platform analytics review or supplies backend exports. Keep all real account metrics, work IDs, screenshots, and user comments in private project ledgers — never inside public Skills.

## 1. Export first, then reconcile coverage

- Start from authorized work-level exports before reading individual detail pages. Inspect workbook sheets, headers, row counts, and the last actually populated date (never sum truncated hourly series as lifetime views or mix account-day and work-lifetime figures).
- Preserve exact native field names, denominators, statistical windows, update timestamps, and `field_states` (`observed`, `missing`, `not_updated`, `unknown`). Never interpret an unconfirmed `0` or early retention drop as algorithmic throttling ([Douyin algorithm disclosure](https://trust.douyin.com/algorithm/)).
- Keep the exact observed time grid: never interpolate missing retention seconds, equate final-sample retention to completion rate, or divide raw homepage visit events into unique-person conversion rates.

## 2. Diagnose entry, promise, and payoff separately

| Observed signal | Inspect next on the actual published video | Do NOT infer |
| --- | --- | --- |
| High search traffic share | Compare actual search queries to title, cover, first line, and answer; keep separate from feed cohorts | Aggregate retention equals search retention; stuff unrelated trending keywords |
| Steep drop in opening interval | Inspect frame-0 recognition/motion, audio onset, first visible event, and rerun `opening_hook.py` on the published file | Low rate proves a specific defect without watching |
| Strong first 2 s, sharp drop right after | Inspect opening → ~8 s viewing promise → first body payoff handoff | Louder frame-0 fixes a broken bridge |
| Good early hold, weak average/late retention | Inspect `first_verified_payoff_s` (actual published video, never auto-chapters), dead stretches, and cuts | Hook alone fixes body; speeding up narration helps understanding |
| Big relative platform gain | Display absolute value, baseline definition, and window beside the percentage | Relative gain means absolute benchmark achieved |
| Weak click-through on search / profile / collection surfaces while retention is normal | Check the cover at thumbnail size (object + question readable?) and whether the title's search words match the actual queries | A retention fix will raise clicks; stuffing trending words helps |
| Good completion but few likes, saves, shares, or comments | Check whether an aha frame exists and holds at phone scale, whether the insight passes a one-sentence retell, and whether the pinned comment offers a save tip or extension question | The topic was boring; adding a CTA to the video tail will help |
| Replay or rewatch spike at one timestamp | Identify the shot there (usually the aha frame or a satisfying process) and reuse that visual type in the next brief | A replay spike means confusion without watching the shot |

## 2b. Compare creative patterns across episodes

Tag every release with its creative choices (recorded in the release handoff): `hook.pattern`, `narrative_frame`, dominant emotional payoff, timing tie-in, and title search words. Across several episodes, compare matched windows on the same metric for episodes that differ mainly in one tag, so the account learns which hook types and emotions work for its audience. Treat fewer than three comparable episodes per tag as a hypothesis, not a finding, and never credit a pattern for a gain that topic, timing, or traffic source explains better.

## 3. Reconcile platform advice & comments against media evidence

- Treat platform AI suggestions and creation-assistant labels as untrusted external hypotheses: log the exact displayed label alongside supporting metrics, conflicting metrics, and missing definitions before adopting or deferring.
- Deduplicate comments cleanly (`scripts/platform_evidence.py`): keep displayed comment totals, unique comment IDs, root threads, replies, and distinct non-author commenters separate.
- Track factual/wording corrections separately across publication text, burned-in captions, and audible narration on the exact published version — an edited description never verifies the video's audio or burned-in subtitles.

## 4. Output a compact `next_production_brief`

End every retrospective with ONE concrete next-episode handoff (feeding back into `science-video-topic-selection` and `science-video-production`), changing **one main creative variable per round**:
- **Observed pattern & competing explanations:**
- **Single creative change for next episode:**
- **Owner (`topic` | `script/hook` | `visual/pacing` | `audio/captions`) & continuous review segment:**
- **Original-name metric & matched comparison window to evaluate later:**
- **What remains unmeasured / private limits:**
