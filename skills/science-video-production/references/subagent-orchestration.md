# Video subagents

Use specialized subagents when a video task has independent work or needs an independent review. The parent remains the director and integrator: it owns the user's scope, scientific explanation, shot order, current approvals, shared episode/shot records, final decisions and delivery. Small edits can stay with the parent. Six role definitions do not mean six agents must run on every task.

## Roles and ownership

| Role | Delegate when needed | Owned output |
| --- | --- | --- |
| [`video_researcher`](../agents/video_researcher.toml) | Scientific mechanism, engineering sequence or an analogy needs evidence | Source-backed mechanism/sequence notes and corrections to the assigned script section |
| [`video_visual_artist`](../agents/video_visual_artist.toml) | Assets, structural detail, composition, material or light need work | Assigned geometry/material/light modules or asset files; their interface and preview requests |
| [`video_animator`](../agents/video_animator.toml) | Process interaction, rigging, character performance or camera choreography is substantial | Assigned motion/rig modules, shared-state/event mapping, caches and preview requests |
| [`video_audio_editor`](../agents/video_audio_editor.toml) | Narration continuity, timing, subtitles, sound or editing needs dedicated work | Assigned narration/audio/edit/subtitle files and a render/mix execution request |
| [`video_producer_windows`](../agents/video_producer_windows.toml) | Local Blender/MoneyPrinterTurbo/model/FFmpeg execution needs a known owner | Actual job submission, monitoring/recovery, new media and technical receipts |
| [`video_reviewer`](../agents/video_reviewer.toml) | An independent explanation or audiovisual review is required | A new scoped review report tied to actual files, times/frames and perception capabilities |

The parent directs opening and transitions with the existing [explanation design](production-checkpoints.md) and [retention methods](viewer-retention-design.md). It does not outsource the whole film to unrelated per-shot agents. Roles reuse the [one global Skill](global-skill-installation.md), not their own copies of production standards.

## Shared assignment contract

Give each agent the current user request and corrections, task/shot IDs, stage and route, global Skill path, relevant existing inputs with versions, exact file/directory ownership, expected output and dependencies. State whether execution is authorized now or only a plan/module is requested. Include any pause, cancellation or prohibited version. Use the existing task message and work log; no extra episode schema or approval stage is needed.

All agents work in a shared workspace. They must preserve others' changes, stay within assigned ownership, and return an integration request for shared files. Give a shared `.blend`, timeline, episode record or output directory one writer at a time. A useful split is geometry/material modules versus animation modules with agreed object names, units, axes, frame range and callable interfaces. Parallel agents must not each rebuild the same scene or synthesize a separate narrator for every shot.

All roles read the current global `SKILL.md` and only the responsibility references needed for their task. The task's current instructions and approvals control the role's scope. Role configuration grants no new production, installation, upload or publication authorization. Inherit the host's tools, model and permissions; do not invent capabilities or weaken settings. No recursive delegation unless the parent explicitly requests it.

Return a concise result: assigned scope; changed/created files and versions; actual checks with evidence paths; known defects/unreviewed ranges; dependencies and next action. Keep large media, frame sequences, models and logs local. Send local paths and compact findings, selecting only needed review media for transfer. Local execution and human/model perception are separate capabilities; agent identity alone does not establish either.

## Scheduling and handoff

