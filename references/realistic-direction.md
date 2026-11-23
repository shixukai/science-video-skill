# Realistic direction: honest, clear, told, heard, paced and finished

Craft handbook for live-action-looking science films across local realistic routes, the [Google Flow route](google-flow-production.md), and verified user captures. Adds no extra gate or score; `scripts/realistic_audit.py` locates issues only. Store optional film-level decisions in `design.realistic_direction` and shot-level settings in `shotbook.realism.observation_level` and `time_scale`.

## Use this page by stage

| Stage | Decisions to make or check |
| --- | --- |
| G1 design | Truth register & `time_scale` per shot, observing stance, thread, scene coverage, shot jobs, camera package, light/sound plan |
| 0–5 s hook | Hook register, usable-core in-point (trimmed ramp), frame-0 event sound, natural first line |
| G2 rough cut | Coverage & shot jobs read cleanly, narration-led lengths, ambience continuity, retell probe |
| G3 sample | Hardest-event physical plausibility, screen direction, light/grade match, event-sound sync |
| G4/G5 final | Whole-film camera/light/grade consistency, cadence, zero digital silence, evidence colors, encode detail |

## Rigor: what a photoreal shot claims

Photoreal imagery makes silent claims about scale, speed, color, and physics that provenance disclosures (“AI生成，非实拍/观测”) do not excuse. Keep every silent claim honest.

### Assign a truth register to every shot

Set `shotbook.realism.observation_level` before prompting and mark register switches on first use:

| Register (`observation_level`) | Permitted look | First-use spoken cue (once) | Never |
| --- | --- | --- | --- |
| Verified capture (`naked_eye`/`instrument`, `authentic_recording`) | Real user footage with honest crop/speed/grade | Only speed/processing changes (“这段放慢了四倍。”) | Cut generated shots in as capture |
| Reconstruction (`naked_eye`) | Physically plausible real-time scale | Episode disclosure; name recreations of named events | Present recreation as archive record |
| Instrument view (`instrument`) | Real instrument markers (see below) | Name tool/speed once (“放慢约三十倍” / “热像仪里越亮越热”) | Impossible depth/color/lighting |
| Model (`not_observable`) | Non-photographic overlay, clean non-graphic 3D cutaway anchored to host, or explicit exception | “示意一下” / “如果我们能看见水分子……” | Photoreal glossy atoms/fields, or industrial parts standing in for organs |

**Instrument look markers:** high-speed (bright hard light, zero motion blur); time-lapse (locked camera, sweeping shadows); macro (razor-thin focus falloff); optical microscope (flat field, thin plane, real stains); SEM (grayscale, huge depth of field, zero bokeh); thermal (low res, surface emission — glass opaque, steel reflective); Schlieren (uniform field, refractive silhouette, no depth).

### Declare and verify time scale

Set `shotbook.realism.time_scale` (`real_time`, `slowed_xN`, `time_lapse_xN`, `edited_ellipsis`) and verify from actual frames (video models drift into dreamy slow motion):
- **Ballistics & fall (`t = √(2h/g)`):** `0.1 m ≈ 0.14 s`, `0.5 m ≈ 0.32 s`, `1 m ≈ 0.45 s` (flying droplets/sparks act as built-in clocks at `g/N²`).
- **Pendulum (`T = 2π√(L/g)`):** `0.25 m ≈ 1.0 s`, `1 m ≈ 2.0 s`.
- **Flames & sparks:** Pool-fire flicker `f ≈ 1.5/√D Hz` (`~5 Hz` at `0.1 m`); steady candle/blue hob cones should not sway like cloth; sparks/lightning are brief.
- **No speed-up frame-rate conform:** Never speed 24 fps clips to 30 fps (+25% breaks `real_time`). Regenerate or declare the true `slowed_xN` scale — never stretch clips to cover narration.

### Audit physical plausibility on the hardest event

Frame-step the key physical event at G3 and repair failures at the source (captions never fix broken physics):
- **Liquids:** crisp sheets/droplets, volume conserved, flat settling, matching viscosity (reject syrupy water or refilling glasses).
- **Steam/smoke/flames:** steam forms above hot water and vanishes into dry air; smoke persists; flames flicker at size-appropriate rates.
- **Light:** consistent shadow direction, parallax reflections, real glass refraction/caustics.
- **Rigid mechanics:** external gears counter-rotate, meshing teeth/contacts match (use controlled 3D for precision gearing).
- **Heat/phase & bodies:** boiling nucleates on hot surfaces; ice melts from surfaces; accurate finger/limb counts and joints.

### Keep numbers, instruments and readable surfaces honest

Keep generated dials, screens, and packaging defocused, blank, or out of frame (AI models hallucinate glyphs). Show real numbers solely from fact cards via narration or permitted text layers.

### Show safe procedure; frame hazards as hazards

Use safe grip/PPE whenever people handle heat, tools, chemicals, or electricity; depict hazards as consequences from safe framing with calm, complete safety guidance — never as casual how-tos.

### Protect evidence colors

