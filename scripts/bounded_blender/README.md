# Fixed bounded Blender executor

One PowerShell entry and one pinned C# guardian support two explicit local diagnostic capabilities. Candidate changes belong in independently reviewed JSON data and a closed, hash-bound scene package, not generated PowerShell/C# wrappers.

| executor | fixed Python entry | output |
| --- | --- | --- |
| `blender-local-three-keyframes` | `run_three_keyframes.py` | Frames 0, 33, 47; Animation=false |
| `blender-local-bounded-reveal` | `run_bounded_reveal.py` | Exactly frames 0..47 at 24 fps; Animation=true |

Both profiles require 960×540, 256 samples and the existing reviewed RTX5060Ti OptiX setting. The continuous scope adds StartFrame=0, EndFrame=47 and FPS=24, and requires all 48 ordered States and PNG paths. There is no arbitrary entry, executable command, Python expression, `--render-anim`, timeout or full-video mode. The Python scene entry is private, independently reviewed project code and must implement the selected profile using distinct source states. Repeating three stills is not a continuous result. This adapter does not replace applicable Skill, source-rights, design or audiovisual requirements.

## Configuration and immutable code

`run-blender-local.ps1` pins `blender-guardian.cs`. The fixed argv uses background/factory startup/disable-autoexec and exactly the selected Python entry plus actual Skill root and lock. The input manifest freezes the complete package, including entry and manifest. Unknown fields, extra files, escaping or reparse-point paths, old execution records and existing outputs fail closed. No user scene is opened or preferences saved.

Configuration fields are `schema_version`, `executor`, `candidate_id`, `candidate_root`, `input_manifest`, `skill_lock`, `skill_root`, `blender`, `service_evidence`, `expected_outputs`, `argv`, `prerequisite_receipts`, `scope`. The synthetic fixture in `test_blender_reuse.py` shows the static shape; `test_blender_continuous.py` shows the continuous extension.

The config or a precisely bounded materialization template must receive the existing independent review. A reviewed template may allow named digest slots to be populated locally from verified evidence while requiring every static value unchanged. Perform that local comparison and the real evidence checks in the same turn, then pass the concrete config digest as `-ReviewedConfigSHA256`. The digest binds bytes, not permission or reviewer identity. Do not create a new cloud round trip merely to sign a fresh PID, timestamp or lock hash. A static source/path/scope change is not an allowed dynamic substitution.

`prerequisite_receipts` preserves every applicable existing prerequisite, including previously required voice/ASR deliveries. Each receipt binds its exact path, digest and expected saved-file count. An empty array is valid only when no such prerequisite applies; it cannot waive an existing requirement.

Local digest substitution is limited to the exact slots authorized by the independent template review. It does not authorize starting, stopping or restarting a service, obtaining new access, changing source paths, dropping prerequisites or relaxing a failed check.

## Lifetime precision and admission

`Get-ExactUtcTicks` preserves DateTime and DateTimeOffset values directly. It parses only timezone-qualified ISO strings and rejects unspecified or ambiguous times. Never pass a typed DateTime through implicit string formatting: that can discard fractional seconds. Matching remains exact UTC ticks, with zero tolerance, alongside PID, parent, executable path/hash and listener checks. A one-tick mismatch still refuses execution.

The service record binds independently verified startup evidence for exactly two Python processes and localhost:8199. It is not a permanent PID allowlist. The wrapper reads current workers, lifetimes, hashes, listener and empty queue under the shared lock. Extra/missing/mismatching workers or failed observations refuse launch; it never stops services. Raw observations are saved before admission decisions.

## Limits and recovery

The C# native safety implementation retains its suspended, atomic Job assignment, process identity checks, no-breakaway policy, one-close cleanup, 295-second shutdown and 300-second limit, and private completion-port tree-exit evidence. Only one guardian invocation is permitted per process. A 48-frame capability does not promise completion within the cap.

The common lock is `parent(candidate_root)/local-gpu-execution.lock`. A durable `local-gpu-execution-uncertain.json` beside it is created before native invocation. Any existing marker blocks a new candidate. Only the matching owned nonce/config/root marker can be cleared after confirmed no-process or root+tree exit. Unknown state or wrapper death preserves the inhibit even when an OS lock is released. Never switch roots or delete markers to bypass uncertainty.

For an explicit known-no-start recovery, preserve the old claim, failure outcome and raw evidence. Verify the terminal no-start result and absence of native/output artifacts, and require the shared unknown marker to be absent without deleting it. A separately reviewed recovery identity in the same workspace may reuse immutable inputs and still-valid binding evidence. Its record must link the predecessor; it is not an automatic retry or a new first attempt disguised by erased logs.

## Targeted tests and evidence limits

- `python -I -S -B test_blender_reuse.py -v`: static contract mirror/source invariants.
- `python -I -S -B test_blender_continuous.py -v`: continuous delta and forbidden scope/argv/output cases.
- `pwsh -NoProfile -File test-blender-contract.ps1 -ReportPath <new-path>`: baseline config prefix/service fixtures and C# compile only.
- `pwsh -NoProfile -File test-blender-continuous-contract.ps1 -ReportPath <new-path>`: one valid continuous prefix, eight invalid changes and C# compile only.
- `pwsh -NoProfile -File test-utilization-telemetry.ps1 -CorePath run-blender-local.ps1 -ReportPath <new-path>`: extract and evaluate the actual resource condition AST for 11%, 12%, 100%, unavailable telemetry and retained capacity/shape refusals. No native/GPU execution.
- `pwsh -NoProfile -File test-lifetime-precision.ps1 -ReportPath <new-path>`: actual JSON-to-DateTime conversion, actual admission function, timezone/fractional ticks and negative identity cases. No live queries or compiler.

Run only tests affected by a change, plus necessary compatibility checks. Preserve original failures before fixing, use new receipt paths, and do not regenerate unrelated assets or repeat unchanged environment preparation. These test harnesses never invoke Guardian.Run, Blender, live CIM/HTTP/GPU tools or rendering. Synthetic checks, successful compilation and an individual bounded execution each prove only their observed scope, not general end-to-end speedup, audiovisual acceptance, or publication authorization.

## GPU utilization telemetry

Aggregate GPU utilization is recorded only. There is no utilization admission ceiling, and 11% or 12% does not by itself refuse a run. Existing VRAM/RAM/disk capacity checks, exact process/service/queue identity, shared locking, unknown inhibition, one-shot claim and Job terminal verification remain unchanged. Historical failed receipts are immutable and do not define the current admission rule.
