# Episode Art & Image-Quality Record

> Compact private review sheet. Copy into the episode directory and fill **only sections relevant to this route and stage**. Save new snapshots per stage (e.g., `art-G3-v1.md`, `art-G5-v1.md`). Bind every referenced file individually in `qa.gates.<stage>.evidence`.

## 1. Scope, Media & Reviewer
- **Episode / stage / date / record version**:
- **Reviewed media & SHA-256** (and covered shot/time range):
- **Active baseline / reference** (path/hash, approved scope, actually opened `yes/no`):
- **Reviewer, viewing scale/device & method**: continuous normal-speed AV | full-res `1920×1080` stills | phone thumbnail (`270/360 px`); state perceptual limits honestly.

## 2. Visual Checks (Fill Applicable Items Only)
| Area | Shot / Time | Observed state (form, light, space, motion, detail) | Defect / Gap | Action & Recheck |
| --- | --- | --- | --- | --- |
| Opening Frame 0 & Hook (full-res `1920×1080`) | | | | |
| Subject identity, structure & material finish | | | | |
| Continuous action, contacts & object results (`subject_motion` / `object_result_review`) | | | | |
| In-picture text / annotations (3D: single-letter only; non-3D: deletion test & readable hold) | | | | |
| Disturbing-imagery / body-horror check (clean anatomy, intact skin, zero carved flesh) | | | | |
| Master vs final encode detail retention (fine lines, gradients, flicker, compression) | | | | |
| Covers (`3:4` / `4:3` / `1:1`) & phone thumbnails (realistic setting, `compose_cover.py` grid) | | | | |

## Annotations and dynamic binding
- Fill only when in-picture labels/arrows/3D single letters exist: shot/time, target/anchor, removal loss, stable-readable hold interval, editable source/font, tip/shaft/occlusion extremes.

## Animation scene-design card
- Fill only for substantial animation or empty-scene repair: shot/step, observation task, fixed reference vs changing state, shared driver/contact, visible outcome at phone size, and continuity anchor across cuts.

## 3. High-Risk Sample / Before-After Comparison (When Applicable)
| Shot / Interval | Risk tested | Before / Reference | Current export | Result (`pass/revise/pending`) |
| --- | --- | --- | --- | --- |
| | | | | |

## 4. Feedback & Defect Closure (`qa.feedback` / `qa.visual_frames.failures`)
- **Feedback ID / dimension / affected range**:
- **What changed vs what stayed unchanged**:
- **Repaired file & SHA-256 / actual recheck interval & result**:

## 5. Verifiable Evidence Files (Bind Each in `qa.gates.<stage>.evidence`)
| Relative file | SHA-256 | Shot / time | Review scope |
| --- | --- | --- | --- |
| | | | |

- **Remaining gaps / unreviewed scope**:
