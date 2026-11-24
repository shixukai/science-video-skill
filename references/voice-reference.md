# Narration, voice invocation and actual listening

The universal default Mandarin voice across **all routes** ([series profile](../config/series-profile.json)) is **local IndexTTS-2.5 voice clone (`IndexTeam/IndexTTS-2.5`, preset `mandarin-indextts25-clone-polished-v1`)** via [synthesize_indextts2.py](../scripts/synthesize_indextts2.py) (`lang="ZH"`, `duration_factor=1.0`, `interval_silence=220`, `paragraph_silence_s=0.55`, `use_emo_text=False`, `use_bf16=True`, `use_cuda_kernel=False`, `use_qwen_emo=False`) conditioned on the private `<= 15 s` prompt in `CODEX_HOME/data/science-video-production/voice-baseline.json`, followed by whole-track `#5` speech polish (`mandarin-clone-polish-v1`, zero echo) via [prepare_voice_master.py --polish](../scripts/prepare_voice_master.py). Microsoft Edge neural TTS ([synthesize_edge_tts.py](../scripts/synthesize_edge_tts.py)) provides **paired English (`en-US-AndrewMultilingualNeural`, `+4%`)** and **cloud Mandarin fallback (`zh-CN-YunxiNeural`, `+4%`)**, mastered linearly via `prepare_voice_master.py`.

## Invocation location and confirmation

Confirm the local IndexTTS-2.5 runtime and private prompt path from current/prior requests or private `CODEX_HOME/data/science-video-production/voice-baseline.json` before invoking local synthesis. Ask only if genuinely missing — never hard-code private local paths or prompts into the public Skill, never auto-create environments or download weights, and record actual model identifiers honestly in `model_version_reference`.

## Check the script before full-episode synthesis

