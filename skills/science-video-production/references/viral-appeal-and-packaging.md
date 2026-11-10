<a id="爆款吸引力诚实钩子包装与留存"></a>
# Viral appeal: honest hooks, packaging and retention

Use this page to make a science film that ordinary viewers choose, keep watching, and share. It applies to editorial topic selection and to every complete new film meant for feed platforms. A user-selected topic keeps its scope; apply these methods to find its strongest honest entry instead of changing the topic. The [topic contract](topic-contract.md) owns the question and scope, [viewer retention](viewer-retention-design.md) owns explanation progression, [visual system](visual-system.md#design-the-two-cover-ratios-independently) owns cover finish, and [production checkpoints](production-checkpoints.md#platform-topic-selection-and-data-review) owns platform data records. This page owns appeal screening, package-first design, the first seconds, retention cadence, interaction and the post-publication learning loop. It adds no gate, score or record schema.

A hit science video usually combines four things: a **broad entry** many people recognize, a **first-second pull** that stops the scroll, **continuous visible payoff** that keeps viewers watching, and a **reason to share or comment** afterward. Every hook must be honest: the film itself delivers what the title, cover and first seconds promise. Mismatch is punished by early exits and negative comments, so honesty is also the better-performing strategy.

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
3. **The first three seconds.** The first picture and the first spoken line, written together.

Choose the package with the strongest promise that the film can fully deliver, then write the script to fulfill it. If no candidate is compelling, the angle is weak; revise it now, when it is cheap. Keep title, cover, first frame and first line promising the same question, as checked by the existing [cover-to-opening alignment](topic-contract.md#continuously-check-the-covers-question-against-the-actual-opening).

Title patterns that work for Chinese feed platforms (examples only, each must match the actual film):

| Pattern | Example |
| --- | --- |
| Surprise question | 冰明明是固体，为什么会浮在水上？ |
| Everyday mechanism | 电磁炉隔着玻璃，凭什么能把锅烧热？ |
| Extreme precision | 比头发丝还细的线条，是怎么刻进芯片的？ |
| Transformation | 一个小小的瓶胚，怎样变成你手里的饮料瓶？ |
| Visible comparison | 同样是轮胎，为什么花纹差这么多？ |

Use numbers only when sourced. Do not use “震惊”, “99%的人不知道”, invented danger or claims the film does not show. A process-chain title such as “全流程” requires the film to cover that chain.

## Win the first three seconds

Feed viewers decide within one to three seconds. For a complete new film intended for feed platforms, this is the default design target, not a numeric gate:

- **The first frame is already the hook**: the topic's most striking real visual, in motion. No logo, black frame, title card, slow establishing shot or greeting such as “大家好”.
- **The first spoken line** (roughly one breath) offers a specific observation, meaningful fact, real tension or genuine question matched to the picture; a question is not mandatory.
- **Right after the hook**, establish why it matters and what the viewer will see answered. This is the recognizable context required by [viewer retention](viewer-retention-design.md#establish-context-and-a-reason-to-watch-before-explaining): the hook shows the object in its most interesting state, so context and hook are the same shot rather than competing sections.

| Hook pattern | First picture | First line pattern |
| --- | --- | --- |
| Result first | The finished product or final state | The concrete observable result and why it is interesting |
| Strange phenomenon | The real phenomenon happening | The expectation it breaks |
| Extreme contrast | Two states or objects side by side | The difference and the question it raises |
| Direct question with evidence | The object performing its task | The question the film answers |
| Satisfying process | The most satisfying moment of the process | What makes it hard |

Hook footage must come from this film's legitimately produced material and must be explained later in the body; a result preview must clearly return to the start of the process, as viewer retention already requires.

Reject opening and handoff lines that merely direct the viewer to look, or pair an empty question with an empty 'first look at...' command: they create no observation, tension or payoff. Do not swap them for another stock suspense phrase. In natural spoken language, connect a recognizable object or use with a specific visible change, relevant fact, real difficulty or genuine question; let the following picture and line add a concrete piece of information without dumping the whole explanation upfront. Match claims and visual causality to the actual evidence; a familiar application or comparison must also be accurate. Questions and audience directions are allowed when they serve the story, but neither is a required formula.

In a cam demonstration, “想知道它怎么动？先看这个轮子。” just delays the observation. If the footage shows the lift, “凸起转到顶杆下面，顶杆就抬起来了。” gives viewers the action; cut closer on that lift so the next sentence can explain the contact. Use the visible event of this film to write the line.

Apply the [spoken-script edit](voice-reference.md#edit-mandarin-for-the-ear) at G1. Check the opening through the first body observation against the planned cut; repair empty directions, title echoes and unsupported suspense before full narration synthesis. Recheck the affected interval in the existing G2/G5 review.

## Keep a reason to stay

Map these onto the existing `payoff_steps` and section handoffs instead of creating another plan:

- **Payoff cadence.** Viewers should receive a new visible payoff (an observation, a reveal, a satisfying motion) or a sharper question regularly. Find gaps in the actual rough cut; as a starting point, look hard at any stretch of roughly 20 seconds with no new payoff.
- **Concrete re-hooks.** Let the result that just appeared reveal the next specific problem or observation. A visible consequence, a useful comparison or a real question can carry the handoff. “更精彩的在后面” and “看到最后” supply no reason to stay.
- **Escalation.** Order sections so difficulty, stakes or spectacle rise when dependencies allow. Place the strongest reveal late, without withholding the core answer artificially.
- **Purposeful pattern change.** Change scale, viewpoint, sound or rhythm where attention would sag, and make every change carry information.
- **Remove dead air.** Cut greetings, channel introductions, repeated summaries and filler such as “接下来我们来看看”. Keep a natural, brisk narration pace under the accepted voice preset; do not slow down for completeness or speed up artificially.
- **Shareable moments.** Slow motion, macro detail, before/after, cross-section reveals and perfect fits invite rewatching and sharing; plan at least one per film where the topic supports it.

## End fast and invite real interaction

Deliver the answer, return to the opening image with the new understanding, and end. Avoid long outros, recaps and requests for likes. When it is natural, end with one genuine question tied to the content that viewers can answer from their own experience (“你家的锅是哪一种？”), or a final frame that loops cleanly into the first. Do not fabricate controversy to drive comments.

## Duration, format and series identity

The topic contract still lets the complete explanation determine duration; never skip necessary steps to hit a length. When a complete chain is long, the honest way to fit feed platforms is to split it into a series of episodes, each with its own question and payoff, or to make a separately commissioned short cut-down that points to the full film. The series default canvas is 1920×1080 landscape; a vertical version requires an explicit request and its own layout review.

Build series recognition: a consistent title style, cover design and accepted voice; use recurring visual devices such as a cutaway only where the topic supports them. A one-sentence pointer to a next episode is allowed only when that episode actually exists or is committed.

## Scroll-viewer appeal check

Before offering a G2 rough cut or G5 candidate, the reviewer watches from the first frame as a scrolling viewer with no context, then records in the existing `qa.expression_plan` or `qa.expression_review` notes:

1. At about one second: what is on screen, and would I stop?
2. At about three seconds: what has happened or become clear, and what would I stay to find out?
3. Through the body: the times where I would swipe away, and why (no new payoff, unclear object, repetition, slow narration).
4. At the end: one thing I could tell a friend, and whether I would comment, share or save.

Swipe-risk points go to the responsible author as concrete repairs. This check is a diagnostic from an internal reviewer, not an audience test, a score or a gate, and it never replaces real platform data.

## Learn from what actually performs

After authorized publication, record each platform's own metrics under [platform data review](production-checkpoints.md#platform-topic-selection-and-data-review), using the platform's field names and definitions (for example 2-second exits, 5-second completion, completion rate, average viewing time, likes, comments, shares, saves and cover click-through). Compare actual exit points with the swipe-risk points predicted before publication, and change one main variable per round (title, cover, hook pattern or angle) under the existing experiment records.

Apply [entry/intent/payoff diagnosis and the next-production brief](production-checkpoints.md#diagnose-entry-promise-and-payoff-separately) before turning a metric into an opening, length or style prescription. Search-intent mismatch, recommendation entry loss and delayed explanatory payoff need different tests; average viewing is not an exit timestamp and platform chapter labels are not media truth.

Keep a private, evidence-backed pattern library in the project: which angles, hooks, titles and covers performed, with versions and data windows. Feed it back into appeal screening. Account data, works and feedback stay private; only general methods may enter this public Skill.
