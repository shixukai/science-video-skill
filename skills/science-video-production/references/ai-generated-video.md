<a id="写实风格moneyprinterturbo-制作与本地模型素材"></a>
# Realistic style: MoneyPrinterTurbo production and local-model assets

This page governs actual realistic-route execution: use existing MoneyPrinterTurbo to arrange/composite local video assets. Use the current local video model for needed AI shots, or directly use applicable authorized user captures. 3D animation follows the [Blender route](engineering-blender.md); main-tool choice follows [tool routing](tool-routing.md#lock-the-primary-tool-by-final-film-style).

<a id="开工模态锁定"></a>
## Lock modality at startup

Apply the [realistic contract](realistic-production.md) first. `pure_2d` denotes supporting layers or specifically approved scope, not a free replacement for realistic main imagery. Modality and realism are distinct dimensions; never label AI/3D as real photography.

The table distinguishes actual asset provenance, not freedom to substitute primary tools; follow the [fixed style/tool pairing](tool-routing.md#lock-the-primary-tool-by-final-film-style). Entire episodes may mix only self-produced visuals and verified authorized user captures under the [original-visual contract](science-and-rights.md#original-visual-provenance-contract); third-party imagery is research only. **Register one** `modality` **per shot's main picture**, recording supporting mixed-layer sources separately in the asset ledger:

| modality | Meaning | When to choose |
| --- | --- | --- |
| `real_footage` | Continuous original footage with verified user authorship/use authorization | Real phenomenon anchors, observation evidence or explicit capture requests |
| `pure_2d` | Pure-2D mechanisms/diagrams (e.g. controlled huashu animation) | Supporting layers or specifically approved nonrealistic scope |
| `controlled_3d` | Controlled Blender 3D animation/rendering | 3D-animation style or explicit 3D mixed-project sections; realistic materials do not change route or permit capture claims |
| `ai_generated` | Continuous local video-model output, not still pans posing as video | Needed AI assets for the realistic route; actual MoneyPrinterTurbo production remains required and cannot replace Blender 3D animation |

Judge capture requirements from current `medium.real_anchor` and chosen shot modalities. `real_footage` requires actual used continuous real-video sources; approved AI/3D routes need no extra capture merely to satisfy default checks. Clarify missing/unknown `modality`; null cannot bypass anchors. An original project's explicit `authentic_continuous_video` still requires its whole-episode real anchor despite changed defaults. Specific 2D exceptions, science, provenance and disclosure still apply.

<a id="写实路线步骤"></a>
## Realistic-route steps

1. **Bind existing local projects:** Locate the MoneyPrinterTurbo checkout, verify actual provenance/version/composition entrypoint. Only when generation is needed, locate the local video model from context, inventories and run records and verify model/workflow/environment. Use known locations rather than rebuilding same-name projects or downloading another weights set.
2. **Topic, science and full explanation:** Complete original topic, claims, conditions, sources, continuous script and explanatory shots. Obtain a working track through the existing voice workflow, then schedule generated shots from actual times. MoneyPrinterTurbo writing tools may organize content, not replace scientific verification or turn shot fragments into a full explanation.
3. **Shot asset design:** Verify actual ranges of authorized user capture first; execute this and step 4 only for needed AI assets. Register `modality=ai_generated`, identity/structure, scale, start/process/end, style and scientific prohibitions, planning against actual native model size, frames/duration and current audio. When conditioning images are supported, reuse the local image model for starts; still outputs are not video generation.
4. **Actual calls and samples:** Invoke the confirmed local video model through the existing frozen entrypoint; retain actual workflow, prompts/parameters, task ID and outputs. Produce a risk-representative sample before batching unvalidated approaches. Record/fix missing nodes, weights, services or VRAM locally; no silent cloud or stock-montage substitution.
5. **Inspect actual assets:** Continuously view identity, action, science states, materials and joins at normal speed; repair under the [realistic contract](realistic-production.md). Task return, pretty endpoints or historical samples do not pass current shots.
6. **Produce through MoneyPrinterTurbo (required):** Use actual generated/verified user-capture local videos, explicitly preserving explanation order, necessary actions and sufficient duration. Choose local-asset tasks or the existing complete-picture-track composition function below. No default random cutting, looping to extend length or repeated voice replacement.
7. **Recheck narration, captions and sound:** Reuse accepted complete audio/timed subtitles. Without timed captions use prepared local recognition/alignment and verify the actual timeline. Empty audio fields must not make MoneyPrinterTurbo switch to another TTS.
8. **Output/disclosure:** Re-layout captions for final aspect, mix/export and actually recheck final encoding; handle platform/companion disclosure under [generated-content publication](science-and-rights.md#actual-publication-steps-for-generated-content-declarations).
9. **Sample/full film:** Perform independent normal-speed viewing/listening under [quality acceptance](quality-acceptance.md), repairing known defects before expansion/delivery.

<a id="本地视频模型与-moneyprinterturbo-交接"></a>
## Handoff between local video model and MoneyPrinterTurbo

<a id="定位预检与运行记录"></a>
### Location, preflight and run records

- Read actual current inventories/workflows/verified runs first; check interpreter, engine/nodes, video weights/encoders, input/output paths and service address. Ports/history are location clues, not proof of current availability. Directory existence, working image models or previous success do not establish video-generation readiness. Reuse current environments; Skill updates do not automatically launch services, download models or alter original projects.
- Distinguish images, text-to-video, conditioned video and control renders by actual output chain. Blender guidance, VAE encode/decode, resampling or upscaling do not automatically convert a 3D scaffold to realistic AI video. If the conversion step is removed, reassess remaining imagery/modality rather than retaining the removed step's labels/approval. Control renders may be intermediate inputs; realistic body footage must meet current route/actual review. Repair assets/implementation on failure; style changes still require specific existing/new user authorization. Historical text-to-video success does not test image-to-video; local paths, ports and media records stay private.
- Use the current actual ComfyUI API workflow: preflight nodes/models, submit `/prompt`, save `prompt_id`, query `/history/{prompt_id}` and actual outputs. Verified historical SaveVideo also puts media under `outputs[node_id].images`; locate video by actual `filename/subfolder/type`, not an assumed `videos` field or prefix as a full path. After connection loss/timeout inspect that same task before resubmitting.
- Bind actual workflow/code, model identity/available weight version, prompts/parameters/seeds, condition inputs/hashes, task ID, actual output paths/hashes, dimensions, fps, frame count and duration. Record acquired evidence, not invented weight hashes or submission as completion. Separate historical scripts' service start/stop, sample overwrites and hardcoded submissions before treating them as episode executors.

<a id="moneyprinterturbo-的实际制作范围"></a>
### Actual MoneyPrinterTurbo production scope

Verify these interfaces against actual checkout source before use. Bind repository identity to the user's URL or checkout's real source/commit. Record unknown provenance honestly; upstream README links do not establish current remote. Do not fetch a same-name public repository or update upstream code merely for Skill maintenance.

- **Local-asset arrangement:** Verified implementations accept actual local videos through `video_source=local` and `video_materials`; these inputs do not invoke a video model. Explicitly choose order/crops from scientific shots. Verified multi-output mode may reorder; `sequential` can take only each clip's first portion and loop shortages. A sequential flag alone does not prove exact shot execution. Prepare sufficiently long, purpose-trimmed clips and inspect complete action, order, repetition and audiovisual joins after composition.
- **Complete-picture-track composition:** When a continuous picture track already follows the shots, reuse verified `app.services.video.generate_video(video_path, audio_path, subtitle_path, output_file, params)` for local composition, avoiding unnecessary automatic arrangement. Call through this episode's frozen adapter without bypassing `render_gate.py`; after upgrades verify signature, audio replacement, BGM and font behavior.
- **Voice reuse:** Explicitly supply valid `custom_audio_file` on the task path. Preserve failure if missing/unusable; never leave it empty to trigger default TTS. Verified composition replaces original video audio. If scientific observation needs synchronous original sound, define retention/mixing first to avoid losing evidence. Retain voice-standard continuous Mandarin narration and actual listening.
- **Subtitles:** Prefer existing aligned SRT. Custom audio has no automatic TTS timeline; task subtitles require checking current `subtitle_provider` and actual local Whisper/alignment weights. Missing weights may download; other providers may skip captions. Configuration names prove neither output nor fully offline operation. Align to final editing, not stale times from changed timelines.
- **Publication side effects:** Read the used entrypoint/noncredential configuration to confirm local-only production. Verified CLI video stages may cross-post; do not assume no publication effects. Use local composition or confirm auto-upload/cross-posting disabled; never read/output credential values. Publication follows separate specific current authorization.
- Bind model tasks/generated files through existing `execution`, asset ledger and actual runs; record MoneyPrinterTurbo's actual composition inputs/outputs separately. Only additionally chosen external Skills enter `tool_applications`. Do not install an entire external video framework to connect an existing repository.

<a id="主体或起态偏离时的条件输入修复"></a>
### Repair condition inputs when identity/start states deviate

1. Inspect the failed clip at normal speed; identify wrong object identity, necessary referent or initial relationship at specific times, not merely more prompt adjectives.
2. If the authorized entrypoint supports conditioning images, prepare this shot's first frame, checking whole-frame identity/composition and local action prerequisites. A separation-after-contact action must actually begin in contact; an existing gap is not separation. If unsupported, record the gap and choose an available same-route approach.
3. Preserve valid subject, referent and camera for local failures, repair the region, recheck the whole and freeze actual input/hash. Pixel differences aid diagnosis, not scientific validation.
4. Bind actual conditioning input to the call and inspect generated start, complete action and joins. First-frame approval does not pass video; persistent failure returns to relevant design/source, not fast-cut concealment.

Condition inputs are optional repairs, not mandatory per shot. Verify timing/mechanism under [continuous acceptance](quality-acceptance.md#inspectable-items). For repeated failure trace original output to first distortion: input/control, generation, local composition, upscale or encode. Repair bad source geometry/action/material, not upscale factor. If the relation stays invisible, reassess control/shot design instead of stacking masks, redraws and source-binding scripts as progress.

Reject bad sources in internal normal-fps previews sufficient to read relationships/joins before formal HD/final review of usable approaches. Proxies do not equal G3/G5 or HD approval. Reuse unchanged decodes/assets/accepted voice/captions; process affected dependencies only. Record actual preparation, model/render, decode/write, upscale, composite and review times, distinguishing nested/overlapping intervals; unrecorded gaps are not GPU wait. Existing automatic pixel checks may cover necessary frames without manual frame-by-frame handoff. Verify streaming/cache reuse only when measured repeated decoding/writes are bottlenecks and supported; do not build new generic frameworks/environments for an unproven sample.

<a id="硬禁"></a>
## Hard prohibitions

- Never label AI footage as real capture, observation or a real-material anchor, or claim capture acquired in ledger `kind`/declarations.
- Never fabricate nonexistent observation evidence, experimental records or specific historical scenes with AI and use them as evidence.
- Scientific simplifications must be checkable: include conditions, direction, cause and scale boundaries in claims/prohibited imagery. AI does not exempt science review.
- Stills plus Ken Burns/pan/zoom/hard-cut slides **are not** `ai_generated` video and cannot replace `real_footage` or qualified continuous explanation.
- After user lock to `ai_generated`, do not revert to pure-2D samples under a series default and claim the selected route completed.

<a id="权利与披露"></a>
## Rights and disclosure

Under [science and assets](science-and-rights.md), record generation-tool terms, visual/audio provenance, identifiable people and actual uses; accurately distinguish AI, simulation and photography. Platform controls, `qa.release.ai_disclosure` and asset-level `ai_disclosure_required` have their sole owner there.

<a id="与纯2d--实拍混剪"></a>
## Mixing with pure 2D or real footage

Use only contract-compliant visuals in mixed edits, not third-party public/CC/Commons/paper footage. Register sources per-shot `modality`; disclose under [science and assets](science-and-rights.md). Never label AI as capture or use it to close capture-anchor gaps.

<a id="工具选择"></a>
## Tool selection

Reuse confirmed local models/MoneyPrinterTurbo first; handle missing required capability under [preparation/failure](tool-routing.md#preparation-and-installation-before-calls). Follow [precise control and efficient iteration](production-checkpoints.md#precise-control-and-efficient-iteration) for states, same-target trials and iteration.
