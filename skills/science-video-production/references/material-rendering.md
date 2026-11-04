# General Material Rendering Standard for 3D Video

**Visual target.** At the intended viewing size and normal playback speed, the viewer should be able to recognize what an object is made of, how its surface has been finished, and how its shape and thickness affect its appearance. These qualities should remain apparent as the camera, object, or light moves.

This standard applies to product visualization, technical explainers, cutaway animations, and fully staged scenes. Geometry may be simplified to suit the visual style. Preserve three qualities across subjects: continuous tonal transitions on broad curves, narrow highlights on thin edges, and distinct responses from adjacent finishes under the same light. The [supplied reference clip, opening two seconds](https://x.com/sparklabhq/status/2116947945400742285) is an optional comparison candidate; inspect the actual interval before recording observations or claiming it was reviewed. A link or page-text retrieval is not continuous video perception or permission to reuse its footage.

This standard governs **3D video material rendering**. It does not change the main-tool route, scientific colors or commissioned scope. For an asset-only static commission, inspect only applicable static appearance; moving reflections remain unreviewed until actual video is available. In-picture text still follows the [3D single-letter rule](spatial-typography.md): material detail does not authorize printed labels, engraved words, numbers or explanation plaques. Genuine synchronized narration/accessibility captions remain in their separate clear 2D layer. Industrial work also follows the [studio lighting direction](visual-system.md#industrial-product-studio-material-standard), without imposing that backdrop or lighting setup on every subject.

## 1. Define each material and its finish

Specify both the **base material** and the **surface finish** for every major visible surface. “Aluminum” identifies the substrate. “Fine bead-blasted aluminum” and “aluminum with a satin black powder coat” describe two surfaces an artist can render and a reviewer can distinguish.

| Material or finish | Required visual behavior |
|---|---|
| **Polished or semi-gloss metal** | The surface reflects both bright and dark areas of its surroundings. A more polished finish generally produces sharper reflection boundaries. Silver metal may appear charcoal gray where it reflects a dark environment and bright silver where it catches a light source. Both regions should read as parts of the same continuous surface. |
| **Bead-blasted, matte, or brushed metal** | A bead-blasted finish produces diffuse-looking reflections with soft transitions. A brushed finish has a directional sheen that follows the machining direction of the part. From a distance, the viewer should notice the sheen. Individual machining marks should become visible only when the camera is sufficiently close. |
| **Painted or coated surfaces** | The viewer should see both the coating color and light reflected by its surface. Gloss paint may show a recognizable reflection of a window or light panel. Satin and matte coatings soften that reflection. Exposed substrate should appear only where the coating ends, has worn away, or has been cut through. |
| **Rigid plastic and rubber** | Glossy molded plastic, textured plastic, and dry rubber should remain distinguishable under the same light, even when all three are black. Glossy plastic may carry a clear environmental reflection. Fine-textured rubber generally produces a broader, weaker highlight. Dark areas should retain enough variation to reveal the underlying form. |
| **Glass and transparent materials** | Show the interaction between surface reflections and the scene visible through the material. As the viewing angle changes, the reflection and the objects behind the surface should move consistently with their respective positions. Where thickness is visible, edges, refraction, or the separation between front and rear surfaces should help convey it. |
| **Wood, fabric, stone, and other textured materials** | Grain, weave, and other surface features should have a credible scale and orientation. Wood grain follows the direction of the component, and a fabric weave follows folds in the cloth. The finish must also be apparent. Varnished wood and unfinished wood can share the same grain pattern while reflecting light quite differently. |

## 2. Use reflections to reveal shape

- **Flat surfaces.** Reflections should remain stable across a flat panel. Any visible distortion should correspond to a physical feature, such as embossing, a dent, or manufacturing waviness, at a scale appropriate to the object.
- **Curved surfaces.** Highlights and tonal transitions should follow the curvature. A viewer should be able to trace a reflection and see where a surface bulges, tapers, or changes direction. A cylinder, sphere, and cone should produce distinct highlight shapes even when they use the same material.
- **Edges and bevels.** The width of an edge highlight should suit the part. A thin rolled lip may catch a fine arc of light, while a rounded corner can carry a broader band. As the edge turns away from the light, the highlight should weaken or disappear naturally.
- **Highlight width and sharpness.** Evaluate these separately. A large light panel can create a broad reflection with a crisp boundary on polished metal. A rougher finish softens that boundary. A wide highlight alone is insufficient evidence that a surface should look rough.

## 3. Match surface detail to scale and viewing distance

Detail should appear progressively as the camera approaches.

| Viewing distance | What should be visible |
|---|---|
| **Wide shot** | Overall color, major material boundaries, and broad patterns of light and shade. Fine texture should resolve into an overall impression of gloss, grain, or softness. |
| **Medium shot** | Differences between gloss and matte finishes, component edges, seams, and transitions between surface treatments. |
| **Close-up** | Appropriately scaled machining marks, surface grain, coating edges, mesh openings, non-text surface features, and wear. Where thickness matters, the viewer should be able to distinguish the front surface, the edge, and the structure behind it. |

If individual brush marks, grains, or scratches are conspicuous in a wide shot, check their scale and contrast. Wear should also match the object's condition and use. A newly assembled object can look convincing with clean surfaces. On a used object, wear should concentrate where handling, contact, friction, or exposure would produce it.

## 4. Preserve the spatial relationship between materials

- **Contact and separation.** Local shadows should help distinguish parts that touch, overlap, fit inside one another, or sit slightly apart. A tight joint and an open gap should differ in apparent width and depth.
- **Reflected surroundings.** Nearby surfaces may influence one another where the lighting and finish support it. For example, a reflective metal part beside a blue panel may pick up a subtle blue reflection on the side facing the panel. The reflection should correspond to the panel's position and extent.
- **Openings and layers.** Mesh, vents, openings, and transparent covers should reveal depth where the shot permits it. The structure behind an opening should have its own lighting and position. In a close-up, a small sideways camera move should reveal some relative motion between the front layer and the structure behind it.
- **Cutaways and cross-sections.** A cut should expose the materials that occupy that part of the object. If a component has a coating, a substrate, and an inner lining, the cut edge should preserve their order and relative thickness wherever the scale of the shot makes them visible.

## 5. Keep textures and reflections consistent in motion

**Textures, non-text surface features and permitted spatial single-letter markers stay attached to the object. Reflections respond to changes in viewing angle and lighting.**

During a camera orbit, wood grain, a scratch or a permitted spatial marker should remain fixed to its location on the surface. A reflected light panel or highlight should move smoothly across the object as the viewing geometry changes. This distinction is especially important on curved parts, where a stationary highlight can make convincing geometry look flat as soon as the camera moves.

Review fine mesh, parallel lines, narrow bevels, and dense surface patterns at final output resolution and normal playback speed. As details become too small to resolve, they should gradually merge into the overall appearance of the surface. They should remain free of visible flicker, crawling patterns, intermittent bright pixels, and moiré.

## Carry the material setup into the actual animation

Develop the intended material/light appearance alongside inexpensive motion blocking; do not postpone all look development until the complete animation is built. A static imported model with PBR materials does not establish the appearance of a later scene that rebuilds its shaders, discards its lights or uses a different rendering path.

Blender Workbench, studio/matcap shading and viewport `diffuse_color` are suitable for explicitly internal pose, contact and timing diagnostics. They do not exercise the node-based material/light setup required here and cannot be the evidence for metal response, coatings, transmission or final material quality. A motion-only proxy may be shared when explicitly requested for that limited purpose; it must not be offered as the material/style candidate. A request for 3D animation rather than realistic footage does not by itself replace the established material direction with clay or flat colors. Preserve any explicit alternative art direction within its actual scope.

Start new or changed material/light work with the grouped appearance samples below. Before expanding to longer appearance-review candidates or batch beauty rendering, complete or validly reuse that still/motion coverage in the intended material-capable renderer. New jobs use the documented [appearance execution purpose](blender-execution.md#prepare-one-job-per-shot-or-coherent-scene); a motion-only recipe is not the default for that deliverable. Use EEVEE or Cycles according to the actual finish, reflection/transmission and temporal requirements; engine choice and sample count alone cannot pass the look. Reuse an existing qualifying scene/sequence instead of commissioning another experiment or user approval round.

The visual artist hands off the actual editable shader assignments, required textures with scale/orientation, scene lights/reflection environment and color-management settings in the existing scene/library and dependency records. The animator reuses this setup for the animated geometry; a convenience color helper must not silently replace it. New visible parts receive compatible real surface finishes. Scientific state colors drive the actual active shader/parameter under the selected renderer, retaining their meaning during promotion from a viewport proxy.

The producer checks the effective engine after driver construction and job overrides, active material slots and connected shader outputs, declared external dependencies, lighting and color state for the rendered sequence. The `appearance` executor rejects an incompatible engine or missing active output binding before a frame is written. Passing those checks establishes implementation only; the artist/parent still owns the actual appearance result. An unused PBR material in the file or an earlier still does not prove that the animated subject uses it. Return a missing setup to its owner. Then inspect actual representative output at the intended view/delivery size for this standard's visual behavior; metadata and plausible parameter values remain technical evidence only. Keep known material failures open until the corresponding appearance output is reviewed. Perform these checks in the existing lookdev/G3/G5 workflow, without a new pass flag, extra gate, per-object render quota or automatic full-episode rerender.

For a failed appearance, diagnose the actual surface and source before another render request. A dark polished face may lack reflected surroundings; an erased white face may be receiving excessive reflected-source radiance. Check the relevant surface/normal, reflected source position/extent and local clipping before changing global exposure or adding more lights. A planar surface may legitimately carry a broad uniform reflection; do not invent curvature or require texture where the actual material has none. Return loss of required shape/edge/finish information with its observed location. Preserve correct parts and combine a cause-level correction into the next bounded continuous candidate instead of cycling isolated variants or resetting the task history. A few local pixel samples can diagnose clipping; white highlights or a whole-frame brightness score alone cannot approve or reject the material.

## 6. Acceptance criteria

Before batch rendering a 3D video, provide **one close-up still and one 3–5 second turntable or camera-orbit shot** for each major material or representative group of materials. Group suitable surfaces intelligently; this is not a test per duplicate part or shader instance. Keep the lighting fixed during this motion test and include a bright region, a tonal transition, and a shadowed region on the subject.

The still may be extracted from that same rendered sequence. Reuse an existing sequence/range when its actual material, finish, geometry scale, lighting, output resolution and motion cover the intended checks; otherwise produce only the missing coverage through one bundled local lookdev request. Identify the unresolved material/light questions, relevant closest views, scientific-state extremes and expected end condition in the existing request. Inspect these actual grouped results for normal/smoothing defects, clipped highlights, lost surface distinctions and unstable reflections before expanding to the complete affected interval. Do not render a long first trial merely to reach a later close-up where such a defect can first be seen. A third-party reference, parameter match or unviewed clip cannot supply this evidence. Do not regenerate a qualifying test merely to fill another form.

Keep this evidence in the existing scene/design and applicable G3 art records. It is lookdev within the current workflow, not another approval stage, a new audio requirement or a prescribed length for the scientific representative sequence. Material-test success cannot replace the complete process/action sample or final-film review. Plan the diagnostic allowance from this actual work and measured cost; do not inherit an unrelated motion-repair zero allowance as the sampling plan for new appearance risks. A frozen zero/exhausted allowance remains binding and returns to the parent under the [diagnostic admission rules](blender-execution.md#task-bound-diagnostic-admission); it does not justify skipping these samples or choosing a larger untested render. Reuse matching accepted motion/audio and material evidence, reopening only affected coverage. Recheck the approved material under the actual final shot lighting, resolution, viewing conditions and encode; changed conditions reopen only the affected coverage. Static-only asset work retains the static scope above.

| Review item | Pass condition |
|---|---|
| **Material recognition** | Materials that need to appear different are distinguishable under the same lighting, including surfaces with similar base colors. |
| **Shape readability** | Reflections and shading reveal the principal curves, changes of direction, edge profiles, and visible thickness. |
| **Credible scale** | Texture, bevels, openings, and wear are proportionate to the object. Close-ups hold up under inspection, and wide shots remain visually clean. |
| **Stability in motion** | Highlights move continuously, permitted surface features remain attached, and fine detail plays back without distracting shimmer or aliasing. |
| **Readability in the final video** | The material differences that matter to the shot remain visible at the audience's actual viewing size and normal playback speed. |

## Copy-ready production brief

> Render all major surfaces with physically plausible, visually distinct material behavior. Define the base material, surface finish, and condition of each component. Under the same lighting, differences in reflected light, highlight sharpness, texture, and color should make the intended materials easy to distinguish. Use continuous tonal transitions to reveal curved forms and appropriately scaled highlights to describe bevels, thin edges, and cut surfaces. Preserve the visible thickness and spatial relationship of coatings, substrates, and adjacent parts. Introduce surface detail progressively with camera proximity. During motion, textures and permitted surface features must remain attached to the object while reflections respond naturally to changes in view and lighting. Evaluate the result at final delivery resolution, intended viewing size, and normal playback speed. Follow the existing single-letter-only 3D picture-text rule; material detail does not authorize labels or explanatory text.
