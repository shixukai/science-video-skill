# One global Skill; projects retain production data only

Keep exactly one executable global `science-video-production` installation, identified by its actual invocation location. Use the current host's supported installation mechanism. Local Codex defaults to `${CODEX_HOME}/skills`, or `.codex/skills` under the user home when unset. A host-managed personal Skill uses its official personal-skills checkout; identify it by the Skill frontmatter name and verify the checkout root and official remote. The locator supports the runtime home's `skills/remote-skills` and the managed cloud host's `/root/.codex/skills/remote-skills`, excluding disabled entries under `uninstalled`. These are alternative installation locations, not permission for a second copy. Locate by SKILL `name`, not version guesses from legacy folders. Do not install, copy or modify this Skill inside projects, or create `rules/<skill>`, `skill-snapshot-*`, project `.agents/skills` or `.codex/skills` copies.

At startup/continuation read the global entrypoint and route references, checking old projects against latest user requirements; old locks prove historical execution, not current rules.

[Video subagents](subagent-orchestration.md#installation-and-invocation) use this same global entrypoint. The six maintained TOML definitions sync only to personal Codex `agents` for host discovery; they are not separate Skills or project installs. Role updates do not automatically restart work/change running contexts. A read-only runtime home is not a reason to change security permissions or disguise maintenance source as an installation. Use the official personal-Skill workflow where supported and report any uncompleted role installation separately; the existing fallback invocation remains available. Current conversation/catalog caches are not proof that a saved installation has or has not refreshed.

## Maintain the installed Git working tree

When the user explicitly commissions assistant-local maintenance, use one assistant-local Git working tree instead of requiring access to their computer. Inspect and preserve existing local work before obtaining the current remote. Do not create parallel candidate copies or claim that this source checkout is installed on another host. Run offline checks here; production still requires the actual unique global installation below. Report source commit, push and installation states separately. This explicit maintenance scope takes precedence over the installed-location default in the following paragraphs.

For this local Codex installation, keep the Skill at `${CODEX_HOME}/skills/science-video-production` (default `~/.codex/skills/science-video-production`) with `SKILL.md` and `.git` at its root. `origin` is `https://github.com/shixukai/science-video-skill.git`, and `main` tracks `origin/main`. This directory is the single editing and execution location; there is no version-suffixed installation or separate maintenance repository. The official managed-host alternative above retains its host-required layout.

Before editing, inspect status and fetch the remote in this directory. Reconcile local and remote changes without overwriting either, edit the actual Skill files, rebuild the navigation index when its bodies change, and run relevant checks. Commit and push within the user's authorized scope; report the exact commit and whether the working tree and upstream agree. Do not create temporary modification directories, staged source copies, candidate repositories, extra clones or Git worktrees. Git history retains committed versions. Test data is not a place to edit or install the Skill.

## What projects retain

- Keep scripts, shots/audio/subtitles, assets, adapters, provenance, actual run/review records and a write-once rule-file hash lock. Call Skill scripts globally; a lock is a digest record, not an executable Skill.
- Project-specific reference images, instantiated templates and concrete supporting assets may be stored with provenance/hashes; do not copy complete rules, checkers/defaults. Keep maintenance edits in the installed Git tree. Tests use in-memory mutations or small synthetic data fixtures, without copying the installed Skill.
- Global updates do not automatically validate old locks. After current jobs finish, compare changes, write a new migration record for affected design/execution/review and unreviewed scope, and generate applicable current locks. Never rewrite receipts, backdate passes, automatically render or revive canceled projects.
- Never unpack historical installs to bypass new rules. Read archived originals/hashes only for historical tracing; they are not production entrypoints.

## Remove existing copies

List actual directories first and distinguish full installs, partial backups, historical entrypoint text and maintenance source. Handle this Skill only, preserving other Skills, user media and neighboring evidence. Before removing redundant copies, reconcile their changes with the installed tree and remote history. Verify the retained version and successful push before deleting obsolete editing directories; do not create another temporary source copy or backup directory for this cleanup. Historical entry text may be archived/renamed clearly as non-entrypoint evidence with original contents/mapping retained.

Legacy paths needing compatibility may link to the single global directory, without independent files; resolved paths must equal the global installation. Old hashes differing from global still require migration; links do not revive old approvals. The canonical installed directory itself is the Git working tree. Separate GitHub maintenance clones and temporary editing trees are not retained.

Rescan known project roots after cleanup and report coverage, unread directories, independent copy count and compatibility links. Failed scans do not prove absence. Trace creators of new copies rather than repeatedly deleting files. Archives serve recovery/evidence only; public repositories exclude private project paths, feedback and production evidence.

## Executable checks

`scripts/global_skill.py` performs read-only location/scanning:

    python -X utf8 <global-skill-root>/scripts/global_skill.py --scan <project-directory> <another-project-directory>

The `render_gate.py lock/run` CLI checks unique-global installation before writing locks/invoking project executors, rejecting project copies/repository source. Offline structural/unit tests are not production runs. Use in-memory overlays for rule mutations; synthetic episode fixtures may be short-lived and cleaned automatically, but must not become Skill editing directories or full Skill copies.
