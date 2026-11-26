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
- **Narrative frame (`narrative_frame`)**: `everyday_problem_solving` | `verified_historical_incident` | `what_if_counterfactual` | `direct_mechanism_discovery` (concrete story/problem arc instead of lecture delivery)
- **Appeal plan** ([emotional payoff & share triggers](../references/viral-appeal-and-packaging.md#engineer-the-emotional-payoff-aha-frame-and-share-triggers)): dominant emotion (`awe` | `surprise` | `satisfaction` | `relief_or_usefulness`) / aha frame & its time (~60–85%) / one-sentence retell line / save tip for pinned comment / sensory signature sound / loop-friendly last frame echoing Frame 0 / title search words
- **Hook lab (0–5 s, `topic_alignment.opening.hook`)**:
  - `host_relation`: `standalone` | `part_of_host` (`host_system` + `whole_to_part_bridge` if inside a larger host)
  - 3+ candidates across 2+ patterns (e.g., counter-intuitive contradiction, `everyday_pain_point`, `overlooked_detail`, visible consequence — zero opening definitions/formulas or clickbait percentages; record why losers lost)
  - Selected Frame 0 (already moving) / first sound / first spoken line + payload clause (`<= 3.5 s`, priming shared intuition, relatable friction, or an overlooked physical detail; visual-verbal counterpoint — never narrate visible pixels) / muted & phone read
  - ~8 s concrete **non-spoiling** viewing promise kept in **the same opening `\n\n` TTS paragraph** as the hook (physical puzzle/clue named without prematurely revealing the core answer)
  - Opening-to-body handoff (final opening line + first body observation written together; enter the first active test/action immediately at 8–15 s with zero static parts list)
- **Body payoff map (`payoff_steps`), breathing-point cadence & ending return (`answer_time_s`)**: chain beats via "Therefore / But" causal pivots, one-new-entity-per-breath pacing, and escalating obstacles (False Summits) instead of flat additive lists; control information density by landing a concrete **breathing-point micro-climax** every ~15–25 s (never `> 30 s`: animated visual reveal + `0.25–0.45 s` foley micro-breath, mini controlled experiment/comparison, or gentle 0.5 s micro-prediction question) where **pictures replace prose** for every abstract mechanism; deliver final answer late (`>= 75%`), ban premature ending signals (`总结一下`/`所以说到底`/`in conclusion`), land the closing sentence on an everyday reframing takeaway within `<= 3.5 s`, and draft 1 off-video **pinned-comment / copy engagement seed** (experience extension question or same-collection next-episode teaser) for `science-video-publishing`.

## 4. Silent Visual Storyboard, Script & Route Execution
- **Silent causal visual plan (design BEFORE locking prose):** 4–6 continuous visual cause-and-effect beats inside ONE persistent, bright real-world environment & recognizable physical host (name the real host asset / open-licensed glTF, the in-situ cutaway showing driver + mechanism + outcome + host anchor in `28–60 mm` storytelling lenses, and the controlled side-by-side comparison — zero flat gray/black void backdrops, zero box hero substitutes, zero blind `> 75 mm` 2 cm slivers, zero legacy episode template reuse).
- **Script & audio master (lean narration pointing to verified visuals):** path / hash / actual spoken duration (time shots from real audio after muted visual preflight passes, never write prose to patch unreadable visuals)
- **Key expression difficulties (`expression_cards`):** fixed vs changed variables, visible outcome, low-cost comparison if `uncertain=true`
- **Route artifacts:**
  - *Google Flow*: cloud backend (`gemini_api_cli` via `scripts/gemini_api_cli.py` | `google_flow_web`), disk prompt ledger (with `response_id` or card index), `>= 1080p` clip probes, paired `episode.zh.json` & `episode.en.json` (`max(span_zh, span_en)`), `48 kHz` audio disposition (`keep foley` vs `mute`), `google_flow_audit.py` report
  - *Controlled 3D / Local Realistic*: locked tool/project version, open-licensed 3D host & CAD silhouette manifest, `scripts/colab_cli.py audit-blend --strict` report (Frame 0 + body frames), muted `1920×1080` Colab `blender-stills` preflight + `build_visual_review.py beat-board` receipt, `render_gate.py` receipts
- **Text deletion test (`presentation_text`):** list only kept in-picture items and required notices (default AI disclosure off-frame / platform control).

## 5. Review, Packaging & Delivery
- **Hook sample (0–5 s) & G3 representative sample**: file, `opening_hook.py` report, cold 2 s test, continuous audiovisual notes
- **Final candidate (G5)**: full-resolution `1920×1080` inspection, dual listening (headphones + phone speaker), independent explanation & expression review, `feed_package.py` 9:16 dark-band derivative (for vertical feeds), `compose_cover.py` covers (`3:4` / `4:3`)
- **Delivery & release handoff (G6/G7)**: `check_episode.py` receipt, archive move (`release-candidate` → `archive` after user confirms publish), Douyin standing collection (`透视日常造物` / `解码巅峰工程` / `丈量天地寰宇` / `探秘生命法则`), `#科普` tag, no-download toggle, AI disclosure.
- **Unresolved gaps / pending items**:
