# 3D Animation Production: High-Poly Industrial Blender & Visual-First Craft (v2.0)

3D science videos use **Blender** (default for mechanical CAD, cutaways, non-rigid deformations, and `.blend` rigs) or agent-selected **[`vork`](tool-routing.md#vork-execution)** (for invisible fields, waves, Slang GPU simulations, or custom shaders). **ALL Blender Cycles rendering—lookdev stills, preflight boards, hook samples, and full sequences—defaults strictly to Google Colab GPU** (`scripts/colab_cli.py`); local Blender is restricted to headless `.blend` authoring, physics baking, and `audit-blend --strict`.

## Five Iron Laws of Controlled 3D (Zero Exceptions)

1. **Silent Visual Causality First (Video, Not Audiobook):** Design the continuous visual proof BEFORE writing or locking narration. Every key mechanism beat must read clearly **100% muted** — if viewers need voiceover to guess what is happening, redesign the scene and animation, not the script.
2. **Real-World Scene Persistence (Zero Void / Cardboard Backdrops):** Build ONE complete, bright, lived-in real-world environment + real host machine/vehicle (`camera_strength >= 0.70` natural 4K HDRI + architecture + grounded everyday/industrial props). **NEVER hide the real environment (`env.hide_render = True`) and substitute a flat gray/black backdrop (`Stage_MacroBackdrop`) during body cutaways.** Keep cutaways mounted **in-situ inside the real host** with natural shallow-DOF bokeh depth behind them.
3. **True High-Poly Industrial Silhouettes (Zero Primitive Box Substitutes):** Inspect local and open-licensed high-poly CAD/glTF models FIRST (e.g., full vehicles, furniture, appliances, tools) and verify real-world engineering silhouettes before writing geometry code. **NEVER build curved, cast, or sculpted industrial hardware out of rectangular boxes or plain cylinders** (e.g., an automotive brake caliper is a ~65° curved arc-swept cast body hugging the disc with bridge ribs, pad window, mounting ears, and braided hose — NEVER a red brick!).
4. **Causal Context-Preserving Framing (Zero Blind Macro Slivers):** Every explanatory shot keeps **driver/actuator + active mechanism + physical result + recognizable host anchor** readable together in the SAME frame (`28–60 mm` storytelling lenses or translucent/cutaway outer shells). **NEVER zoom `80–105 mm` into a 2 cm material corner** where the viewer loses where the part sits on the machine or what drives it.
5. **Zero Legacy Garbage Template Reuse:** Never copy old failed episode scripts, dark-void lighting presets (`camera_strength <= 0.4`), `Stage_MacroBackdrop` cardboard planes, or `create_box` hero builders from historical batches. Reuse ONLY verified high-poly CAD/glTF models and clean PBR/CAD math utilities.

## Scope of asset-only tasks

For model, static-preview, or cataloging commissions alone, deliver the editable asset, structure/contact verification, and archive records without inventing narration, shot plans, or G3. Video commissions carry full G1–G5 audiovisual obligations.

## High-poly industrial modeling standard for Colab 3D

Default visual benchmark: **Apple Keynote hardware teardown / Branch Education / Animagraffs precision mechanical cinema (`high_poly_industrial_3d`, modeling profile `high_poly_industrial_v1`)** — full real-world host integration, accurate curved/cast/machined silhouettes, dual-wall cutaways, authentic fasteners/hoses/brackets, and tactile PBR finish separation.

1. **Asset-first real silhouettes & high-poly density (zero toy primitives):**
   - Scan local `cc0_models` (`CarConcept.glb`, Poly Haven glTFs) and open-licensed CAD/glTF libraries (`CC0`/`CC-BY`) FIRST for full host vehicles, rooms, tools, and appliances; verify real-world engineering photos/drawings for every custom-modeled mechanism before coding.
   - **Hard ban on box/cylinder fakes:** Curved cast housings, calipers, levers, brackets, and multi-stepped gears/wheels MUST be authored as true swept arcs, lofted profiles, multi-step lathes, or subdivided sculpted meshes — never beveled cubes (`audit-blend --strict` flags axis-aligned box-like hero meshes as `primitive_box_hero_detected`).
   - **Curvature floors:** Hero cylinders/lathes `>= 64` radial segments (`96–128` for hero rings/rotors/dials); secondary rods/pins/fasteners `>= 32–48` segments; hoses/springs/cables `resolution_u >= 24`, `bevel_resolution >= 8`.
   - **Genuine multi-part density:** Target `>= 50,000` visible evaluated triangles across hero + host scenes (screening floor `>= 25,000` in `colab_cli.py`, checked on **Frame 0 AND body frames** — never inflate counts with hidden junk or lose >70% of scene geometry mid-film).
2. **Machined chamfers, clean normals, real wall thickness & shadow gaps:**
   - Every machined edge receives physical `0.15–0.8 mm` chamfers (`1–3 mm` cast/molded fillets) with `segments >= 3` and angle-limited `Bevel` (`~30°`) + `WeightedNormal` or `EdgeSplit`. Always pass `affect="EDGES"` to `bmesh.ops.bevel()` on cylinder rims in Blender 4.5.
   - Every cutaway shell, housing, duct, and transparent vessel requires **real dual-wall thickness** (never paper-thin single-sided faces) and crisp `0.15–0.5 mm` physical seam gaps between mating parts.
   - Apply `(1.0, 1.0, 1.0)` uniform scale and verify outward normals before bevels, anisotropic brushing, or physics baking.
3. **Functional industrial hardware vocabulary & neural-3D boundary:**
   - Include real functional hardware where the actual machine has it: counterbored ISO 4762 hex-socket bolts, washers, retaining pins, mounting ears, reinforcing ribs, O-ring/seal grooves, diamond knurling, springs, braided hoses with banjo fittings, and cable anchors.
   - Restrict single-image neural 3D (`TRELLIS.2 --geometry-only` MIT / `Hunyuan3D 2.1`) strictly to **organic, crinkled, soft, or matte background props** — never glossy CNC metals, precision mechanisms, or optical glass.
4. **Role-based PBR finish separation & phone-readable physical cues:**
   - Separate fixed frames, moving actuators, elastomers, and working media under the same light: dark matte/powder-coated or sand-cast fixed frames vs. brushed/turned steel or warm brass moving actuators vs. deep matte vulcanized rubber (`linear ~(0.010, 0.011, 0.014)`, `Roughness=0.60–0.88`, `Specular IOR Level=0.12–0.18`) vs. translucent rippled liquids (`IOR`, `visible_transmission=False` on area lights).
   - Size every physical deformation, clearance gap, or directional fluid/thermal cue for **360 px phone readability** (`>= 1.5%–3%` frame height — bold animated deformation, discrete moving flow packets/pulses, or true contact heat glow; **never sub-pixel `<= 1 mm` needles, floating glowing toruses, or cartoon neon bars**).
   - Obey [3D single-letter spatial typography](spatial-typography.md): ZERO text, digits, words, units, or plaques inside 3D renders.
5. **Deterministic baking & mandatory strict preflight:**
   - Bake Bullet/cloth/fluid simulations into quaternion F-curves and remove `rigidbody_world` before Colab multi-shard upload; pack all textures/HDRIs (`bpy.ops.file.pack_all()`).
   - Run **`python -X utf8 scripts/colab_cli.py audit-blend --blend <scene.blend> --shards <N> --strict --report <audit.json>`** locally BEFORE every Colab upload (blocking fake backdrop planes, mid-episode environment deletion, box-substituted hero meshes, non-uniform scales, and hollow single-stage glides).

## Real-Life Grounded Provenance: Draw Scenes from Real Life, Never Imaginary Void Sets

**Every vehicle, room, workshop, tool, and architectural backdrop must come from real everyday life or real industrial manufacturing — and MUST STAY PRESENT across opening, cutaway, comparison, and closing shots.**

1. **Unmistakable real-world host on Frame 0 and throughout:**
   - Automotive brake mechanism → **real complete car (`CarConcept.glb` or full sculpted vehicle quarter) in a bright sunlit service bay / driveway** (body panels, fender wheel arch, brake pedal/line, suspension strut, steering knuckle, concrete floor with safety lines, tool cabinet, lift post), with the curved caliper cut open **in-situ on the car's wheel hub** — NEVER a floating wheel in a pitch-black void or a cutaway pasted on a gray wall.
   - Mechanical safe lock → **full steel safe seated inside a bright, lived-in sunlit home study** (walnut bookcase with hardcover books, warm brass desk lamp, paneled walls, sunlit window), with the **safe door cut open in-situ** so the exterior dial, internal lock case, 3 brass wheels, fence lever, and sliding door deadbolts all remain physically anchored inside the safe door with the warm study softly visible behind.
   - Household/factory mechanisms → authentic sunlit kitchens, bathrooms, offices, or factory halls matching real everyday memory.
2. **In-situ spatial continuity (hard ban on hiding the environment):**
   - Keep the real architectural space and host structure visible through natural shallow-DOF bokeh (`f/2.8–f/5.6` wide/medium, `f/8–f/11` in-situ cutaways) across ALL body cuts.
   - **Hard Ban List:** Zero `Stage_MacroBackdrop` / flat gray or black studio cardboard cards; zero `env.hide_render = True` scene deletions on body cuts; zero dim `camera_strength < 0.65` pitch-black exterior worlds (dark worlds allowed ONLY when the actual science phenomenon occurs in darkness, e.g., nighttime headlights or astronomy); zero floating glowing rings/halos; zero unintroduced mystery comparison blocks; zero Playmobil lollipop trees.
3. **Cycles optical & AgX calibration:**
   - Gate thermal/fluid emission strictly with `ShaderNodeLightPath -> Is Camera Ray` (`visible_transmission=False` and `visible_camera=False` on area lights; `visible_glossy=False` on fill strips).
   - Never blast cutaway faces with close-range frontal spotlights (`< 0.6 m` perpendicular to cut plane); use angled directional grazing key + cool rim lighting so brushed aluminum/steel grain stays crisp without whiteout blowout.
   - Calibrate dark linear Rec.709 albedos honestly under AgX (`deep matte rubber ~(0.008–0.014)` with `Specular IOR Level <= 0.18`; `sintered friction pad ~(0.04, 0.03, 0.025)`; `crimson caliper ~(0.38, 0.015, 0.010)`).

## Cinema-Grade Blender Visual Richness: Replicating Live-Action Magnetism in Cycles

1. **Storytelling lens range (`28–60 mm`) — ban blind macro slivers:** Establish host context at `28–40 mm`, stage in-situ causal cutaways at `38–58 mm` keeping upstream driver + active contact + downstream effect in ONE readable frame, and only tighten to `60–70 mm` when host edges and adjacent causal parts remain unmistakable (use an in-situ cutaway window or translucent outer housing instead of blind `85–105 mm` 2 cm corner crops).
2. **Multi-arena progression & discrete hard cuts:** Stage at least **3 distinct purposeful viewpoints/scales/comparisons** across a 45–75 s film (e.g., whole real host in bright setting → in-situ transparent/cutaway mechanism showing full causal chain → controlled 50/50 real-hardware side-by-side failure comparison → active deformation & recovery with result visible → return to whole working host). Use discrete hard cuts (`>= 1.5–2 cuts / 10 s`, no `> 12 s` static glides).
3. **Dynamic per-beat lighting & optical depth:** Shift mood purposefully across beats (bright sunlit exterior → crisp directional cutaway key + rim separating fixed housing from moving parts → warm thermal/pressure accents during load → clean dual-lit 50/50 comparison) with realistic Cycles DOF bokeh and subtle Compositor `Glare (FOG_GLOW)` for true heat/highlights.
4. **Spoken-verb dominance at 360 px phone scale:** Every physical action (braking halt, elastic shear, snap-back clearance + disc free spin, dial reversal drop-off, fence drop + deadbolt retraction) must visibly dominate the frame **during the exact interval** without relying on narration to guess what moved.

### Mandatory captioned sentence-to-keyframe beat review before full Colab render

Follow this **Visual-First** preflight sequence before dispatching any full-sequence `scripts/colab_cli.py blender-render` job:

1. **Pass Muted Visual-Proof Preflight FIRST:** Build the real-host 3D scene, pass `scripts/colab_cli.py audit-blend --strict` (Frame 0 + body frames), and render full-resolution `1920×1080` Colab stills (`scripts/colab_cli.py blender-stills`) covering **every causal beat** (`>= 10–12` stills). Inspect ALL stills **100% MUTED** first:
   - *Real silhouette check:* Does the hero look like the genuine real-world machine (curved cast body, authentic hardware, zero box primitives)?
   - *Environment persistence check:* Is the real-world room/garage/vehicle unmistakably present — zero flat gray/black backdrop cards?
   - *Muted causal readability check:* Can a stranger understand *where this sits*, *what drives it*, and *what physical state changed* without a single word of text or audio?
2. **Sync Lean Narration & Build Captioned Beat Board:** Once muted visuals pass, finalize lean conversational narration pointing to those exact verified states, synthesize continuous IndexTTS-2.5 `#5` audio + `captions.srt`, and run:
   ```sh
   python -X utf8 scripts/build_visual_review.py beat-board --stills-dir <stills-dir> --captions <captions.srt> --fps 30 --output <beat-board-dir>
   ```
3. **Pass the 1-Second Layperson Pointing Test on EVERY panel:** Read ONLY the spoken caption beneath each still in `beat-board.jpg` and verify `< 1 s` referent lock, clear fixed-vs-moving anchors, in-frame driver + target + result, and zero P1 blockers before rendering the 0–5 s hook sample or full sequence.

### Physical-State Integrity, F-Curve Semantics and Pre-Colab Numerical Audit

1. **Single continuous workpiece:** Animate ONE continuous mesh across sequential stages — never park duplicate static lookalikes downstream.
2. **Complete state swaps:** On fracture/shatter/melt swaps, hide the intact parent (`hide_render = True`) on the exact swap frame and keep fragments cleanly clear of supports.
3. **Blender `CONSTANT` forward-segment rule:** At hard cuts `f_cut`, set `interp="CONSTANT"` on outgoing `f_cut - 1` and `LINEAR`/`BEZIER` on incoming `f_cut` (putting `interp="CONSTANT"` on `f_cut` freezes the incoming shot).
4. **2-second local numerical audit:** Immediately after saving the packed `.blend`, run headless Blender verification asserting non-zero camera/subject motion across every cut, zero `FONT` objects, `(1,1,1)` mesh scales, zero active `rigidbody_world`, and exact physical mechanism displacement/alignment invariants.

## Actual execution of bright lighting and materials

Apply [bright style & industrial material standards](visual-system.md#bright-style-and-premium-materials) and [material rendering](material-rendering.md) directly inside the final Cycles camera (`purpose=appearance`; never Workbench proxies):
- **Distinguish substrates honestly:** Polished chrome/steel reflects continuous studio/HDRI gradients; brushed aluminum/brass aligns anisotropy to the true machining axis; powder-coated/anodized metal shows satin sheen over fine micro-bump; sintered friction linings and matte vulcanized rubber stay deeply matte (`Roughness 0.60–0.88`, low dielectric specular `0.12–0.20`) without chalky whiteout; liquids/glass use physical `IOR`, real wall thickness, and animated flow/ripples.
- **Give curved metal real light to reflect:** Shape cylinders and cast curves with broad angled softboxes/skylights and dark negative-fill flags so specular roll-offs reveal true 3D form and bevel edges without clipping interfaces to pure white.

## Blender backgrounds and spatial completion

The environment is half the film's believability and spatial orientation — never an afterthought toggled off after second 3:
- **Specific real-world context:** Place every machine/mechanism in its true everyday or industrial home (car in sunlit service bay/driveway, safe inside sunlit wood-paneled study, shower valve in tiled sunlit bathroom) with credible architecture, furniture/equipment, contact shadows, and parallax depth.
- **Zero flat-backdrop cutaways:** Do NOT delete `env_root` on cutaways or place a flat gray/black plane behind floating parts. Keep the surrounding host housing and softly blurred room/bay behind every cutaway and comparison so viewers stay anchored in one continuous world.
- **Review at every gate:** Check full-res `1920×1080` stills across the whole timeline to catch missing environments, flat gray voids, or repeated identical camera angles before expanding.

## Character rigging, motion capture and lip sync

Activate ONLY when human hand/body performance genuinely clarifies operation (e.g., pressing a pedal, turning a dial/handle). Prefer reusing a clean local rigged hand/character; separate skeleton, skin weights, and clean contact/grasp timing; verify contact/clipping at normal speed in G2/G3 before expansion.

## Bounded trials and reliable reuse

### Qualify critical assets before whole-film integration

Qualify the hero mechanism's true silhouette, real-host mounting fit, and key moving/deforming state in 1080p Colab stills BEFORE animating or rendering 10+ cuts. Never polish textures on a wrong silhouette (e.g., a boxy caliper); fix shared geometry or adopt a verified open-licensed 3D model first. Reuse local GPU/Colab execution rules in [blender-execution.md](blender-execution.md) (chunked SHA-256 upload, detached `nohup` rendering, remote 1 MB pre-split download, surgical frame-exact patching, prompt `colab stop`).

## Archive used 3D assets in one library

### Standing authorization for library archiving

Read local `shared_3d_library.standing_authorization` in `config/series-profile.json`; when authorized and matching `target_root`, archive reusable verified models cleanly under `<category>/<asset-name>/<version>/` with SHA-256 manifests and license notes without overwriting prior versions.

### Open-licensed models may be adopted directly

1. **Search local & open libraries FIRST:** Always inspect your local CC0/glTF asset library (`CarConcept.glb`, Poly Haven glTFs) and structured `asset-index.json` via `scripts/find_3d_assets.py`, then fetch use-compatible `CC0`/`CC-BY` models (Poly Haven, Sketchfab CC0, Khronos, NASA/NIH public domain) when a real vehicle, room prop, or host assembly is needed.
2. **Verify license, scale, normals & internals:** Confirm commercial/modification rights, record creator/license/hash, import cleanly without auto-running scripts, strip unrelated stickers/brand logos, and adapt/cutaway only what the mechanism requires. Never substitute promotional prerenders for 3D geometry.
