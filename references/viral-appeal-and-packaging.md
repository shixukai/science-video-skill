# Viral appeal: honest hooks, packaging and retention

Use this page to design honest hooks, viewing promises, open-loop retention, and vertical-feed packaging for feed films. Pre-script topic discovery lives in the standalone `science-video-topic-selection` Skill; platform submission & data retrospectives live in `science-video-publishing`. Only [the first two seconds](#win-the-first-two-seconds) adds a gated record (`topic_alignment.opening.hook`, `qa.opening_hook`); the viewing promise, open-loop ledger, and `retention_timeline.py` are planning/screening aids, not extra gates.

## Carry topic appeal into production

Carry forward the Topic Decision Card's two core hooks from [science-video-topic-selection](../skills/science-video-topic-selection/SKILL.src.md): **what viewers see that earns a stop**, and **what they can explain/judge afterward**. Preserve commissioned topics as-is and find their strongest honest entry.

## Design the package before the script

Before locking the G1 script, finalize:
1. **3–5 sourced titles** (`<= 30` CJK codepoints) in direct, single-breath everyday speech — lead with a concrete physical/structural contradiction, keep familiar everyday verbs (`加油枪怎么知道油加满了而跳枪？` instead of `油一满，没电线的加油枪怎么知道该停？`), and ban clickbait (`震惊`, `99%的人不知道`, `凭什么`, `凭啥`), invented danger, or unfulfilled promises.
2. **Cover concept:** one large recognizable subject in a topic-matched realistic setting + upper-left 1-line topic noun & 2-line question composed strictly via `scripts/compose_cover.py` ([cover standards](visual-system.md#finished-cover-standards-for-engineering-and-manufacturing-topics)).
3. **0–5 s Hook Lab:** 3+ genuinely distinct hook candidates across >= 2 patterns pairing moving Frame 0, first sound, and natural first line. Keep title, cover, first frame, and first line promising the same question ([cover-to-opening alignment](topic-contract.md#continuously-check-the-covers-question-against-the-actual-opening)).

| Pattern | Example title |
| --- | --- |
| Everyday structural contradiction | 瓶盖一拧就断，当初怎么装上去的？ |
| Surprise physical contradiction | 冰明明是固体，为什么会浮在水上？ |
| Everyday mechanism | 电磁炉隔着玻璃，怎么把锅烧热的？ |
| Extreme scale / limit paradox | 百米高树没有水泵，怎么把水送上树顶？ |
| Visible comparison | 同样是轮胎，为什么花纹差这么多？ |

## Win the first two seconds

For complete new feed films, design, produce, and test the 0–5 s opening FIRST at final quality (`production-policy.json opening_hook`). Prioritize two creative jobs: **Stop** (a recognizable subject already doing something concrete on frame 0 — camera moves or overlays do not count) and **Stay** (the next beat opens one concrete question or clue without dumping the full answer).

### Why openings lose viewers

The anti-preamble rule rejects delaying background, **not necessary subject naming** ([minimum viewer orientation](viewer-retention-design.md#orient-the-viewer-before-introducing-a-detail)). Repair these failures before body polish:
- **Context-first delay or AI clickbait slogan** (`圆出口竟能拉出方便便…怎么做到的？`) → lead with the concrete observation in warm everyday speech (`<= 20` spoken units / `~3.5 s`).
- **Throat-clearing / abrupt look-or-camera directions** (`大家好`, `你知道吗`, `先看这个`, `接下来我们来看看`, `顺着截面往里看`, `剖开就能看到`, `放大截面`) → cut the stage command; start on the visible event and bridge through causal curiosity while the picture executes the cutaway or push-in.
- **Static/fading start, black lead, logo, late caption, or conditioning-still head** → hard start: fully exposed moving Frame 0, sound present at frame 0, first syllable `<= 0.35 s`, first caption on at frame 0 (trim `>= 0.15 s` off AI video ramp heads).
- **Disembodied internal fragment or tiny distant shell** → use the [host-to-part bridge](#anchor-a-part-inside-its-host) within 0–5 s.
- **Stacked-modifier phrasing or post-hook 5–10 s clutter drop** → keep direct everyday verbs and visually isolate the first focal interface.

### The opening beat sheet

| Time | Picture | Sound | Caption |
| --- | --- | --- | --- |
| Frame 0 | Subject already in motion, phone-readable (for `part_of_host`, recognizable host/bay acting); no fade/logo/black | Event sound or narration onset, zero fade-in | First caption on screen |
| `<= 0.35 s` | Continuous action | First syllable started | Synced |
| `2.0–3.5 s` | Clear visible change/contrast | Natural **payload clause** finished (`<= 20` spoken units, `<= 3.5 s`, warm everyday grammar, zero AI compression) | Matches payload |
| `3.5–8 s` | Stay with subject / finish host-to-part bridge by 5 s | Concrete [viewing promise](#lock-a-concrete-viewing-promise-by-about-8-seconds) | Matches promise |

### Anchor a part inside its host

For an internal component inside a larger host (`host_relation=part_of_host`, recording `host_system` and `whole_to_part_bridge`), open on the recognizable complete host or working cabin/bay in real action and bridge in one unbroken 0–5 s push-in or simultaneous cutaway into the real mounting site — never a distant empty shell or floating studio box.

At **2 s**, check what the film is about, **what visible clue makes it worth watching**, and what question stays open ([orientation](viewer-retention-design.md#orient-the-viewer-before-introducing-a-detail)). The full sentence need not end at 2 s; the natural payload deadline is **3.5 s** (`<= 20` spoken units) at unhurried series pace — never speed up speech.

### Find the hook in this film's material

List the film's 3–5 strongest visual moments (climax reveal, cutaway, breakage/failure, before/after contrast, extreme scale, hand acting on the object). A later climax works ONLY if newcomers understand its subject and question immediately — **later background cannot retroactively supply a missing referent** (and record any return in `hook.return_in_body`).

| `hook.pattern` | Moving Frame 0 | Warm conversational first line (examples) |
| --- | --- | --- |
| `result_first` | Finished state forming | “别看手里的饮料瓶这么大，它原本只是个试管大小的小瓶胚，一吹就撑起来了。” |
| `strange_phenomenon` | Phenomenon in action | “冰已经冻成硬块了，放进水里却还是稳稳浮在上面。” |
| `extreme_contrast` | Two states diverging | “旁边的叶子早就湿透了，荷叶上的水珠却还能自己滑走。” |
| `question_with_evidence` | Object doing its task | “隔着这块常温的玻璃板，锅底是怎么自己热起来的？” |
| `satisfying_process` | Peak mechanism action | “凸轮转到凸起那一侧，上面的顶杆就会顺势被顶起来。” |
| `stakes_in_action` | Real consequence | “胎纹一旦磨平，雨天踩刹车，车子会多滑出去一大截。” |
| `failure_or_breakage` | Real failure happening | “冬天露在外面的水管裂开，很多时候是被里面结的冰撑开的。” |

### Run the hook lab at G1

1. Record >= `min_candidates` genuinely distinct candidates across >= 2 patterns in `topic_alignment.opening.hook.candidates` (comparing different visual events, not reworded lines on one image) with concrete `lost_because`.
2. Fill the winning hook's `pattern`, `host_relation` (+ `host_system`/`whole_to_part_bridge`), `first_frame`, `frame0_motion`, `first_sound`, `first_line`, `payload_clause`, `tension`, `muted_read`, `phone_read`, `source_shot_id`, and `return_in_body`.
3. Time `first_line` aloud at warm conversational pace (`<= 20` spoken units / `~3.5 s`, no harsh/blunt phrasing or telegraphese); revise text rather than warping TTS rate.

### Produce and test the hook first

- Build the 0–5 s hook sample at final HD quality/fps first with whole-track leading silence trimmed so narration starts `<= 0.35 s` (zero fades, frame-0 event sound).
- Measure with `python -X utf8 scripts/opening_hook.py measure <export> --captions <srt> --preview-dir <dir> --report <new.json>` (keep local previews local; fix flags or justify real exceptions).
- **Cold two-second test:** An independent reviewer with zero script/package exposure plays 0–2 s muted first (recording `muted_at_1s`, `muted_at_2s`, `would_stop`, `tension_or_question`, `host_system_seen`/`part_in_whole_clear`), then replays with sound/captions through 5 s and the first body payoff (`object_named`, `sound_at_2s`). Bind the passed report in `qa.opening_hook.sample` before G3 expansion and `qa.opening_hook.final` before G5. Failed cold tests return to the hook lab.

### Keep the hook honest

Hook footage must belong to the film and be explained by the body. Cut empty look-directions and abrupt narrator camera/cutaway commands (“想知道它怎么动？先看这个轮子。” → “当凸起正好转到顶杆下方时，顶杆就被顺势顶了起来。”; “顺着截面往里看，里面藏着两股力。” → “同一块玻璃反差这么大，是因为它内部早就藏着两股互相拉扯的力。”) and apply [spoken-script editing](voice-reference.md#edit-narration-and-dialogue-for-the-ear).

## Lock a concrete viewing promise by about 8 seconds

Right after the payload (finishing by `promise_window_s` = `8 s`), state one concrete sentence naming what physical change or inner cause explains the paradox (`topic_alignment.opening.viewing_promise`: `line`, `fulfilled_by_scope_id`, `time_s`). Never use empty suspense (“揭开它的秘密” / “看到最后你就明白了”) or abrupt zoom orders (“把冰放大到分子这一层”). Example: “同样是水，结冰反而变轻，是因为水分子结冰时撑开了很多六边形的小空隙。”

## Keep a reason to stay

### Keep one question open until the final answer

Track `opens_question`, `closes_question`, and `time_s` inside `payoff_steps[]`:
- Keep the `main` question open until the last 10–20% of runtime.
- Open the next concrete question before or as each section closes the current one so viewers never hit a "nothing left to find out" dead zone.

### Payoff cadence and re-hooks

- Land a fresh visible payoff or sharper question regularly (review stretches `> 20 s` without payoff).
- Bridge beats with concrete curiosity (“铜线圈已经通上电了，可它自己并没有发烫——那锅底的热量又是从哪儿来的呢？”), place a strong honest visual reveal around 40–60%, trim dead air without losing warm conversational connectors, and plan at least one crisp shareable visual moment where supported.

### Locate retention risks on the actual cut

Run `python -X utf8 scripts/retention_timeline.py measure <export.mp4> --episode <episode.json> --report <new.json>` on G2/G5 cuts to pinpoint payoff gaps, closed-loop stretches, early answers, long tails, or static/silent holes (locator only, never a gate).

## End fast after explaining the mechanism

Deliver the final answer late (`ending.answer_time_s`), reconnect cleanly to the opening image, and **land calmly within `answer_to_end_review_s` (`6 s`) right after explaining the mechanism** — zero trailing questions (“你平时遇到过吗？”), comment prompts, recaps, slogans, or like/follow CTAs unless explicitly commissioned.

## Duration, format and series identity

No duration floor or ceiling: let clear explanation set runtime while keeping standalone everyday feed episodes tightly focused on one core contradiction. Master canvas is `1920×1080` landscape; align topic lane, contradiction-first titles, locked covers, and accepted voice for recognizable series identity.

## Package the landscape master for vertical feeds

For the Douyin composer group (Douyin and native cross-posts), compose a `1080×1920` dark night-viewing derivative from the accepted `-textless` 16:9 master + formal captions via `scripts/feed_package.py` (handing the accepted 16:9 landscape master directly to Xiaohongshu and YouTube; see companion `science-video-publishing` Skill for release execution):
- **Layout:** Full-width `1080 px` picture + dark flat bands (`slate` default; `night`/`navy`/`warm_charcoal` options; zero strokes/shadows/boxes/stickers) with persistent 1-line topic + 2-line question header above and larger re-wrapped captions below (preserving final-line baseline and never splitting numbers/units).
- **Command:** `python -X utf8 scripts/feed_package.py compose <textless.mp4> --captions <srt> --topic <noun> --question <line1\nline2> --output <feed916.mp4> --report <new.json>` (keep `--ending-question` off by default). View at phone size and bind `deliverables.textless_master`, `deliverables.feed_package`, and `qa.feed_package` (does not reopen G5).

## Scroll-viewer appeal check

On G2 rough cuts and G5 finals, an independent reviewer watches from frame 0 with no context and records in `qa.expression_plan` / `qa.expression_review`: (1) frame 0–1 s stop power, (2) 2 s named object + tension (muted & voiced), (3) ~8 s concrete promise, (4) exact swipe-risk timestamps & causes, and (5) clean fast ending + promise honesty.

## Learn from what actually performs

Post-publish metric diagnosis (`2s跳出率`, `5s完播率`, retention curves, saves/shares) and `next_production_brief` creation are handled by the standalone `science-video-publishing` Skill (`references/platform-retrospective.md`) and [platform data review](production-checkpoints.md#platform-topic-selection-and-data-review). Change one main creative variable per comparison round.
