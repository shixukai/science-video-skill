<a id="爆款吸引力诚实钩子包装与留存"></a>
# Viral appeal: honest hooks, packaging and retention

Use this page to make a science film that ordinary viewers choose, keep watching, and share. It applies to editorial topic selection and to every complete new film meant for feed platforms. A user-selected topic keeps its scope; apply these methods to find its strongest honest entry instead of changing the topic. The [topic contract](topic-contract.md) owns the question and scope, [viewer retention](viewer-retention-design.md) owns explanation progression, [visual system](visual-system.md#design-the-two-cover-ratios-independently) owns cover finish, and [production checkpoints](production-checkpoints.md#platform-topic-selection-and-data-review) owns platform data records. This page owns appeal screening, package-first design, the first two seconds, retention cadence, interaction and the post-publication learning loop. Only the [first-two-seconds contract](#win-the-first-two-seconds) adds records (`topic_alignment.opening.hook`, `qa.opening_hook`) and a measured/cold-tested check; the other sections add no gate, score or schema.

A hit science video usually combines four things: a **broad entry** many people recognize, a **first-second pull** that stops the scroll, **continuous visible payoff** that keeps viewers watching, and a **reason to share or comment** afterward. Every hook must be honest: the film itself delivers what the title, cover and first seconds promise. Promise mismatch is a concrete editorial risk to inspect, not proof of a particular exit/comment cause. Honesty is required regardless of measured performance; whether a package improves outcomes remains a hypothesis until comparable data exists.

## Screen appeal before deep research

For editorial topics, generate several angles on the same object before choosing one: how it is made, why it fails, its extreme version, a surprising comparison, a common misconception, what it costs or what precision it needs. Then check each angle against these drivers:

| Appeal driver | Test question | Honest example (verify before use) |
| --- | --- | --- |
| Broad entry | Have most adults touched, used, seen, chosen or worried about this? | 电磁炉、轮胎、手机镜头、冰块、电梯 |
| Real surprise | Is there a sourced fact that contradicts a common expectation? | 冰是固体却比水轻 |
| Visible spectacle | Is there a process that is satisfying to watch: forming, cutting, melting, assembling, slow motion, a cross-section reveal? | 瓶胚吹成饮料瓶的连续变形 |
| Extreme scale | Is there a sourced extreme of size, precision, speed, force or temperature? | 比头发丝细得多的芯片线宽 |
| Personal stakes | Does it affect viewers' money, safety, health or a daily choice, without fear-mongering? | 为什么轮胎花纹磨平后雨天更危险 |
| Social currency | Will viewers gain something to tell a friend or settle an argument? | 一个能当场演示给别人的解释 |
| Timeliness | Does it connect to a current season, event or product release, without exploiting tragedy? | 季节现象、新品发布涉及的技术 |

A selected editorial topic should have a broad entry plus at least two other strong drivers, and at least one driver must be visible in the picture, not only spoken. If no angle passes, revise the angle before spending research, generation or rendering time. Record the judgment in the existing topic card: entry and stakes in `adult_relevance`, surprise or mystery in `conflict_or_question`, the spectacle or visible payoff in `causal_visualization`, and the strongest losing angle in `alternatives`. Appeal remains an editorial hypothesis until real platform data exists.

## Design the package before the script

Before locking the G1 script, draft the package viewers will actually see in the feed:

1. **Three to five title candidates.** Each names a concrete object and a concrete question or sourced surprise, within the series title limit in [series profile](../config/series-profile.json).
2. **One or two cover concepts.** One large subject in its most surprising real state (before/after, cutaway, extreme close-up, result), plus a short question. Series cover style and finish still follow the visual system.
3. **The first two seconds.** Run the [hook lab](#run-the-hook-lab-at-g1): at least three hook candidates, each a first picture already in motion, its first sound and a front-loaded first line, written together.

Choose the package with the strongest promise that the film can fully deliver, then write the script to fulfill it. If no candidate is compelling, the angle is weak; revise it now, when it is cheap. Keep title, cover, first frame and first line promising the same question, as checked by the existing [cover-to-opening alignment](topic-contract.md#continuously-check-the-covers-question-against-the-actual-opening). In a recommendation feed the video autoplays from its first frame and the cover is usually not seen first, so the first frame and first line carry the click decision there; the cover matters most on profile, search and series pages.

Candidate title patterns to test for Chinese feed platforms (examples only, each must match the actual film):

| Pattern | Example |
| --- | --- |
| Surprise question | 冰明明是固体，为什么会浮在水上？ |
| Everyday mechanism | 电磁炉隔着玻璃，凭什么能把锅烧热？ |
| Extreme precision | 比头发丝还细的线条，是怎么刻进芯片的？ |
| Transformation | 一个小小的瓶胚，怎样变成你手里的饮料瓶？ |
| Visible comparison | 同样是轮胎，为什么花纹差这么多？ |

Use numbers only when sourced. Do not use “震惊”, “99%的人不知道”, invented danger or claims the film does not show. A process-chain title such as “全流程” requires the film to cover that chain.

## Win the first two seconds

Feed platforms report two-second exits, and a recommendation feed autoplays the film from its first frame. For every complete new film intended for feed platforms, the first two seconds are therefore designed first, produced first at final quality and tested on the actual export. The rules below are production defaults with values in [production policy](../config/production-policy.json) `opening_hook`, not optional advice. A departure needs a recorded commission or scientific reason; commissioned direct answers, chapters and local excerpts follow their scope. Body sections keep the topic contract's rule that explanation, not a stopwatch, decides duration.

### Why openings lose viewers

Diagnose the actual opening against these failures before polishing anything else:

| Failure seen in the first two seconds | Why viewers leave | Repair |
| --- | --- | --- |
| Context-first line such as “杯里的冰浮在水面。同样是水，结冰后为什么……” | The tension arrives at four to five seconds; the first clause states something ordinary | Put the tension in the first clause: “冰是固体，却浮在水上。” Move the context into the picture |
| Throat-clearing starters: “大家好”, “你知道吗”, “你有没有想过”, “今天我们来聊”, “在我们的生活中”, “这是一个……” | Nothing happens; the viewer hears a format, not a reason | Delete them; start with the object and its event |
| Look-directions: “先看”, “看这个”, “我们来看看”, “想知道……？先看……” | Announces viewing instead of giving the observation | Let the picture show it and say what it means |
| Slow empty establishing wide shot, aerial, generic scenery or a tiny distant subject | Nothing recognizable at phone size | Open on the subject in its most striking honest state at phone-readable scale; when the topic is a part inside a larger host, keep the active host or functional host cabin/bay recognizable rather than retreating to tiny distant exteriors, empty scenery or an unrecognizable fragment |
| Isolated internal mechanism, unrecognizable fragment or floating studio cutaway when the topic is a part inside a larger machine, vehicle, appliance or organism (or a distant simplified exterior shell that hides cabin/bay action) | Viewers either see disembodied parts without knowing what host system they belong to, or see a tiny simplified exterior far from the mechanism | Establish macro host-to-part orientation inside the 0–5 s opening: open on either the complete host or an immediately recognizable functional host space/cabin/bay (for example a driver's cockpit with steering wheel, seat, belt path and pillar, or an appliance's working bay) in real action and drive an unbroken single-take push-in or simultaneous cutaway directly into the mechanism's mounting site by 5 s; do not force a whole-exterior view when a functional cabin/bay already establishes unmistakable host identity at higher detail |
| A still-looking first half-second: an image-to-video clip that starts on its conditioning still, a Blender action or camera easing in from rest, a Ken Burns push on a still | Reads as a paused or loading video | Cut in mid-action at peak motion; trim the slow head of generated clips; no ease-in on the first shot |
| Fade from black, logo, title card, music intro, audio fade-in or leading silence in the narration master | Dead time while the thumb is moving | Hard start: fully exposed first frame, sound present at frame 0, first syllable by 0.35 s |
| First caption late or missing | Many feed viewers watch muted | The first caption line is on screen from frame 0 when narration starts there |
| A 16:9 film shown in a vertical feed | The landscape picture plays as a band of roughly one third of the phone height | Large, central, high-contrast subject; recognition must not depend on fine detail |
| A hook unrelated to the film's question | Bait; later exits and distrust | Use an honest moment of this film that the body explains |

### The two-second beat sheet

| Time | Picture | Sound | Caption | The scrolling viewer |
| --- | --- | --- | --- | --- |
| Frame 0 | The subject is already in motion in its most striking honest state, recognizable inside a phone-feed band (for a subsystem/mechanism topic, the recognizable host or functional host cabin/bay is already acting—with an unbroken single-take bridge or simultaneous cutaway—rather than a disembodied rig, unrecognizable fragment or distant empty exterior); fully exposed; no black, fade, logo or title card | Sound is already present: a meaningful event sound or the narration onset, never a fade-in | First caption line visible when narration starts | Sees something happening |
| By 0.35 s | Motion continues | First syllable of narration has started | — | Hears a voice that says something specific |
| By 2.0 s | A visible change, consequence or contrast has happened; a second shot is allowed if each reads at phone size | The **payload clause** (the words that carry the tension) has finished: at most `payload_max_spoken_units` spoken units from the start of the first line, about two seconds at series pace; the tension word comes early in that clause | Caption matches the payload | Can name the object and feel the surprise, contrast, stakes or question |
| 2–5 s | Stay with the same subject; show why it matters, and for a subsystem/mechanism topic complete the unbroken single-take host-to-part bridge from the recognizable host or functional cabin/bay into the mechanism's real mounting site and scale | Say what the film will answer; do not restate the hook | — | Has macro system orientation and a concrete reason to keep watching |

A question is not mandatory. A specific surprising observation, a sourced extreme or a visible consequence often hooks faster than a question. The payload must still be true and shown.

### Find the hook in this film's material

Before writing the first line, list the three to five most arresting visible moments anywhere in the planned film. Typical candidates are the climax reveal, an extreme close-up or cutaway, a failure or breakage, a before/after contrast, the most satisfying moment of a process, an extreme of scale or speed, and a hand acting on the object; visible human action draws attention when it is part of the real operation. Rate each for motion salience (large, fast or transforming), rarity of the view (inside, macro, slow motion), clear stakes, contrast and recognizability inside a phone-feed band. The strongest moment is often a result or climax from later in the film: open on it, then return to the start of the process with a clear signal, and record that return in `hook.return_in_body`.

| `hook.pattern` | First picture (in motion at frame 0) | Front-loaded first line (examples; verify before use) |
| --- | --- | --- |
| `result_first` | The finished product or final state forming | “瓶胚一吹，就成了饮料瓶。” |
| `strange_phenomenon` | The real phenomenon happening | “冰是固体，却浮在水上。” |
| `extreme_contrast` | Two states or objects side by side, already diverging | “叶子都湿了，荷叶却不沾。” |
| `question_with_evidence` | The object performing its task | “隔着玻璃，锅凭什么变烫？” |
| `satisfying_process` | The most satisfying moment of the process | “凸轮一转，顶杆就抬起。” |
| `stakes_in_action` | The consequence that touches viewers' money, safety or daily choice | “胎纹磨平，雨天刹车更远。” |
| `extreme_scale` | A scale anchor beside the extreme object | “这些线，比很多病毒还细。”（首帧已是芯片结构的放大画面） |
| `failure_or_breakage` | The real failure happening | “这根水管，是被冰撑裂的。” |

Rewrite context-first openings by moving the tension forward and letting the picture carry the context: “晴天抬头，太阳之外，大片天空也显出颜色……” becomes “阳光近乎白色，天却是蓝的。” over a moving sky shot; “雷雨夜，远处天空先亮了一下，过一会儿雷声才传来……” becomes “同一道闪电，雷声晚到几秒。” with the flash already on screen at frame 0. Numbers, extremes and comparisons need sources and must match this film's conditions.

### Run the hook lab at G1

1. Record at least `min_candidates` hook candidates in `topic_alignment.opening.hook.candidates`, covering at least two patterns. Each states the first picture, first line and tension; losers state `lost_because`.
2. For the selected hook fill `pattern`, `host_relation` (`standalone` or `part_of_host`; when `part_of_host`, also fill concrete `host_system` and `whole_to_part_bridge` showing how the 0–5 s opening visually anchors the recognizable host or functional host cabin/bay and bridges in one unbroken single-take move or simultaneous cutaway to the mechanism's true mounting site—without retreating to an unnecessary distant exterior or cutting to a floating rig), `first_frame`, `frame0_motion`, `first_sound`, `first_line`, `payload_clause` (quoted verbatim from `first_line`), `tension`, `muted_read` (what a muted viewer understands from picture and caption), `phone_read` (how the subject reads inside a phone-feed band), `source_shot_id` and `return_in_body`. `opening.voiceover` starts with `first_line`.
3. Read the first line aloud at the series pace with a timer. If the payload is not finished by about two seconds, shorten or reorder it; never plan to speed up the voice.
4. `check_episode.py --stage plan` (or `opening_hook.py plan <episode.json>`) checks this structure only. Appeal is decided on actual media below.

### Produce and test the hook first

- **Production priority.** The hook shot is the first shot built to final quality: lighting, material, motion and sound. It is never a placeholder in any version shown for viewing-experience feedback.
- **Hook sample.** The first representative sample of a new film covers 0–5 s at the target canvas and frame rate with the actual narration master excerpt, captions and sound. It may be its own short sample or the opening of the G3 representative sequence.
- **Hard start in the edit.** Align the narration master's first syllable to 0.35 s or earlier by moving or trimming the whole track's leading silence; this is a whole-track offset, not per-shot processing. Do not fade picture or sound in. Place a real event sound at frame 0 when the picture has one.
- **Measure.** Run `python -X utf8 scripts/opening_hook.py measure <export> --captions <captions> --preview-dir <dir> --report <new-report.json>` on the sample and on every complete candidate. It flags black or fading starts, a barely moving first half-second or first two seconds, late sound, late first caption and a murky first frame, and writes a phone-feed strip and a letterboxed 0–3 s feed clip that stay local. Repair flags; record a concrete scientific or commission reason in the report's `exceptions` only when the flag is intended.
- **Cold two-second test.** A fresh reviewer without script, package or production history watches the feed clip and 0–5 s hook sample from frame 0: first 0–2 s muted, then 0–2 s with sound, then continues through 5 s. Record in the report's `cold_test`: what is on screen at 1 s and at 2 s muted, what is heard by 2 s, the object named, the tension or question felt, whether they would stop, and the swipe reason if not; when `host_relation=part_of_host`, also record `host_system_seen` (what host object or functional host cabin/bay is visually recognizable in the picture, never inferred from a caption noun alone) and `part_in_whole_clear` (`true` only when a first-time viewer can visually see what host system the film is about and where inside that host or functional cabin/bay the mechanism sits). Use `context=cold_view` only for a genuine first view; an informed review cannot pass this test.
- **Bind and gate.** Bind the passed sample report under `qa.opening_hook.sample` before G3 approves expansion, and the report on the current final export under `qa.opening_hook.final` before G5. A failed cold test returns to the hook lab: change the picture, pattern, host framing or line. Louder whooshes, flashes, text plates or a faster voice do not repair a weak hook.
- **Non-feed commissions.** Set `qa.opening_hook.status=not_applicable` only with the commission reference and a concrete non-feed reason.

### Keep the hook honest

Hook footage must come from this film's legitimately produced material and must be explained later in the body; a result preview must clearly return to the start of the process, as viewer retention already requires. Do not use “震撼”, “99%的人不知道”, invented danger, false counterintuition or a promise the film does not show.

Reject opening and handoff lines that merely direct the viewer to look, or pair an empty question with an empty 'first look at...' command: they create no observation, tension or payoff. Do not swap them for another stock suspense phrase. In natural spoken language, connect a recognizable object or use with a specific visible change, relevant fact, real difficulty or genuine question; let the following picture and line add a concrete piece of information without dumping the whole explanation upfront. Match claims and visual causality to the actual evidence; a familiar application or comparison must also be accurate.

In a cam demonstration, “想知道它怎么动？先看这个轮子。” just delays the observation. If the footage shows the lift, “凸起转到顶杆下面，顶杆就抬起来了。” gives viewers the action; cut closer on that lift so the next sentence can explain the contact. Use the visible event of this film to write the line.

Apply the [spoken-script edit](voice-reference.md#edit-mandarin-for-the-ear) at G1. Check the opening through the first body observation against the planned cut; repair empty directions, title echoes and unsupported suspense before full narration synthesis. Recheck the affected interval in the existing G2/G5 review.

## Keep a reason to stay

Map these onto the existing `payoff_steps` and section handoffs instead of creating another plan:

- **Payoff cadence.** Viewers should receive a new visible payoff (an observation, a reveal, a satisfying motion) or a sharper question regularly. Find gaps in the actual rough cut; as a starting point, look hard at any stretch of roughly 20 seconds with no new payoff.
- **Concrete re-hooks.** Let the result that just appeared reveal the next specific problem or observation. A visible consequence, a useful comparison or a real question can carry the handoff. “更精彩的在后面” and “看到最后” supply no reason to stay.
- **Escalation.** Order sections so difficulty, stakes or spectacle rise when dependencies allow. Place the strongest reveal late, without withholding the core answer artificially.
- **Purposeful pattern change.** Change scale, viewpoint, sound or rhythm where attention would sag, and make every change carry information.
- **Remove dead air.** Cut greetings, channel introductions, repeated summaries and filler such as “接下来我们来看看”. Keep a natural, brisk narration pace under the accepted voice preset; do not slow down for completeness or speed up artificially.
- **Shareable moments.** Slow motion, macro detail, before/after, cross-section reveals and perfect fits offer candidate moments worth inspecting, not proven rewatch/share effects; plan at least one per film where the topic supports it.

## End fast and invite real interaction

Deliver the answer, return to the opening image with the new understanding, and end. Avoid long outros, recaps and requests for likes. When it is natural, end with one genuine question tied to the content that viewers can answer from their own experience (“你家的锅是哪一种？”), or a final frame that loops cleanly into the first. Do not fabricate controversy to drive comments.

## Duration, format and series identity

The topic contract still lets the complete explanation determine duration; never skip necessary steps to hit a length. When a complete chain is long, propose a series with self-contained questions/payoffs or a separately commissioned cut-down when useful. Neither proposal changes an already commissioned complete-chain film: preserve that deliverable unless the user chooses the changed scope. The series default canvas is 1920×1080 landscape; a vertical version requires an explicit request and its own layout review.

Build series recognition: a consistent title style, cover design and accepted voice; use recurring visual devices such as a cutaway only where the topic supports them. A one-sentence pointer to a next episode is allowed only when that episode actually exists or is committed.

## Scroll-viewer appeal check

Before offering a G2 rough cut or G5 candidate, the reviewer watches from the first frame as a scrolling viewer with no context, then records in the existing `qa.expression_plan` or `qa.expression_review` notes. Start with the [cold two-second test](#produce-and-test-the-hook-first) on the phone-feed clip when it has not already been recorded for this exact file:

1. At frame 0 and about one second: what is on screen and moving, and would I stop?
2. By two seconds: what object can I name, what tension, surprise, stakes or question do I feel, and what would I stay to find out? Check muted and with sound.
3. Through the body: the times where I would swipe away, and why (no new payoff, unclear object, repetition, slow narration).
4. At the end: one thing I could tell a friend, and whether I would comment, share or save.

Swipe-risk points go to the responsible author as concrete repairs. A failed two-second answer returns to the hook lab before other polish. Apart from the bound `qa.opening_hook` record, this check is a diagnostic from an internal reviewer, not an audience test or a score, and it never replaces real platform data.

## Learn from what actually performs

After authorized publication, record each platform's own metrics under [platform data review](production-checkpoints.md#platform-topic-selection-and-data-review), using the platform's field names and definitions (for example 2-second exits, 5-second completion, completion rate, average viewing time, likes, comments, shares, saves and cover click-through). Compare actual exit points with the swipe-risk points predicted before publication, and compare the published 2-second exit rate with the hook's pattern, `opening_hook.py` measurements and cold-test notes. Change one main variable per round (title, cover, hook pattern or angle) under the existing experiment records. When the two-second exit stays high on a vertical-first platform even though the hook passed its cold test, record the landscape band as a private hypothesis and strengthen phone-band composition (larger, more central subject; stronger contrast). The user has declined a default vertical version; keep the 16:9 series canvas and make a vertical cut only when the user explicitly requests one.

Apply [entry/intent/payoff diagnosis and the next-production brief](production-checkpoints.md#diagnose-entry-promise-and-payoff-separately) before turning a metric into an opening, length or style prescription. Search-intent mismatch, recommendation entry loss and delayed explanatory payoff need different tests; average viewing is not an exit timestamp and platform chapter labels are not media truth.

Keep a private, evidence-backed pattern library in the project: which angles, hooks, titles and covers performed, with versions and data windows. Feed it back into appeal screening. Account data, works and feedback stay private; only general methods may enter this public Skill.
