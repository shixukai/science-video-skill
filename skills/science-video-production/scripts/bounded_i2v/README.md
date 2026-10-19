# Bounded reusable I2V runner

This is a narrowly scoped replacement candidate for the formerly per-shot-hardcoded **Windows Wan2.2 I2V** entry. It is not the Blender PowerShell/C# guardian, a general render framework, a service installer, or a quality gate. Blender data-binding decoupling remains separate work. Actual video generation remains subject to the user's current authorization and task pause/stop instructions.

## Fixed capability and invariant core

Deploy `runner.py`, `i2v_core.py`, and `rain_resource_collector.py` once. Review and hash these files once per actual code/dependency/permission change. Each candidate uses a separate immutable JSON config plus an incremental independent review bound to the exact config SHA and the same core hash map. No candidate/root/PID/prompt literals are edited in Python. No startup, shutdown, install, proxy, redirect, cancellation, or permission expansion is provided.

This version deliberately supports only: Windows, an existing reviewed service at 127.0.0.1:8199, reviewed Wan graph classes, original conditioning PNG, 832×480, 49 frames, 24fps, batch1, seed20261018, 20 steps, cfg5, uni_pc/simple, denoise1, shift8, mp4/h264, silent internal testing. Its existing conservative admission thresholds remain GPU utilization≤10%, four samples spanning≥6s, RAM≥16GiB, free VRAM≥12GiB, free disk≥2GiB; 600s admission/observation budget is not GPU termination. These limits are not new defaults for other models, topics or Blender.

Actual Skill 1.6.5 or 1.6.6 must match the exact referenced installed-file manifest; arbitrary versions do not pass. Changing tools, weights, loader roots, interpreter, service launch configuration or reviewed scope requires corresponding fresh checks and affected review. This implementation still rehashes actual model/tool/Skill bytes where the inherited entry requires it. It removes code rewrites and cross-cloud holder waiting, **not** integrity checks, and makes no measured speed claim.

## Configuration and independent review

`candidate.schema.json` documents shape; `runner.validate_config` is the executable fail-closed validator. The public fixtures are synthetic and intentionally cannot authorize actual execution. A deployable config must reference actual readable files and exact hashes in its bindings: three models/loader resolution and model provenance; condition PNG; source API and canonical graph SHA; ffprobe; startup/launch/identity evidence; authorization; collector/interpreter; current applicable Skill manifest; design and silent scope. Reuse unchanged pinned static references instead of copying or downloading evidence for every candidate. The gate verifies them against actual local files.

The canonical candidate root is `task_root/i2v-candidates/candidate_id`. A common-lock-sibling `local-gpu-execution-uncertain.json` is created before possible work and retained across an abrupt holder exit/unknown state. Both compatible engines refuse any existing marker; only the current matching owner may clear it after known-noPOST or verified terminal state. A task-global `i2v-attempt-ledger/candidate_id.json` prevents copying or moving a candidate folder to reset submission. A fresh reviewed candidate ID is not permission to retry an uncertain prior POST. `lineage.kind` is `new_candidate`, `completed_parent`, or `known_no_post_recovery`; non-new modes bind actual preserved evidence and completed runner-work/lock-release receipts. A successful parent's visual acceptance is not inferred from technical success.

A review JSON must contain `status: pass`, `independent_of_executor: true`, `config_sha256`, and `core_sha256` for the three code files. The authorized launch supplies the trusted SHA of that review and config. The runner never manufactures its own independent pass.

Platform-independent inspection:

    python -I -S -B runner.py --dry-run --config candidate.json --config-sha256 <sha>

Dry-run checks configuration only and outputs the core hash map. It does not check live Windows identity/resources, claim independent review, or submit. The tests additionally check graph capability and unchanged hashes across two distinct configs.

Authorized Windows execution with the already reviewed interpreter:

    python.exe -I -S -B -X utf8 runner.py --config candidate.json --config-sha256 <sha> --review review.json --review-sha256 <sha>

Before runtime entry, independently review actual core plus immutable candidate/config and source/design scope, including the actual original conditioning image provenance/rights, not just its hash. Missing provenance or design review does not authorize running. This narrow entry replaces only an already-authorized 49-frame silent internal chain; it does not replace origin_guard, render_gate, G3 or their applicable stage requirements, and must not be used to bypass them. At runtime, the code owns the existing task common lock, records its real holder identity, and launches the separately reviewed read-only collector in an independent child process. That collector independently verifies actual parent PID/lifetime, lock metadata/byte lock, common-lock sharing violation, service lifetime chain/listener, empty queue and fresh resource samples. The gate independently validates returned nonce, times, identity and observations before the sole POST. **No cross-cloud hand-written binding_review or post-launch wait remains.** This is process-independent observation under reviewed code, not an independent human visual or scientific review.

## Recovery and publication boundary

Raw command results, partial sampling and failures are flushed before admission decisions. `known_no_post` is distinct from `unknown_do_not_retry`. Unknown/accepted unfinished service work retains the common lock and is read-only reconciled; it is never resubmitted or declared stopped by timeout. Do not terminate its holder and treat that as completion.

Minimum attempt, accepted task ID, terminal history and media verification are saved before optional backup. `archive-pending.json` is a continuation pointer, not proof of backup. No upload/download/backup is on the execution critical path. A `runner-completion.json` is written only after verified common-lock closure; it explicitly is **not** an OS process-exit receipt. Matching partially written terminal records can be resumed without overwriting them. Actual output still needs continuous viewing and applicable independent quality review; silent technical output is not delivery, G3 or publication approval.

## Tests and remaining validation

    python -B -m unittest discover -s tests -v

Tests use only synthetic fixtures and mocked collector/network boundaries plus actual subprocess CLI dry-runs. They cover resource refusal retaining samples, known-noPOST reservation, unknown POST no retry, config/root/identity/threshold drift, incremental-recovery writes and identical core hashes across configs. They do not exercise Win32 sharing locks, CIM/PowerShell or live GPU. Those platform behaviors are inherited but newly configured code needs a permitted Windows acceptance test before adoption; this candidate must not silently replace an active production chain.

The current Skill already describes immutable executors, static evidence reuse, fresh dynamic checks and minimum recovery in `production-checkpoints.md`. This implementation makes that option concrete for the stated I2V boundary; it does not add a new requirement that every video use this runner.
