# Video subagents

Delegate to specialized roles only when complex production, parallel independent files, or mandatory independent review warrant it — small edits stay with the parent. The parent remains director and integrator: owning user scope, whole-film narrative ([whole-film direction](viewer-retention-design.md#direct-the-whole-film-before-polishing-its-parts)), shared `episode.json`, route lock, and final delivery.

> **Route isolation:** Every role reads global `SKILL.md` and strictly obeys [SKILL.md's Route Isolation gate](../SKILL.md#route-isolation-load-only-the-active-route). On `google_flow`, load ONLY `google-flow-production.md` and shared craft/review guides — never `tool-routing.md`, `ai-generated-video.md`, or 3D engine guides.

## Roles and ownership

| Role | Delegate when needed | Owned output |
| --- | --- | --- |
| [`video_researcher`](../agents/video_researcher.toml) | Mechanisms, primary sources, analogies, titles/covers, Hook Lab, or platform-data analysis | Source-backed mechanism notes, title/cover proposals, 3+ hook candidates, script fixes |
| [`video_visual_artist`](../agents/video_visual_artist.toml) | Hook frame-0 look, covers (`compose_cover.py`), shot cards/prompts, geometry/materials/lighting | Assigned asset/cover/lookdev files, interfaces, preview requests |
| [`video_animator`](../agents/video_animator.toml) | Frame-0 hook motion, causal process animation, camera choreography, or character rigs | Assigned motion/rig modules, event/time mappings, preview requests |
| [`video_audio_editor`](../agents/video_audio_editor.toml) | Warm conversational script edit, hard-start hook, IndexTTS-2.5 `#5` / Edge master, sound design, captions | Assigned narration/audio/edit/caption files, `continuity_diagnostics`, mix/encode requests |
| [`video_producer_windows`](../agents/video_producer_windows.toml) | Local/cloud execution queue, hook-first rendering/audits, storage moves, authorized release prep | Verified exports, `opening_hook.py` / `google_flow_audit.py` / `check_episode.py` receipts, verified local links |
| [`video_reviewer`](../agents/video_reviewer.toml) | Independent explanation, expression, cold 2 s hook test, or scroll-viewer appeal review | Scoped time-coded report bound to exact media/SHA-256 and stated perception capability |

For [Google Flow](google-flow-production.md), the parent owns UI preflight, the disk prompt ledger, strict 1-by-1 serial cloud submission/upscaling/download, and immediate stop on anti-bot/CAPTCHA gates; coordinate IndexTTS-2.5 `#5` Mandarin clone / Edge English whole-track mastering, FFmpeg compositing, audits, and independent bilingual review across roles as needed.

## Shared assignment contract

- **What to pass authors:** User request & corrections, active route, stage, shot/task IDs, global Skill path, exact file ownership, overall episode question/payoff + selected hook + incoming/outgoing beat connections, current script/inputs with versions, and whether execution is authorized now. (Keep independent reviewers on the two-phase cold-view packet below.)
- **Single-writer discipline:** Never let two agents concurrently edit the same shared scene, timeline, episode JSON, or colliding render prefix; disjoint files may run in parallel. Audio editor owns ONE canonical narration master across cuts (no per-shot audio slicing/normalization).
- **Proportionate checks & bandwidth:** Enforce [risk-based rechecks](quality-acceptance.md#risk-based-rechecks-and-evidence-reuse) (no invented tolerances or per-shot frame quotas) and [local links & bandwidth conservation](../SKILL.md#local-review-links-and-bandwidth-conservation) on every role.
- **No role expands authorization:** Maintenance commissions never resume live media jobs or publish; role definitions inherit host tools/permissions without granting new installation, upload, or publication authority.

## Scheduling and handoff

1. **Lock narrative & route first:** Parent settles topic, package, Hook Lab, whole-script coherence, and the single active route under [SKILL.md](../SKILL.md#route-isolation-load-only-the-active-route).
2. **Hook sample first:** Build the 0–5 s hook at target HD quality first (artist/animator → audio hard start → producer `opening_hook.py` → fresh reviewer cold 2 s test) before refining or expanding the body.
3. **Parallel disjoint authoring, single execution queue:** Visual, motion, and audio work run on separate files; heavy renders/syntheses/encodes queue through `video_producer_windows` in consolidated packages (reusing verified results without needless silent intermediate encodes or per-frame relays).
4. **Independent review & recovery:** Send finished outputs to fresh `video_reviewer` contexts (separate reviewer identities for G5 explanation vs expression). On exhausted 3D repair budgets or recurring defect families, return one cause/cost packet for the parent's changed-method decision.

## Independent review

Run independent reviews in **two phases**:
1. **Phase 1 (Cold view):** Supply ONLY audience, responsibility, media/version, allowed viewing scope, capability limits, and any safety warning. Withhold intended answers, unseen question wording, author rationale, and predicted dropout points until the reviewer records its first-view account and time-coded findings (label as `informed` if already exposed).
2. **Phase 2 (Diagnosis):** Supply the brief, fact cards, intended payoff, and references to diagnose concrete gaps.

Reviewers must honestly state image, continuous-video, and audio perception capabilities (leaving unperceived items unreviewed) and record real reviewer/task identity — never sharing first-view observations across separate G5 explanation and expression passes.

## Installation and invocation

The six TOML files in `agents/` sync to `${CODEX_HOME}/agents` (default `~/.codex/agents`) via:

```powershell
python -X utf8 "<global-skill-dir>/scripts/sync_video_agents.py" --check
python -X utf8 "<global-skill-dir>/scripts/sync_video_agents.py" --install --replace-existing
```

`--check` validates definition files only (not host discovery). If a custom role is not yet exposed by the host, fall back immediately to a standard worker carrying that TOML's instructions and record the fallback honestly. Sync companion skills separately via `scripts/sync_companion_skills.py`.

## Accept handoffs by meaning, not only by file presence

Verify the actual dependency handed off (supported claim conditions, visible relation, audio timing/qualifiers, verified media stream) rather than file existence alone. When a shared claim, timing, or interface changes, notify downstream consumers before they build on stale inputs. Separate observed defects from suggested fixes (e.g., never accelerate speech just to shorten a pause), and let the parent resolve cross-role conflicts without any role silently rewriting another role's in-use files.
