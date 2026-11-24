# Visual Design System

This page owns visual craft, lighting/materials, disturbing-imagery safety, in-picture text rules, covers (`scripts/compose_cover.py`), A/D/I L3 standards, and connection topology. Follow the single active route under [SKILL.md's Route Isolation gate](../SKILL.md#route-isolation-load-only-the-active-route). See [quality acceptance](quality-acceptance.md) for acceptance and [science and rights](science-and-rights.md) for provenance.

## Bright Style and Premium Materials

Default to effective subject lighting that makes key forms bright, crisp, and finely finished while preserving true colors, readable dark structure, and controlled highlights. Choose background value independently (dark/black sets are valid; never equate "bright" with a white backdrop or lifted exposure). Use [art direction](art-direction.md) for color roles, light hierarchy, and noise diagnosis, and return review media via [verified local links](../SKILL.md#local-review-links-and-bandwidth-conservation).

### Industrial Product Studio Material Standard

Industrial products and hardware use clean industrial studio lighting: broad soft key gradients on curved surfaces, deep readable shadows, and fine bevel/edge highlights without glowing outlines. On Controlled 3D routes, pair with [general 3D material standards](material-rendering.md) (distinguish polished metal, satin paint, glossy plastic, and matte rubber; never flatten into category presets), [high-poly industrial Colab 3D modeling](engineering-blender.md#high-poly-industrial-modeling-standard-for-colab-3d) (real machined bevels, `>= 64`-segment hero curves, weighted normals, wall thickness, seam gaps and studio-faithful CNC detail), and [Blender implementation](engineering-blender.md#actual-execution-of-bright-lighting-and-materials) / grouped lookdev evidence. Static stills verify static appearance only; continuous video verifies moving highlights.

## Current Baseline and References

Follow the commissioned route under [SKILL.md's Route Isolation gate](../SKILL.md#route-isolation-load-only-the-active-route). Pure-2D rules below apply only to explicitly authorized 2D scopes; covers always follow [cover standards](#design-the-two-cover-ratios-independently). Use [series profile](../config/series-profile.json) and [bright premium palettes](../assets/style/bright-premium-palettes.json) as starting points, keeping private design boards and originals inside the project.

### Visual Anchors of the Approved Style

For explicitly authorized pure-2D illustration, maintain credible proportions, volumetric light/shadow masses, distinct material cues, edge hierarchy, natural depth, and equal finish across wide scenes, subjects, and close-up mechanisms — never dropping from finished exteriors to crude icons or thin-line teaching slides. Reference images stay research-only.

### From Visual Anchors to Actual Assets

1. Specify what each reference supplies (structure, lighting, composition, or motion) and what stays excluded (unrelated logos, backgrounds, unsupported parts); third-party images never enter production picture.
2. Share stable object/material identities across shots and inherit valid prior process states rather than resetting or propagating prior-shot defects. Keep scientific overlays and formal captions on separate editable layers.
3. Compare full composites side by side against references using A01–A10 and fix the largest gap first before independent art review. Bind versions under [shotbook references](shotbook.md#bind-design-and-asset-references).

### From Cover Finish to Controllable Dynamic Scenes

Carry cover identity, real-world context, and material truth into the film's locked medium, redesigning composition for each shot's explanatory task:
1. **Closed explanatory scope:** whole-object orientation → key change/comparison → visible result → return to whole.
2. **Phone-scale readability first:** size key contacts and state differences so they read at mobile scale before detailing backgrounds.
3. **Action-ready separation:** build exposed hidden faces and separate only layers that actually move or occlude independently.
4. **Real subject change:** show actual state transitions in the locked medium; Ken Burns pans, particles, or label swaps never replace process motion.
5. **Preview with narration:** watch normal-speed voiced playback at phone scale and record gaps under [stage evidence](quality-acceptance.md#stage-evidence-for-art-methods).
6. **Expand within covered risk scope:** add samples for new objects, scales, or mechanisms before full expansion.

### Actual Implementation of Approved Designs

Compare full rendered composites directly beside the approved design board (bound via [shotbook references](shotbook.md#bind-design-and-asset-references)) for silhouette, space, lighting, edges, color, and text. Fix form divergence at the asset level rather than hiding it with grading or filters.

## Preserve Recognition and Give the Topic Room

In authorized 2D scopes, keep natural colors and coherent authorship across wide scenes and close-ups without reverting to dark thin-line slides. Prioritize colors in order: **scientific factual colors > variable-color semantics > theme colors > decorative accents** (never rely on color alone when shape or line style can reinforce distinction).

### Handle Potentially Disturbing Imagery

Flag likely distressing visuals (exposed organs, wounds, substantial blood, graphic surgery/dissection) at storyboarding and asset selection, recording `shots[].shotbook.claim_support` and `shots[].visual_note`:
- Cut incidental graphic detail or reframe via external cues / before-and-after observables.
- Use clean non-graphic cutaways or schematics for necessary internal anatomy, preserving realistic soft-tissue compliance and circumferential deformation rather than replacing soft organs with rigid metal pistons, dies, or blades.
- Keep raw graphic detail completely out of 0–5 s hooks, covers, and thumbnails; inspect affected cuts/masks under [viewing safety](quality-acceptance.md#reviewers-and-viewing-safety).
- **No peeled-skin, carved-window, or body-horror cutaways in AI video or covers:** NEVER prompt or accept peeled, carved-open, translucent, or glass-sleeved human skin exposing subcutaneous vessels, blood, flesh, or needle/pin piercings on human hands, fingers, or limbs in **either AI video or covers** (including watercolor/editorial "cutaway windows"). Anchor human exterior topics on clean, intact human scenes (e.g., an intact sunlit hand wearing a neat fabric bandage) cutting cleanly to standalone non-fleshy microscopic biophysics or pure non-human schematics.
- **Full-resolution `1920×1080` inspection:** Always inspect opening Frame 0 and hero frames at full `1920×1080` resolution (never rely solely on shrunk `270–480 px` contact sheets) before passing hooks or final renders.

## Pure-2D Explanation and Real Assets

In explicitly authorized `pure_2d` mode, explain mechanisms through 2D art/animation (with painted volume and shading allowed, no pseudo-3D). Live-action observation anchors require verified authorized user capture (`real_footage`); on AI-generated routes, disclose generated media accurately without pretending it is live action ([science and rights](science-and-rights.md#minimum-production-statement)). Design wide, medium, and close-up views separately so subjects stay unmistakable at phone scale under [audiovisual correspondence](production-checkpoints.md#match-each-sections-picture-sound-and-in-picture-text).

## Aspect Ratio and Frame Composition

Default canvas is `1920×1080` (16:9) HD landscape using `landscape_captions` in `series-profile.json`. Compose subjects, safe areas, and captions across the full frame with purposeful negative space (never stretch frames, crop contacts, add filler particles, or shrink the frame into a corner to dodge UI).

The `1080×1920` [vertical feed package](viral-appeal-and-packaging.md#package-the-landscape-master-for-vertical-feeds) is a delivery derivative of the accepted 16:9 master: dark night-viewing bands hold the persistent topic/question header above the picture and re-wrapped captions below (from a textless master + formal SRT), without relaxing in-picture text rules.

### Whole-Film Color and Composition Thumbnail Strip

Assemble storyboard key states in sequence to check shot-size progression, focal centers, value/accent roles, density, and visual repetition; verify transitions and rhythm in the voiced rough cut.

## Text, Centering, and Motion

Keep all necessary text phone-readable using legally obtained editable fonts (never model-drawn text or shrunk proxy raster text). Ordinary synchronized captions remain an editable 2D layer (`1–2` semantic lines in the lower safe zone; never split terms or numbers from units), with close-fitting backplates computed from actual glyph bounds and a stable final-line baseline. On Controlled 3D routes only, in-picture auxiliary markers are strictly limited to editable [3D single-letter markers](spatial-typography.md). Non-3D annotations follow [precision technical annotations](annotation-style.md) and [landscape annotation tokens](../assets/style/precision-annotations.tokens.json).

### Body Auxiliary Text: Use and Hold

- **No upper-left or upper-right scene descriptions in body shots** (no shot titles, process tags, or recurring corner chapter badges; chapter overviews belong only in dedicated transition frames).
- **3D routes:** Prohibit all explanatory picture text (words, units, plaques); allow ONLY necessary single-letter spatial markers under [spatial typography](spatial-typography.md) while keeping synchronized captions 2D.
- **Non-3D routes:** Apply the deletion test — add concise auxiliary labels/units/conditions ONLY when removing them loses information needed for the current observation (never duplicate spoken narration or label obvious views).
- **Readable dwell:** Respect `audience_text.auxiliary_reading` floors in [production policy](../config/production-policy.json) as one continuous, stable, legible reading interval (excluding entrance/exit animation or occlusion). Verify at normal speed and phone scale without pausing.

## Audience Picture and Delivery Records

Centralize text inventory in `episode.presentation_text`. Keep production processes, tool limits, versions, and QA status strictly out of audience picture.

### Visible Text Purposes and Production Excuses

Every on-screen, caption, voiceover, and cover text item must serve a real audience/legal purpose (`topic`, `mechanism`, `accessibility`, `scientific_condition`, `attribution`, `license`, `ai_simulation`, or explicitly consented `watermark`). Prohibited categories (`material_defect`, `internal_qa`, `production_excuse`, `production_meta` — e.g. “素材不足只能这样画” or “本片验收已通过”) must be deleted even if rephrased.

- Keep scientific qualifications where needed (`cue_review` with `interpretation=scientific_condition` when flagged); fulfill AI/simulation disclosures via platform controls and companion records by default (`placement=companion`).
- Maintain `presentation_text` (`channels`, `items` covering formal voiceover/caption text in original order, `required_notices` with `placement=audience|companion` and `placement_basis`) and inspect actual media at G2/G3/G5 in `qa.presentation_text.<stage>` (binding formal UTF-8 sources, `companion_notices`, and G5 covers). Source screening aids only; actual media inspection is required.

### In-Picture Markings Require Specific Consent

Never burn AI notices, watermarks, credits, or production markings into video, captions, covers, or assets without explicit user consent covering exact `text`, `surface`, `position`, `time_range` (`[0, 1]` for covers), and `graphic_sha256` (`user_approval.scope`, `user_message_ref`, `user_quote`, `evidence {file, sha256}`). Ordinary synchronized captions and necessary non-3D scientific labels are exempt.

Bind `overlay_evidence {file, sha256}` at G2/G3/G5 using [overlay-evidence-template.json](../assets/overlay-evidence-template.json) and `scripts/label_permission_guard.py`, checking actual corners, openings/endings, captions, and subject areas. When AI itself is the scientific topic, clear keyword false positives via `cue_review` (`interpretation=scientific_subject`) without granting marking permission.

## Design the Two Cover Ratios Independently

Compose one large recognizable subject inside a topic-matched realistic setting with a 1-line topic title and 2-line question in the upper left (the film must answer that question). Never substitute a captioned video frame, raw 3D viewport box, mechanism slide, blank/gradient backdrop, or mechanical crop. Compose `3:4` and `4:3` (and `1:1`/`16:9` when requested) independently.

### Realistic Backgrounds for Every Cover

Every commissioned cover across all ratios, languages, and routes MUST use a **realistic background** showing where the subject genuinely operates, occurs, or is tested, with credible perspective, lighting, materials, and depth ([original visual provenance](science-and-rights.md#original-visual-provenance-contract)). Cartoon scenery, flat graphics, unrelated scenery, and bare studio backdrops fail review. Keep the upper-left title zone calm and evenly lit (bright or dark) so flat type reads cleanly.

### Finished Cover Standards for Engineering and Manufacturing Topics

| Item | Production & review standard |
| --- | --- |
| Content promise | Match the film's actual question and scope; never promise “全流程” or parameters the film omits |
| Subject & framing | One large immediately recognizable subject (lower-center or center-right foreground/midground); keep outer housing visible if using a clean cutaway |
| Materials & science | Accurate material light response (metal, glass, resin, frost, composites) with clean geometry and zero body-horror cutaways |
| Title & question | **Strictly locked via `config/production-policy.json` (`cover_typography`) and `scripts/compose_cover.py` — never write ad-hoc typography scripts or tweak fonts/sizes/colors by eye.** **(1) Locked font:** Chinese uses **`Noto Sans SC`** only (`main_weight=850`, `subtitle_weight=740`, `allow_fallback_family=false`); English uses locked `fonts.en` (`800`/`700`). **(2) Fixed pixel grid (`no_auto_shrink=true` — shorten copy if overflowing):** `1:1` (`1080×1080`): `108/56 px` (`x=64,y=64`, EN `84/42`); `3:4` (`1080×1440`): `114/60 px` (`x=64,y=68`, EN `88/44`); `4:3` (`1440×1080`): `110/58 px` (`x=72,y=62`, EN `90/44`); `16:9` (`1920×1080`): `128/66 px` (`x=88,y=74`, EN `108/54`). Strictly **1-line** topic noun + **2-line** `\n`-separated question. **(3) Closed `cover_typography.color_presets` only (`stroke_shadow_or_backing=false`, flat fill, zero strokes/shadows/boxes):** `daylight_terracotta` (`#994B37` / `#193E4B`), `daylight_navy` (`#1E3246` / `#243F4D`), `dark_terracotta` (`#E39B78` / `#EAE4D8`), `dark_ocean_gold` (`#F2C14E` / `#E6F1F5`). Never rely on AI-rendered cover text. |
| Background & light | Authentic topic setting with clean low-clutter upper-left title zone matching light (`luma >= 0.48`) or dark (`luma <= 0.22`) presets |
| Ratios & delivery | Independently compose requested ratios (default `3:4` + `4:3`); bind finished images, text-free bases, editable text layers, phone thumbnails, comparisons, and receipts in `qa.covers` |

### Production Workflow

1. Lock subject, authentic setting, and 1-line title + 2-line question.
2. Build clean text-free art per commissioned ratio, then typeset strictly via:
   `python -X utf8 scripts/compose_cover.py compose <raw.png> --ratio <1:1|3:4|4:3|16:9> --title <1-line> --question <line1\nline2> --palette <daylight_terracotta|daylight_navy|dark_terracotta|dark_ocean_gold> --lang <zh|en> --output <out.png> --report <new-receipt.json>`
3. Inspect full-size exports and phone thumbnails (`270 px` portrait / `360 px` landscape) plus disturbing-imagery safety; recheck repairs independently.

### Actual Cover Image Binding and Release

Bind `qa.covers.visual_review {file, sha256}` using [cover-review-template.json](../assets/cover-review-template.json) (`approved_cover` or `initial_style_reference`), each ratio's locked `typography` block from `compose_cover.py` (checked by `scripts/cover_guard.py`), phone previews, and baseline comparisons. Record realistic-setting observations in `observations.style_match` and fail stylized/unrelated backgrounds. Validate with `scripts/check_episode.py <episode.json> --stage covers --report <new.json>`.

### Series Cover Consistency at Publication

Keep `Noto Sans SC` weights, per-ratio pixel grids, closed color presets, upper-left 1+2 hierarchy, editorial subject finish, and realistic contextual backgrounds strictly consistent across the series via `scripts/compose_cover.py`. Compare every new cover against the series baseline at full and phone sizes; verify selected cover and crop in G6 prerelease preview (post-submission verification stays with the user under [publication handoff](production-checkpoints.md#manual-clicks-and-publication-review-handoff)).

### Transferable Practices from Approved Covers

- **`3D打印`** (sunlit lab workbench + UV resin vat; “光照进液体，/ 为何只硬一部分？”)
- **`车窗结霜`** (winter dawn frosted windshield + pines; “气温没到0°C / 为何先结霜？”)
- **`涡轮叶片`** (open morning hangar + cutaway blade + turbofan; “为什么 / 做成空心？”)
- **`漏电保护器`** (sunlit residential panel + cutaway breaker; “漏了一点电，/ 怎么知道要跳闸？”)
- **`间歇泉`** (mineral cone + white water jet + open sky; “为什么 / 喷喷停停？”)
- **`爆米花`** (golden kernels vs fluffy white popped corn; “为什么 / 突然开花？”)

Transfer the pattern (authentic topic setting, large clear subject/cutaway, calm upper-left title zone, flat `1+2` typography); recompose freshly for each topic and ratio.

## Sound Quality

All voice synthesis, conversational phrasing, mastering, and dual listening belong to [voice reference](voice-reference.md) (and [realistic sound direction](realistic-direction.md#sound-make-the-pictures-world-audible) for layered ambience/foley).

## Three-Scale Form and Production Detail

Design establishing, medium, and close-up views separately so contours, line weights, and detail density fit each scale (never blindly zoom a medium asset). Refine in order: **silhouette/proportions → structure/contacts → value/edges → necessary materials**. For objects requiring independent movement/occlusion, maintain editable separated layers and clean backplates (verify by hiding/nudging layers without baked duplicates or holes). Keep semantic colors stable under lighting/grading (track source/working/Rec.709 spaces separately), target `>= 4.5:1` contrast for body text against worst moving frames, and bind design boards via `design.board_reference` + `design.approval.actual_feedback_ref`.

### Detail Retention in the Final Encoding

Compare working master against final encode at normal playback size first, then zoom to diagnose lost fine lines, edge halos, gradient banding, texture crawl, or semantic color drift. Fix at the responsible source/scaling/encode step rather than applying blanket sharpening or bitrate bloat.

## Positive Completion Standards for Finely Finished 2D

Evaluate A/D/I items below against applicable references in the film's locked medium (identity, structure, composition, color semantics, contacts, rhythm, and continuity apply across realistic, 3D, and 2D; layer-split checks apply only to controllable layered pipelines).

### Animation Scene Design and Execution

Carry main animation through real subject states and interactions under [animation scene design](animation-scene-design.md), keeping auxiliary graphics supportive and reusing [stage art evidence](quality-acceptance.md#stage-evidence-for-art-methods).

### Substantial Pictures and Finely Developed Scenes

If a frame feels empty, check whether the promised state change, comparison, or structural detail is actually shown; fix framing, state progression, spatial lighting, and scale anchors under [emptiness diagnosis](animation-scene-design.md#diagnose-what-is-missing-first) instead of stuffing filler decoration.

### Representative Samples and L2/L3 Calibration

Pick high-risk segments (dense mechanism, scale/medium join, negative-space composition) and compare matched before/after revisions item by item without fabricating bad drafts to fill tables.

### Static Picture A01–A10

| ID | L3 finish requirement | Check focus |
| --- | --- | --- |
| A01 Contour & shape | Accurate silhouette, intentional proportions/curves; no generic blob placeholders | Overview + phone scale against structural refs |
| A02 Structure & contacts | Credible joints, supports, and internal close-up detail matching environment finish | Inspect joints/contacts and full composite |
| A03 Composition & priority | Core question/focus readable first; purposeful negative space | Full frame + phone scale value/edge hierarchy |
| A04 Color & value | Clear role separation; lighting/grading preserves scientific variable colors | Foreground/background contrast + shape backup |
| A05 Space & occlusion | Clear depth, support, occlusion order, and cross-shot spatial identity | Check occlusion and viewpoint bridges |
| A06 Lines & edges | Clean corners, masks, and edge hierarchy surviving final encoding | Native, zoomed, and final-encode edge check |
| A07 Materials & light | Consistent, object-attached shading/textures stable in motion (when used) | Compare on/off; reject crawling or weak-form glow |
| A08 Detail density | Deliberate rhythm of focus detail vs simplified background | Remove nonfunctional clutter; verify motion stability |
| A09 Scale adaptation | Wide/medium/close views designed separately with consistent identity | Bind `design.keyframe_scales.{whole_scene,object_midshot,mechanism_closeup}` at G3 |
| A10 Typography & annotations | Legal editable fonts, clean glyph bounds, accurate leaders, readable holds | Check densest captions and moving backgrounds |

### Continuous Action D01–D08

| ID | L3 finish requirement | Check focus |
| --- | --- | --- |
| D01 Expressing relationships | Visible actions/states directly prove the causal or comparative claim | Normal-speed playback verifying real subject change |
| D02 Time allocation | Clear time for recognition, process, comparison, and holds matching narration | Thumbnail strip + voiced rough cut rhythm |
| D03 Spacing & paths | Natural trajectories, speed curves, and undistorted motion extremes | Inspect keyframe spacing; match real physics |
| D04 Anchors & contact | Fixed fulcrums/contacts stay locked; sliding/separation obeys mechanics | Motion extremes and occluded contact checks |
| D05 Intermediate states | Continuous topology/color/layers with zero ghosting or residual old layers | Full playback + start/mid/end checks |
| D06 Primary & secondary action | Supporting motion obeys physics and stays subordinate to main claim (when needed) | Verify no forced squash/recoil on rigid bodies/rays |
| D07 Camera & bridging | Motivated framing/scale moves preserving orientation on entry and return | Verify recognizable anchors across cuts |
| D08 Attention planning | Picture, markers, captions, and sound sequence attention without collision | Check segment-by-segment against actual audio |

### Whole-Film Integration I01–I05

| ID | L3 finish requirement | Check focus |
| --- | --- | --- |
| I01 Explanatory closure | Question, premises, mechanisms, boundaries, and answer close cleanly | Independent explanation/expression review on film alone |
| I02 Sound & picture rhythm | Warm natural narration, aligned accents, clean room tone and mix | Full normal-speed dual listening (headphones + phone) |
| I03 Channel division | Picture proves, narration guides, captions match, labels minimal | Deletion test; no triple-repeated prose |
| I04 Whole-film consistency | Coherent form, type, material, and motion language across acts/scales | Full playback + thumbnail strip across joins |
| I05 Editable assets & compositing | Independently moving layers have clean backplates and reproducible versions | Hide/nudge check + source version binding (when applicable) |

### Reusable Explanatory Frameworks and Implementation Choices

Adapt [explanation recipes](../assets/explanation-recipes.json) to the topic's real relations, and consult [external skills curation](video-skills-curation.md) only within the locked medium and route.

### Connection Topology and Interface Continuity

Whenever pipes, cables, linkages, or connectors appear, design explicit port roles (confirmed by documentation/real observation, never guessed from color), diameter/fittings transitions, coaxial mating/insertion, occlusion order, and continuity across cuts/motion.

- In `shots[].shotbook.connections`: if absent, record `applicable=false`, honest `not_applicable_reason`, and `links=[]`. When present, record `links[]` (`id`, `kind`, `from`/`to` with `object_id/port_id/role/role_basis`, `diameter_and_transition`, `joint_geometry`, `occlusion`, `continuity`, plus `topology_change_reason` for intentional disconnect/reconnect).
- At G3 (`qa.visual_frames.animation.connection_review`) and G5–G7 (`qa.visual_frames.connection_review`), inspect overview, joint close-up, and motion/cut key states continuously and bind `status`, `actually_inspected`, `media_sha256`, `plan_sha256` (`connection_guard.plan_sha256(episode, shot_ids)`), `reviewer`, and per-link `observations` (`topology_and_ports`, `diameter_and_transition`, `joint_geometry`, `occlusion`, `continuity`) + `views`.