Preserve fact-card colors (flames, indicators, spectra, tissues) through grade and encode; mention added dye once (“给水染了点颜色，方便看清”) and verify sampled regions before/after grading.

### Speak the register without slowing the film

Tuck the register cue into an already informative sentence once (“这一下只用了不到十分之一秒——我们把它放慢了大约三十倍。” / “分子看不见，这里先示意一下它们怎么排队。”) rather than burning a beat on a disclaimer.

## Accessibility: make the unfamiliar feel already known

### Show, then name, then use

Let the viewer see the event happen first → name the term once on screen (“水一下子变成了蒸汽，这叫汽化”) → reuse naturally later. Never introduce two new terms in one shot.

### Translate magnitudes into things viewers can picture

Convert abstract numbers into one everyday same-dimension comparison recorded in the fact card (e.g., 15 mL water → ~24–25 L steam at 100 °C: “一勺水变成的蒸汽，比一整桶桶装水还多。”). One clear comparison beats stacking two.

### One new idea per shot, one task per moment

Avoid piling a new referent, new term, camera move, and caption change onto one moment ([competing attention](viewer-retention-design.md#diagnose-competing-attention-before-making-the-edit-faster)).

### Let hands and familiar objects carry scale

Use hands, coins, utensils, or everyday containers for instant scale; prefer partial figures/hands over faces (less drift, zero uncanny valley) and lock recurring identity references.

### Analogy shots

Show only the valid physical correspondence and cut straight back to the real subject at matching orientation/action; keep biological models anchored to clean host anatomy rather than unrelated industrial hardware.

### Probe with a retell

Write one plain sentence viewers should be able to repeat after each section and check at G2 against actual footage ([understanding probe](quality-acceptance.md#probe-understanding-without-inventing-an-audience-test)).

## Narrative: build scenes, not shots

### Choose one observing stance

Pick ONE primary stance (`design.realistic_direction.stance`): **Observer** (locked-off, unfolding phenomenon), **Investigator** (hands-in-frame tests/comparisons), or **Follower** (tracks one object/signal across scales). Signal stance shifts visibly.

### Give every shot a job

Assign every shot a job (**orient**, **ask**, **evidence**, **turn**, **payoff**, or **return**). Cut jobless beauty shots unless serving a payoff/return hold.

### Cover a scene the way a crew would

Plan connected coverage sets (**establishing → action medium → mechanism insert → consequence → re-establish**) generated under one verbatim scene preamble; condition inserts on wide frames, hold the 180° line and screen direction, and match action phase across cuts.

### Carry one thread

Anchor opening, body, and ending to one recurring real object/place (`design.realistic_direction.thread`) so the ending [reframes the opening](viewer-retention-design.md#make-the-opening-image-understandable-by-the-ending).

## Shot cards and generation prompts

### Write a shot card before the prompt

Fix **job/register/time_scale**, **subject (size/material)**, **single start→end physical action**, **place**, **physical light sources**, **camera (height/lens/focus/support)**, **sound need**, and **exclusions** in `shotbook.origin` before prompting.

### Word prompts physically

- Replace AI-look buzzwords (`cinematic`, `8K`, `hyperrealistic`, `dramatic lighting`) with concrete light sources, lens equivalent, materials, and physics.
- Reuse one **verbatim scene preamble** per scene (fixed key light direction and color temperature); assign **one action per clip** with an explicit start state and named camera support (`locked-off on a tripod`, `slow 20 cm slider`).
- State exclusions positively in main prompts (“clear air above the pan”) since negative words often summon unwanted objects.

### Generate and select in the right order

Filter candidates strictly in order and stop at the first failure: **physics/science → identity & screen direction → phone-scale readability → texture → beauty**.

## Sound: make the picture's world audible

Layer sound under the single narration master ([voice reference](voice-reference.md#one-narration-master-and-one-shared-processing-chain)):
- **Room tone/ambience:** One continuous location bed carried across cuts with `150–400 ms` world crossfades — never digital zero between clips.
- **Event sounds & perspective:** Nearby contacts within 1 frame (`-45..+125 ms`) with mid/high transients audible on phone speakers; match proximity to shot scale; keep realistic acoustic lags (e.g. thunder).
- **Instrument views, baked audio & music:** Give slowed shots a consistent stretched/softened treatment; mute baked-in AI speech/music; keep optional music ducked/out under key evidence; use J/L-cuts across scene changes.

## Pacing: cut by what the viewer needs

### Use each clip's usable core

Step past every generated clip's conditioning-still ramp (`slow_ramp_head`) and cut out before late drift or tail freeze (`frozen_tail`), applying [hook trim](viral-appeal-and-packaging.md#win-the-first-two-seconds).

### Let narration and the shot's job set its length

Size each shot to `max(actual narration time, job minimum)` plus purposeful holds (orient `1–2 s`, action/ask `2–4 s`, comparison `change + ~1 s`, payoff hold `1.5–3 s`). Holds `> 1.6 s` keep subtle subject motion or reviewed observation holds ([subject motion](quality-acceptance.md#subject-motion-and-long-static-holds)). Never loop, freeze, or slow clips to cover narration overrun — split into coverage instead.

### Break the generator's cadence

Vary shot duration by narration/job and cut on motion rather than chaining equal-length raw clips (`uniform_cadence`).

### Choose cut points

- Group spatial worlds into coherent acts (`0.20–0.30 s` dissolves only across world boundaries; never ping-pong outdoor/studio single shots).
- Use `0.12–0.30 s` J/L-cuts inside breath valleys so sentences flow naturally across cuts.
- Bring visual referents on screen at or slightly before their spoken noun, cut *after* state changes complete, and leave `~0.2 s` landing room on clause-final Mandarin verbs.

## Texture: one camera, one light, one grade

### Fix a camera package

Lock one `design.realistic_direction.camera_package` per film (e.g., 24–35 mm wide, 50 mm medium, 85–100 mm macro; consistent focus depth, camera height, delivery fps/shutter, and support vocabulary).

### Motion blur and frame rate

Match timeline fps to native source cadence (e.g., `24 fps` CFR on pure Google Flow timelines; `30 fps` default otherwise) — never duplicate frames (`duplicate_frames_in_motion`) or play 24 fps faster at 30 fps.

### Move the camera as a real crew could

Locked-off for evidence/comparisons; slow slider/dolly for reveals; macro rail for detail; handheld strictly for human presence — zero floating AI orbits.

### Diagnose the AI-look signature

Fix waxy smoothing, HDR glow, crunchy oversharpening, boiling texture, fake uniform bokeh, and morphing details **at the source** (physical prompt, shorter clip, start-frame conditioning, gentler upscale) — never mask them with fake grain, blur, vignette, or glow ([art direction](art-direction.md#image-cleanliness-locate-the-source-of-snow-like-noise-first)).

### Keep light continuous

Keep key direction, daylight vs tungsten color temperatures, and shadows consistent across every shot in a location.

### Grade in a fixed order

1. **Conform** fps/resolution/Rec.709 → 2. **Normalize** white balance & exposure → 3. **Match within scene** (consistent hand skin & unclipped highlights) → 4. **Restrained bright look** ([bright style](visual-system.md#bright-style-and-premium-materials)) → 5. **Verify evidence colors unchanged** → 6. **Encode check** (`12–20 Mbps`, inspect gradients for banding).

### Resolution and upscaling

Generate natively as high as stable, upscale with restraint, and verify 100% + phone-size temporal stability ([HD output](quality-acceptance.md#hd-video-output)).

## Measure the edit before judging it

Screen exports locally via `scripts/realistic_audit.py`:

    python -X utf8 scripts/realistic_audit.py measure <export.mp4> --report <new-audit.json> [--shots <shots.json>] [--preview-dir <dir>] [--delivery-fps <fps>]

Flags to inspect in media: `frame_rate_mismatch`, `duplicate_frames_in_motion`, `uniform_cadence`, `slow_ramp_head`, `frozen_tail`, `grade_jump_in_scene` (requires `--shots` scene labels), `digital_silence` (`< -70 dBFS >= 0.15 s`), and `no_audio_stream`. Exit `0` clean / `1` review flags / `2` error (screening locator only, never acceptance).

## Diagnose by symptom

| Symptom | Root cause | First repair |
| --- | --- | --- |
| Pretty frames yet "looks fake" | Missing ambience/event sound or wrong `time_scale` | Layer room tone & synced contacts; verify physics speed |
| "Where are we?" after a cut | Missing establishing/re-establish or flipped 180° | Add coverage shot & maintain screen direction |
| "What am I looking at?" in close-up | Insert before orientation / term before visual | Orient first; show → name → use |
| Rushed or flat rhythm | Clip-length pacing, untrimmed ramps, zero holds | Size to narration/job, trim ramps, add payoff holds |
| Shots clash visually | No shared preamble/camera/light/grade | Lock scene preamble & match grade within scene |
| Expert objects to shot | Wrong register, physics, or shifted color | Fix register/source physics; never patch with disclaimer |

## Worked example: why does a drop of water make hot oil explode?

Compact template pattern (source all values before production):
- **Stance:** Investigator (hands comparing cold vs hot oil) · **Thread:** stainless pan & greens · **Camera:** counter height (35/50/100 mm macro, locked-off evidence) · **Light:** daylight window left (neutral), warm hood tungsten above · **Ambience:** kitchen room tone + hood hum.
- **Beat progression:** (1) `instrument / slowed_x30` macro Frame 0 mid-splash + stretched crack/sizzle: “热油里落进一滴水，油花一下子就溅了出来。” → (2) `naked_eye` wide hands drying greens → (3) `naked_eye` cold-oil control showing dyed water sinks (`1.00 > 0.92 g/mL`) → (4) `instrument / slowed_x30` hot-oil flash vaporization (~1,600× steam expansion: “一勺水变成的蒸汽，比一整桶桶装水还多。”) → (5) `naked_eye` calm safe oil-fire handling (turn off heat, slide lid from side, wait calmly until cool) → (6) clean return to drying greens before cooking.
