<a id="按制作场景调用工具"></a>
# Invoke tools by production scenario

Select the primary production tool from the table first, then add only capabilities actually missing for this task. Reuse existing models, Blender and MoneyPrinterTurbo projects.

Fixed external sources, versions and licenses are in the [external-source index](../indexes/external-skills.json); verify actual installation/runtime capability in the current host.

<a id="按成片风格锁定主制作工具"></a>
## Lock the primary tool by final-film style

Determine style from the user's request/current project records, not subject category:

| Final-film style | Required primary tool | Responsibilities and boundaries |
| --- | --- | --- |
| Realistic style (live-action appearance, including AI realism and authorized user capture) | **MoneyPrinterTurbo** | Use the existing repository for actual asset arrangement or verified compositing, accepted narration/subtitles and aspect-correct export. Local video models provide needed generated assets; models, FFmpeg joining or Blender renders cannot replace MoneyPrinterTurbo production. See [realistic workflow](ai-generated-video.md). |
| 3D-animation style (controlled 3D scenes/animation, including photorealistic 3D materials) | **Blender** | Complete main modeling/asset reuse, materials/light, camera, animation and actual rendering in Blender; supporting audio/subtitle/mix/encode tools may be reused. AI “3D-looking” video or MoneyPrinterTurbo montage cannot replace Blender. See [3D workflow](engineering-blender.md). |

If no style is specified/selected in context, use the series realistic default with MoneyPrinterTurbo; engineering does not automatically select Blender. Execute existing explicit style choices without asking about tools again. Later explicit user style/tool changes control their recorded scope. Missing tools, generation difficulty, old preferences or internal sample comparisons do not authorize changing routes. State exact required-tool gaps and continue independent research, scripting and design.

Use both routes by section only within explicit mixed-style scope, recording projects/shot IDs separately. Supporting captions/arrows do not constitute another film style or require a second main project. Covers/independent 3D assets follow their commissions; video routing does not force covers through MoneyPrinterTurbo.

Record style, main tool, project version and actual input/output in brief, shot design and `execution`. Realistic films retain MoneyPrinterTurbo calls/composites; 3D retains Blender sources/build code/render records. G1 checks route, G2/G3 samples, G5 final output; configuration tool names do not prove execution.

<a id="本地执行最少传输与吞吐"></a>
## Local execution, minimal transfer and throughput

Bandwidth conservation is a hard execution requirement for the parent and every subagent. Work the user's computer can perform at the required quality must run locally: asset preparation, model inference, rendering, editing, encoding, transcription/alignment, media probing and validation. Reuse local inputs and transfer only necessary changes. Apply these requirements within the selected production route and existing authorization:

