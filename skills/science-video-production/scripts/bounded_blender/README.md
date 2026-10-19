# Fixed Blender local diagnostic adapter

This is a deliberately narrow implementation, not a general renderer or a new production gate. It supports the existing three-frame profile only: frames 0/33/47, 960×540, 256 samples, the reviewed RTX5060Ti OptiX configuration, a single background factory-startup Blender process, and the existing 295-second shutdown / 300-second native limit. It does not authorize a new render, change a Skill quality requirement, or accept a video.

## What stays fixed

`run-blender-local.ps1` and `blender-guardian.cs` are versioned execution code. Candidate changes are JSON data, not textual substitution or generated PowerShell/C#. The C# source hash is pinned in the PowerShell core. The native Job, suspended atomic assignment, private completion port, identity check, one-close cleanup, no-breakaway semantics and bounded tree observation retain their previous implementation. One invocation per PowerShell process is mandatory; restart is not authorization to repeat a candidate.

The local configuration and its exact SHA256 must undergo the existing independent candidate review. Supply that externally reviewed digest as `-ReviewedConfigSHA256`; computing the current file hash yourself is not independent approval. Review includes the frozen Python entry and all imported project code, executable provenance, actual Skill lock, stage authorization, startup evidence, prerequisite receipts, expected output and fresh candidate destination. A SHA digest proves binding, not reviewer identity or permission. Do not use synthetic fixtures as approval records.

## Data interface

See `fixture()` in `test_blender_reuse.py` for a synthetic configuration. Fields: `schema_version`, `executor`, `candidate_id`, `candidate_root`, `input_manifest`, `skill_lock`, `skill_root`, `blender`, `service_evidence`, `expected_outputs`, `argv`, `prerequisite_receipts`, `scope`. Unknown fields are rejected. Fixed argv must match exactly; no shell, arbitrary command, Python expression, alternate entry, animation render flag, output path or timeout can be supplied.

The input manifest is `{schema_version: 1, files: [{path, bytes, sha256}]}`. It freezes the complete package, including `manifest.json` and `run_three_keyframes.py`. Relative paths cannot escape roots or cross reparse points. Package extras, existing output and prior execution records fail closed. The Python entry remains responsible for the current Skill render-entry checks; this adapter does not replace them.

`service_evidence` binds an independently checked, current startup record. Its shape is `{schema_version: 1, startup_verified: true, workers: [{PID, Parent, Exe, Created, SHA}, ...], listener: {LocalAddress, LocalPort, OwningProcess}}`. Exactly two Python service processes, their parent relationship and localhost:8199 listener are supported. The recorded values are not a permanent PID allowance: every invocation reads live process lifetimes/binary hashes/listener/empty queue under the shared lock. Any missing, unreadable, extra or mismatching worker refuses launch. A restarted service requires new startup evidence and configuration review, not a source edit.

`prerequisite_receipts` contains `{path, sha256, count}` for existing task prerequisites. Candidate review must preserve all applicable prerequisites, including already required voice/ASR deliveries. An empty array means no such prerequisite applies to that candidate; it cannot waive an existing requirement.

## Failure and recovery

Raw service and resource observations are persisted before admission decisions, including failed resource reads. The shared lock is `parent(candidate_root)/local-gpu-execution.lock`. Both engine adapters must use the same workspace and lock location. Before native invocation, a CreateNew `local-gpu-execution-uncertain.json` is written beside that lock. Any existing marker blocks a fresh execution. Only this invocation's nonce/config/root-matching marker may be cleared after confirmed no-process or root+tree exit; uncertainty or wrapper death preserves it even when the OS lock is released. No service is stopped and no arbitrary PID/name kill is performed. Reconciliation first reads actual evidence; it never means erase the marker and retry blindly.

## Tests and limits

`python test_blender_reuse.py -v` runs synthetic offline configuration-mirror and source-invariant checks. These are not execution of PowerShell or Windows APIs. Private historical replay can verify original archive hashes against different configs without publishing projects.

`pwsh -NoProfile -File test-blender-contract.ps1 -ReportPath <new-json-path>` is a scratch-only test. It parses the actual launcher, evaluates only the config-validation prefix ending before `$queueLock`, exercises the actual admission function on fake objects, and compiles C# in memory without calling Guardian.Run. It does not read live services, call HTTP/CIM/GPU tools, invoke native Job operations, start Blender, or render. Temporary synthetic files are retained for diagnosis. Run in a fresh PowerShell process; do not run the full launcher as a test.

Cloud author environment had no pwsh/C# compiler. At author handoff, Windows parsing/compilation and actual Job/runtime acceptance were NOT verified. Even a successful contract/compile test will not prove Job lifecycle execution, performance improvement, or audiovisual quality. Rendering remains paused until the user-authorized stage is resumed and all applicable requirements hold.