Synthesize full narration only from the parent-integrated G1 script after checking [whole-film direction](viewer-retention-design.md#direct-the-whole-film-before-polishing-its-parts). Fix structural or promise disconnects before synthesizing a long track; paper reads never substitute for actual audio listening.

### Edit narration and dialogue for the ear

Write and edit every spoken script in a **warm, unhurried, peer-level conversational register** — like an observant, knowledgeable friend standing next to the viewer looking at the same everyday object, never an impatient interrogator, lecturing textbook, clipped command list, or shouting short-video host. Read aloud in each language's natural spoken idiom (never force Mandarin sentence order into English) and resolve Mandarin polyphones (`<字|PINYIN4>` when needed) before synthesis.

**Positive spoken-craft standard:**
- **Speak with curiosity, not interrogation or lecturing.** Lead with shared everyday observation (`你会发现`, `有意思的是`, `可仔细想想`, `多半是`) instead of challenging or scolding (`凭什么`, `凭啥`, `偏要`, `到底为什么`, `别傻了`, `真以为`, `千万别再`, `听好了`, `记住这一点`). For safety advice, explain the calm reason rather than barking bare imperatives.
- **Prime shared intuition before breaking it (honest expectancy violation).** Curiosity peaks in the "tip-of-the-tongue" sweet spot (Loewenstein's Information Gap Theory) when a viewer's sane physical intuition clashes with a visible reality. Calmly validate what everyday intuition predicts (`按理说……`, `照常理看……`, `换作平时……`) right before the visible contradiction (`可……却/反而……`), instead of using combative strawmen (`你以为……其实……` / `别傻了`).
- **Protect the information gap — promise the clue or arena, never spoil the core answer early.** In the 0–8 s opening and viewing promise, name the exact physical puzzle or observable change worth watching (`温度越低，水分子怎么反而越排越松？`), NOT the final mechanism (`是因为撑开了六边形空隙`) or spoiler crutches (`其实原理很简单`, `说到底就是因为`, `简单来说就是`). Let the body earn the mechanism late.
- **Drive beat transitions with "Therefore / But" causal momentum and escalating obstacles (False Summits).** Replace flat encyclopedia listing (`此外`, `另外`, `与此同时`, `除此之外`, `不仅如此`, `其次`) with physical consequence (`于是`, `这么一来`, `正因为这样`) or an immediate new constraint (`可新问题马上来了`, `光靠这一步还不够`, `如果只做到这儿，高温一煎还是会……`). When answering one sub-question naturally triggers the next physical hurdle, viewers stay for guided discovery rather than passive fact-dumping.
- **Let sentences breathe with end-weight suspense, physical agency, and felt scale.** Keep natural spoken connectors (`其实`, `这时候`, `慢慢地`, `结果呢`, `原来`, `难怪`) instead of staccato 6–10 char headlines (`“冰是固体，却浮在水上。”`), rigid textbook nominalizations (`进行…`, `产生…作用`, `这一过程称为…`), or riddle-host clichés (`“答案藏在……里”`, `“接下来拆开看：”`). Place the physical buildup before the surprising clue (end-weight syntax), let parts act with vivid proportionate physics verbs (`轻轻一按`, `顺势被顶起来`, `把热油顶开并带出油面` — zero crude shortcuts like `狠狠砸碎`, `干爆`, `直接干掉`, `直接掀翻`, `全靠它`, `说白了就一个原因`), anchor abstract numbers to felt everyday scale (`胀成一千六百倍大的蒸汽团，就像在锅底瞬间吹开一只气球`), and **introduce the visible behavior before the technical term** (or skip jargon when plain speech is clearer).
- **Bridge through causal curiosity, never abrupt camera or cutaway commands.** Let the **picture** execute the cutaway, zoom, or macro push-in while the **narration** stays inside the viewer's own chain of reasoning. Never interrupt a visible phenomenon with unmotivated stage-direction orders (`顺着截面往里看`, `切开它的截面`, `剖开锅底就能看到`, `放大锅底截面`, `把冰放大到分子这一层`, `凑近这层金属网`, `把镜头拉近`, `仔细看拉头里面`) — first motivate *why* the interior matters by naming the paradox or causal link, then describe what is physically happening inside.
- **Shape spoken prosody and rhythmic contrast for neural TTS.** Because continuous synthesis (`IndexTTS-2.5` with `use_emo_text=False`, or `edge-tts` `+4%`) derives vocal phrasing from sentence structure and punctuation, alternate flowing setup sentences (`~22–34` CJK chars) with crisp pivot/reveal clauses (`~10–18` CJK chars), using a clean comma, single `——`, or chapter-level `\n\n` before a genuine twist so the ear feels a micro-beat of anticipation. Apply the same native curiosity rhythm in paired English (`"By all rights..."`, `"Except something strange happens —"`, `"Which immediately creates a new problem:"`), never stiff Mandarin calques. Land endings calmly back onto the opening scene right after explaining the mechanism (no trailing filler question, no hard mid-breath cutoff).

| Stiff, flat, or spoiling draft (avoid) | Warm, curiosity-driving conversational rewrite (target register) |
| --- | --- |
| “冰是固体，却浮在水上。” | “按理说东西越冷越紧实，可冰明明已经冻成硬块了，放进水里却还是稳稳浮在上面。” |
| “同样是水，结冰反而变轻，是因为水分子结冰时撑开了很多六边形的小空隙。” *(spoils core answer at 6 s)* | “同样重的一杯水，冻成冰以后居然会胀大一圈——温度越低，水分子怎么反而越排越松？” *(keeps gap open)* |
| “钢化玻璃正面敲不破，边角轻轻一磕却碎成一片。顺着截面往里看，里面藏着两股互相拉扯的力。” | “钢化玻璃正面敲不破，边角轻轻一磕却碎成一片。同一块玻璃反差这么大，是因为它内部早就藏着两股互相拉扯的力——可为什么偏偏一碰边角就全盘失守？” |
| “不粘锅连鸡蛋都粘不住，放大锅底截面，就能看到底层的微米小坑。” | “不粘锅连煎蛋都粘不住，它自己是怎么牢牢挂在金属锅底上的？光靠粗糙的小坑咬住还不够，高温反复煎炒一样会掉。” |
| “此外，油面上升后会封住小孔。另外，薄膜受到负压作用发生位移。” *(flat "and then" + nominalization)* | “油面一漫过来封住小孔，细管里的空气瞬间被抽空，薄膜立刻往里一吸，顺势就把开关顶开了。” *(causal + physical agency)* |
| “砸一块陶瓷，凭什么生出几千伏高压？” | “打火机里这块小陶瓷，手指轻轻一按，怎么就能压出几千伏高压？” |
| “凸轮一转，顶杆就抬起。” | “凸轮转到凸起那一侧时，上面的顶杆就会顺势被顶起来。” |
| “它为什么不悄悄蒸发，偏要炸？” | “油这么烫，水为什么不慢慢蒸发掉，反而会一下子溅出来呢？” |
| “先看冷油，水染了色。” | “我们先拿一杯凉油试试，滴进一滴染过色的水。” |
| “别掀盖、别端锅，等它凉透。” | “盖严之后先别急着掀开，也别端着锅走动，等油温慢慢降下来就稳妥了。” |

**Ten mechanical/editorial screens before synthesis** (screened by `scripts/google_flow_audit.py` and `scripts/opening_hook.py`):
1. **`clickbait_contrast_hook`:** Zero `凭什么`/`凭啥` anywhere in titles, covers, feed headers, narration, or captions; zero marketing formulas (`圆出口竟能拉出方便便，袋熊是怎么做到的？`) or stacked pre-noun modifiers (`油一满，没电线的加油枪怎么知道该停？` → `加油枪怎么知道油加满了而跳枪？`).
2. **`blunt_or_harsh_tone`:** Strip `偏要`, `别傻了`, `真以为`, `千万别再`, `听好了`, `看好了`, `说穿了`, `先说结论`, `一秒看懂`, `一句话告诉你`, bare imperative chains, and crude violent verbs (`干爆`/`直接干掉`/`狠狠砸碎`).
3. **`abrupt_camera_stage_direction`:** Strip unmotivated narrator camera/cutaway/zoom orders (`顺着截面往里看`, `切开…截面`, `剖开…就能看到`, `放大…截面/小切口/来看`, `把…放大到…这一层`, `凑近…看`, `把镜头拉近`, `仔细看…里面`); let the visuals cut in while narration follows the causal reason.
4. **`telegraphic_short_sentences`:** No coined 2–4 char shorthand (`圆出口`, `拉方块`, `硬带压平`) or rapid-fire staccato clauses (`mean < 22` CJK chars/sentence).
5. **`prompt_header_colon`:** Strip slide colons (`第一步靠…：`, `先打破一个常识误区：`, `核心在于：`, `关键在于：`, `原因如下：`, `说白了，`).
6. **`strawman_reversal_density`:** Avoid repeating `不是 A，而是 B / 并非…而是… / 你以为…其实…` across paragraphs.
7. **`semicolon_tail_stuffing`:** Never bolt an unpictured caveat onto a shot tail with `；`; put each condition test inside its matching chapter.
8. **`slogan_closing_formula`:** No stacked 3+ symmetrical `[7–9 chars]，[7–9 chars]。` couplets or advertising slogans.
9. **`premature_answer_spoiler` & `empty_suspense_filler`:** Never dump opening spoiler crutches (`其实原理很简单`, `说到底就是因为`, `简单来说就是因为`, `直接告诉你答案`) or empty hype/preamble (`揭开…秘密`, `看到最后你就明白了`, `下面我们一起来看`, `带你一探究竟`, `一起揭秘`; English: `"welcome back"`, `"in this video we will"`, `"the short answer is"`, `"here's the secret"`, `"you won't believe"`, `"stay until the end"`).
10. **`additive_list_transition_density`:** Avoid piling up `>= 3` flat encyclopedia list connectors (`此外`, `另外`, `与此同时`, `除此之外`, `不仅如此`, `其次`, `值得注意的是`, `总而言之`) in one script; replace additive listing with causal (`于是`/`正因为这样`) or tension-raising (`可问题是`/`光靠这一步还不够`) pivots.

Also strip production syntax (`[pause]`, speaker tags, timestamps) before TTS, keep conditional claim meaning intact under [claim preservation](science-and-rights.md#preserve-claim-meaning-through-production-handoffs), and keep the opening `hook.first_line` payload within `payload_max_spoken_units` (`20` spoken units, `~3.5 s`) naturally (trim leading silence so first syllable starts by `audio_onset_max_s` without speeding speech). Editorial references: [Humanizer-zh](https://github.com/op7418/Humanizer-zh), [lieflat-less-ai-tone](https://github.com/larashero3-dotcom/lieflat-less-ai-tone).

## Reuse the accepted voice before making new auditions

**Changing script wording, cuts, episodes, or agents does NOT reopen voice selection.** Reuse the accepted recipe (`mandarin-indextts25-clone-polished-v1` / private `voice-baseline.json`) without asking the user to re-audition; reserve user auditions strictly for explicit requests or genuinely unresolved voice choices.

| Setting | Default Mandarin (`mandarin-indextts25-clone-polished-v1`) | Paired English & cloud fallback (`edge-tts`) |
| --- | --- | --- |
| Backend & tool | `IndexTTS` / `local_indextts2` (`IndexTeam/IndexTTS-2.5`), `scripts/synthesize_indextts2.py` | `Microsoft Edge` / `edge-tts`, `scripts/synthesize_edge_tts.py` |
| Speaker & params | `user_clone` (`<= 15 s` private WAV prompt), cohesive `\n\n` paragraphs, `duration_factor=1.0`, `interval_silence=220`, `paragraph_silence_s=0.55`, **`use_emo_text=False`** | EN: `en-US-AndrewMultilingualNeural` (`+4%`); ZH fallback: `zh-CN-YunxiNeural` (`+4%`), continuous single call (`SentenceBoundary`), `48 kHz` mono WAV |
| Whole-track master | `prepare_voice_master.py --polish` (`mandarin-clone-polish-v1`: HP 75 Hz, gentle EQ + 2:1 comp, **no echo**, `-18 LUFS` / `-2 dBTP` / `48 kHz`) | `prepare_voice_master.py` (`mandarin-continuous-master-v1`: `-18 LUFS` / `-2 dBTP` constant linear gain, `\|rate\| <= 6%`) |

Production owns routine audio QA. Repair heard defects at source: rewrite tangled/blunt text before retaking; retake a complete contextual chapter for timbre/register drift; fix pure level steps via clean silence-valley gain envelopes; realign captions and picture after edits.

## Continuous narration and synthesis units

Generate each episode continuously from cohesive conversational paragraphs (`3–5` narrative sections — never per-shot `\n\n` breaks or spliced `1.5–2 s` dead-air holes) and sanitize punctuation before TTS (no stacked `！？`/`！！` or theatrical ellipses that trigger pitch spikes). Split initial generation ONLY for verified interface-length limits or stability failures at complete semantic boundaries. Avoid patchwork micro-splicing (pasting 3+ short retakes); regenerate the complete chapter or continuous script whenever register/timbre shifts.

## One narration master and one shared processing chain

Build ONE continuous narration master before cutting picture; every shot references that single bus with **zero per-shot gain, normalization, EQ, compression, pitch, or speed resets**. Keep final mix (`-16 LUFS ± 1 LU`, `-1.5 dBTP`) distinct from the dry narration stem (`-18 LUFS`, `-2 dBTP`).

```sh
# #5 speech polish + two-pass loudness (IndexTTS-2.5 Mandarin clone):
python -X utf8 scripts/prepare_voice_master.py --polish --episode-dir <dir> --input <raw.wav> --output <master.wav> --record <postprocess.json> [--boundaries <s1,s2>]

# Linear gain only (edge-tts English / cloud fallback):
python -X utf8 scripts/prepare_voice_master.py --episode-dir <dir> --input <raw.wav> --output <master.wav> --record <postprocess.json> [--boundaries <s1,s2>]

# Read-only continuity preflight:
python -X utf8 scripts/prepare_voice_master.py --analyze-only --episode-dir <dir> --input <candidate.wav> [--boundaries <s1,s2>]
```

Inspect `continuity_diagnostics` before picture assembly:
- **Register/timbre jump (`pitch_register_jump` / `semitone_jump > 2.0`):** retake full chapter or continuous script (never hide with pitch shift/limiter).
- **Pure level step (`level_jump_db > 2.5 dB` with stable timbre):** apply smooth pre-master linear-dB gain envelope strictly inside silence valleys.
- **Isolated transient peak starving loudness (`isolated_transient_limiting_gain`):** tame only that pinpoint millisecond consonant pre-master (never per-shot `loudnorm`).

## Run records and audio binding

Choose ONE mutually exclusive source path in `narration`:
1. **Single full-script run:** `narration.execution` (`status=confirmed`, `mode=local_project|service`, `location`, `confirmation_reference`) matching `narration.generation_record {file, sha256}`, plus `narration.postprocess_record {file, sha256}` (`schema_version=1`, `status=processed`, `source`, `output`, `steps`) when mastered.
2. **Reuse accepted track:** `narration.reuse_record` (`status=previously_accepted`, `reference`, `audio_sha256`).
3. **Necessary segmentation (`### Ordered multisource manifest for necessary segmentation`):** `narration.generation_manifest {file, sha256}` (`schema_version=1`, `mode=ordered_full_segments`, `reason` with `interface_limit|generation_stability|contextual_retake` + `evidence`, `script`, ordered `segments[]` whose UTF-8 bytes reconstruct the full script verbatim with matching runtime/voice settings). Concatenate complete native PCM tracks (`mode=concatenate_full_segments`), optionally follow with `whole_track_linear_gain` (`upstream_record`), and bind seam-spanning listening in `source_listen_review.boundaries[]`.

### Ordered multisource manifest for necessary segmentation

Keep all manifest files episode-relative and verify that concatenated segment inputs reproduce `narration.script_file` byte-for-byte without cropping, overlaps, or invented gaps; pass `--upstream-record` to `prepare_voice_master.py` when mastering a concatenated track so seam continuity is measured automatically.

## Listen separately to source audio and the final mix

Bind actual source listening in `narration.source_listen_review` (checking mispronunciations, swallowed causal words, tone/phrasing, and seams). For the final export, complete normal-speed listening in `qa.audio.listening` on **both headphones and phone speaker** (checking speech priority, room tone, clean transients, and no music masking). Missing listening capability stays honestly `pending` — ASR, waveforms, and LUFS numbers never pass listening.

## Whole-episode narration continuity

`narration.delivery_plan` records `mode` (`continuous_first` or `context_preserving_segments`) and target delivery notes (matching `generation_manifest` when segmented). At G2, G3, and G5, bind `qa.audio.continuity.<stage>` (`status`, `context_sha256`, `media_sha256`, `audio_sha256`, `plan_sha256`, `method=normal_speed_continuous_listening`, `actually_heard`, `ranges`, and observations for `tone/rhythm/speech_rate/loudness/joins`; `transitions` may stay empty unless flagging a concrete cross-shot concern). Log audible drift, abrupt joins, or mechanical pauses as failures (`scope=audio`) in `qa.visual_frames.failures`.

## Provenance and transmission scope

Local synthesis sends nothing offsite; cloud services transmit only authorized script text (never private prompts/voiceprints or unrelated media). Never clone a real person without authorization, never store credentials/voiceprints in public repos, and report service/quota blockers honestly without account rotation or mirror evasion.
