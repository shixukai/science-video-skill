# Reusable Blender sequence execution

Use this for local intermediate 3D frames after choosing the scene and frame range. It does not approve science, appearance, narration or delivery. Assemble audiovisual roughcuts/samples/finals through the existing [phase entry](production-checkpoints.md#开工锁定与真实渲染入口). Existing task-specific launch requirements still apply; the generic runner is not a replacement for a required bounded executor or an unresolved task.

## Prepare one job per shot or coherent scene

Read the [production sequence](engineering-blender.md#有界试制与可靠复用) first. Reuse linked/appended assets and a stable scene driver. Keep shot parameters in JSON rather than generating a new launcher for each revision. Save project-specific files in the project; call [blender_batch.py](../scripts/blender_batch.py) from the unique global Skill.

Start with [blender-job-template.json](../assets/blender-job-template.json). Fill the actual device name, existing Blender executable and driver path; blank entries are deliberately not runnable. Paths resolve relative to the spec file. `inputs` lists all external assets, libraries, fonts, textures, imported project helpers and caches actually read. The runner hashes them, the Blender binary and its own executable script, and checks loaded external Blender resources; this does not discover arbitrary files a custom driver opens later. Declare those too.

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

## Device, ownership and recovery

Cycles jobs explicitly select `CPU` or `GPU`; GPU jobs select the actual backend and exact enumerated device name, with `device_id` when names are ambiguous. No implicit CPU fallback or utilization ceiling is implemented. Keep applicable host/user limits and existing project queue, ownership, capacity and budget checks. An optional `resource_check` Python file can expose `check(spec) -> {"ok": bool, ...raw observations/reason...}` to reuse an existing check immediately before building. Include that module and its dependencies in `inputs`. A false result is recorded and stops execution; the hook cannot invent its own policy threshold. Consult the [current-evidence rule](production-checkpoints.md#静态证据条件复用与动态新鲜检查).

The Blender process holds an OS lock for its output job. If its launcher disconnects, the worker still owns the lock. Do not delete the lock file to force a retry. Inspect the actual process and `state.json`; a failed or interrupted job can resume only once the lock is available and input hashes match. An existing output directory without the matching `job.json` is never adopted.

Each frame has a hash, source-job signature, actual settings, optional anchor metadata and measured state/render-write times. Resume reuses only matching files/receipts; incomplete or corrupt job-owned files are preserved under `invalid/` before replacement. Completed attempts remain in `attempts/`. If source changes during execution, the attempt is marked `inputs_changed`; restored source bytes do not retroactively validate those frames. Keep that output and prepare a fresh job. Completion is always `complete_unreviewed`, not a quality pass.

## Rendering cost and scheduling

Use target-fps motion previews with inexpensive viewport/Workbench, EEVEE or low-cost Cycles settings suited to the actual scene. Validate engine-specific transparency, reflections, cutaways and fine fibers in the final engine before expanding. Keep the approved look, geometry and temporal continuity; do not lower samples blindly or hide defects with denoising. Persistent Data is enabled by default for Cycles but can be disabled for a demonstrated memory constraint. GPU setup and scene building occur once per worker.

Separate resource checks, scene building, frame-state updates and render/write time using attempt receipts. Record editing, reviews, queueing and packaging separately in the existing work log. These timings do not include all Blender startup or human/agent iteration time. Estimate remaining cost from representative measured frames and identify the scene/profile; do not claim a universal speedup from one warm-cache batch.

Flamenco is an optional scheduler, not a new production gate or a prerequisite for a single machine. Its [built-in Blender sequence job](https://flamenco.blender.org/usage/job-types/builtin/) accepts frame ranges/chunks and image output; use it directly for a verified baked `.blend`. For procedural scenes, a custom task must invoke the same global runner and declared driver. Preserve logs, job identity and final input/frame checks. The local runner serializes one output job; distribute independent shot jobs rather than concurrently writing the same directory. Multi-machine deployment additionally needs verified shared paths and storage-lock behavior; local tests do not establish distributed safety. Do not install services, copy the Skill into projects or reset existing tasks merely to adopt this workflow.

Learning references: Blender Studio [Playblast](https://studio.blender.org/tools/artist-guide/project_tools/usage-playblast), [Shot Assembly](https://studio.blender.org/tools/pipeline-overview/shot-production/shot-assembly), and [Pipeline Usage](https://studio.blender.org/tools/pipeline-overview/quick-start/usage). Borrow their separation of assets, shots, previews and edit; adopt extra infrastructure only when it solves a measured production need.
