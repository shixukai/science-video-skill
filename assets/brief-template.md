# Episode Production Brief

> Compact working sheet. Fill only fields applicable to this commission; keep canonical schema/hashes in `episode.json` without duplicating prose.

## 1. Commission & Route
- **Episode / version / stage**:
- **Class (`R/N/B`) & delivery scope**: `release_package` | `video_only` | requested covers (`3:4`, `4:3`, `1:1`) | platform actions (`yes/no`)
- **Production route**: `google_flow` (`24 fps` CFR, paired `zh`/`en`) | `controlled_3d` (Blender/Colab or `vork`) | `local_realistic`
- **Voice setup**: Default Mandarin = local IndexTTS-2.5 clone (`scripts/synthesize_indextts2.py` + `#5` polish `mandarin-clone-polish-v1`, zero echo); English/fallback = `edge-tts` (`en-US-AndrewMultilingualNeural` / `zh-CN-YunxiNeural`, `+4%`). Warm conversational tone; no harsh imperatives or sarcastic openings.
- **Owners (`brief.roles`)**: producer / science / director / art / audio / independent reviewer / publisher (if releasing)

## 2. Topic, Audience & Science (G1)
- **Original topic & origin**: `user_requested` | `editorial`
- **Three-sentence anchor**: (1) What viewers already encounter → (2) What deserves a question → (3) What they can explain/judge afterward
- **One-sentence answer & required scope (`R1..Rn`)**:
- **Out-of-scope & prohibited depictions / misconceptions**:
- **Primary factual sources (`S1..Sn`) & claim boundaries**:
- **Visual provenance (`self_created_visuals`)**: planned self-produced visuals; verified user capture only if `real_footage` is used; zero third-party filler.

## 3. Appeal, Opening Hook & Retention Plan
- **Winning angle vs strongest losing angle**:
- **Title candidates (3–5) & selected title**:
- **Cover concept**: 1 large recognizable subject + topic-specific [realistic background](../references/visual-system.md#realistic-backgrounds-for-every-cover) + upper-left 1-line topic title & 2-line question (composed via `scripts/compose_cover.py`).
- **Hook lab (0–5 s, `topic_alignment.opening.hook`)**:
  - `host_relation`: `standalone` | `part_of_host` (`host_system` + `whole_to_part_bridge` if inside a larger host)
  - 3+ candidates across 2+ patterns (and why losers lost)
  - Selected Frame 0 (already moving) / first sound / first spoken line + payload clause (`<= 3.5 s`, priming shared intuition + sensory anchor against visible contradiction; visual-verbal counterpoint — never narrate visible pixels) / muted & phone read
  - ~8 s concrete **non-spoiling** viewing promise kept in **the same opening `\n\n` TTS paragraph** as the hook (physical puzzle/clue named without prematurely revealing the core answer)
  - Opening-to-body handoff (final opening line + first body observation written together; enter the first active test/action immediately at 8–15 s with zero static parts list)
- **Body payoff map (`payoff_steps`) & ending return (`answer_time_s`)**: chain beats via "Therefore / But" causal pivots, gentle 0.5 s micro-predictions, one-new-entity-per-breath pacing, solo `0.25–0.45 s` foley micro-breaths before key turns, and escalating obstacles (False Summits) instead of flat additive lists; deliver final answer late (`>= 75%`), ban premature ending signals (`总结一下`/`所以说到底`/`in conclusion`), and land the closing sentence on an everyday reframing takeaway within `6 s`.

## 4. Script, Shots & Route Execution
- **Script & audio master**: path / hash / actual spoken duration (time shots from real audio, never guesses)
- **Key expression difficulties (`expression_cards`)**: fixed vs changed variables, visible outcome, low-cost comparison if `uncertain=true`
- **Route artifacts**:
  - *Google Flow*: disk prompt ledger, `1080p Upscaled` clip probes, paired `episode.zh.json` & `episode.en.json` (`max(span_zh, span_en)`), `48 kHz` audio disposition (`keep foley` vs `mute`), `google_flow_audit.py` report
  - *Controlled 3D / Local Realistic*: locked tool/project version, scene/asset manifest, `render_gate.py` receipts
- **Text deletion test (`presentation_text`)**: list only kept in-picture items and required notices (default AI disclosure off-frame / platform control).

## 5. Review, Packaging & Delivery
- **Hook sample (0–5 s) & G3 representative sample**: file, `opening_hook.py` report, cold 2 s test, continuous audiovisual notes
- **Final candidate (G5)**: full-resolution `1920×1080` inspection, dual listening (headphones + phone speaker), independent explanation & expression review, `feed_package.py` 9:16 dark-band derivative (for vertical feeds), `compose_cover.py` covers (`3:4` / `4:3`)
- **Delivery & release handoff (G6/G7)**: `check_episode.py` receipt, archive move (`release-candidate` → `archive` after user confirms publish), Douyin standing collection (`透视日常造物` / `解码巅峰工程` / `丈量天地寰宇` / `探秘生命法则`), `#科普` tag, no-download toggle, AI disclosure.
- **Unresolved gaps / pending items**:
