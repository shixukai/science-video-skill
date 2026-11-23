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