- **Keep processing near the data.** Reuse the installed tools, confirmed model locations, loaded models and verified assets. Run file searches, JSON/log filtering, hashes, measurements and report generation locally; return paths/IDs, concise results and relevant errors. Keep full logs, source media, weights and intermediate frame sequences locally instead of repeatedly sending them through the conversation or a remote runner.
- **Transfer only what the next step needs.** Use local review when the reviewer has actual access and perception capability; remote media calls must satisfy the [pre-submission requirement](#review-media-without-repeated-uploads). Remote processing needs an explicitly selected service or a demonstrated local capability/capacity gap; convenience or faster remote execution alone cannot override bandwidth conservation. Reuse verified local models/assets and cached downloads; do not fetch or upload a whole project/library for a local change. Use existing authorization without adding a per-transfer permission request.
- **Reuse local working data.** Prefer an appropriate local fast disk for new active working sets and temporary media. Fetch missing assets from the approved library/NAS on demand, reuse verified local copies and archive changed files incrementally. Preserve originals, existing job-bound paths, version evidence and required backups; do not move a running job's inputs or repeatedly copy a whole library/project for a local change. Cache/reuse remains subject to the existing input-integrity checks.
- **Use CPU and GPU actively; preserve quality.** Select compatible GPU rendering/inference and hardware decode/encode when they meet the required quality. Overlap independent CPU preparation, analysis and post-processing with GPU work. Do not pre-emptively simplify materials, lighting, geometry or output quality because rendering might be expensive. Verify the actual selected backend and per-stage time; investigate idle gaps and inherited CPU/fixed-thread settings before treating low GPU utilization as a hardware limit.
- **Scale useful parallelism.** Coordinate worker count, threads per worker and batch size using current memory/VRAM demand, actual throughput and errors. Sustained high CPU/GPU usage is acceptable while the system remains responsive and stable. Increase useful concurrency when capacity remains; reuse a valid measured setup and put necessary calibration in the existing short sample, not a benchmark before every launch. The target is qualified output per unit time, not a utilization percentage.
- **Back off before system responsiveness is lost.** Use available current observations of memory/VRAM pressure, sustained paging or I/O stalls, desktop responsiveness and device/thermal errors. When resource contention causes slowdown or instability, reduce this task's workers, per-worker threads or batch size, or pause new submissions; preserve completed frames and resume at a demonstrated stable setting. Handle OOM/device faults in the affected job instead of repeatedly relaunching the same failing workload. Keep normal hardware/OS protections, job ownership, output locks and explicit host/user/task-specific limits; do not terminate unrelated tasks. Missing optional telemetry is not a new blocker. Resource admission follows the [current-evidence rule](production-checkpoints.md#conditional-reuse-of-static-evidence-and-fresh-dynamic-checks), without invented utilization caps, fixed reserve quotas or idle-wait gates.
- **Optimize the complete workflow.** Reuse initialized processes/scenes, batch compatible work, overlap independent stages and resume valid outputs. Re-render only affected ranges; text/audio-only changes normally recompose existing frames. Compare end-to-end time and qualified output throughput at the same quality, including transfer, loading and I/O. Keep the accepted resolution, motion sampling, geometry, voice and review requirements; high utilization alone is not proof of improvement. Use the existing [timing records](production-checkpoints.md#segmented-timing-and-controlled-service-reuse) for measured configurations and results.

## Review media without repeated uploads

**User review materials use clickable local-file links.** When asking the user to judge a video, audio file, image, document or report, verify that the current intended local file exists and return a normal Markdown file link with a short material/version label and an absolute filesystem target. Use forward slashes in Windows link targets and angle brackets around targets containing spaces. Do not wrap the whole link in backticks or use file://, vscode:// or an invented web URL. A bare path or inline-code path alone is insufficient for the requested handoff. For several requested candidates, give a clearly labelled link for each and briefly identify the relevant review question or interval.

Keep the file local; do not upload it to cloud storage or another site merely to create a link. Return links without attaching/uploading media, embedding players/images/media tags, invoking preview/display tools or opening a player automatically. Do not substitute GIFs, thumbnails or frame galleries for the same review material in chat. The user may click the link to open it intentionally; this is distinct from automatic presentation. A later explicit user request controls any change to this handoff. Agent inspection remains subject to the media-transfer requirements below.

**Mandatory before each outbound media call or batch:** establish the specific production, review or delivery need and the recipient's required capability, check prior submissions for the same content/context, and select the smallest sufficient representation and range. Record purpose, recipient, selected files/ranges/hashes and their locally measured byte total in the existing work/review log; one batch entry is enough. If necessity, deduplication or sufficient payload selection is unresolved, do not submit media: prepare/check locally or retain the corresponding review as unreviewed while continuing independent work. Measure local files before sending them. For tools that create media during the call, bound the requested dimensions/range/count before calling and record returned sizes when exposed; unknown sizes remain unknown. Do not invent a universal MB/frame cap or claim file sizes are wire measurements.

Quality, full-film coverage and independent review must be achieved within this constraint, not used as blanket exceptions for raw-frame uploads or repeat batches. When a proxy loses needed detail, send only the necessary higher-fidelity range or contextual detail. Only an explicit user instruction changes the scope of this constraint. Apply the user's current allowance as well as restrictions: permission for moderate review uploads permits context-preserving contact sheets, necessary original detail or short playable intervals for a capable recipient. Do not keep enforcing an older self-chosen byte ceiling or shrink to a contextless crop. Reuse one concise existing log entry for the review bundle, appending actual files/results rather than creating per-frame approvals; already authorized transfers need no repeated user permission. This does not authorize whole-project uploads, routine full-frame-sequence image calls or automatic media display in chat. On continuation or a new user transfer restriction, apply the current rule before the next media submission; this requires no render restart or rewriting of historical receipts.

Local files do not imply local perception. Treat `view_image`, `emitImage` and image-bearing tool results sent to a remote model as media submissions. Local decoding, hashes, geometry checks and FFmpeg measurements can stay on the computer. A path or a successful playback command does not give an agent video/audio perception.

1. **Detect and select locally.** Run applicable frame-integrity, black/freeze/change, geometry/camera and audio checks locally; return compact findings and time ranges. These checks locate candidates for inspection, not aesthetic or scientific approval. Keep the original frames and full logs on disk. Do not loop image-view tools over a whole frame sequence as routine review, or send every intermediate render merely because it exists.
2. **Choose media for the question.** For motion and pacing, use a locally encoded, normal-frame-rate clip with the required sound and complete affected cycle/joins when the reviewer can actually perceive it. For static diagnosis, start with selected key states or a readable, labelled contact sheet, then request originals or contextual crops only where detail is unresolved. Preserve source identity, frame/time, crop and scale. Do not paginate the entire sequence into sheets to imitate playback. If continuous perception is unavailable, mark that coverage unreviewed; hundreds of still-image calls cannot supply it. Keep the existing normal-speed first-view and independent-context rules.
3. **Match the representation to the review.** Prepare lightweight review derivatives locally; do not change production masters. Use resolution/compression adequate for the actual question. Full-resolution text, fine geometry, texture, color or compression defects may need original frames and surrounding context. Proxy findings apply only to what remains observable; they do not replace required final-encode or full-film review. Choose a bounded batch for the current question rather than a universal frame/byte quota.
4. **Avoid duplicate submissions.** Assign one owner per review responsibility, media version and range; retain the separate G5 explanation and expression reviewers. Update the pre-submission entry with the actual result status and any changed crop/scale. Reuse observations for unchanged content in the same context; the parent receives paths, time-coded findings and only needed evidence, not another copy of every inspected frame. Repeat a submission only for a concrete reason such as missing detail, a new comparison or required independent review. A fresh reviewer must receive the media it needs without relying on the author's verdict; a shared path/hash is not a shared model cache. If a batch response is missing or oversized, inspect its status and resend only the missing needed items, not the whole batch automatically.
5. **Account honestly.** When diagnosing transfer cost, count actual media-submission events and repetitions, and record locally measured derivative sizes in the existing log. File bytes are an estimate of selected payload, not measured network traffic: encoding, resizing, cache behavior, retries and protocol overhead may differ. Report wire bytes only when actually measured and scoped. Do not upload more images to investigate an upload problem or print base64/full media logs into the conversation.

<a id="按需选择与应用证据"></a>
## Need-based selection and application evidence

`tool_applications` defaults empty and records only actually selected external Skills: `need`, `selection_reason`, `source_id`, `usage_mode` (`method`/`runtime`), `read_reference` (actual version/file), `shot_ids`, `status`. Method references must be read/applied to shots without installing whole frameworks.

`planned` means pending implementation. `applied` attaches `artifact_evidence` (file/SHA-256), with outcomes in existing QA. `runtime` also attaches `installation_evidence` and `execution_evidence`; valid same-version/environment evidence may be reused.

<a id="逐镜选择与同目标小样"></a>
## Per-shot selection and same-target samples

Lock the primary tool by style as above. Realistic films follow the [realistic contract](realistic-production.md), 3D the [Blender requirements](engineering-blender.md). The 2D tools below serve supporting layers or specifically commissioned 2D scope, not main production in either route. Drawings/code animation are not video-model calls.

- Realistic atmosphere, environment establishment and opening phenomena: produce through MoneyPrinterTurbo. Prepare assets with confirmed, use-authorized local video generation, also evaluating continuous original footage with verified user authorship/use authorization. Third-party public, CC/Commons and paper footage is research only, never filler because downloadable/licensed. Generated footage is representation/illustration, not actual observation evidence. Scientific arguments still need verifiable sources; citing a paper does not introduce its video into production. Delivery provenance follows the [original-visual contract](science-and-rights.md#original-visual-provenance-contract).
- 3D processes requiring exact structure, contact order, direction, topology or mechanism states: Blender must drive whole/local/bridge from shared geometry/state without a prior video-model trial. These requirements do not authorize silent Blender substitution on a realistic route. Both outputs need scientific sources/actual continuous-state checks.
- For explicit mixed-style shots, distinguish each output's role/main tool first, e.g. generated environment and controlled mechanism layers have separate provenance. After composition check identity, scale, light/shadow and before/after states. Retain modality/asset ledgers and never mislabel a composite as capture.
- Composite narration, synced captions, verifiable evidence annotations and necessary picture text as editable post-production layers rather than relying on model-drawn accurate text; they cannot repair wrong subject action or fabricated evidence.

Compare same-target local samples only when assets, parameters or expression choices remain within one route. Fix required subjects, start/end, discoveries and viewing conditions. Record actual inputs/versions, output hashes, normal-speed gaps, measured time and repair count in existing records, leaving unmeasured items unknown. Continue existing stages after selection; a sole usable route needs direct validation, not mandatory per-shot comparison.

### Blender-to-ComfyUI pipeline trials

Use a short paired trial when a neural redraw is a plausible improvement for the selected shot. It is optional, not a prerequisite for ordinary Blender production. Keep the [selected production route](#lock-the-primary-tool-by-final-film-style); a trial does not make generated pixels equivalent to controlled geometry.

1. **Freeze a shared shot.** Use the same Blender scene, camera, objects, action, native frame range and viewing conditions. Define visible invariants such as component count, holes, interfaces, contact order and final state before rendering. Save the beauty sequence and the actual control input. Choose a frame count and resolution supported by the candidate model; keep both comparison clips at the same duration and fps. Identify native versus resized/interpolated outputs and any differing settings. This compares complete pipelines, not necessarily one isolated variable.
2. **Verify the actual control path.** Inspect the running node schema and saved graph: the full condition sequence must reach the video-control input, with the reference frame connected separately when used. First-frame I2V alone is not a controlled video-redraw test. A native-node example is `LoadVideo → GetVideoComponents.images → Canny → Wan22FunControlToVideo.control_video`, with the beauty first frame connected to `ref_image`, matched high/low-noise sampling, then VAE decode and encoding. Consult the [upstream template](https://github.com/Comfy-Org/workflow_templates/blob/main/templates/video_wan2_2_14B_fun_control.json), verifying the installed schema and model/accelerator pairing. Record actual versions, hashes, graph, seed, sampling, condition parameters and frame mapping. Depth, Mist, Normal and Canny are not interchangeable.
3. **Check preservation before appearance.** Inspect the encoded output for the required objects, openings, thin layers, motion and relationships; attractive texture cannot offset a lost part or changed mechanism. Record concrete defects by frame/time. Review continuous stability through the existing [actual viewing requirements](quality-acceptance.md#reviewers-and-viewing-safety); stills can establish local defects but cannot prove smoothness or absence of flicker. Preserve a failing candidate and its repair cost. Full-frame neural output remains `ai_generated`; for masked redraw or compositing, record generated and retained controlled layers separately, with their actual Blender/control dependencies. Use controlled geometry for an explanation whose required relationships the redraw does not preserve.
4. **Measure time to a usable result.** Follow the existing [stage timing definitions](production-checkpoints.md#segmented-timing-and-controlled-service-reuse). Report shared preparation once and each route's preparation/control export, startup, queue, loading, execution, encoding, repairs and actual review. The redraw route includes its required Blender work: if controls come from a beauty render, include that dependency; a cheap depth/clay-export alternative is a different trial. Separate first deployment/download costs from reusable work and state cache conditions. Measure route wall time; overlapping stages are not additive. Mark untimed work and unseparated stages instead of calling execution time the full total or pure inference.
5. **Adopt the demonstrated use, not the tool name.** A useful production method needs the required quality plus an observed quality or total-time benefit at comparable viewing conditions. A failed redraw still informs shot selection; it does not establish that all models fail. Keep unreviewed results as candidates. One short trial does not justify a series-wide engine/model change, universal speed claim, fixed low-VRAM setting, or replacing material/light work with automatic redraw.


Recheck tool/asset changes by [affected dependencies](quality-acceptance.md#handling-failures); continuations compare [global migration](global-skill-installation.md) without hot-switching active jobs.

<a id="调用前准备与安装"></a>
## Preparation and installation before calls

1. Check existing installations, readable entrypoints, projects and dependencies; absent session listings do not mean uninstalled. Reuse verified environments without overwriting customization or downgrading for historical indices.
2. For missing required runtime, check source/version, dependencies, current installation authorization and host permissions; execute existing authorization directly. Reading methods alone requires no framework installation. Cloud transfers, costs, accounts and model downloads follow their own authorization.
3. Read entrypoints after installation, verify versions and run the minimum needed capability with actual output binding. Library archiving follows [standing authorization](engineering-blender.md#standing-authorization-for-library-archiving).
4. Stop a repeatedly failing dependency without new repair evidence, record gaps and continue independent work; never silently replace a locked main tool. Unlocked supporting capabilities may use existing equivalents.

<a id="场景选择"></a>
## Scenario selection

| Task | Entry and output | Execution points |
| --- | --- | --- |
| Realistic video | [MoneyPrinterTurbo workflow](ai-generated-video.md) → finished composite | Explicit order/crops, complete narration reuse, check loops/captions/publication side effects |
| 3D animation/independent assets | [Blender production](engineering-blender.md); [library search](../scripts/find_3d_assets.py) → sources, renders or assets | Search library first; asset-only work invents no episode audio/G3 |
| Rigging/mocap/lip sync | [Character performance](engineering-blender.md#character-rigging-motion-capture-and-lip-sync) → editable character/action/face curves or explicit generated-video layer | Activate by shot need, reuse characters/audio; separately check skeleton, skin, retarget, contact and mouth. Candidates are not installed/tested claims |
| AI-realistic continuous assets | Current local video model/ComfyUI → video/call records | Verify video nodes, weights/output; image models are not video generation |
| Edit, mix, transcode, aspect | `ffmpeg-skill` → new media/checks | Check local codecs/filters; preserve sources |
| Mandarin recognition/caption alignment | Prepared local ASR/aligner → SRT/caption version | Align final timeline; verify Mandarin models/caption renderer |
| Approved 2D animation/support | Existing `huashu-art-motion`, Motion Canvas, Manim or Remotion → editable layers/picture tracks | Select relationship-appropriate capability, not replacement realistic/3D main production |
| Existing HTML/React supporting layers | Existing HyperFrames/Remotion → graphic track | Read entrypoints, verify dependencies/runtime rights; no migration for ordinary edits |
| First frame, background, cover | Existing legal assets or selected image tool → still asset | Follow host image-tool requirements; stills are not registered as video |
| Foreign-language captions/dubbing | Approved subtitle/voice tools → aligned captions/new-language audio | Translation is not dubbing; verify voice, uploads and costs under actual authorization |

Consult [source/capability index](../indexes/external-skills.json) for other tools only when needs arise, not to install the catalog.

For complex tasks with independent work/review, delegate under [subagent coordination](subagent-orchestration.md). The parent retains overall narrative/delivery and the local producer coordinates jobs. Role definitions do not alter routes, stages or actual permissions.

<a id="交给子工具的任务"></a>
## Assignments to supporting tools

Supply question, shot/semantic timecodes, before/end states, formal narration/approved voice, applicable style/assets, aspect/fps, allowed text and output directory. Return outputs to the same episode/full narration; cuts do not select a new voice or synthesize another isolated TTS sentence.

Reuse tool checks in existing stages; review content, image and listening under their owning references. Upstream colors, seconds, effects and default voices do not override this design.

<a id="huashu-art-motion-执行"></a>
## huashu-art-motion execution

Use only in approved 2D scope. Read its `references/09-视频动画语法.md` and needed syntax cards, copy `scripts/engine/` into a new episode project and freeze upstream commit/project changes. Check relationships before parameterized clips: e.g. `y1` center/satellite nodes do not directly represent condensation; use layered assets/scene code for cup wall, vapor and drops.

Prefer verified environments; these upstream parameterized entrypoints require shot-specific paths, content and duration:

```sh
uv run --isolated --python python3 --with playwright --with pillow --with numpy python <episode-project>/render.py --spec <shot.json> --out <new-picture-track.mp4>
uv run --isolated --python python3 --with playwright --with pillow --with numpy python <huashu-installation>/scripts/qa.py --spec <shot.json> --out <new-QA-directory>
```

New environments/Chromium installation follow existing authorization/host permissions. After export use ffprobe for codec, dimensions, fps, frames/duration, then inspect selected frames/continuous samples. Reuse accepted voice/full narration. Use legitimate refined assets for complex people/nature shapes; code controls editable action/composition.

Upstream code/docs are MIT, fonts their respective OFL, stroke-order derivative data Arphic; author characters/frames are demonstrations only. Check production-asset rights separately.

<a id="其他执行说明"></a>
## Other execution notes

- **FFmpeg/local Mandarin ASR:** Read current tool docs before `probe.py`, processing and `check.py`. Edit before recognizing/aligning with prepared Mandarin models; default English is not a Mandarin solution. Fully offline use first verifies local weights. Without `subtitles`/`drawtext`, distinguish SRT, soft captions and burned captions; do not claim unproduced caption versions.
- **HyperFrames/Remotion:** Read only used capability entrypoints/dependencies and reuse projects/audio. Set `HYPERFRAMES_NO_TELEMETRY=1` for local HyperFrames; asset transfer/feedback follows actual authorization. Check Remotion Skill/engine licenses separately. Use Studio `--no-open`; open through permitted browser tools only when needed.
- **browser-video-recording:** Use only for necessary operation demos; it composites screenshots, not continuous capture. Explicitly set `cursor_asset`, `cursor_hotspot`, run `scripts/render_browser_demo.py --config <config> --output <new-output.mp4>`, and avoid default fullscreen masks/system-cursor capture branches. Add episode narration to silent output.
- **Model/cloud candidates:** Verify exact entrypoints, prepared models/accounts and authorization first; do not guess commands for unknown sources. Prompt guides are not executable renderers, translators not TTS, cloud transcription not fully local processing.

<a id="来源识别"></a>
## Source identification

Use actual repositories/files/licenses in the [fixed-source index](../indexes/external-skills.json), not duplicated/mismatched post links. `video-dubbing` is not verified as executable; same-name candidates such as `app-demo-agent` require real-source checks.

Use [precise control/efficient iteration](production-checkpoints.md#precise-control-and-efficient-iteration) for shot states/trial records.
