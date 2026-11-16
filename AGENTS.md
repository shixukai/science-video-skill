# Maintain the installed Skill directly

This repository root is the installed `science-video-production` Skill and its only editing location. Keep `SKILL.md`, its resources and `.git` together here. Follow [the installation and maintenance contract](references/global-skill-installation.md#maintain-the-installed-git-working-tree).

- Inspect Git status and fetch `origin` before maintenance. Reconcile local changes with `origin/main` in place; preserve unrelated work.
- Edit, validate, commit and push here within the user's authorized scope. Do not create temporary modification directories, separate clones, worktrees, staged source copies or version-suffixed installs.
- Keep production projects, media, private evidence and credentials outside this repository. Tests use memory-backed rule mutations or self-cleaning synthetic data, not copies of the Skill.
- After changing responsibility bodies, run `python -X utf8 scripts/rebuild_standard_index.py` and `python -X utf8 scripts/check_reference_system.py .`. Run the relevant regression tests and report their actual results.

Maintain instructions in English; preserve each commissioned language for narration, captions and examples. Updating rules does not authorize video generation or publication.
