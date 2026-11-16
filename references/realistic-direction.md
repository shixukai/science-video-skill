# Realistic direction: honest, clear, told, heard, paced and finished

This page is the craft handbook for realistic films. The [realistic production contract](realistic-production.md) owns main-picture rules, records and sample evidence. This page decides how to design, generate, cut, mix and finish a live-action-looking science film so that it is rigorous, easy to follow, told as a story, credible to the ear, well paced and physically finished. It applies to the local MoneyPrinterTurbo route, the [Google Flow route](google-flow-production.md) and verified user captures within each route's actual controls.

Everything here works inside existing stages and records. It adds no approval gate, score or per-shot form. Use a section when its decision is live for the current shot or failure; leave inapplicable rows unused. Measured screening from [`scripts/realistic_audit.py`](#measure-the-edit-before-judging-it) locates problems for a reviewer; it never accepts a film.

Film-level decisions go in the optional `design.realistic_direction` record (`stance`, `thread`, `camera_package`, `scene_preambles`, `ambience_by_location`, `grade_reference`, `audit_reports`). Shot-level decisions go in `shotbook.realism.observation_level` and `time_scale`, the action card and the bound generation submission. Leave a field empty rather than guessing, and do not backfill it after generation as if it had directed the work.

## Use this page by stage

| Stage | Decisions to make or check here | Where they live |
| --- | --- | --- |
| G1 paper design | Truth register and time scale per shot; observing stance; one place/object thread; scene coverage sets and screen direction; shot jobs; narration-first shot lengths; camera package and light plan; sound plan per location; magnitude translations with fact cards | Brief, script, `shotbook.realism`, `design.realistic_direction`, action cards |
| Hook sample (0–5 s) | Register of the hook shot and how it is marked, usable-core in-point, first event sound, first spoken line within the payload deadline | Existing hook records and `scripts/opening_hook.py` report |
| G2 sound rough cut | Coverage and shot jobs actually read; pacing by narration and job; ambience continuity; narration–picture alignment; first retell probe | `qa.expression_plan`, edit timeline, audit report |
| G3 representative sequence | Physical plausibility audit of the hardest event; screen direction; texture, light and grade matching inside a scene; event-sound sync; register signposting | `qa.visual_frames`, failure ledger, audit report |
| G4/G5 candidate and final | Whole-film camera, light and grade consistency; cadence; digital silence; evidence colors after grade; final-encode banding and detail | G5 review records, audit report of the exact export |

## Rigor: what a photoreal shot claims

A shot that looks filmed is read as a record. Viewers believe the subject looks like this, moves like this, sounds like this and happens this fast. The production disclosure (“AI生成，非实拍/观测”) covers provenance. It does not cover a wrong speed, an impossible color or an invisible quantity made to look photographed. Rigor in realistic film means keeping each of those silent claims true.

### Assign a truth register to every shot

Decide the register before writing the prompt and record it in `shotbook.realism.observation_level`. Mark a change of register the first time it happens.

| Register (`observation_level`) | What viewers infer | Permitted look | Framing on first use (example narration) | Never |
| --- | --- | --- | --- | --- |
| Verified capture (`naked_eye` or `instrument`, medium `authentic_recording`) | This happened, as filmed | The actual footage; crop, speed and grade recorded | Only speed or processing that changes meaning: “这段画面放慢了四倍。” | Generated shots cut in as if they were part of the capture |
| Reconstruction (`naked_eye`) | This is what it looks like at true size and speed | Photoreal at true scale and real time, physically plausible | None per shot; the episode disclosure applies. Name it a recreation when viewers could take it as a specific record (a named person, place, date or experiment): “我们按实验记录重现了这一幕。” | A specific historical event, person or experiment presented as documentation |
| Instrument view (`instrument`) | This is what the instrument shows | The instrument's real output (see the next table) | Name the instrument or speed once: “放慢大约三十倍”“这是显微镜下的样子”“热像仪里，越亮越热。” | An instrument view with color, depth, blur or lighting the instrument cannot produce |
| Model (`not_observable`) | This is an explanation, not a picture of reality | Realistic host plate plus a clearly non-photographic explanation layer, a warm non-graphic 3D biological cutaway anchored to the host organism, or the existing [per-shot nonrealistic exception](realistic-production.md#declaration-structure-and-validation-scope) | “示意一下”“如果我们能看见水分子……” | Glossy photoreal atoms, electrons, field lines, heat or forces lit and focused as if a camera saw them, or unexplained industrial fixtures substituted while narration names biological organs |

Instrument views keep the look markers of the real instrument:

| Instrument | Real look markers | Typical generated error |
| --- | --- | --- |
| High-speed camera | Bright, hard light; no motion blur inside a frame; under mains lighting, visible 100 Hz flicker (50 Hz mains) | Soft motion blur; dim, moody light |
| Time-lapse | Locked camera; shadows sweeping consistently with the light source; clouds and people streaking | Camera drift; light jumping |
| Macro | Very thin focal plane with strong focus falloff; working light close to the subject | Everything in focus |
| Optical microscope | Bright-field disc or full field, thin focal plane, color only from real stains or optics | Glossy 3D lighting and depth of field like a macro lens |
| Electron micrograph (SEM) | Grayscale; very large depth of field (no bokeh); edge-bright topographic shading; color only as stated false color | Colored “photographs” with bokeh |
| Thermal camera | Low resolution; a palette that maps temperature with a stated scale; measures surface emission, so glass is opaque and polished steel reads falsely cold and reflects | Seeing through glass; a palette with no meaning |
| Schlieren | Refractive-index gradients against a uniform field; monochrome or knife-edge color; silhouetted objects; no depth | Colored smoke presented as air flow |

Mark a register change with the cut as well as the words: a change of framing family, a distinct sound treatment for instrument views, or a hold on the transition. When a hook opens on an instrument view before narration can name it, the sound treatment marks the register and the verbal marker comes at the register's first return. Do not repeat the framing on every later shot in the same register.

### Declare and verify time scale

Record `shotbook.realism.time_scale` as `real_time`, `slowed_xN`, `time_lapse_xN` or `edited_ellipsis`. Video models drift toward a default dreamy slow motion and smooth, weightless movement, so verify the scale from the frames rather than trusting the prompt.

- **Free fall and ballistics.** Fall time is `t = √(2h/g)`. At the policy's 30 fps delivery, a 0.1 m fall takes about 0.14 s (≈4 frames), 0.5 m about 0.32 s (≈10 frames), 1 m about 0.45 s (≈14 frames) and 2 m about 0.64 s (≈19 frames). Frame-step the fall; observed duration divided by expected duration is the actual slow-down factor, and it must match the declared `time_scale`.
- **A built-in clock.** Droplets, sparks or crumbs flying in frame are ballistic. At `slowed_xN` their apparent downward acceleration is `g/N²`, so a shot with no deliberate fall can still be timed.
- **Oscillation.** A pendulum or hanging object swings with period `T = 2π√(L/g)`: about 1.0 s for 0.25 m and 2.0 s for 1 m. A lamp or rope swinging slowly reads as huge or slowed.
- **Size and speed are coupled.** Gravity-driven motion scales with the square root of length, so miniature effects are filmed slowed by `√(scale ratio)` to look full-size. Undeclared slow motion therefore makes small rigid subjects read gigantic and heavy. The rule fails for liquids, droplets and flames, where surface tension and viscosity dominate: slowed small water still reads small, so judge droplet size and breakup, not speed alone.
- **Flames.** Buoyant flames flicker faster when smaller. The pool-fire correlation `f ≈ 1.5/√D` Hz (D in metres) holds for buoyant pool and burner fires from a few centimetres to tens of metres and gives about 5 Hz for a 0.1 m fire. A candle in still air burns steadily, and a premixed gas-hob flame is a steady blue cone; flicker on either is a defect.
- **Sparks and discharges.** Real sparks and lightning strokes are brief; a discharge crawling for seconds is slowed or fake.
- **Frame-rate conversion is a speed change.** Never conform 24 fps material to 30 fps by playing its frames faster. That speeds motion by 25% and silently breaks `real_time`. See [motion blur and frame rate](#motion-blur-and-frame-rate).

When the scale is wrong, choose one of two fixes: regenerate with timing and states described, or declare the true slow-down and frame it as an instrument view. Never retime a clip only to fill narration. A deliberate speed change is a new `time_scale` and is recorded.

### Audit physical plausibility on the hardest event

At G3, watch the representative sequence at normal speed, then frame-step the key event. Check the rows relevant to this topic. These are the most frequent failures of generated footage in science subjects.

| Domain | What real footage shows | Typical generated failure | First repair |
| --- | --- | --- | --- |
| Liquids | Water breaks quickly into sheets and droplets; volume is conserved through pours; surfaces settle flat; viscosity matches the liquid | Syrupy water, glasses refilling, splashes hanging in the air, levels tilting | Describe the liquid and its viscosity, start and end levels; condition on the start frame; shorter clip |
| Steam, smoke, flames | Steam appears a little above the hot surface and vanishes as it mixes with dry air; smoke persists and drifts; flames rise and flicker at a size-consistent rate | Steam that behaves like smoke, flames that sway like cloth, smoke from boiling water | Name the actual phenomenon; specify where it forms and how it disappears |
| Light | Shadows agree with visible sources; reflections show the surroundings and shift with parallax; refraction bends or inverts the background; caustics appear under sunlit water or glass | Shadows in two directions, reflections of nothing, glass that does not refract | Describe the physical light sources and their positions; reduce reflective clutter |
| Rigid mechanics | External gears counter-rotate and internal ring gears co-rotate, with speeds in inverse ratio to tooth counts; belts and chains share surface speed, and crossed belts reverse direction; wheels roll without slipping; tools touch before they cut | Gears turning the same way, teeth that never mesh, effects before contact | Use verified user capture or controlled 3D for the precise mechanism; keep generated shots for context |
| Heat and phase change | Ice melts from its surfaces; boiling bubbles nucleate on hot surfaces; condensation forms on cold surfaces | Uniform melting, bubbles appearing mid-liquid without cause, fog on hot surfaces | State the heated and cooled surfaces in the shot card |
| Bodies and organisms | Correct counts (five fingers, six insect legs, eight spider legs), joints bending one way, plausible gait | Extra fingers, fused limbs, legs sliding | Frame on hands only when needed; regenerate; partial framing |

A wrong physical event is repaired at its source. A caption that explains away visibly wrong physics is not a repair.

### Keep numbers, instruments and readable surfaces honest

Generated gauges, screens, labels, packaging and charts produce gibberish or plausible wrong values. Keep generated instrument faces defocused, out of frame or turned away. Show a real value only from the fact card, through the medium's permitted [text layer](visual-system.md#body-auxiliary-text-use-and-hold) or narration. A generated chart is never data.

### Show safe procedure; frame hazards as hazards

What looks real gets copied. When people handle tools, heat, chemicals, electricity or animals, grip, sequence and protective equipment follow the sourced safe practice. When the topic is a hazard, show the event as an accident or consequence from a safe framing, never as a deliberate step a viewer could repeat. Say that it is dangerous, give the complete safe action the source supports, and never stage a hazardous step as a casual demonstration or a how-to.

### Protect evidence colors

Flame, indicator, spectral, tissue, mineral and material colors follow the fact card through prompt, generation, grade and encode. Mention added dye or false color once (“给水染了点颜色，方便看清”). The bright style never re-tints evidence; compare sampled evidence regions before and after the grade.

### Speak the register without slowing the film

Put the marker inside a sentence that already carries content, at first use:

- “这一下只用了不到十分之一秒——我们把它放慢了大约三十倍。”
- “这是显微镜下的洋葱表皮，颜色来自染料。”
- “分子看不见，这里先示意一下它们怎么排队。”

One clause is enough. A separate disclaimer sentence costs a beat and is rarely needed.

## Accessibility: make the unfamiliar feel already known

Realistic footage has one big advantage over diagrams: viewers already recognize kitchens, hands, rain and engines. Spend that recognition deliberately.

### Show, then name, then use

Introduce a term in this order: the viewer sees the thing happen; narration names it once while it is on screen; later narration uses the name without redefinition. Example: the drop visibly vanishes into a swelling bubble → “水一下子变成了蒸汽，这叫汽化” → later lines just say “汽化”. Never name before showing, and never introduce two new terms in one shot.

### Translate magnitudes into things viewers can picture

Convert large or small quantities into a comparison of the same dimension that the film can show: volume to a familiar container, length to a hand or a hair, time to a blink, mass to a known object. Prefer objects this audience handles every day. Compute the comparison, record it in the fact card with its rounding, and keep one comparison per magnitude. Example: at 100 °C and normal pressure, steam occupies about 1,600 times the volume of the hot liquid water it came from (about 1,700 times if measured from room-temperature water). One tablespoon (≈15 mL) therefore becomes about 24–25 L of steam, more than a standard 18.9 L water-dispenser bottle: “一勺水变成的蒸汽，比一整桶桶装水还多。” Show the spoon and the bottle; do not stack a second comparison on top.

### One new idea per shot, one task per moment

A shot introduces at most one new relationship. While viewers must locate a referent, do not also introduce a term, a camera move and a caption change. Apply [competing attention](viewer-retention-design.md#diagnose-competing-attention-before-making-the-edit-faster).

### Let hands and familiar objects carry scale

Use hands, tools, coins, leaves, doors or a person in frame whenever size matters, with optical cues that agree (shallow focus reads small, deep focus reads large). Prefer hands and partial figures to faces. They read instantly, drift less between generations, avoid the uncanny, and keep attention on the subject. A recurring person needs a fixed identity reference (conditioning frame or ingredient) with the same wardrobe, hands and setting.

### Analogy shots

When an [analogy](production-checkpoints.md#expression-plan-for-each-key-difficulty) becomes its own live-action shot, show only the correspondence that holds, then cut straight back to the real process at the matching position, direction or action. Internal biological explanations in `Model` register should stay anchored to the host organism's clean anatomical cutaway rather than cutting to unexplained industrial fixtures while narration names biological organs.

### Probe with a retell

For each section, write the one sentence a non-specialist should be able to repeat after watching it. At G2, compare that sentence with what the cut actually shows, using the existing [understanding probe](quality-acceptance.md#probe-understanding-without-inventing-an-audience-test). Ensure the visual sequence explicitly answers the viewer's most immediate physical counter-question (for example, why a soft circular sphincter stretches around an already-firmed block instead of rounding it back out). If the sentence needs a word or step the film never showed, repair the section.

## Narrative: build scenes, not shots

Generated footage arrives as isolated beautiful clips. A film needs scenes: connected shots in one place and time that let viewers watch something happen and understand why it matters.

### Choose one observing stance

| Stance | Best for | Camera behavior | Risk to avoid |
| --- | --- | --- | --- |
| Observer | A phenomenon that unfolds by itself (frost, a storm, a reaction) | Patient, mostly locked-off, returns to the same vantage | Passive beauty with no question |
| Investigator | Comparisons, tests, take-apart explanations | Hands in frame, inserts on what the hands reveal | Turning into a staged lab advert |
| Follower | A transfer chain or journey (one drop, one workpiece, one signal, one sample) | Tracks the same object through places and scales | Losing the object at a scale jump |

Record the stance in `design.realistic_direction.stance`. A change of stance needs a visible cue, such as the hands reappearing or the tracked object being found again.

### Give every shot a job

Each shot does one of these jobs: **orient** (where and what), **ask** (a visible question or difficulty), **evidence** (the change that answers part of it), **turn** (a new condition that changes the result), **payoff** (the answer becomes visible) or **return** (the opening situation, now understood). Write the job beside the shot in the action card. A shot with no job is cut or merged; a beauty shot survives only as a payoff or return hold. Questions come from something visible that does not yet make sense, and each “但是……” is followed by a shot that shows the “but”; the [whole-film direction](viewer-retention-design.md#direct-the-whole-film-before-polishing-its-parts) owns the larger arc.

### Cover a scene the way a crew would

For each scene, plan a coverage set rather than a single clip:

1. **Establishing**: the place and the active object, wide enough to orient.
2. **Action medium**: the person, tool or event doing the work.
3. **Mechanism insert**: the close detail that carries the explanation.
4. **Consequence**: the result or reaction that proves the change.
5. **Re-establish** (when the next beat depends on it): back to orientation before leaving the place.

Not every scene needs all five. A scene made only of inserts loses orientation, and a scene made only of wides never shows the mechanism.

Make the set match:

- Generate the set together under one scene preamble so place, light and lens agree.
- Condition inserts on stills taken from the selected wide, and start a match-action shot from the previous clip's last frame where the model supports it.
- Keep the 180° line and screen direction (pour, fall, travel, flow) across the scene. Reject mirrored generations; keep eyelines and hand sides consistent.
- Design the cut points between shots: match action phase, direction and screen position.

### Carry one thread

Choose one real place or object that the opening establishes, the body revisits as the question advances, and the ending [shows again with new understanding](viewer-retention-design.md#make-the-opening-image-understandable-by-the-ending). Record it in `design.realistic_direction.thread`. Stakes come from the topic's real consequences; do not stage accidents, failures, reactions or danger the sources do not support.

## Shot cards and generation prompts

### Write a shot card before the prompt

Keep these fields in the existing shot design and bind the actual submission in `shotbook.origin`. They are the prompt's source of truth, not an extra form.

| Field | Write | Example |
| --- | --- | --- |
| Job and register | Shot job, truth register, time scale | turn; instrument; slowed_x30 |
| Subject | Identity, true size, material and condition | one clear water drop, about 4 mm, in neutral soybean oil |
| Action | Physical driver, start state → end state, on-screen duration at the declared scale | drop just below the surface → flashes into a vapor bubble → bursts up through the oil; about 15 s on screen at slowed_x30 (≈0.5 s real), cut as shots 5a/5b/7 from continuous takes or matched angles |
| Place | Real setting, period, wear, what is in the background | home kitchen, stainless pan on a gas hob |
| Light | Physical sources, direction, quality, color temperature, and which source is neutral | daylight window camera-left (neutral); warm range-hood light above |
| Camera | Height, distance, lens equivalent, focus depth, support and move, capture and playback frame rate | oil-surface level, 100 mm macro equivalent, shallow focus, locked-off, high-speed capture played at 30 fps |
| Sound need | Event and ambience sounds this shot must carry | stretched sizzle and burst; kitchen room tone |
| Exclusions | What must not appear | text, hands, extra objects, smoke |

### Word prompts physically

- **Describe physics, not praise.** Words such as cinematic, epic, 8K, ultra-detailed, hyperrealistic, masterpiece, award-winning, stunning, dramatic lighting, vibrant colors or “documentary look” tend to pull generators toward the glossy, over-sharpened AI look. Replace them with light sources, lens, material and action.
- **Reuse one scene preamble verbatim** for every shot in a scene: place, light sources and their positions, lens default and playback frame rate. Change only the shot-specific clauses, and never move the key light inside a scene.
- **One action per clip**, with its start state described. A clip asked to do three things does none of them cleanly.
- **Name the camera support and move** (“locked-off on a tripod”, “slow slider move left about 20 cm”) instead of “dynamic camera”.
- **Describe true imperfections only**: the patina, water spots or wear the real object has at this distance, consistent with [art direction](art-direction.md#image-cleanliness-locate-the-source-of-snow-like-noise-first). Do not ask for dirt or grain to fake realism.
- **Handle exclusions carefully.** Put exclusions in the model's negative-prompt field when it has one. In many video models, words like “no smoke” or “no hands” in the main prompt can summon the object, so describe the wanted state positively instead (“clear air above the pan”, “only the oil surface and the pan rim in frame”). Still check the output.
- Use the language the active model follows best; keep the audience-language narration separate.

Example for the turn shot above (scene preamble, then the shot clause):

> Scene: a home kitchen in daylight; stainless steel pan on a gas hob; neutral soybean oil; soft daylight from a window camera-left, warm light from the range hood above; 50 mm equivalent unless stated; 30 fps playback.
> Shot: extreme close-up at oil-surface level, 100 mm macro equivalent, locked-off on a tripod, shallow focus with the pan rim softly out of focus; a hard shaft of sunlight from the same window, camera-left, lights the oil surface brightly. A single clear water drop has just sunk below the surface of shimmering hot oil; it flashes into a vapor bubble that swells under the surface and bursts upward, throwing small oil droplets outward in arcs. High-speed footage captured at about 900 fps and played back at 30 fps, so this phase lasts about four seconds on screen with no motion blur. Clear air above the pan; only the oil surface, the drop and the pan rim in frame.

### Generate and select in the right order

Generate the number of candidates the risk deserves; a context wide needs fewer than the key mechanism. Reject at internal normal-speed previews before paying for final quality. Select in this order and stop at the first failure: **science and physics → identity, screen direction and continuity with neighbors → action readable at phone size → texture → beauty.** A gorgeous candidate that fails physics is discarded, not graded.

## Sound: make the picture's world audible

Live-action picture over silence, or over narration alone, reads as fake within seconds. Build the track in layers from sources that the selected route and [science and rights](science-and-rights.md) permit, under the narration master owned by the [voice reference](voice-reference.md#one-narration-master-and-one-shared-processing-chain) and the final mix defaults in the production policy.

| Layer | Direction | Starting point to calibrate by listening | Failure to return |
| --- | --- | --- | --- |
| Room tone and ambience | One continuous bed per location/act, carried across cuts in that location and crossfaded cleanly (`150–400 ms`) when the world changes | Clearly audible in narration gaps on a phone speaker, never masking consonants under narration; avoid dropping individual shot foley fades to `0.0` at every cut | Digital silence between clips; ambience restarting or pumping down/up at each cut |
| Event sound | Contacts, pours, clicks, ignitions and impacts on their visible frame | Within one frame of the visible contact for nearby events | Early or late hits; one generic whoosh for different events |
| Sound perspective | Close shots near and detailed; wide shots with more room and distance | Change perspective with shot scale, not per clip | Close-miked sound on a distant wide |
| Instrument views | A distinct, restrained treatment for slowed or magnified views (stretched or softened event sound) | Consistent across all shots of that register | Real-time sound over obviously slowed picture |
| Generated baked-in audio | Keep only sound that matches picture and science; mute generated speech, music and mismatched effects | Decide per clip before the mix | Invented voices or music under narration |
| Music | Transitions, aesthetic holds and the ending; ducked or out under explanation and evidence | Lower than ambience during key evidence | Constant music masking event sound |

- **Sync.** Viewers detect sound that leads the picture by more than about 45 ms or lags it by more than about 125 ms (ITU-R BT.1359), so keep nearby contacts within one frame. Distant events are the exception: sound lags about 3 ms per metre (one frame per roughly 11 m at 30 fps). Keep that delay when distance is part of the scene or the science. Narration semantics follow the policy's `semantic_sync_warning_ms`.
- **Phones.** Small phone speakers reproduce little deep bass, so an impact carried only by low frequencies disappears. Give event sounds a mid/high transient and check on both policy listening environments.
- **Silence by design.** Before a reveal, drop to room tone, never to digital zero.
- **Across cuts.** Use J-cuts and L-cuts so the next place is heard a moment before it is seen, or let a sound continue across a cut to bind two shots.
- **Science sound is evidence.** Delays, pitch and silence follow the source, as with thunder after lightning. A satisfying effect never replaces a sourced sound relationship.

## Pacing: cut by what the viewer needs

### Use each clip's usable core

Image-to-video clips often begin on the conditioning still and ramp up to speed; long generations can drift, morph or freeze near the end. Step through the head until the action runs at full speed and set the in-point there. Check the tail for identity drift or a freeze and set the out-point before it. The [hook trim](ai-generated-video.md#realistic-route-steps) applies to every generated shot. The audit reports `slow_ramp_head` and `frozen_tail` per shot.

### Let narration and the shot's job set its length

Estimate each shot's length from its narration first, then apply the job's minimum picture time:

1. **Narration time.** At the policy speech rate of 180–240 CJK characters per minute (185–220 CJK/min on counter-intuitive mechanisms), Mandarin runs at about 3.2–3.8 characters per second; count characters, not words, and measure the actual track once it exists.
2. **Job minimum.** The table below gives the least picture time a job needs even without words.
3. **Shot length** is the larger of the two, plus any wordless hold. If narration outruns one shot by far, split it into coverage (for example, ask → insert) rather than holding one clip or slowing it.

| Job | Minimum picture time (starting point) | Ends when |
| --- | --- | --- |
| Orient | 1–2 s | The place and active object are recognized |
| Action / ask | 2–4 s | The action completes or the question is visible |
| Evidence comparison | Change duration plus about 1 s | Viewers can compare before and after |
| Payoff or aesthetic hold | 1.5–3 s | The result has landed, with ambience and no new words |
| Compressed repetition (montage beat) | 0.5–1.5 s each | The accumulating change is clear |

Holds longer than about 1.6 s keep residual subject motion (droplets settling, steam clearing, a sizzle dying down) or are recorded as reviewed observation holds under [subject-motion review](quality-acceptance.md#subject-motion-and-long-static-holds). The [roughcut](viewer-retention-design.md#let-the-roughcut-determine-order-and-duration) and the actual narration decide the final lengths.

### Break the generator's cadence

Fixed generation lengths make every shot last the same time, which flattens attention. Vary length by narration and job, change shot size or angle meaningfully between consecutive shots of the same subject, and cut on motion so energy carries across the join. The audit flags `uniform_cadence` when several consecutive shots have nearly identical lengths; keep such a run only for a deliberate rhythm.

### Choose cut points

- Cut on action, in the middle of a movement whose phase matches across the cut.
- Group outdoor wildlife/live shots and 3D cutaway/model sequences into sustained multi-shot chapters (`4–7` chained shots per chapter for multi-stage mechanisms) rather than ping-ponging bright outdoor scenes and dark studio shots on isolated single shots (`world_ping_pong_cuts` in `google_flow_audit.py`); use restrained `0.20–0.30 s` dissolves only across world transitions when the editing environment supports them, or a matched whole-to-part anatomical bridge.
- Offset sound and picture slightly (`0.12–0.30 s` J-cuts and L-cuts inside natural breath valleys) so narration carries seamlessly across cuts instead of freezing on dead pauses before every edit.
- Cut after a state change completes, not just before it. Never cut away during the change the narration promised.
- Bring the referent on screen at or slightly before the noun that names it.
- Mandarin often puts the result at the end of the clause (“……一下子变成了蒸汽”). Land the visible event on that verb, and leave about 0.2 s of picture after the comma before cutting.
- Build each section as a wave: compress what is already understood, slow down at the key observation, release with a hold, then open the next question.

Never loop, freeze or slow clips to cover narration. Restructure the edit, tighten the line or generate the missing action.

## Texture: one camera, one light, one grade

### Fix a camera package

Decide the package once per film, record it in `design.realistic_direction.camera_package`, and describe it identically in every prompt of a scene.

| Item | Example decision |
| --- | --- |
| Lens family by role | Establishing 24–35 mm equivalent; medium 50 mm; detail 85–100 mm macro |
| Focus depth logic | Deep focus for places and machines; shallow for small objects and hands; macro falloff only at macro scale |
| Camera height | Eye or counter height for human scenes; surface level for small phenomena |
| Frame rate and shutter | Deliver 30 fps constant (policy default) with motion blur of about a 1/60 s shutter; declared high-speed instrument shots are blur-free by design |
| Support vocabulary | Tripod, slider, dolly, macro rail, handheld (human scenes only) |

### Motion blur and frame rate

Generate at or near the delivery frame rate and conform every source before editing. Some cloud models deliver only 24 fps; for example, Veo output on the Flow route is commonly 24 fps. Never conform 24 fps material by playing frames faster: that speeds motion by 25% and breaks `real_time`. If only 24 fps exists, use motion-compensated conversion when its output is artifact-free at normal speed, or record the resulting speed change as a new `time_scale`. Frame-blended conversions smear motion, and duplicated frames stutter on movement; the audit flags `duplicate_frames_in_motion`. Apart from declared high-speed shots, frames that are razor-sharp during fast motion read as computer-made.

### Move the camera as a real crew could

| Move | Use it for | Generator default to avoid |
| --- | --- | --- |
| Locked-off | Evidence, comparisons and state changes, so subject change is not confused with camera change | Constant drift over a comparison |
| Slow slider or dolly | Reveals and gentle parallax in places | Floating orbits around everything |
| Macro rail push-in | Entering a small detail at macro scale | Impossible continuous zoom from aerial to microscopic without a cut |
| Handheld | Human activity and presence only | Handheld shake on objects or nature scenes |
| Crane or drone | Real geography when the place matters | Swooping through spaces a drone could not fly |

### Diagnose the AI-look signature

| Symptom | Likely cause | First repair | Not a repair |
| --- | --- | --- | --- |
| Waxy, over-smooth surfaces and skin | Generator smoothing; denoise or upscaler | Physical material words; another candidate; gentler upscale | Added grain or sharpening |
| Halos, glow and oversaturation | Style-inflation prompt words; HDR-like look | Remove style words; describe real light; restrained grade | Global desaturation that kills evidence colors |
| Ringing and crunchy edges | Upscaler sharpening | Lower sharpening; native-resolution generation | Blur |
| Boiling fine texture in motion | Temporal instability of fine detail | Simplify fine patterns; shorter clip; another seed | Heavier compression or noise reduction that makes it waxy |
| Everything in focus at macro, or fake uniform bokeh | Lens not described | Lens and focus depth in the prompt | Post blur painted on |
| Morphing small details (fingers, threads, text, liquid volume) | Weak identity conditioning, long clip | Condition the start frame; shorter clip; reframe | Fast cutting to hide it |

Decorative grain, vignette, glow and blur stay out under [art direction](art-direction.md#image-cleanliness-locate-the-source-of-snow-like-noise-first). Historical 2D illustration texture tokens (`bright-nature.tokens.json`) never license grain or noise overlays on realistic footage.

### Keep light continuous

Within a location, keep the key direction, time of day and color temperatures, with motivated sources (window, lamp, sky, the hob). Decide which source is neutral (for example, 5600 K daylight) and keep fixed offsets for the others in every shot (range-hood tungsten around 3000 K reads warm). Cutting between shots whose shadows flip, or whose warm and cold sources swap, breaks the scene even when each shot is beautiful.

### Grade in a fixed order

1. **Conform**: frame rate, resolution and color space to the delivery settings. Tone-map phone HDR/HLG captures to Rec.709 here.
2. **Normalize**: match white balance on neutral surfaces, black and white points and exposure across generations, seeds and user captures.
3. **Match within each scene**: shots of one scene read as one camera. Keep skin hue consistent on hands across generations, and keep evidence highlights (oil sheen, steel speculars, wet surfaces) unclipped with a soft roll-off.
4. **Creative look**: one restrained grade for the whole film under the [bright standard](visual-system.md#bright-style-and-premium-materials).
5. **Protect evidence**: compare sampled evidence colors before and after; revert any shift.
6. **Encode check**: inspect smooth gradients (sky, sweeps, steam) for banding. First find the stage that introduced it (8-bit intermediates, repeated compression, a bitrate below the policy's 12–20 Mbps) and fix that stage. Only then consider a minimal dither, and check the result again after platform re-encoding. Dither is an encode fix, not texture.

### Resolution and upscaling

Generate at the highest resolution the model renders stably, then upscale with restraint. Judge at 100% and at phone size, and check temporal stability in motion. Texture invented by an upscaler is not detail; the [HD output](quality-acceptance.md#hd-video-output) rules apply.

## Measure the edit before judging it

`scripts/realistic_audit.py` screens an actual export for problems that are tedious to find by eye. Its thresholds are calibratable starting points in `config/production-policy.json` under `realistic_audit`.

    python -X utf8 scripts/realistic_audit.py measure <export.mp4> --report <new-audit-report.json> [--shots <shots.json>] [--preview-dir <local-preview-dir>] [--delivery-fps <fps>]

`--shots` takes the edit's actual shot list, `[{"id": "SH1", "start_s": 0.0, "scene": "kitchen"}, ...]`. It is more reliable than automatic cut detection, which finds only hard cuts and misses dissolves and soft cuts. `--delivery-fps` overrides the policy rate when the episode's `design.output` specifies another frame rate. Bind each report in `design.realistic_direction.audit_reports`.

| Flag | Meaning | Look at |
| --- | --- | --- |
| `frame_rate_mismatch` | `r_frame_rate` and `avg_frame_rate` differ by more than 1% (variable frame rate), or the rate differs from the policy delivery rate or `--delivery-fps` | Conform settings |
| `duplicate_frames_in_motion` | Repeated frames inside moving passages, typical of 24→30 conversion | Source frame rates, conversion method |
| `uniform_cadence` | At least four consecutive shots of 1 s or longer whose lengths sit within about ±12% of each other | Pacing by narration and job |
| `slow_ramp_head` | A shot's first 0.3 s moves much less than its own body, typical of an untrimmed image-to-video head | In-point |
| `frozen_tail` | A shot's last 0.3 s is frozen while its body moves | Out-point; freeze padding |
| `grade_jump_in_scene` | Luma, white balance or saturation jumps across a cut between two shots labeled with the same scene; needs `--shots` scene labels, so auto-detected cuts never raise it | Shot matching |
| `digital_silence` | RMS below −70 dBFS for at least 0.15 s on a 16 kHz mono downmix | Room tone continuity |
| `no_audio_stream` | The export has no audio | Mix and export |

Coverage limits: shots shorter than about 0.9 s are not screened for ramps or freezes, so montage beats need eyes. Cross-scene grade differences are reported in `cuts` but never flagged.

With `--preview-dir`, the audit writes a side-by-side image for each flagged item: the frames on both sides of a flagged cut, the first frame against a body frame for a ramp head, and a body frame against the last frame for a frozen tail. Exit codes are 0 for no flags, 1 for flags to review and 2 for an input or execution error. A flag is a place to look; record an intentional choice (a deliberate freeze, a rhythmic montage) as such in the existing review notes. A clean report proves nothing about science, story or beauty.

## Diagnose by symptom

| What the reviewer notices | Likely dimension | First repair | Not a repair |
| --- | --- | --- | --- |
| “Looks fake” but every frame is pretty | Sound or physics: silent bed, wrong speed, weightless motion | Ambience and event layers; verify the time scale | Grading or sharpening |
| “Where are we?” after a cut | Narrative coverage: missing establishing or re-establish shot; flipped screen direction | Add the coverage shot; keep the 180° line and a thread anchor | A location caption |
| “What am I looking at?” in a close-up | Accessibility: insert before orientation; term before showing | Orient first; show, then name | More narration |
| Narration feels rushed over the pictures | Pacing: shots sized by clip length, not narration | Narration-first lengths; split into coverage | Faster speech or slowed clips |
| Boring though informative | Pacing: uniform cadence, untrimmed heads, no holds | Cut by narration and job; trim to the usable core; add payoff holds | Faster narration or more effects |
| Each shot beautiful, film incoherent | Texture: no camera package, light or grade continuity | Scene preamble; normalize and match the grade | A heavier overall look |
| An expert objects to a shot | Rigor: register, time scale, physics or color | Reassign the register; regenerate; reframe as a model | A disclaimer caption |

## Worked example: why does a drop of water make hot oil explode?

This is a planning illustration of every section above. Numbers marked as fact-card items still need sources before production. Speech times assume about 4.2 CJK characters per second (≈250 per minute, inside the policy range); picture times follow the narration-first rule and are replaced by measured times once the track exists.

- **Question:** 为什么热油里进一滴水，会“炸锅”？
- **Facts to source:** at room temperature water is denser than cooking oil (≈1.00 vs ≈0.92 g/mL), and hot oil is lighter still (≈0.82 g/mL near 180 °C), so a drop sinks. Frying oil is around 160–190 °C, far above water's 100 °C boiling point at normal pressure. Steam occupies about 1,600 times the volume of its hot liquid water. The expanding vapor bursts through the oil and throws oil droplets. On an oil fire: turn off the heat, slide a lid on from the side, keep it on and leave the pan until it cools; never use water. Also source fire blankets and kitchen (Class F) extinguishers, and if the fire spreads, leave and call 119.
- **Stance:** investigator (a cold-versus-hot comparison carried by hands). **Thread:** the pan and the greens being cooked. **Camera package:** counter height; 35 mm establishing, 50 mm medium, 100 mm macro equivalent; locked-off for evidence; 30 fps playback. **Light:** daylight window camera-left is neutral; range-hood tungsten above reads warm in every kitchen shot. **Ambience:** kitchen room tone with range-hood hum.

| # | Job | Register / time scale | Picture and camera | Sound | Narration (zh) | Chars → speech | Picture time |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Hook: ask | instrument / slowed_x30 (verify) | Frame 0 mid-burst: oil droplets flying from one drop, macro at surface level with the pan rim and a strand of greens in frame; locked-off; hard window light from camera-left | Stretched crack and sizzle at frame 0, marking the instrument register | 一滴水，油就炸了。 | 7 → 1.7 s (≤245/min opening cap; onset ≤0.1 s) | 2 s |
| 2 | Orient + stakes | naked_eye / real_time | Wide: kitchen, pan of shimmering oil, hands patting washed greens dry with a towel | Room tone, hood hum, soft towel | 炒菜前要把菜沥干，就是为了躲开这一下。 | 17 → 4.0 s | 4 s |
| 3a | Ask | naked_eye / real_time | Medium close: greens held at the pan edge; a drip falls by accident (about 5–10 cm, ≈3–4 frames of fall), pops and spits; the hand pulls back | Small pop, sizzle | 油有一百七八十度，水一百度就开—— | 14 → 3.3 s | 3.5 s |
| 3b | Ask (consequence) | naked_eye / real_time | Insert: tiny oil spots landing on the hob around the pan, settling | Sizzle dying down | 它为什么不悄悄蒸发，偏要炸？ | 12 → 2.9 s | 3.5 s |
| 4a | Evidence: setup | naked_eye / real_time | A clear glass of cold oil on the counter; a hand holds a dropper of dyed water above it | Quiet room tone | 先看冷油，水染了色。 | 8 → 1.9 s | 2.5 s |
| 4b | Evidence | naked_eye / real_time | Side view, locked-off: the dyed drop sinks and rests at the bottom, wrapped in oil | Tiny plink | 同样大小，水比油重，会直接沉下去，被油整个包住。 | 20 → 4.8 s | 5 s |
| 5a | Turn | instrument / slowed_x30 (verify) | Hot pan, macro: a drop just under the surface | Stretched sizzle, low rise | 换成热油，沉到油下的水 | 10 → 2.4 s | 3 s |
| 5b | Turn | instrument / slowed_x30 (verify) | The drop flashes into a swelling vapor bubble under the surface | Rising rumble | 一下子变成蒸汽——画面放慢了大约三十倍。 | 17 → 4.0 s | 4 s |
| 6a | Evidence (magnitude) | naked_eye / real_time | A tablespoon of water held over the counter | Room tone | 水变成蒸汽，体积会胀大一千多倍。 | 14 → 3.3 s | 3.5 s |
| 6b | Evidence (magnitude) | naked_eye / real_time | The spoon beside a full 18.9 L water-dispenser bottle, hand for scale | Room tone | 一勺水变成的蒸汽，比一整桶桶装水还多。 | 17 → 4.0 s | 4 s |
| 7 | Payoff | instrument / slowed_x30 (verify) | The bubble bursts through the surface and throws oil droplets outward in arcs; the droplets settle during the hold | Burst crack, droplets pattering | 这么多蒸汽要从油底下冲出来，就把上面的油一起掀了出去。 | 25 → 6.0 s | 6 s + 1.5 s hold with settling droplets |
| 8a | Turn: hazard | naked_eye / real_time | A small, contained flame in a pan on the hob; no hands near it; no water, no fireball | Low flame roar | 同样的道理，油锅起火时泼水，火会被蒸汽一下掀起来。 | 22 → 5.2 s | 5.5 s |
| 8b | Turn: safe action | naked_eye / real_time | A hand turns the knob off (≈1.3 s), then cut: a lid slides on from the side, held like a shield, and seals the pan; the flame goes out | Knob click, lid scrape and clank, roar cut off | 先关火，用锅盖从侧面推上去盖严； | 14 → 3.3 s | 3.5 s (two clips) |
| 8c | Turn: safe action | naked_eye / real_time | The lid stays on; the pan is left untouched on the hob | Room tone returns | 别掀盖、别端锅，等它凉透。 | 10 → 2.4 s | 3 s |
| 9 | Return | naked_eye / real_time | The dried greens go into the oil with a gentle, even sizzle; same wide as shot 2 | Steady pleasant sizzle; music enters softly | 沥干的菜下锅，只剩下这阵好听的滋啦声。 | 17 → 4.0 s | 4 s + 1.5 s hold with steam rising |

The plan runs about 60 s of picture over about 54 s of speech; the difference is wordless holds and job minimums.

What the example demonstrates:

- **Registers:** shot 1 marks the instrument register by sound because no narration can name it within the hook; the verbal marker arrives in shot 5b, within the register's first return (5a–5b), and the slow-down factor is verified from frames.
- **Rigor:** the dye is disclosed because color is evidence, and the density claim is phrased for equal sizes.
- **Accessibility:** the magnitude is computed (15 mL × about 1,600 ≈ 24 L, more than 18.9 L) and shown with an everyday object rather than just said.
- **Safety:** the drip is an accident rather than a demonstration, and the hazard comes with the complete sourced safe action and no fireball.
- **Narrative and scale:** hands carry scale and stakes without faces. Coverage moves wide → medium → insert → consequence → return. The ending returns to the opening situation, now understood.
- **Pacing:** lengths follow the narration and the job, long lines are split into coverage, and holds keep residual motion.
- **Sound and light:** ambience runs continuously through the kitchen, and the window key stays camera-left in every shot.
