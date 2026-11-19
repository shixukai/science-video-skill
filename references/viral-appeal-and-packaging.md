# Viral appeal: honest hooks, packaging and retention

Use this page to make a science film that ordinary viewers choose, keep watching, and share. It applies to editorial topic selection and to every complete new film meant for feed platforms. A user-selected topic keeps its scope; apply these methods to find its strongest honest entry instead of changing the topic. The [topic contract](topic-contract.md) owns the question and scope, [viewer retention](viewer-retention-design.md) owns explanation progression, [visual system](visual-system.md#design-the-two-cover-ratios-independently) owns cover finish, and [production checkpoints](production-checkpoints.md#platform-topic-selection-and-data-review) owns platform data records. This page owns appeal screening, package-first design, the first two seconds, the viewing promise, the open-loop ledger and retention cadence, ending timing, the vertical feed package, interaction and the post-publication learning loop. Only the [first-two-seconds contract](#win-the-first-two-seconds) adds a gated record (`topic_alignment.opening.hook`, `qa.opening_hook`) and a measured/cold-tested check. The [viewing promise](#lock-a-concrete-viewing-promise-by-about-8-seconds), [open-loop ledger](#keep-one-question-open-until-the-final-answer) and [ending timing](#end-fast-and-invite-real-interaction) add optional planning fields and a screening tool, not a gate or score; the [vertical feed package](#package-the-landscape-master-for-vertical-feeds) adds a delivery record for vertical-feed destinations.

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
2. **One or two cover concepts.** Show one large subject in its most surprising real state against a realistic background from the topic's actual setting. Pair it with an upper-left 1-line topic-noun main title and 2-line question subtitle in flat series colors, following the [cover standard](visual-system.md#finished-cover-standards-for-engineering-and-manufacturing-topics).
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

For every complete new film intended for feed platforms, design and produce the opening first at final quality and test the actual export. Two seconds is an editorial observation point, not a verified platform ranking threshold. The rules below are production defaults with values in [production policy](../config/production-policy.json) `opening_hook`, not optional advice. A departure needs a recorded commission or scientific reason; commissioned direct answers, chapters and local excerpts follow their scope. Body sections keep the topic contract's rule that explanation, not a stopwatch, decides duration.

Prioritize the hard creative choices here, not more paperwork: discover an event, compare how to reveal it, reject weaker alternatives, then make and inspect the existing hook sample. The user's opening-first emphasis does not require 80% of text/runtime, extra candidates or extra generations. Reuse the existing hook, candidate experiment and sample/final records.

### Why openings lose viewers

Diagnose the actual opening against these failures before polishing anything else:

The anti-preamble rule rejects background that delays the observation, not necessary subject naming. Apply [minimum viewer orientation](viewer-retention-design.md#orient-the-viewer-before-introducing-a-detail): put the recognizable object/function and the interesting event or question together. Do not make an unfamiliar technical detail the first payload merely to meet a short timing target; an image that experts recognize may still need a natural spoken referent for general viewers.

| Failure seen in the first two seconds | Risk to inspect, not measured audience causation | Repair |
| --- | --- | --- |
| Context-first line such as “杯里的冰浮在水面。同样是水，结冰后为什么……” or AI clickbait slogan such as “圆出口竟能拉出方便便，它是怎么做到的？” | Context-first delays tension to 5+ seconds; compressed marketing-account contrast slogans (`竟能…怎么做到的`) and coined shorthand (`圆出口拉方块`) trigger immediate AI-voice distrust | Lead with the concrete observation in natural everyday grammar within `payload_max_spoken_units` (`20` units, `~3.5 s`): “这块冰明明是固体，落进水里却自己浮了上来。” Let the picture carry the setting |
| Throat-clearing starters: “大家好”, “你知道吗”, “你有没有想过”, “今天我们来聊”, “在我们的生活中”, “这是一个……” | Nothing happens; the viewer hears a format, not a reason | Delete them; start with the object and its event |
| Look-directions: “先看”, “看这个”, “我们来看看”, “想知道……？先看……” | Announces viewing instead of giving the observation | Let the picture show it and say what it means |
| Slow empty establishing wide shot, aerial, generic scenery or a tiny distant subject | Nothing recognizable at phone size | Open on the subject in its most striking honest state at phone-readable scale |
| A part inside a larger machine, vehicle, appliance or organism shown as an isolated mechanism, unrecognizable fragment, floating studio cutaway or tiny simplified exterior | Viewers see disembodied parts without knowing their host, or a distant shell that hides the action | Apply the [host-to-part bridge](#anchor-a-part-inside-its-host) inside the 0–5 s opening |
| A still-looking first half-second: an image-to-video clip that starts on its conditioning still, a Blender action or camera easing in from rest, a Ken Burns push on a still | Reads as a paused or loading video | Cut in mid-action at peak motion; trim the slow head of generated clips; no ease-in on the first shot |
| Fade from black, logo, title card, music intro, audio fade-in or leading silence in the narration master | Dead time while the thumb is moving | Hard start: fully exposed first frame, sound present at frame 0, first syllable by 0.35 s |
| First caption late or missing | Many feed viewers watch muted | The first caption line is on screen from frame 0 when narration starts there |
| A 16:9 film shown in a vertical feed | The landscape picture plays as a band of roughly one third of the phone height | Large, central, high-contrast subject; recognition must not depend on fine detail |
| A hook unrelated to the film's question | Bait; later exits and distrust | Use an honest moment of this film that the body explains |

### The opening beat sheet

| Time | Picture | Sound | Caption | The scrolling viewer |
| --- | --- | --- | --- | --- |
| Frame 0 | The subject is already in motion in its most striking honest state, recognizable inside a phone-feed band (for `part_of_host`, the recognizable host or functional host bay is already acting; see the [host-to-part bridge](#anchor-a-part-inside-its-host)); fully exposed; no black, fade, logo or title card | Sound is already present: a meaningful event sound or the narration onset, never a fade-in | First caption line visible when narration starts | Sees something happening |
| By 0.35 s | Motion continues | First syllable of narration has started | — | Hears a voice that says something specific |
| By 2.0–3.5 s | A visible change, consequence or contrast has happened; a second shot is allowed if each reads at phone size | The **payload clause** (the words that carry the concrete observation or tension) has finished in natural spoken grammar: at most `payload_max_spoken_units` (`20`) spoken units from the start of the first line (`~3.5 s` ceiling at unhurried series pace), with zero marketing-account clickbait slogans (`竟能…怎么做到的`) or coined 2–4 character shorthand | Caption matches the payload | Can name the object and feel the surprise, contrast, stakes or question without hearing robotic AI compression |
| 3.5–8 s | Stay with the same subject or move toward the thing the promise names; complete any host-to-part bridge by 5 s | The [viewing promise](#lock-a-concrete-viewing-promise-by-about-8-seconds): one concrete sentence naming what the film will show or answer; do not restate the hook | Caption matches | Knows what staying will give them |

### Anchor a part inside its host

When the topic is a part inside a larger machine, vehicle, appliance or organism, open on the complete host or an immediately recognizable functional host space in real action (for example a driver's cockpit with steering wheel, seat, belt path and pillar, or an appliance's working bay). Reach the mechanism's true mounting site and scale by 5 s with one unbroken single-take push-in or a simultaneous cutaway. Do not retreat to a tiny distant exterior, empty scenery, an unrecognizable fragment or a floating studio rig; a functional cabin/bay that already establishes host identity at higher detail needs no added whole-exterior view. Record this as `host_relation=part_of_host` with a concrete `host_system` and `whole_to_part_bridge`.

At **2 s**, ask what the film is about, what visible clue makes it worth watching, and what question remains open. Recognizing the camera, instrument or setting is not the same as recognizing the subject or the clue. See [subject versus source](viewer-retention-design.md#orient-the-viewer-before-introducing-a-detail). This does not require the full first sentence to have finished. The configured payload deadline is **3.5 s**, with at most **20 spoken units**; actual normally paced audio, not word count, establishes timing. Do not accelerate speech to fit the earlier observation point.

A question is not mandatory. A specific surprising observation, a sourced extreme or a visible consequence often hooks faster than a question. The payload must still be true and shown.

### Find the hook in this film's material

Before writing the first line, list the three to five most arresting visible moments anywhere in the planned film. Typical candidates are the climax reveal, an extreme close-up or cutaway, a failure or breakage, a before/after contrast, the most satisfying moment of a process, an extreme of scale or speed, and a hand acting on the object; visible human action draws attention when it is part of the real operation. Rate each for motion salience (large, fast or transforming), rarity of the view (inside, macro, slow motion), clear stakes, contrast and recognizability inside a phone-feed band. A result or climax from later in the film is eligible only when its subject/function and question are understandable in the opening itself; later background cannot retroactively supply a missing referent. Establish that orientation with the first readable picture and natural first line, then clearly signal any return to the process start in `hook.return_in_body`. Choose another moment when that cannot be done without overloading the opening.

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

1. Record at least `min_candidates` hook candidates in `topic_alignment.opening.hook.candidates`, covering at least two patterns. Compare genuinely different events, viewpoints, comparisons or reveal designs, not the same image with three rewritten lines. In existing candidate notes, connect **ordinary expectation → visible surprise/change → one concrete unresolved question → first body evidence**. An honest observation need not contradict a fabricated expectation. Each candidate states picture, first line and tension; `lost_because` compares the strongest rejected alternative on recognizability, visible interest, honest payoff and feasible production. If all candidates merely change wording, return to the material inventory; if the best cannot be produced within scope, choose an executable design instead of expanding permissions or generating indefinitely.
2. For the selected hook fill `pattern`, `host_relation` (`standalone` or `part_of_host`; when `part_of_host`, also fill `host_system` and `whole_to_part_bridge` under the [host-to-part bridge](#anchor-a-part-inside-its-host)), `first_frame`, `frame0_motion`, `first_sound`, `first_line`, `payload_clause` (quoted verbatim from `first_line`), `tension`, `muted_read` (what a muted viewer understands from picture and caption), `phone_read` (how the subject reads inside a phone-feed band), `source_shot_id` and `return_in_body`. `opening.voiceover` starts with `first_line`.
3. Read the first line aloud at a calm conversational pace with a timer. Keep the payload within `payload_max_spoken_units` (`20` units, `~3.5 s`) using natural everyday grammar—never crush normal Chinese syntax into robotic telegraphese (`“圆出口拉方块”`), marketing-account contrast templates (`“竟能…怎么做到的”`), or sped-up speech. Shape the line for the ear: open on a stressed content word, keep the first clause short and land the sentence on the tension word (“冰是固体，却**浮**在水上。”). When the synthesized master excerpt sounds flat or rushed, reword at source; do not add a separate rate, pitch or per-line synthesis outside the one narration master.
4. `check_episode.py --stage plan` (or `opening_hook.py plan <episode.json>`) checks this structure only. Appeal is decided on actual media below.

### Produce and test the hook first

- **Production priority.** The hook shot is the first shot built to final quality: lighting, material, motion and sound. It is never a placeholder in any version shown for viewing-experience feedback.
- **Hook sample.** The first representative sample of a new film covers 0–5 s at the target canvas and frame rate with the actual narration master excerpt, captions and sound. It may be its own short sample or the opening of the G3 representative sequence.
- **Hard start in the edit.** Align the narration master's first syllable to 0.35 s or earlier by moving or trimming the whole track's leading silence; this is a whole-track offset, not per-shot processing. Do not fade picture or sound in. Place a real event sound at frame 0 when the picture has one.
- **Measure.** Run `python -X utf8 scripts/opening_hook.py measure <export> --captions <captions> --preview-dir <dir> --report <new-report.json>` on the sample and on every complete candidate. It flags black or fading starts, a barely moving first half-second or first two seconds, late sound, late first caption and a murky first frame, and writes a phone-feed strip and a letterboxed 0–3 s feed clip that stay local. Repair flags; record a concrete scientific or commission reason in the report's `exceptions` only when the flag is intended.
- **Cold two-second test.** An independent internal reviewer without script, package or production history watches the feed clip and 0–5 s hook sample from frame 0: first 0–2 s muted, then 0–2 s with sound, then continues through 5 s. Record in the report's `cold_test`: what is on screen at 1 s and at 2 s muted, what is heard by 2 s, the object named, the tension or question felt, whether they would stop, and the swipe reason if not; when `host_relation=part_of_host`, also record `host_system_seen` (what host object or functional host cabin/bay is visually recognizable in the picture, never inferred from a caption noun alone) and `part_in_whole_clear` (`true` only when a first-time viewer can visually see what host system the film is about and where inside that host or functional cabin/bay the mechanism sits). Use `context=cold_view` only for a genuine first view; an informed review cannot pass this test or be renamed as a fresh reviewer after revision. The staged muted/sound observation is one first-review session. `sound_at_2s` records what was actually heard, even if the natural payload ends later within its deadline. Continue normal-speed actual watching/listening through the payload, host bridge and first body payoff. This internal review needs no recruited or real-time audience and is not measured retention.
- **Bind and gate.** Bind the passed sample report under `qa.opening_hook.sample` before G3 approves expansion, and the report on the current final export under `qa.opening_hook.final` before G5. A failed cold test returns to the hook lab: change the picture, pattern, host framing or line. Louder whooshes, flashes, text plates or a faster voice do not repair a weak hook.
- **Non-feed commissions.** Set `qa.opening_hook.status=not_applicable` only with the commission reference and a concrete non-feed reason.

### Keep the hook honest

Hook footage must come from this film's legitimately produced material and must be explained later in the body; a result preview must clearly return to the start of the process, as viewer retention already requires. Do not use “震撼”, “99%的人不知道”, invented danger, false counterintuition or a promise the film does not show.

Reject opening and handoff lines that merely direct the viewer to look, or pair an empty question with an empty 'first look at...' command: they create no observation, tension or payoff. Do not swap them for another stock suspense phrase. In natural spoken language, connect a recognizable object or use with a specific visible change, relevant fact, real difficulty or genuine question; let the following picture and line add a concrete piece of information without dumping the whole explanation upfront. Match claims and visual causality to the actual evidence; a familiar application or comparison must also be accurate.

In a cam demonstration, “想知道它怎么动？先看这个轮子。” just delays the observation. If the footage shows the lift, “凸起转到顶杆下面，顶杆就抬起来了。” gives viewers the action; cut closer on that lift so the next sentence can explain the contact. Use the visible event of this film to write the line.

Apply the [spoken-script edit](voice-reference.md#edit-narration-and-dialogue-for-the-ear) at G1. Check the opening through the first body observation against the planned cut; repair empty directions, title echoes and unsupported suspense before full narration synthesis. Recheck the affected interval in the existing G2/G5 review.

## Lock a concrete viewing promise by about 8 seconds

A viewer who stopped for the hook still leaves within the next few seconds when staying has no visible value. Feed platforms report this separately (for example Douyin's 2 s exit and 5 s completion). Right after the payload, and finished by the end of `retention_design.promise_window_s` (`8 s`) in [production policy](../config/production-policy.json), say one concrete sentence that the film will keep:

- It names something the viewer will actually see later (a part, a moment, a comparison, a result) or the specific question the body answers, so it can be checked against the finished film.
- An honest structure count (“关键在三步”) is allowed only when the body delivers that number of distinct steps in that order.
- It is not a contents list, a teaser of the whole answer, a format announcement or a stock suspense phrase (“下面我们就来揭开它的秘密”, “看到最后你就明白了”).
- The picture stays with the hook subject or moves toward the thing promised; do not cut to unrelated context while the promise is spoken.

| Weak promise | Concrete promise (examples; verify before use) |
| --- | --- |
| 今天我们就来揭开冰浮起来的秘密。 | 答案藏在冰晶里这些六边形的空隙里。 |
| 接下来带你看看电磁炉的原理。 | 秘密在玻璃下面这圈铜线，它根本不发热。 |
| 看完你就知道轮胎有多重要了。 | 我们把同一段湿路面，分别换上新胎和磨平的胎试一次。 |

Record `topic_alignment.opening.viewing_promise` with `line`, `fulfilled_by_scope_id` and, once real audio exists, `time_s`. G2/G5 viewing checks that the promised thing is actually and visibly delivered; a promise the film does not keep is a packaging failure in the same way as clickbait.

## Keep a reason to stay

Map these onto the existing `payoff_steps` and section handoffs instead of creating another plan.

### Keep one question open until the final answer

Use the existing `payoff_steps[]` as an **open-loop ledger**. In each step, record the concrete new question it opens in `opens_question` and the question it answers in `closes_question` (`main` for a step that delivers the film's main answer, otherwise the exact text of the earlier question; when the ending delivers the main answer, `ending.answer_time_s` closes it), and add `time_s` once real audio exists. These are optional planning fields, not a gate.

- The main question opens in the first seconds and closes only with the final answer, normally in the last 10–20% of the runtime. Partial answers are encouraged when each one exposes a deeper, specific question.
- Each chapter opens its next concrete question before or as it closes the current one. The viewer should never reach a point where everything they wanted to know is answered while the film continues.
- At G1, list the questions open after each step. Mark the first step after the promise where none is open, and any step that answers the main question early without opening a deeper one. Repair the order or the handoff sentence, not the speech rate.

| Step (example; verify before use) | Opens | Closes |
| --- | --- | --- |
| Hook (0–3 s) | main: 冰是固体，为什么会浮在水上？ | — |
| R1 density comparison | 同样的水分子，为什么结冰后反而占地方更大？ | — |
| R2 hydrogen-bond lattice | 那冰化成水时，这些空隙去哪了？ | 同样的水分子，为什么结冰后反而占地方更大？ |
| R3 melting and 4 °C water | — | 那冰化成水时，这些空隙去哪了？ |
| Ending answer | — | main |

### Payoff cadence and re-hooks

- **Payoff cadence.** Viewers should receive a new visible payoff (an observation, a reveal, a satisfying motion) or a sharper question regularly. As a starting point, look hard at any stretch longer than `retention_design.payoff_gap_review_s` (`20 s`) without a new payoff in the actual rough cut.
- **Concrete re-hooks at every handoff.** Let the result that just appeared reveal the next specific problem: “铜线通电了，可它自己并不烫——那热量是从哪来的？” A visible consequence, a useful comparison or a real question can carry the handoff. “更精彩的在后面” and “看到最后” supply no reason to stay.
- **Midpoint escalation.** Retention commonly sags again once the first explanation lands. Place the second-strongest honest visual reveal (a cross-section, slow motion, an extreme of scale) around 40–60% of the runtime when dependencies allow; never a fabricated twist.
- **Escalation.** Order sections so difficulty, stakes or spectacle rise when dependencies allow. Place the strongest reveal late, without withholding the core answer artificially.
- **Purposeful pattern change.** Change scale, viewpoint, sound or rhythm where attention would sag, and make every change carry information. A single shot longer than `retention_design.long_shot_review_s` with little visual change is a review point, not a cut quota.
- **Remove dead air.** Cut greetings, channel introductions, repeated summaries and filler such as “接下来我们来看看”. Keep a natural, brisk narration pace under the accepted voice preset; do not slow down for completeness or speed up artificially.
- **Shareable moments.** Slow motion, macro detail, before/after, cross-section reveals and perfect fits offer candidate moments worth inspecting, not proven rewatch/share effects; plan at least one per film where the topic supports it.

### Locate retention risks on the actual cut

On a G2 rough cut or G5 candidate, run:

    python -X utf8 scripts/retention_timeline.py measure <export.mp4> --episode <episode.json> --report <new-retention-report.json> [--preview-dir <local-dir>]

It reads the export and the timed ledger and writes a local timeline image. It flags payoff gaps, intervals after the promise with no open question, a late viewing promise, an early main answer, a long tail after the answer, long low-change shots and silent mix intervals. Untimed ledger fields are listed as missing, not passed. Use the flags to choose which intervals to rewatch at normal speed, and record findings in the existing `qa.expression_plan` or `qa.expression_review` notes. A flag that is intended (an aesthetic hold, a deliberate silence) gets a concrete reason in the report's `exceptions`. The tool is a locator, not a gate, score or audience prediction.

## End fast and invite real interaction

Deliver the final answer late (normally in the last 10–20%; earlier than `retention_design.final_answer_min_ratio` of the runtime is a review point). Then return to the opening image with the new understanding and end within `retention_design.answer_to_end_review_s` (`6 s`) of the answer sentence finishing. Record `ending.answer_time_s` once real audio exists. Avoid long outros, recaps and requests for likes. When it is natural, end with one genuine question tied to the content that viewers can answer from their own experience (“你家的锅是哪一种？”). Prefer a last frame that matches the first frame's subject and composition, so a replay loops cleanly. Do not fabricate controversy to drive comments.

## Duration, format and series identity

The topic contract still lets the complete explanation determine duration; never skip necessary steps to hit a length. When a complete chain is long, propose a series with self-contained questions/payoffs or a separately commissioned cut-down when useful. Neither proposal changes an already commissioned complete-chain film: preserve that deliverable unless the user chooses the changed scope. The series master canvas is 1920×1080 landscape. Vertical-feed destinations receive the [vertical feed package](#package-the-landscape-master-for-vertical-feeds) derived from the accepted master; a native vertical re-edit still requires an explicit request and its own layout review.

Build series recognition: a consistent title style, cover design and accepted voice; use recurring visual devices such as a cutaway only where the topic supports them. A one-sentence pointer to a next episode is allowed only when that episode actually exists or is committed.

## Package the landscape master for vertical feeds

A 16:9 film in a vertical feed plays as a band roughly one third of the phone height, and the empty bands above and below carry nothing. For vertical-feed destinations, deliver a 1080×1920 **feed package** derived from the accepted G5 master unless the user asks otherwise:

| Destination | File |
| --- | --- |
| Douyin composer group (Douyin, Xigua, Toutiao, Fanqie Novel) and Xiaohongshu | Feed package. The Douyin composer submits one file to every selected destination, so Xigua receives the package too unless the user asks for a separate landscape Xigua submission |
| YouTube and other landscape-first destinations, the release queue master and the archive | The accepted 16:9 master |

- **Layout.** The master keeps its picture, burned-in captions and sound. It is scaled to the full 1080 px width and centered in the frame. A persistent two-tier header sits in the top band, inside the platform's top safe area: line 1 is the cover's topic noun, and the next one or two lines are the film's question (the same promise as the cover subtitle and the first line). Use flat series colors on a quiet flat band, left-aligned like the cover hierarchy, with no stroke, glow, shadow or backing box. Leave the bottom band clear for platform UI.
- **Text rules.** The header is packaging outside the picture. It does not relax body-text rules or the 3D single-letter rule inside the picture. It must match the actual film question under the [cover-to-opening alignment](topic-contract.md#continuously-check-the-covers-question-against-the-actual-opening), uses no clickbait wording, and never carries AI/production markings, which follow [specific consent](visual-system.md#in-picture-markings-require-specific-consent). Break lines by meaning; do not shrink type to force a long question in.
- **Optional zoom.** `--zoom` up to `feed_package.max_zoom` enlarges the picture by cropping the master's left and right edges. Use it only after checking the whole film that no scientific subject, contact point, label or caption is cut; the report records the cropped fraction. The default is no crop.
- **Make and check it.** Run `python -X utf8 scripts/feed_package.py compose <accepted-master.mp4> --topic <topic noun> --question <question with \n line breaks> --output <feed-package.mp4> --report <new-feed-package-report.json>`. The package is a derivative: it does not reopen G5 picture or sound approval. Actually view, at phone size, the header legibility, the first 5 s and, when zoomed, a scrub through the film for cropping. Record the file in `deliverables.feed_package` and the check in `qa.feed_package` (status, report, package and source master SHA-256, phone-view observation). Upload this file in the Douyin composer and on Xiaohongshu, and check it in the G6 preview.
- **Learning.** Compare 2 s exit and 5 s completion between packaged and earlier unpackaged releases as a one-variable experiment under [learn from what actually performs](#learn-from-what-actually-performs).

## Scroll-viewer appeal check

Before offering a G2 rough cut or G5 candidate, the reviewer watches from the first frame as a scrolling viewer with no context, then records in the existing `qa.expression_plan` or `qa.expression_review` notes. Start with the [cold two-second test](#produce-and-test-the-hook-first) on the phone-feed clip when it has not already been recorded for this exact file:

1. At frame 0 and about one second: what is on screen and moving, and would I stop?
2. By two seconds: what object can I name, what tension, surprise, stakes or question do I feel, and what would I stay to find out? Check muted and with sound.
3. By about eight seconds: what concrete thing has the film promised to show or answer?
4. Through the body: the times where I would swipe away, and why (no new payoff, no open question, unclear object, repetition, slow narration).
5. At the end: did the film keep its promise, did it end soon after the answer, and is there one thing I could tell a friend? Would I comment, share or save?

Swipe-risk points go to the responsible author as concrete repairs. Failure to recognize the object/event or find a concrete reason to continue at the observation point returns to the hook lab before other polish; an unfinished natural sentence at 2 s alone is not failure. Apart from the bound `qa.opening_hook` record, this check is a diagnostic from an internal reviewer, not an audience test or a score, and it never replaces real platform data.

## Learn from what actually performs

For a commissioned retrospective, analyze metrics the user provides under [platform data review](production-checkpoints.md#platform-topic-selection-and-data-review), using the platform's field names and definitions. Compare actual exit points with predicted swipe risks. Read each metric against the design decision it can test:

| Platform metric (Douyin field, when available) | Design decision it can test |
| --- | --- |
| 2 s exit (`2s跳出率`) | Hook pattern, first frame, first sound, `opening_hook.py` measurements and cold-test notes |
| 5 s completion (`5s完播率`) | The viewing promise and the 3.5–8 s picture |
| Drops inside the retention curve | Open-loop ledger gaps, payoff gaps, the midpoint and `retention_timeline.py` flags at the same published timestamps |
| Completion (`完播率`) and average view share (`平均播放占比`) | Final answer position, tail length after the answer and the ending loop |

Change one main variable per round (title, cover, hook pattern, promise wording, angle or packaging) under the existing experiment records. When the 2 s exit stays high on a vertical-first platform even though the hook passed its cold test, check that the vertical feed package was actually used, then strengthen phone-band composition with a larger central subject and clearer contrast. Keep the 16:9 series master; make a native vertical re-edit only when the user explicitly requests one.

Apply [entry/intent/payoff diagnosis and the next-production brief](production-checkpoints.md#diagnose-entry-promise-and-payoff-separately) before turning a metric into an opening, length or style prescription. Search-intent mismatch, recommendation entry loss and delayed explanatory payoff need different tests; average viewing is not an exit timestamp and platform chapter labels are not media truth.

Keep a private, evidence-backed pattern library in the project: which angles, hooks, promise wordings, titles, covers and packaging performed, keyed by `hook.pattern` against 2 s exit and by promise type against 5 s completion, with versions and data windows. Feed it back into appeal screening. Account data, works and feedback stay private; only general methods may enter this public Skill.
