# Narration, voice invocation and actual listening

The universal default Mandarin voice across **all routes** ([series profile](../config/series-profile.json)) is **local IndexTTS-2.5 voice clone (`IndexTeam/IndexTTS-2.5`, preset `mandarin-indextts25-clone-polished-v1`)** via [synthesize_indextts2.py](../scripts/synthesize_indextts2.py) (`lang="ZH"`, `duration_factor=1.0`, `interval_silence=220`, `paragraph_silence_s=0.55`, `use_emo_text=False`, `use_bf16=True`, `use_cuda_kernel=False`, `use_qwen_emo=False`) conditioned on the private `<= 15 s` prompt in `CODEX_HOME/data/science-video-production/voice-baseline.json`, followed by whole-track `#5` speech polish (`mandarin-clone-polish-v1`, zero echo) via [prepare_voice_master.py --polish](../scripts/prepare_voice_master.py). Microsoft Edge neural TTS ([synthesize_edge_tts.py](../scripts/synthesize_edge_tts.py)) provides **paired English (`en-US-AndrewMultilingualNeural`, `+4%`)** and **cloud Mandarin fallback (`zh-CN-YunxiNeural`, `+4%`)**, mastered linearly via `prepare_voice_master.py`.

## Invocation location and confirmation

Confirm the local IndexTTS-2.5 runtime and private prompt path from current/prior requests or private `CODEX_HOME/data/science-video-production/voice-baseline.json` before invoking local synthesis. Ask only if genuinely missing — never hard-code private local paths or prompts into the public Skill, never auto-create environments or download weights, and record actual model identifiers honestly in `model_version_reference`.

## Check the script before full-episode synthesis

Synthesize full narration only from the parent-integrated G1 script after checking [whole-film direction](viewer-retention-design.md#direct-the-whole-film-before-polishing-its-parts). Fix structural or promise disconnects before synthesizing a long track; paper reads never substitute for actual audio listening.

### Edit narration and dialogue for the ear

Write and edit every spoken script in a **warm, unhurried, peer-level conversational register** — like an observant, knowledgeable friend standing next to the viewer looking at the same everyday object, never an impatient interrogator, lecturing textbook, clipped command list, or shouting short-video host. Read aloud in each language's natural spoken idiom (never force Mandarin sentence order into English) and resolve Mandarin polyphones (`<字|PINYIN4>` when needed) before synthesis.

**Positive spoken-craft standard:**
- **Speak with curiosity, not interrogation or lecturing.** Lead with shared everyday observation (`你会发现`, `有意思的是`, `仔细看的话`, `可仔细想想`) instead of challenging or scolding (`凭什么`, `凭啥`, `偏要`, `到底为什么`, `别傻了`, `真以为`, `千万别再`, `听好了`, `记住这一点`). For safety advice, explain the calm reason rather than barking bare imperatives.
- **Let sentences breathe in relaxed everyday Mandarin.** Keep natural spoken connectors (`其实`, `这时候`, `慢慢地`, `顺着往里看`, `结果呢`, `原来`, `难怪`) instead of staccato 6–10 char headlines (`“冰是固体，却浮在水上。”`), rigid textbook nominalizations (`进行…`, `产生…作用`, `这一过程称为…`), or riddle-host clichés (`“答案藏在……里”`, `“接下来拆开看：”`).
- **Use accurate, proportionate everyday verbs — zero crude force verbs.** Prefer vivid, accurate physics verbs (`轻轻一按`, `顺势被顶起来`, `把热油顶开并带出油面`) over crude shortcuts (`狠狠砸碎`, `干爆`, `直接干掉`, `直接掀翻`, `全靠它`, `说白了就一个原因`).
- **Land transitions and endings softly.** Bridge sections through natural curiosity (`看到这儿，你可能会好奇…`, `顺着这条细缝往里看…`) and settle calmly back onto the opening scene after explaining the mechanism (no trailing filler question, no hard mid-breath cutoff).

| Stiff or blunt draft (avoid) | Warm, natural conversational rewrite (target register) |
| --- | --- |
| “冰是固体，却浮在水上。” | “冰明明已经冻成硬块了，放进水里却还能稳稳浮在上面。” |
| “砸一块陶瓷，凭什么生出几千伏高压？” | “打火机里这块小陶瓷，手指轻轻一按，怎么就能压出几千伏高压？” |
| “凸轮一转，顶杆就抬起。” | “凸轮转到凸起那一侧时，上面的顶杆就会顺势被顶起来。” |
| “它为什么不悄悄蒸发，偏要炸？” | “油这么烫，水为什么不慢慢蒸发掉，反而会一下子溅出来呢？” |
| “先看冷油，水染了色。” | “我们先拿一杯凉油试试，滴进一滴染过色的水。” |
| “别掀盖、别端锅，等它凉透。” | “盖严之后先别急着掀开，也别端着锅走动，等油温慢慢降下来就稳妥了。” |

**Seven mechanical/editorial screens before synthesis** (screened by `scripts/google_flow_audit.py` and `scripts/opening_hook.py`):
1. **`clickbait_contrast_hook`:** Zero `凭什么`/`凭啥` anywhere in titles, covers, feed headers, narration, or captions; zero marketing formulas (`圆出口竟能拉出方便便，袋熊是怎么做到的？`) or stacked pre-noun modifiers (`油一满，没电线的加油枪怎么知道该停？` → `加油枪怎么知道油加满了而跳枪？`).
2. **`blunt_or_harsh_tone`:** Strip `偏要`, `别傻了`, `真以为`, `千万别再`, `听好了`, `看好了`, `说穿了`, `先说结论`, `一秒看懂`, `一句话告诉你`, bare imperative chains, and crude violent verbs (`干爆`/`直接干掉`/`狠狠砸碎`).
3. **`telegraphic_short_sentences`:** No coined 2–4 char shorthand (`圆出口`, `拉方块`, `硬带压平`) or rapid-fire staccato clauses (`mean < 22` CJK chars/sentence).
4. **`prompt_header_colon`:** Strip slide colons (`第一步靠…：`, `先打破一个常识误区：`, `核心在于：`, `关键在于：`, `原因如下：`, `说白了，`).
5. **`strawman_reversal_density`:** Avoid repeating `不是 A，而是 B / 并非…而是… / 你以为…其实…` across paragraphs.
6. **`semicolon_tail_stuffing`:** Never bolt an unpictured caveat onto a shot tail with `；`; put each condition test inside its matching chapter.
7. **`slogan_closing_formula`:** No stacked 3+ symmetrical `[7–9 chars]，[7–9 chars]。` couplets or advertising slogans.

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
