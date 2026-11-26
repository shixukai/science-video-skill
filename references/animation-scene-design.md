# Animation scene design: from physical state to complete shots

For substantial animation or turning static assets into animation, design subject, context, visible change and shot handoffs before asset refinement. Record results in existing action cards and [art records](../assets/art-direction-template.md#animation-scene-design-card). Realistic main imagery follows the [realistic production contract](realistic-production.md); 2D implementation stays within approved scope/supporting layers.

## Diagnose what is missing first

| Actual symptom | First diagnosis | First repair | Unsupported conclusion |
| --- | --- | --- | --- |
| Detailed object looks like a specimen pasted on flat color | Missing observation context/necessary reference | Define scale, environment/carrier and relationship; retain isolated specimens when purposeful | Simple backgrounds do not automatically fail; do not force ground, plants or people |
| Object only rotates/zooms while narration describes growth/change | Missing stated object-state change | Design continuous intermediate states, change region and accumulated result | Camera motion or material flashes are not growth evidence |
| Many objects, unclear focus | Confused relational hierarchy | Prioritize the current relationship through value, edges and action; remove competing events | Layers, motion volume and frame coverage do not prove richness |
| Close-up is larger but adds no information | No discovery task for shot scale | Add genuinely needed structure/state or omit the close-up | Unsupported microstructure is not refinement |
| Attractive shots remain thin as a sequence | No information progression/state memory | Retain established state and advance the question through new views/comparison | More/faster cuts do not automatically help |
| Change visible only in enlarged screenshots | Key difference below viewing-scale readability | Repair framing, shape difference, local value or timing | Code values/pixel differences cannot replace normal viewing |

Distinguish necessary negative space from missing content: state the region's observation, motion, comparison or text role, then check real usefulness. Large quiet backgrounds are allowed; do not fill them when subject, relationship and payoff hold. Complete Blender videos also follow [background/spatial completion](engineering-blender.md#blender-backgrounds-and-spatial-completion): local negative space/minimal inspection does not authorize omitted environments or identical backgrounds/platforms throughout.

## Beat-by-Beat Visual Density: Never Let the Body Go Hollow After Second 5

A vivid 0–4 s hook followed by 30 s of one lone prop changing tint on an empty dark table causes immediate viewer drop-off. Before building or rendering body shots, verify every explanatory beat (roughly every `4–7 s`) against three visual-density questions:

1. **Fresh visual world, scale, or comparison:** What genuinely NEW environment, scale jump (macro / cross-section / microscopic), controlled split-screen comparison (A vs. B), or unmistakable physical transformation enters the frame in this beat that was NOT already on screen 5 s ago?
2. **Spoken-verb dominance at phone scale:** Does the exact physical action the narrator describes (heating, cooling, bending, latching, breaching, flowing) visibly occupy and drive the center of a 360 px phone frame during those exact spoken seconds—rather than leaving a static object idling while voiceover carries the story alone?
3. **Purposeful multi-layer richness:** Do foreground, midground, and background each contribute real context, depth, lighting atmosphere, or visual contrast—avoiding the "sterile CAD bench in a pitch-black box" look across consecutive beats?
4. **Real-life grounding & Mute Test (`素材来源于生活`):** Does every prop, vehicle, tool, and architectural backdrop come from real everyday life or real manufacturing rather than an imaginary neon void, mismatched vehicle, or generic lab stand-in—and can a muted viewer instantly recognize both the real-world setting and the active physical event within `< 1 s`?
5. **Show-First Visual Replacement (`画面替文字`):** Science video's core edge is turning abstract forces, pressure, temperature, flow, or scale into concrete visible behavior. If on-screen explanatory text is deleted and voiceover is trimmed to minimal causal glue, does the animation, cutaway, or side-by-side controlled experiment still prove the mechanism on its own? Never rely on pure monologue or text blocks to explain what a visual demonstration or mini-experiment can show directly.

## Non-text visual pointing grammar and widescreen aspect-ratio framing

When explanatory text labels are prohibited or minimized (especially on 3D routes under [spatial typography](spatial-typography.md)), viewers lose the crutch of reading part names off arrows. The picture itself must therefore carry **unambiguous visual pointing** and **purposeful 16:9 widescreen composition** on every single beat:

1. **Non-text visual pointing (replace missing 3D text with optical hierarchy):**
   - **Active-Part Spotlight & Ghosting:** Inside any multi-part cutaway (`>= 3` nested parts), dim, desaturate, or ghost inactive housings and surrounding sleeves to quiet low-contrast matte/translucent silhouettes (`~15%–30%` visual weight) while keeping the ONE currently spoken component crisp, high-contrast, and visibly moving. Never dump 8–10 brightly lit metallic parts at equal visual weight and expect the viewer to guess which piece the voiceover just named.
   - **Functional Color & Finish Role Coding (ban same-metal cutaway clutter):** Assign unmistakably distinct material/value families by **physical function**—for example: **fixed frame/anchor** in dark matte charcoal or gunmetal, **active moving actuator/slider/valve** in warm brushed brass, copper, or clear anodized accent, and **working fluids/media** in vivid physically distinct states (translucent crimson hot stream vs. cobalt cold stream, solid crystalline block melting into surging molten amber, or crisp directional gas streamlines). Never stack brass-on-brass or chrome-on-chrome interacting mechanisms where moving sleeves vanish against stationary housings.
   - **In-Frame Cause-to-Effect Continuity (never crop the actuator out of shot):** Whenever an external action drives an internal response (a hand lifting a chair lever pressing a top valve pin, a knob turning a spring carrier, a flame heating a wax cartridge), keep **both the driver/actuator and the responding internal target visible inside the SAME shot**—or link them in an unmistakable spatial cutaway—so cause and effect read directly in one glance.
   - **Unmistakable Physical Flow, Valve-Gate, and Area-Proof Grammar (ban sci-fi slop crutches):**
     - Show **gas or liquid flow direction** with crisp, discrete, animated 3D directional flow ribbons, chevrons, or dense moving bubble/droplet packets visibly rushing through open ports and bypass passages—never faint motionless translucent fog that looks like glass reflection.
     - Show **valve throttling or shutoff** with a crystal-clear exposed gap where the moving gate physically narrows and slams flush against the port seat—never bury the actual closing slit underneath blurred transparent pipe walls.
     - Show **area or force proofs** by highlighting the *actual* load-bearing physical faces or unfolding/extracting the two compared cross-sections cleanly side by side—**STRICTLY BAN** arbitrary floating glowing toruses, neon energy halos, unexplained floating white cubes, or jelly discs pasted onto the wrong stationary part.
2. **16:9 widescreen framing for slender or vertical mechanisms (ban "telephone-pole" dead zones):**
   - **Never center a skinny vertical mechanism (`< 25%` of frame width) inside `75%` empty blank grey wall** across consecutive shots. A lone vertical tube floating in empty widescreen void crops off spatial anchors and destroys both visual appeal and motion comprehension.
   - **Use diagonal `30°–45°` hero framing or purposeful camera roll/elevation** for slender columns, pistons, and valves so the active mechanism spans `55%–85%` of the 16:9 canvas while keeping axial motion unmistakable.
   - **Keep recognizable host anchors in frame during relative motion:** Whenever explaining *what moves vs. what stays still* (such as an office chair seat + outer tube rising while the star base + steel rod remain fixed), keep recognizable portions of the host (seat pan, lever handle, star base, or wall pipe + showerhead) visible inside the shot so relative displacement reads immediately without guessing.
   - **Use horizontal unfolded or 50/50 split comparisons across the 16:9 width:** When comparing two geometries, materials, or states (full circular top cap vs. rod-pierced bottom annulus; hot vs. cold ports; solid vs. melted wax expansion), arrange them **horizontally left-to-right filling the 16:9 frame** instead of squeezing tiny vertical overlays inside a narrow pipe.
   - **Genuine shot-scale and angle progression:** Every consecutive cut must change shot scale, camera axis, or explanatory stage meaningfully (`whole host → host-to-mechanism anchor → isolated mechanical action → horizontal proof/comparison → real-world payoff`)—never repeat 5+ nearly identical front-on tube cutaways in a row.

### Distinguish missing from insufficiently visible

When inspecting existing work, classify each item as present and clear / present but inconspicuous / missing / unreviewed before choosing repair. Existing growth, close-ups or two-object differences do not justify generic tasks to add them again. Record precise times, preserved structure, actual change and observation method. If sparse frames do not reveal change, add key-state/continuous observation first; not clearly seen does not mean absent.

When materials/transparent edges already work but key new areas are too small, preserve effective assets and prioritize framing, references and state expression.

## Work order: action intent before detailed art

Write the visible relationship/state sequence before choosing refined key states, occluded surfaces and independent parts. Finished stills check appearance; they do not establish a workflow of generating a beautiful whole image and making it drift afterward.

1. Extract observation task, conditions, main object and adjacent-shot relationships from current explanatory shots. Use nouns and concrete changes for an executable instruction.
2. Sketch cheap before/key-intermediate/result states. For comparison/structure use difference-revealing states rather than inventing process. Mark retained, new, disappearing, deforming and occluded portions.
3. Design composition, state change and asset separation together. Verify key relationships at target viewing size before refining outlines, structure, light and materials.
4. Create a continuous representative segment in the original timeline. Schedule events, observation pauses and cuts from actual meaning/audio; paper-example seconds are not sync evidence.
5. Inspect the current full composite first, then diagnose with local views/overlays hidden. Restore the original composition for continuous recheck after repair. Existing G2/G3/G5 evidence requirements remain.

### Distinguish holds from sustained contact before hand-editing curves

For held poses/positions, preserve explicit start/end states and check interpolation for hidden drift during the hold. Sustained moving contact requires continuous constraints, contact points and object responses along the intended path, not automatic ease-in/out around every contact key causing sliding, separation or unsupported slowing. Adjust interpolation, tangents or segments only for affected controllers/intervals; do not globally smooth/simplify animation. Existing solutions, caches or measured rates follow their real conditions, not uniform linear/Bezier conversion. Review the complete action/joins; attractive curves do not prove contact/causality.

## Four responsibilities of shot content

These are design questions, not four required layers or four types of content present in every frame.

| Responsibility | What to specify | Picture contribution |
| --- | --- | --- |
| Subject | Concrete object, recognizable structure, current state and truly changing part | Recognition and continuous tracking |
| Context | Location, scale, necessary setting/carrier/observation conditions and what stays off-screen | Relative size, space and conditions |
| Relationship | How contact, growth, transfer, comparison, constraints or structure are visible | Details support explanation rather than merely show related objects |
| Discovery | New observation, retained result and why the next shot needs it | Time/shot progression provides actual benefit |

Environment needs a concrete role, e.g. scale, light/color/occlusion, verified conditions or action handoff. Do not add unsupported wind, fog, collision or melting for activity. Clean local spaces are allowed when mechanisms need no exterior setting; composition, materials and relationships still require completion.

## Scene-design checks

Check these within the [visual-system A/D/I standards](visual-system.md#static-picture-a01a10). This page supplies state/action methods, not a duplicate art-rating table.

| Production item | First action | Normal-speed check | Criteria |
| --- | --- | --- | --- |
| Subject, setting and detail | Compose from identifying structure, actual scale and support/occlusion; main shape before contact/material | Object/features read at target size; close-ups add information | A01–A09 |
| Main action/state memory | Initial → intermediate → result and retained/new/removed portions; parameters change actual objects | Old structure stable, change motivated, result retained; no whole-image scale/subtitle updates posing as process | D01/D04/D05 |
| Timing/supporting motion | Allocate recognition, change, comparison and holds by mechanism; restrain secondary motion at difficult points | No arbitrary elasticity, bounce or drift; stated change can be observed fully | D02/D03/D06 |
| Camera, handoffs and sound | New observation per scene; bridge through features/direction/state and align events/meaning | Identity retained; main action, necessary labels and captions do not compete | D07/D08/I01–I03 |
| Compositing/output | Shared geometry/anchors, completed hidden faces/backplates, surface-attached materials | No sliding skin, ghosts, jitter or intersections; final encoding preserves key gaps/edges | A06/A07/D05/I04/I05 |

## Make existing change readable as evidence

For implemented but unclear shots, use the table's composition, main-action, state-memory, camera and narrative standards; do not add another quality level.

| Problem | Production action | Acceptance observation |
| --- | --- | --- |
| Large subject, tiny terminal change | Identify the smallest conclusion-supporting feature, e.g. a new fork, boundary displacement or contact. Let it determine shot scale while preserving needed old structure. Reduce irrelevant texture/background edges | Feature locatable in the full target-size frame; subject screen percentage or temporary review enlargement is insufficient |
| Growth mixed with camera motion | Provide a stable window at key relationships; retain old forks/contact surfaces. Transform object/reference together when moving and establish result before leaving close-up | Distinguish actual object change from camera zoom/pan; fixed-camera diagnosis does not replace final normal-speed review |
| Comparison differs but not at first glance | Specify discriminating feature, e.g. branch location/width/density. Hold irrelevant initial state, scale, angle, light and time constant; align comparable local regions if needed | See target differences from chosen conditions, not random texture/value/scale; do not exaggerate morphology beyond evidence |
| Promised condition change announced only in words | Add readable nodes for genuinely needed condition changes and connect them to later object response. Invisible conditions use evidenced action/state, narration and synchronized subtitles; 3D permits only necessary single letters, other media necessary short labels. Results occur in subject structure | Track condition change → responding parts → retained result. Decorative color/fog/particles are not measurement/mechanism |
| Repeated similar whole views add nothing | State the local feature, compared regions or accumulation recognized on return; carry prior identity/state back. Combine/shorten if no new evidence | Each return locates a new conclusion; titles/material flashes do not establish shared growth |

When comparing onset, use a common observation time and show each onset; do not also force equal post-onset duration. Comparing results after equal elapsed duration requires the opposite. State the comparison first, then choose temporal references; two natural individuals differing in all variables are not a controlled experiment.

For continuously shared conditions, show the same context, corresponding regions and similar results without requiring another condition-change node.

Location markers may appear briefly and leave to locate results; highlighting is not new matter. Marker order for corresponding same-stage areas denotes explanation order, not sequential occurrence. 3D auxiliary text permits only necessary single letters; names/conditions/values belong in narration and genuine synced captions. Other media retain existing necessary-label rules. The goal is correspondence between explanation/evidence, not more picture prose.

### Process actions must leave observable results

For a process explanation, show the workpiece before the operation, the interaction at the active region, and the resulting changed material/structure. Equipment travel alone does not demonstrate what happened to the workpiece. Keep **single-workpiece continuity** across sequential stations (never park a duplicate static workpiece downstream while another moves toward it), and on destructive state swaps (shattering, melting, cutting, collapse) retire the intact parent solid on the exact replacement frame so fragments expose empty supports rather than floating around an unremoved solid (see [physical-state integrity and pre-Colab audit](engineering-blender.md#physical-state-integrity-f-curve-semantics-and-pre-colab-numerical-audit)).

Drive interacting objects from one process state or event timeline. Specify the driver/trigger, when contact or a constraint becomes valid, which objects respond, and what result accumulates or remains. Derive tool travel, workpiece deformation/removal, carried material, instrument feedback and necessary effects from those relationships, rather than unrelated keyframe tracks. A practical implementation is a shared `process_state(t)` consumed by geometry, rigs, overlays and sound-event markers; use explicit event dependencies when continuous functions are unsuitable. Select the actual scientific model first. Controlled geometry is sufficient when it preserves the required relationship; use simulation where its dynamics are necessary, with applicable assumptions and validation.

Give the important explanation a consequential event to follow: establish a goal or constraint, show an action taking effect, expose the developing change, then let the viewer inspect the result. Choose whole/close-up/section/result views for those discoveries, retaining the same object and state at handoffs. Keep the camera quiet when the critical interaction needs attention; vary pacing around anticipation, action and observation using the real narration. Sound cues follow actual depicted events, not every pan or cut. Structure inspection can remain calm; no fixed action count, camera-move quota or simulation requirement applies to every shot.

| Example | Shared state and visible sequence | Production result to check |
| --- | --- | --- |
| Probe test | `probe_z/contact/test_state/result`: align → make contact → acquire/classify → add the result to the map → lift and move | Each displayed result follows its test and remains in the accumulated map; data is measured, simulated or clearly illustrative as appropriate. A lowered probe followed by a long unchanged image is insufficient. |
| Material removal | Tool/exposed interface, protected region and removed volume share the chosen process state; removal progresses at the active interface while unaffected material stays | The changed boundary and intermediate structure are visible. Do not shrink the entire workpiece or reveal an already completed cavity; select the actual etching/machining mechanism. |
| Character operating a fixture | Gaze/reach → valid grasp → workpiece follows hand → seating contact → release/clamp in the order required by the actual support → inspection feedback | Hand, workpiece and fixture share contact/release events; held objects do not drift, jump parents or move before grasping. Body mocap alone does not establish fingers, grip or correct operation. |

Choose the actual mechanism before adding effects. ALD, for example, uses sequential surface reactions and can coat complex topography; generic downward particle rain can misrepresent it. [Lam Research's ALD explanation](https://newsroom.lamresearch.com/Tech-Brief-A-Look-at-Atomic-Layer-Deposition-ALD) is an example of a process-specific visual basis. Likewise, an optical-path graphic must follow the selected system: [ASML's EUV description](https://www.asml.com/en/products/euv-lithography-systems) uses reflective reticles and mirrors. An illustrative ray path must not imply that invisible radiation is an ordinary visible beam. These examples guide verification, not a particle/beam preset for every manufacturing video.

## Write actions so they can be produced

“Slowly forming snowflakes,” “natural water flow” and “cinematic camera” are not executable. Instructions must at least answer:

> In which visible region does which object change from what state to what state? Which structures/references remain fixed, how do intermediate states connect, where is the result visible, and how do camera/supporting motion make it clear?

Select a state model for the subject:

| Relationship | Main controllable states | Meaningful visual change | Typical error |
| --- | --- | --- | --- |
| Boundary-deposition growth (e.g. snow crystals; select other models for other growth) | Growth boundary, branch connections, new regions, retained shape | Old structure continues; matter is added near the boundary | Center-out reveal of a finished image, whole-image scaling, or orderly branch lighting posing as simultaneous growth |
| Material processing | Active surface/boundary, supplied or removed material, protected region and endpoint | Show deposition, reaction, removal or filling progressing at the correct interface; retain the workpiece reference and resulting structure | Reveal an already finished layer; shrink a whole solid to fake etching; use decorative particles with no corresponding material change |
| Test and classification | Test location, stimulus/contact, acquisition, decision and accumulated result | Distinguish untested, testing and classified states; update a map/table from actual measurements, the chosen simulation or clearly illustrative data, with non-color cues (3D permits only necessary single-letter markers, with meaning/quantities in narration and genuine synchronized subtitles; other media retain their text rules) | Hold a probe still while narration alone describes results; random red/green flashing presented as real yield |
| Multiple transfer paths | Each carrier/quantity, source, interfaces, destination and any relevant return path | Establish each route in one coherent section/view, then compare them with stable color/line meaning | Repeatedly jump between shell and section; assume different carriers must travel in opposite directions |
| Deformation/force | Supports, contact, constraints and local shape | Preserve constrained regions and change affected regions accordingly | Whole-layer rocking or jelly bounce imposed on hard objects |
| Transfer/propagation | Local carrier state, propagation location, before/after response | Distinguish local object motion from propagation extent | Uniform translation or looping ripples without response |
| Condition comparison | Shared start/scale/reference, changed conditions, resulting differences | Distinguish compared states through subject differences | Attractive pictures with different scale, lighting and every condition |
| Structure/space/evidence | Composition, positions/constraints, reveal order and inference limits | Inspect relationships through reveal, location or juxtaposition | Inventing process to satisfy “dynamic” |

Masks, visibility and draw-on may reveal real state models or explicitly locate teaching content. A time wipe over a finished image does not prove growth. Review state sequence/results before implementation technique. Static observation may show full form but cannot replace promised change.

## Writing tasks for production agents

Fill the [animation scene card](../assets/art-direction-template.md#animation-scene-design-card) directly, referencing current shots, science and stage-appropriate actual audio/timeline rather than copying another table.

Assignments require accessible applicable reference images, initial/key-intermediate/result states, stable references, distinguishing features and handoff objects. Establish state/composition before refinement. If the tool cannot make the change, repair inputs/implementation within the locked medium. Record concrete remaining capability gaps and continue independent work; do not retreat to symbols with background decoration.

## Production-side inspection

Use existing G2/G3/G5 checks, not mandatory external audience feedback:

- **Design:** Check original question/science for observation task, state links, context role and next-shot payoff. Consider removing elements whose deletion loses no recognition, explanation, composition or required observation conditions.
- **Still:** Inspect complete key-state composites and current approved references, prioritizing main form, relationships and focus before material. Separate technical placeholders/formal style candidates.
- **Continuous:** Watch actual normal-speed export for action location, detectability, retained results and joins, then check meaning with sound. One clear frame cannot prove a segment.
- **Uncertainty:** Temporarily lock camera, hide decoration/overlays or compare same-condition states to diagnose cause; restore formal layers for complete review.
- **Record:** State time, observed differences, A/D/I mapping, repair and unreviewed scope; distinguish clear, inconspicuous, missing and unreviewed content. Stills support their states only. Without continuous perception, leave action, rhythm and audiovisual work unreviewed rather than claiming improvement/L3.

If only color, texture or background improve while subject results, context and progression are absent, return to state/shot design instead of batching similar shots.
