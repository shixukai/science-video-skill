# Reusable Blender sequence execution

Use this for local intermediate 3D frames after choosing the scene and frame range. It does not approve science, appearance, narration or delivery. Assemble audiovisual roughcuts/samples/finals through the existing [phase entry](production-checkpoints.md#开工锁定与真实渲染入口). Existing task-specific launch requirements still apply; the generic runner is not a replacement for a required bounded executor or an unresolved task.

## Prepare one job per shot or coherent scene

Read the [production sequence](engineering-blender.md#有界试制与可靠复用) first. Reuse linked/appended assets and a stable scene driver. Keep shot parameters in JSON rather than generating a new launcher for each revision. Save project-specific files in the project; call [blender_batch.py](../scripts/blender_batch.py) from the unique global Skill.

Start with [blender-job-template.json](../assets/blender-job-template.json). Fill the actual device name, existing Blender executable and driver path; blank entries are deliberately not runnable. Paths resolve relative to the spec file. `inputs` lists all external assets, libraries, fonts, textures, imported project helpers and caches actually read. The runner hashes them, the Blender binary and its own executable script. It executes declared project Python source directly, including imports, so stale `.pyc` files cannot substitute an older driver, helper or resource policy. It checks loaded external images, fonts and libraries again after frame-state changes; native sequence textures in evaluated nodes use Blender's actual frame mapping, and UDIM images bind each tile. Declare every sequence frame the job uses, not just its first image. Custom file reads, simulation caches and external services still require explicit dependency declarations/checks; this is not a universal dependency crawler.

    python <global-skill>/scripts/blender_batch.py prepare shot-spec.json shot-job-v1.json
    python <global-skill>/scripts/blender_batch.py run shot-job-v1.json --blender <existing-blender-executable>
    python <global-skill>/scripts/blender_batch.py run shot-job-v1.json --blender <existing-blender-executable> --resume

`prepare` writes a new immutable job, including its output directory, dependency hashes and executor hash. Changes to scene, assets, settings or executor require a new job/output version; do not edit the signature. No complete Skill copy is made in the project. Continue an existing job with the same version only when its inputs remain valid. Global updates require explicit migration; do not hot-switch a running batch or rewrite old receipts.

`frames` is a sorted integer list or inclusive comma-separated ranges such as `1:100,151:200`. These are native Blender frame numbers, not zero-based video indices. `motion_preview` requires consecutive frames at the declared output fps; sparse `lookdev` images do not prove smoothness. `--frames 1:25` selects a subset of the frozen job, and `--resume` can then complete the remaining frames. A patch keeps its intentional gaps; never fill those gaps by interpolation or by guessing adjacent source frames.

## Scene adapter

Choose exactly one source:

- `blend`: an existing baked/keyframed scene whose animation is reproduced by `scene.frame_set(frame)`. Check at least two different times before treating a saved file as render-ready. A scene saved from a procedural Python state is not automatically a baked animation.
- `driver`: a Python module with `build(spec) -> bpy.types.Scene` and `set_frame(scene, frame, spec) -> JSON-serializable metadata`. Build/import geometry once per process. Update transforms, visibility, materials or animation state per frame. The driver receives `spec.params`; it does not launch Blender, write frame receipts, choose a fallback device or render frames itself.

An adapter for an existing `build_once()` / `set_state(index)` project should call those functions and document its native-frame-to-index mapping. Declare the imported helpers in `inputs`; reuse their geometry rather than rebuilding a second version. Keep exactly reproducible state for out-of-order patch frames. Bake simulations/caches when their result depends on prior playback; arbitrary random-access evaluation is not valid for an unbaked simulation.

Screen labels, captions and titles normally stay outside the raw 3D image sequence. `set_frame` can return anchor metadata for the compositor: frame/time, stable object/anchor ID, pixel coordinates, depth and visibility. Derive coordinates from evaluated world transforms and the actual camera. For example, use `bpy_extras.object_utils.world_to_camera_view(scene, camera, world_point)` and convert `(x, y)` to `(x * width, (1-y) * height)` for a top-left image origin; test bounds, positive depth and any required occlusion separately. Projection alone does not establish visibility. Final typography and arrowhead/stem geometry remain editable in the overlay stage. Physical lettering on an object can remain in 3D when needed for that object's identity.

正式帧和画质样段按[高清输出](quality-acceptance.md#高清视频输出)使用本片 `design.output.width/height`，并在实际渲染中核100%尺寸；合成与编码保持该目标。`blender-job-template.json` 的960×540仅是内部 `motion_preview` 起点，不能原样作为正式画质样段/成片配置；正式任务须明确覆盖宽高与本片帧率，并按真实风险配置采样，不把技术预演参数当正式画质。

## Hand off raw frames to the edit

Keep the accepted narration and editable text/annotation source separate from the raw sequence. The edit records each source job/signature, verified frame files, source fps, selected native range and its destination timeline interval. A sparse patch replaces those exact frame numbers in the original sequence; it is not a shorter consecutive clip. Check the completed range for missing/duplicate frames before encoding at its recorded fps. Do not stretch picture or cut voice with `-shortest` merely to hide a duration mismatch.

Use the existing editor or FFmpeg composition adapter to apply the delivery-size typography after resizing, then combine picture, captions, narration and sound. Preserve linear/color-transform handling for EXR rather than treating it as display-ready PNG. An ordinary text/layout correction reuses the same verified raw frames and anchor metadata; a voice edit reuses picture when timing still matches. New timing, camera, geometry or visibility can change the dependent ranges. Verify the recomposed frames and applicable audiovisual scope through the existing phase entry; frame reuse is not automatic review reuse.

### 可选复用光照分组，而非每次重渲

确需反复平衡主/补光贡献且当前工程已有可用Light Groups或分离光照通道时，可在本地合成重平衡增益，保留线性母版、通道对应、实际输出文件/哈希和可编辑合成。这里只复用真实存在且已在当前环境核过的通道；通用runner的PNG/OPEN_EXR主帧支持不代表已提供多层EXR或Light Groups，不写入臆造的JSON渲染键。需要新设通道时由作者在支持的场景/合成流程中配置，沿已有代表段核实际输出与复用收益，不为每期另设通道试验关卡。

光源位置/尺寸、阴影、遮挡、几何、材质或所讲现象变化仍重渲受影响范围；普通调色或二维提亮不能制造缺失的真实反射/投影。缺所需通道时沿当前可用流程制作，不自动换引擎、装外部工具或调用云服务。通道文件属于作者声明的额外交付，仍核版本和实际范围；工具完成不代画质批准。

## Explicit color settings and actual readback

The generic runner accepts only its documented `render` keys; an unsupported key is an error, not an applied setting. Optional `render.color_management` accepts `display_device`, `view_transform`, `look`, `exposure` and `gamma`; use enum names supported by the actual Blender/OCIO configuration. Absent keys inherit the authored scene. Explicit values are applied in order and read back; invalid/clamped/mismatched values fail before rendering. Do not put a flat `render.exposure` or invented material/light parameter in the spec and assume it works. Other scene, material, texture, light and output controls belong in the declared driver/baked scene. The receipt records actual color state plus available sampling, denoising and light-path diagnostic settings; it does not certify appearance.

For [grain, shimmer and compression diagnosis](art-direction.md#画面洁净度先定位雪花感的来源), compare the local raw output and affected post-processing stages before changing quality. The `motion_preview` template is a technical preview, not a final-look preset. No universal sample/exposure/brightness pass line is implied. Existing frozen jobs keep their input/signature history; a changed executor or settings requires an explicit new job/migration rather than editing its old receipt.

## Complete a repair cycle before expanding

For a motion defect, keep one owner responsible for the whole changed interval and its entry/exit joins. Identify the reproducible failure, intended state relationships and the next usable output before editing. A corrected still is diagnostic progress, not completion of that interval.

- **Test the mechanism before expensive frames.** For cutaway, visibility or camera faults, evaluate the native frame range with the real driver and check the relevant transforms, operand coverage, visibility events and camera clearance. Include opening, hold, closing and neighboring frames, not only the initially reported pair. A finite cutter must cover its intended volume throughout the sweep. Derive a coordinated final state and collect metadata after the required scene evaluation; consolidate stacked revision wrappers when they obscure which camera/cutter/visibility state actually renders. Numerical/geometry checks locate risks; they do not certify appearance.
- **Batch the visual check.** Submit one coherent request containing the changed inputs, all identified risk states and the complete motion interval. Reuse scene builds and unchanged media. Inspect a continuous target-fps preview with reduced spatial/shading cost, then check engine-specific risks in the intended final engine. Do not replace continuous review with a growing succession of isolated frame requests, or restart the asset/environment for each check.
- **Consolidate feedback.** Review the available changed cycle and its joins in one pass, returning the observed defects together with locations and priorities. Fix the common cause before cosmetic symptoms. If a repair moves the fault to another phase or introduces the same class of defect, revisit the representation/state coupling before another parameter-only patch. Preserve the requested motion and explanatory goal; a stable topology, correctly sized cutter or deterministic cached result can replace a fragile implementation without dropping the animation.
- **Control elapsed work.** In the existing work log or task message, give the next usable deliverable and a task-specific estimate based on actual build/render/edit costs. Track cumulative elapsed time, measured execution and uninstrumented gaps separately. If that estimate is missed or the same defect family recurs, the parent resolves the bottleneck and chooses the next bounded implementation change; it does not simply relay another frame request. No universal minute limit, render-count quota or automatic quality reduction is implied.
- **Return to the sequence.** Once the affected cycle is ready, assemble the playable candidate promptly with the retained voice/text and perform the applicable stage review. Keep required input/job/feedback records current, but do not regenerate unchanged script, audio, scene or the entire episode's paperwork for an intermediate test. Unrelated authorized work can continue while a dependency is being repaired. Existing unresolved defects and missing perception remain unreviewed; elapsed time never turns them into a pass.


## Device, ownership and recovery

Cycles jobs explicitly select `CPU` or `GPU`; GPU jobs select the actual backend and exact enumerated device name, with `device_id` when names are ambiguous. No implicit CPU fallback or utilization ceiling is implemented. Keep applicable host/user limits and existing project queue, ownership, capacity and budget checks. An optional `resource_check` Python file can expose `check(spec) -> {"ok": bool, ...raw observations/reason...}` to reuse an existing check immediately before building. Include that module and its dependencies in `inputs`. A false result is recorded and stops execution; the hook cannot invent its own policy threshold. Consult the [current-evidence rule](production-checkpoints.md#静态证据条件复用与动态新鲜检查).

The Blender process holds an OS lock for its output job. If its launcher disconnects, the worker still owns the lock. Do not delete the lock file to force a retry. Inspect the actual process and `state.json`; a failed or interrupted job can resume only once the lock is available and input hashes match. An existing output directory without the matching `job.json` is never adopted.

Each frame has a hash, source-job signature, actual settings, optional anchor metadata and measured state/render-write times. Resume reuses only matching files/receipts; incomplete or corrupt job-owned files are preserved under `invalid/` before replacement. Completed attempts remain in `attempts/`. If source changes during execution, the attempt is marked `inputs_changed`; restored source bytes do not retroactively validate those frames. Keep that output and prepare a fresh job. Completion is always `complete_unreviewed`, not a quality pass.

## Integrity validation without repeated visual review

自动文件完整性与视觉审片分开：新帧须实际校验内容与目标尺寸，损坏/改变帧不可复用；已有解码结果仅在内容SHA、任务/渲染与验证器身份匹配时复用，跨调用仍核内容哈希，不能只信存在、大小或mtime。不重复解压同一已验证内容，也不把缓存或 `complete_unreviewed` 当画质批准。完成统计仍覆盖整项job，不能只看本次选帧就宣称整项完成。

合并同一场景的连续帧与已知风险状态为一次有意义的执行请求，避免反复单帧启动；保留实际锁、输入变化检查及失败历史。全任务内容扫描仍可能产生I/O，不宣称缓存消除了所有扫描或已证明生产加速。校验/哈希/解码耗时与状态更新、渲染写盘分开记录，涵盖续跑的启动扫描，实际优化以同质量测量为准。

正常速观看后按[风险复查](quality-acceptance.md#按风险复查与证据复用)定位疑点和完整修复周期；无需把整序列逐帧交给模型。最终编码的完整解码检查的是另一个产物，不能由原始帧通过代替；同一职责不为多项表格重复发起同样的终检。

## Rendering cost and scheduling

Apply the shared [local execution, minimal transfer and throughput policy](tool-routing.md#本地执行最少传输与吞吐) to working data, devices, concurrency and output review. Keep raw image sequences local; send only the evidence or changed assets actually needed by a remote step.

Use target-fps motion previews with inexpensive viewport/Workbench, EEVEE or low-cost Cycles settings suited to the actual scene. Validate engine-specific transparency, reflections, cutaways and fine fibers in the final engine before expanding. Keep the approved look, geometry and temporal continuity; do not lower samples blindly or hide defects with denoising. Persistent Data is enabled by default for Cycles but can be disabled for a demonstrated memory constraint. GPU setup and scene building occur once per worker.

Separate resource checks, scene building, frame-state updates and render/write time using attempt receipts. Record editing, reviews, queueing and packaging separately in the existing work log. These timings do not include all Blender startup or human/agent iteration time. Estimate remaining cost from representative measured frames and identify the scene/profile; do not claim a universal speedup from one warm-cache batch. For a before/after comparison, hold the scene, frame range, resolution, engine, device and quality settings constant; record startup/warm-cache conditions and compare decoded frame output as well as wall time. A synthetic startup/build-reuse test proves only that mechanism, not the speedup of an existing production that already builds once.

Flamenco is an optional scheduler, not a new production gate or a prerequisite for a single machine. Prefer the existing local execution path; add remote workers only for an authorized need or a measured benefit after transfer, synchronization and queue costs. Its [built-in Blender sequence job](https://flamenco.blender.org/usage/job-types/builtin/) accepts frame ranges/chunks and image output; use it directly for a verified baked `.blend`. For procedural scenes, a custom task must invoke the same global runner and declared driver. Preserve logs, job identity and final input/frame checks. The local runner serializes one output job; distribute independent shot jobs rather than concurrently writing the same directory. Multi-machine deployment additionally needs verified shared paths and storage-lock behavior; local tests do not establish distributed safety. Do not install services, copy the Skill into projects or reset existing tasks merely to adopt this workflow.

Learning references: Blender Studio [Playblast](https://studio.blender.org/tools/artist-guide/project_tools/usage-playblast), [Shot Assembly](https://studio.blender.org/tools/pipeline-overview/shot-production/shot-assembly), and [Pipeline Usage](https://studio.blender.org/tools/pipeline-overview/quick-start/usage). Borrow their separation of assets, shots, previews and edit; adopt extra infrastructure only when it solves a measured production need.
