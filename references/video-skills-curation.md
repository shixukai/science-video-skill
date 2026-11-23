# External video Skills: adopted methods and licenses

Select needed capabilities through [tool routing](tool-routing.md) and execute under [preparation/installation](tool-routing.md#preparation-and-installation-before-calls). Frozen commits, read files, license evidence and candidate state live in the [external-source index](../indexes/external-skills.json); this page lists active external tools and limits only.

## Active external tools and references

Read the table only for capabilities actually missing in this shot; the source index holds fixed commits and license evidence.

| Source | Adoption and license limits |
| --- | --- |
| [FFmpeg Skill](https://github.com/shixukai/science-video-skill) (`ffmpeg-skill`, see source index) | Local FFmpeg edit, mix, loudness, subtitle and transcode workflows. Check local codecs/filters and preserve lossless sources. |
| [vork](https://github.com/voyager-so/vork) (`vork-engine`) | Local Vulkan/Metal headless 3D/VFX engine [automatically selected by the agent](tool-routing.md#vork-execution) for suitable full 3D episodes, 3D shots or supporting field/simulation/shader/plate passes. Source-available `vork Preview License` (version-scoped commercial media permitted at v0.5.1; optional `integrations/blender` is GPL-3.0-or-later; never copy modified binaries, run `vork cloud` unauthorized or reuse example credits as filler). |
| [google-colab-cli](https://github.com/googlecolab/google-colab-cli) | Official Google Colab CLI (`colab`, Apache-2.0; Google Colab Terms of Service govern rented runtimes) for [authorized headless Colab GPU provisioning, execution, minimal transfer and teardown](tool-routing.md#colab-cli-and-remote-gpu-integration). Upstream README declares Linux/macOS support (verify native Windows or WSL2 readiness via `scripts/colab_cli.py preflight`, else fall back to authenticated HTTPS tunnel / local GPU); never invoke interactive `repl`/`auth`/`drivemount`/bare `ssh` from non-TTY agents, and always `colab stop` when done. |
| [Manim Community](https://github.com/ManimCommunity/manim) | Official API for geometry, quantities and animated charts in existing/approved 2D overlays. Engine MIT; redesign defaults for this episode. |
| [Official Remotion Skills](https://github.com/remotion-dev/skills) | Frame-driven animation, captions/export in existing React. No standalone LICENSE found at inspected commit: do not copy text; verify engine runtime rights separately. |
| [HyperFrames](https://github.com/heygen-com/hyperframes) | HTML/CSS/GSAP video rendering for existing HTML graphic projects. Set `HYPERFRAMES_NO_TELEMETRY=1`; verify dependencies and rights before use. |

## Engine, service, text transfer and costs

Check referenced text, actual engines/dependencies, assets/fonts/audio and cloud terms separately. External defaults never override the series voice, primary routes, bandwidth conservation or actual audiovisual acceptance.

- Before Remotion adoption check [current runtime rights](https://www.remotion.dev/docs/license/faq) against organization/use, not community Skill licenses.
- For online ASR/TTS, images/video and asset services, verify destination, actual uploads, existing authorization and pricing. Reading docs uploads no project scripts; installing Skills authorizes neither transfer nor purchases.
- Source verification is never current execution or audiovisual review.
