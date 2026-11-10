<a id="一个全局-skill项目只保存制作数据"></a>
# One global Skill; projects retain production data only

Keep exactly one executable global `science-video-production` installation, identified by its actual invocation location. Use the current host's supported installation mechanism. Local Codex defaults to `${CODEX_HOME}/skills`, or `.codex/skills` under the user home when unset. A host-managed personal Skill uses its official personal-skills checkout; identify it by the Skill frontmatter name and verify the checkout root and official remote. The locator supports the runtime home's `skills/remote-skills` and the managed cloud host's `/root/.codex/skills/remote-skills`, excluding disabled entries under `uninstalled`. These are alternative installation locations, not permission for a second copy. Locate by SKILL `name`, not version guesses from legacy folders. Do not install, copy or modify this Skill inside projects, or create `rules/<skill>`, `skill-snapshot-*`, project `.agents/skills` or `.codex/skills` copies.

At startup/continuation read the global entrypoint and route references, checking old projects against latest user requirements; old locks prove historical execution, not current rules.

[Video subagents](subagent-orchestration.md#installation-and-invocation) use this same global entrypoint. The six maintained TOML definitions sync only to personal Codex `agents` for host discovery; they are not separate Skills or project installs. Role updates do not automatically restart work/change running contexts. A read-only runtime home is not a reason to change security permissions or disguise maintenance source as an installation. Use the official personal-Skill workflow where supported and report any uncompleted role installation separately; the existing fallback invocation remains available. Current conversation/catalog caches are not proof that a saved installation has or has not refreshed.

<a id="项目保存什么"></a>
## What projects retain

- Keep scripts, shots/audio/subtitles, assets, adapters, provenance, actual run/review records and a write-once rule-file hash lock. Call Skill scripts globally; a lock is a digest record, not an executable Skill.
- Project-specific reference images, instantiated templates and concrete supporting assets may be stored with provenance/hashes; do not copy complete rules, checkers/defaults. Temporary maintenance/test copies are isolated validation only and removed afterward, not project production entrypoints.
- Global updates do not automatically validate old locks. After current jobs finish, compare changes, write a new migration record for affected design/execution/review and unreviewed scope, and generate applicable current locks. Never rewrite receipts, backdate passes, automatically render or revive canceled projects.
- Never unpack historical installs to bypass new rules. Read archived originals/hashes only for historical tracing; they are not production entrypoints.

<a id="清理已有副本"></a>
## Remove existing copies

List actual directories first and distinguish full installs, partial backups, historical entrypoint text and maintenance source. Handle this Skill only, preserving other Skills, user media and neighboring evidence. For complete copies first hash every file, archive/compress and verify readback, then remove. Historical entry text may be archived/renamed clearly as non-entrypoint evidence with original contents/mapping retained.

Legacy paths needing compatibility may link to the single global directory, without independent files; resolved paths must equal the global installation. Old hashes differing from global still require migration; links do not revive old approvals. GitHub maintenance sources live outside projects, only for edits/checks/sync, never as another production install or direct production entrypoint.

Rescan known project roots after cleanup and report coverage, unread directories, independent copy count and compatibility links. Failed scans do not prove absence. Trace creators of new copies rather than repeatedly deleting files. Archives serve recovery/evidence only; public repositories exclude private project paths, feedback and production evidence.

<a id="可执行检查"></a>
## Executable checks

`scripts/global_skill.py` performs read-only location/scanning:

    python -X utf8 <global-skill-root>/scripts/global_skill.py --scan <project-directory> <another-project-directory>

The `render_gate.py lock/run` CLI checks unique-global installation before writing locks/invoking project executors, rejecting project copies/repository source. Offline structural/unit tests are not production runs; use isolated temporary directories and clean them.
