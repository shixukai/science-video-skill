# Viral appeal: honest hooks, packaging and retention

Use this page to design honest hooks, viewing promises, open-loop retention, and vertical-feed packaging for feed films. Pre-script topic discovery lives in the standalone `science-video-topic-selection` Skill; platform submission & data retrospectives live in `science-video-publishing`. Only [the first two seconds](#win-the-first-two-seconds) adds a gated record (`topic_alignment.opening.hook`, `qa.opening_hook`); the viewing promise, open-loop ledger, and `retention_timeline.py` are planning/screening aids, not extra gates.

## Carry topic appeal into production

Carry forward the Topic Decision Card's two core hooks from [science-video-topic-selection](../skills/science-video-topic-selection/SKILL.src.md): **what viewers see that earns a stop**, and **what they can explain/judge afterward**. Preserve commissioned topics as-is and find their strongest honest entry.

## Design the package before the script

Before locking the G1 script, finalize:
1. **3–5 sourced titles** (`<= 30` CJK codepoints) in direct, single-breath everyday speech — lead with a concrete physical/structural contradiction, relatable everyday friction, or overlooked decisive detail, keep familiar everyday verbs, and place the object noun people actually search (`加油枪`, `不粘锅`) early in the title so search and feed traffic both find it (`加油枪怎么知道油加满了而跳枪？` instead of `油一满，没电线的加油枪怎么知道该停？`), and ban clickbait (`震惊`, `90%/99%的人都不知道/被误导`, `凭什么`, `凭啥`), invented danger, or unfulfilled promises.
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
- **Context-first delay, opening definitions/formulas, or AI clickbait slogan** (`所谓……是指` / `什么是……` / `根据XX公式` / `90%的人都被误导了` / `你以为……其实……` / `圆出口竟能拉出方便便…怎么做到的？`) → never open with a textbook definition, formula, lecture premise, or fake percentage; lead immediately with a visible contradiction, shared everyday friction, or overlooked physical detail in warm everyday speech (`<= 20` spoken units / `~3.5 s`).
- **Throat-clearing / abrupt look-or-camera directions** (`大家好`, `你知道吗`, `先看这个`, `接下来我们来看看`, `顺着截面往里看`, `剖开就能看到`, `放大截面`) → cut the stage command; start on the visible event and bridge through causal curiosity while the picture executes the cutaway or push-in.
- **Static/fading start, black lead, logo, late caption, or conditioning-still head** → hard start: fully exposed moving Frame 0, sound present at frame 0, first syllable `<= 0.35 s`, first caption on at frame 0 (trim `>= 0.15 s` off AI video ramp heads). **Physical action must visibly occur within `0.0–1.5 s`** (break, snap, dim, separate, spray, deflect)—never spend `1.5–2.0 s` slowly zooming into a static exterior shell before anything happens, and never freeze on a dead post-event frame for `5+ s`.
- **Three-way promise mismatch (title vs. header vs. first 10 s)** → platform title, vertical-feed header question, and the actual `0–10 s` opening beat must promise and immediately investigate the exact same visible mechanism; never hook on one feature in the title while spending the first 25–30 s explaining a different sub-mechanism.
- **Disembodied internal fragment or tiny distant shell** → use the [host-to-part bridge](#anchor-a-part-inside-its-host) within 0–5 s.
- **Stacked-modifier phrasing or post-hook 5–10 s clutter drop** → keep direct everyday verbs, cut stacked double-negation premises (`没通电也没拉黑帘`, `没通电没气泵`), and visually isolate the first focal interface.

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
| `everyday_pain_point` | Familiar daily friction happening now | “端起敞口杯慢倒水，水反而顺着杯壁往下淌。” *(shared physical annoyance — zero scolding `"其实是你的XX出了问题"` or fake medical claims)* |
| `overlooked_detail` | Tiny ignored feature governing the result | “加油枪嘴旁这颗小圆孔，决定了油满就自动停。” *(visually anchored detail, zero empty hype)* |

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

Right after the payload (finishing by `promise_window_s` = `8 s`), state one concrete sentence naming **the exact physical puzzle, observable clue, or test arena** that makes the answer feel within reach (`topic_alignment.opening.viewing_promise`: `line`, `fulfilled_by_scope_id`, `time_s`) — **without prematurely spoiling the final causal mechanism**. Giving away the punchline at 6 s collapses the information gap and causes an immediate swipe-off; conversely, empty suspense (“揭开它的秘密” / “看到最后你就明白了”) or abrupt zoom orders (“把冰放大到分子这一层”) fail to earn trust.
- **Avoid (premature payoff collapse):** “同样是水，结冰反而变轻，是因为水分子结冰时撑开了很多六边形的小空隙。” or repetitive formulaic secret-spoilers at 5 s (“里面没有芯片/电机，管着开关的是锅底一块会失磁的小磁铁/一颗小玻璃珠”) *(explains or names the punchline before the viewer even sees the mechanism — nothing left to discover)*
- **Target (concrete arena, gap stays open):** “同样重的一杯水，冻成冰以后居然会胀大一圈——温度越低，水分子怎么反而越排越松？” / “看同一个小卡扣，往下和往上，各碰到了哪儿。” *(names the concrete physical paradox or visible focal clue while keeping the mechanism open for the body)*
- **Prevent the 5–15 s post-hook dip:** Keep the entire 0–8 s hook + viewing promise inside **one continuous `\n\n` TTS paragraph** (zero inter-paragraph stall right at 3.5 s), then enter the first visible physical test or active state change immediately — never stall into a static parts inventory (“先来了解一下它的结构，它主要由三部分组成……”). Introduce a component only when it physically acts or triggers a hurdle.

## Keep a reason to stay

### Keep one question open until the final answer

Track `opens_question`, `closes_question`, and `time_s` inside `payoff_steps[]`:
- Keep the `main` question open until the last 10–20% of runtime.
- Open the next concrete question before or as each section closes the current one so viewers never hit a "nothing left to find out" dead zone.

### Payoff cadence, causal pivots, and re-hooks

- **Control information density with breathing-point micro-climaxes (every ~15–25 s, never exceeding 30 s):** Science explainers lose viewers when dense facts stack uninterrupted like a classroom lecture. Keep every conceptual chunk focused (`one new entity per breath`, review stretches `> 20 s` without a timed payoff in `retention_timeline.py`, and never exceed `30 s` even in multi-chapter explainers). Right after finishing each small knowledge unit, give viewers a concrete **breathing point / micro-climax** using one of three tools so they have room to digest AND a fresh pull into the next beat:
  1. **Visual reveal / animated state payoff** (picture replaces prose: let an unmistakable visual transformation + `0.25–0.45 s` foley breath deliver the insight without continuous narration),
  2. **Mini controlled experiment or A-vs-B comparison** (change one visible variable and watch the outcome diverge instead of describing it in words), or
  3. **Curiosity-turning micro-prediction / gentle question** (invite a 0.5 s mental bet that naturally opens the next obstacle).
- **Drive every transition with "Therefore / But" momentum, never flat "And Then" listing:** Each beat should either follow as a direct physical consequence (`于是`, `这么一来`) or expose a fresh physical snag (`可新问题马上来了`, `光靠这一步还不够`) — strip additive encyclopedia filler (`此外`, `另外`, `与此同时`, `其次`).
- **Use False Summits (escalating obstacles) around 40–60%:** Right when a partial clue seems to explain the phenomenon, reveal why that surface step alone fails or creates a new constraint, pulling the viewer into the deeper visual reveal:
  - *ZH example:* “铜线圈已经通上电了，可它自己并没有发烫——那锅底的热量又是从哪儿来的呢？” / “如果只靠粗糙小坑咬住涂层，高温反复煎炒还是会脱落——真正拉住它的，还得看中间那一层。”
  - *EN example:* “That seals the hole — but it immediately creates a new problem: what stops the valve from tripping before the tank is actually full?”
- Trim dead air without losing warm conversational connectors, introduce **visible physical behavior before technical terms**, let **visuals replace prose** wherever animation or experiment can carry the explanation directly, and plan at least one crisp shareable visual moment or felt-scale comparison where supported.

### Locate retention risks on the actual cut

Run `python -X utf8 scripts/retention_timeline.py measure <export.mp4> --episode <episode.json> --report <new.json>` on G2/G5 cuts to pinpoint payoff gaps, closed-loop stretches, early answers, long post-answer tails (`> 3.5 s`), mid-video black/blank clip-through frames, low shot-cut density (`< 1.2 cuts/10 s` on `>= 25 s` films), or static/silent holes (locator only, never a gate).

## Engineer the emotional payoff, aha frame and share triggers

Retention keeps people watching; an emotional payoff and a usable insight make them like, save, share, and follow. Plan these at G1 in the brief's appeal plan, alongside the hook (planning guidance, not a gate or score):
- **One dominant emotional payoff:** choose from the topic's honest material: `awe` (scale or limit reveal via a felt comparison or slow pull-back), `surprise` (expectation reversal confirmed by a visible test), `satisfaction` (a precise mechanism clicking into place with clean foley), or `relief_or_usefulness` (a daily snag finally makes sense). Shape the arc as curiosity → rising tension (false summit) → release at the aha frame. Do not average four emotions into flat neutrality, and never manufacture fear or danger.
- **Aha frame (~60–85% of runtime):** one screenshot-worthy image where the hidden mechanism becomes readable at a single glance (cutaway, split-screen, force or flow path, scale overlay). Hold it long enough to read at phone scale (`>= 1.5 s`), give it the strongest foley beat and the shortest spoken line, and never bury it under narration. This is the moment viewers rewatch, screenshot, and screen-record.
- **Retell test (share trigger):** after the aha frame, a cold viewer should be able to pass the insight on in one plain sentence (`原来加油枪是靠一股被油面封住的小气流自己跳停的`). If the retell needs jargon or three clauses, simplify the causal chain. The final reframing line should be the quotable version of that retell.
- **Save trigger:** if the mechanism implies a genuinely useful everyday judgment (choosing, using, or staying safe), put it as a one-line tip in the pinned comment or post copy. People save practical content; keep it off the video tail.
- **Sensory signature:** let the object's own characteristic sound (click, crack, sizzle, hiss) carry Frame 0 and return at the aha frame, so the sound becomes the episode's memory anchor.
- **Loop-friendly last frame:** within the `<= 3.5 s` tail, end on a shot that echoes Frame 0's subject and composition in its now-understood state (the same nozzle clicking off, the same ice cube bobbing). Autoplay replays then feel continuous, and the opening reads differently the second time. Never clip the final answer or fake a seamless loop that hides the resolution.

## End fast after explaining the mechanism

Deliver the final answer late (`ending.answer_time_s`), **eliminate verbal ending signals** (`总结一下`, `所以说到底`, `到这里你就明白了`, `这就是为什么…的原因`; English `"in conclusion"`, `"to summarize"`, `"now you know why"`) that trigger viewers to swipe off 5–8 s early, land the closing sentence cleanly on the mechanism's visible resolution, and **stop calmly within `answer_to_end_review_s` (`3.5 s`)** — zero trailing spoken questions (“你平时遇到过吗？”), comment prompts, next-video outros, recaps, slogans, like/follow CTAs, or **post-answer life-tip / trivia tangents** (`难怪…`, `新买回来的…`, `平时记得…`, `汽车安全锤专门…`, `换把木铲更耐用…`). Never add a 1-second silence + cut back to the exterior after answering to tack on an 8–15 s bonus tip (that combination signals "episode over" and triggers steep end-of-video drop-off).

- **Route the action point & extension question off-video (`science-video-publishing`):** To drive real comment discussion and next-episode anticipation **without** harming completion rate, place the extension question (`你平时有没有遇到过……？评论区聊聊`), same-collection next-episode teaser (`下一条拆解……`), or bonus everyday tip inside the **pinned comment (`置顶评论`) and post description (below the non-spoiling first two lines)** prepared in `science-video-publishing` (or fold an essential everyday observation into the 0–3 s opening resonance).

## Duration, format and series identity

No duration floor or ceiling: let clear explanation set runtime while keeping standalone everyday feed episodes tightly focused on one core contradiction (avoid padding single-mechanism explainers past ~55–60 s with slow setup holds or post-answer tangents). Master canvas is `1920×1080` landscape; align topic lane, contradiction-first titles, locked covers, and accepted voice for recognizable series identity.

## Package the landscape master for vertical feeds

For the Douyin composer group (Douyin and native cross-posts), compose a `1080×1920` dark night-viewing derivative from the accepted `-textless` 16:9 master + formal captions via `scripts/feed_package.py` (handing the accepted 16:9 landscape master directly to Xiaohongshu and YouTube; see companion `science-video-publishing` Skill for release execution):
- **Concrete object header (zero textbook jargon):** `--topic` MUST name the **concrete everyday object or visible event** matching the cover (`钢化玻璃`, `饮料瓶盖`, `加油枪自动跳枪`, `老式电饭煲`), never an abstract textbook discipline label (`材料力学`, `磁性物理`, `流体气压`, `几何光学`, `机械结构`, `电磁屏蔽`, programmatically rejected by `feed_package.py`). Keep `--question` concise (target `<= 16` CJK chars where natural), free of stacked double-negation premises, and 100% aligned with the platform title and first 10 s of the film.
- **Layout & phone-screen presence:** Full-width `1080 px` picture + dark flat bands (`slate` default; `night`/`navy`/`warm_charcoal` options; zero strokes/shadows/boxes/stickers; commercially cleared `Noto Sans SC Bold` only) with persistent 1-line concrete topic + 2-line question header above and larger re-wrapped captions below (preserving final-line baseline and never splitting numbers/units). When the hero mechanism is framed center-safe without vital edge detail, consider `--zoom 1.15–1.333` (4:3 taller center window, raising active picture screen share from ~32% to ~42%) verified via actual phone-size `crop_check` so the subject reads large and magnetic in vertical feeds.
- **Zero batch bypass of cold tests:** Batch-rendered episodes still require an actual completed `opening_hook.py` cold test (`cold_test.status` cannot stay `pending`) plus a quick full-timeline frame skim to confirm zero camera clip-through or blank/off-subject stretches before publishing.
- **Command:** `python -X utf8 scripts/feed_package.py compose <textless.mp4> --captions <srt> --topic <concrete-object> --question <line1\nline2> --output <feed916.mp4> --report <new.json>` (keep `--ending-question` off by default). View at phone size and bind `deliverables.textless_master`, `deliverables.feed_package`, and `qa.feed_package` (does not reopen G5).

## Scroll-viewer appeal check

On G2 rough cuts and G5 finals, an independent reviewer watches from frame 0 with no context and records in `qa.expression_plan` / `qa.expression_review`: (1) frame 0–1 s stop power (zero opening definitions/formulas or clickbait percentages), (2) 2 s named object + intuition-vs-evidence / everyday-friction / overlooked-detail tension (muted & voiced) with visual-verbal counterpoint (picture replaces prose; no pixel-narrating voiceover), (3) ~8 s concrete **non-spoiling** viewing promise flowing straight into a story/problem-solving or active test beat with zero 5–15 s structure-dump dip, (4) exact swipe-risk timestamps & causes (lecture-like info walls `> 20–30 s` without a visual/experiment/question breathing point, talk-over stretches where words explain what the picture fails to show, flat "and then" transitions, working-memory overload, anti-spoiler caption leaks, or monotone stretches), and (5) zero premature ending signals + crisp reframing closing line (`<= 3.5 s` tail) + promise honesty (with extension question / next-episode teaser routed to pinned comment / post copy), and (6) [emotional payoff](#engineer-the-emotional-payoff-aha-frame-and-share-triggers): which single emotion actually landed, whether the aha frame was readable at phone scale and held long enough, the reviewer's own one-sentence retell, and whether the last frame echoes Frame 0.

## Learn from what actually performs

Post-publish metric diagnosis (`2s跳出率`, `5s完播率`, retention curves, saves/shares) and `next_production_brief` creation are handled by the standalone `science-video-publishing` Skill (`references/platform-retrospective.md`) and [platform data review](production-checkpoints.md#platform-topic-selection-and-data-review). Change one main creative variable per comparison round.