1. The parent settles the question, explanation chain and route. Research and asset feasibility can run independently; integrate their findings before locking the affected script/shot design.
2. Once the affected narrative and interfaces are stable, visual, motion and audio/edit work can proceed on separate files. Produce the existing G2/G3 material covering the actual difficult interaction, not just an easy still or turntable. Audio changes return to the editor and invalidate affected timing/口型 alignment.
3. A designated producer owns this work package's job queue. Authors may inspect assets and run scoped lightweight code checks locally; coordinate renders, synthesis, simulations and other heavy work through that queue. One queue owner may run multiple non-conflicting jobs when measured throughput and responsiveness support it. This is not a one-process limit, a GPU-utilization cap or permission to interfere with other tasks.
4. After an output exists, assign the required review to a fresh context. At G5, use separate `video_reviewer` instances for explanation and expression as required by [quality acceptance](quality-acceptance.md#自主解释与表达审查); the author or producer cannot supply their own independent pass. The parent integrates findings, sends bounded fixes to the responsible author, and requests rechecks of the affected context.

Usually start with two or three independent tasks, within the host's actual available slots. Role count, model concurrency and CPU/GPU job concurrency are different. Keep dependent work sequential, reuse an agent for follow-up fixes, and stop unnecessary fan-out. The parent propagates steering/cancellation to active agents and verifies actual job status before recovery; a timed-out message is not evidence that a render stopped. The parent's current authorized stage governs expansion and delivery.

## Independent review

Give a reviewer the intended audience/question, review scope, current exported media and required references. For first-view comprehension, omit the author's shot-by-shot explanation and self-review; collect time-coded findings before opening those materials for diagnosis. Use a fresh agent without production history when the host supports that separation. A fresh subagent is not a human audience test.

Require the reviewer to state whether it can actually inspect images, perceive continuous video and listen to audio. A checker, transcript, contact sheet or successful playback command does not prove normal-speed audiovisual viewing. Missing capability remains unreviewed and returns to the parent for an appropriate review route. Use the existing QA records and failure handling; role completion is not G3/G5 approval.

## Installation and invocation

The TOML files in this Skill's `agents/` directory are maintained custom-agent definitions, not separate Skills or `agents/openai.yaml` UI metadata. Codex discovers personal custom agents under `${CODEX_HOME}/agents`, or `~/.codex/agents` when unset. Keep one global Skill and sync only these six definitions to that personal agent directory. No project-specific Skill or agent installation is needed.

From the installed global Skill, with an existing Python 3.11+ interpreter:

```powershell
$skillRoot = '<absolute global Skill directory>'
python -X utf8 "$skillRoot/scripts/sync_video_agents.py" --check
python -X utf8 "$skillRoot/scripts/sync_video_agents.py" --install
```

`--check` is read-only. If named installed definitions differ, inspect the differences before deliberately updating them with `--install --replace-existing`. Replacements keep hash-named `.bak` copies; unrelated agents and `config.toml` are untouched. `--codex-home` can select an actual non-default Codex home. This helper installs only agent definitions, not the Skill, models, plugins or services.

After installation, verify which role names the current host exposes. A running chat may still expose its earlier role list; refresh/reopen the client or start a new chat when necessary. Do not call an unavailable custom role. If useful in the current session, the parent can give an available `worker`/`default` agent the corresponding definition's instructions and the same bounded assignment, explicitly describing this as a fallback, not a verified custom-role launch.

Natural-language invocation examples:

> Use the global science-video-production Skill. Coordinate the needed video subagents to make this manufacturing explanation. Start with video_researcher and video_visual_artist on separate outputs, then assign motion and audio work. Let video_producer_windows run the agreed local jobs and use fresh video_reviewer contexts for the required reviews.

> Fix only this shot's grasp/contact animation. Assign video_animator the animation module, keep the approved geometry and voice, then have video_producer_windows render the affected sample and video_reviewer inspect contact and timing.

When the host exposes `collaboration.spawn_agent`, the parent supplies `agent_type` using a listed role name, a unique `task_name`, and `message` containing the assignment above. For an independent review use `fork_turns="none"`; explicitly include the global Skill path and review inputs. Use `send_message` for steering a running agent, `followup_task` for continued work, and the available wait/status tools to collect results. Tool names and accepted arguments must follow the current host, not a copied invocation example. Users need only state the desired delegation in ordinary language.

These definitions omit model and reasoning overrides so the host's current defaults apply. They do not alter global concurrency or permission settings. See the [official custom-agent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents) for the client format and configuration semantics.
