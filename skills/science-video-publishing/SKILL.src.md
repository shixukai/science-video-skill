---
name: science-video-publishing
description: Package accepted science videos for vertical feeds (9:16 dark band), prepare and submit authorized releases to Douyin (with Xigua/Toutiao/Fanqie cross-posts and standing collections), Xiaohongshu, and YouTube, archive confirmed published files, and run post-publish platform data retrospectives. Do not use for topic discovery, scripting, voice synthesis, or video rendering.
---

# Science Video Publishing

Own everything **after** a finished video exists: vertical-feed derivative packaging, platform release preparation/submission, verified file archival (`release-candidate` → `archive`), and post-publish performance retrospectives feeding back a `next_production_brief`.

> **Strict isolation:** Do NOT load `science-video-production` scripting, voice-synthesis, video-generation, or 3D-rendering guides during publishing or retrospective tasks. Load [platform-retrospective.md](references/platform-retrospective.md) ONLY when doing platform data review.

## 1. Entry & scope

- **Direct release of an existing finished file:** When the user names an existing finished video for authorized publication, proceed directly with the platform handoff rules below — no G1–G6 production records, `publish_ready` ceremony, or new production QA required. Record known concerns or missing reviews accurately.
- **Production-managed release (`release_package`):** Expect accepted exports in `release-candidate/` (16:9 master, optional `-textless` master, `.srt` captions, independently composed `3:4` and `4:3` covers, post copy, and SHA-256).
- **Authorization & duplicate guard:** Verify existing specific authorization covers the exact account, version, and destinations (reuse still-valid authorization; never ask repeatedly for standing defaults in [publishing-profile.json](config/publishing-profile.json)). Check local release records or user-supplied evidence for duplicate/pending submissions before uploading.
- **Public copy hygiene & anti-spoiler rule:** Keep title (`<= 30` codepoints), description (`<= 1000` codepoints, zero `@` friend mentions), tags, and pinned comments strictly audience-focused. Strip software/render credits or generic “原理示意” disclaimers from public copy; use platform AI disclosure controls instead. **Never spoil the complete mechanism answer in the first two lines of a vertical-feed post description** (mobile players overlay those lines over the playing video, letting viewers read the answer and swipe away); write descriptions as curiosity-preserving everyday resonance + observation cues, and place any bonus everyday tip in a pinned comment rather than a video tail.

## 2. Video format routing & vertical feed packaging

- **Landscape platforms (Xiaohongshu & YouTube):** Hand off the accepted **`1920×1080` 16:9 landscape master** directly (Xiaohongshu uses the 16:9 landscape video together with the finished `4:3` landscape cover `cover_4_3`; YouTube uses the 16:9 landscape master and optional `16:9` cover).
- **Vertical feed platform (Douyin composer group — 抖音 / 西瓜视频 / 今日头条 / 番茄小说):** Compose the `1080×1920` dark night-viewing derivative (`-feed916.mp4`) from the accepted `-textless` 16:9 master + formal `.srt` captions using `science-video-production`'s shared script:

    python -X utf8 "<CODEX_HOME>/skills/science-video-production/scripts/feed_package.py" compose <textless-master.mp4> --captions <captions.srt> --topic <concrete-object-noun> --question <line1\nline2> --output <episode-feed916.mp4> --report <new-feed-report.json>

- **Pre-publish feed checks (mandatory even for batch renders):** (1) `--topic` MUST name the **concrete everyday object or visible event** matching the cover (`钢化玻璃`, `饮料瓶盖`), never an abstract textbook discipline label (`材料力学`, `磁性物理`, `流体气压`); (2) verify exact **three-way alignment** across Douyin title, `-feed916` header question, and the film's actual `0–10 s` opening; (3) confirm the film ends cleanly (`<= 3.5 s` after the core mechanism answer, zero post-answer life-tip tail); (4) confirm `opening_hook.py` cold test is completed (never `pending`) and skim the rendered `-feed916.mp4` at phone scale for header legibility, caption line breaks, visible `0–1.5 s` action, zero mid-video black/blank clip-through frames, and safe `--zoom` framing (up to `1.333` when center-safe). This derivative does NOT reopen G5 video acceptance. Place the verified `-feed916.mp4` beside the master in `release-candidate/` and record its SHA-256.

## 3. Platform submission & handoff rules

Read standing defaults from [publishing-profile.json](config/publishing-profile.json). Always verify real UI toggle states before clicking submit — never assume a setting propagated.

### 3.1 Douyin Creator Center (single composer for 抖音 + 西瓜视频 + 今日头条 + 番茄小说)
Use ONE authenticated Douyin Creator Center form for Douyin and all authorized native cross-posts:
1. **Upload media & covers:** Upload the checked `-feed916.mp4` (or requested master) and current reviewed covers (`3:4` / `4:3`).
2. **Public copy & mandatory tag:** Fill final title and description; select the exact **`科普`** tag in “添加标签” (plus a few relevant mechanism tags within limits).
3. **Mandatory standing Douyin collection (`添加到合集` / `选择合集`):** Classify strictly by the video's **primary physical or scientific mechanism** and select ONE standing collection for every authorized public science video (exclude private/personal clips; never create ad-hoc collections or change order without creator authorization):

| Order | Standing collection | Primary mechanism scope | Typical subjects |
| --- | --- | --- | --- |
| 1 | `透视日常造物` | Everyday objects, packaging, appliances, food/kitchen physics, daily mechanical/safety devices | Fuel nozzles, tamper caps, dry pasta, QR codes, seatbelts, pressure cookers, RCD breakers, pull-tabs, soap bubbles, popcorn |
| 2 | `解码巅峰工程` | Heavy machinery, rail/transit, aviation/aerospace, industrial manufacturing/3D printing, precision scientific/medical instruments | MRI, electron microscopes, elevator safety gears, pantographs/welded rails, SLA 3D printing, turbine blades, neutrino detectors, rockets, spacesuits |
| 3 | `丈量天地寰宇` | Weather, atmospheric optics, phase-change natural physics, geology/volcanology, space/astronomy | Petrichor, clouds, lightning, frost, hurricanes, snowflakes, geysers, supercooled water, rainbows, dew, auroras, coronal rain, lava, tidal locking |
| 4 | `探秘生命法则` | Animal/plant biomechanics, evolutionary physical limits, biological structures/behaviors, human sensory/perceptual mechanisms | Camouflage, beaver teeth, wombat feces, coconut octopus, sea slugs, capsaicin heat, high-altitude birds, redwoods, hadal fish, owl flight, optical illusions |

   *(If creating or updating a `1:1` square collection cover, compose `1080×1080 <= 5 MB` via `compose_cover.py --ratio 1:1`.)*
4. **Native cross-posts:** Select authorized destinations (`西瓜视频`, `今日头条`, `番茄小说`) in the same form.
5. **Eligible Douyin activities:** Inspect displayed options (including “more”); join compatible activities whose terms match what the video actually teaches (prefer narrow subject fit if capped; verify hashtags coexist; never enroll in separate agreements or paid promos).
6. **Monetization & originality:** Enable eligible per-work revenue controls (`广告分成` on Toutiao, Xigua options) and select **`原创`** where provenance qualifies.
7. **Standing no-download preference:** Select **`不允许`** for Douyin save permission and disable download/save on every cross-post destination that exposes the control.
8. **AI-generated content declaration:** Enable **`内容由 AI 生成`** / **`AI 创作`** (or current equivalent) while keeping separate optional creation categories OFF per [publishing-profile.json](config/publishing-profile.json).
9. **Release spacing & scheduler:** Respect `publication_spacing.recommended_min_gap_hours` (`>= 6 h`, avoiding burst posting) unless explicitly overridden. If scheduling, read back the exact local date/time before submitting once.

### 3.2 Xiaohongshu (user-operated composer handoff, 16:9 landscape video)
- Open the official publish page when requested.
- Deliver ONE combined handoff containing: (a) adapted title, (b) adapted description including `#科普` and supported tags, and (c) **paste-ready native directory and file paths** (in separate code blocks, e.g. `C:\...`) for the accepted **`1920×1080` 16:9 landscape video master** (NOT `-feed916.mp4`) and finished **`4:3` landscape cover** (`cover_4_3`).
- Paste plain text ONLY into a title or body field already focused by the creator, then wait. The creator operates upload, cover selection, `科普` topic picker, declarations, settings, and submission.

### 3.3 YouTube Studio
- Hand off the `1920×1080` 16:9 master (and `16:9` cover if commissioned).
- Apply standing `youtube_made_for_kids = false` unless explicitly overridden for that video.

### 3.4 File chooser handoff & local review links
- For any file picker, output the verified absolute directory in one standalone code block and exact filename/full path in a second code block using native OS separators (`C:\...`).
- For user preview of local files, return verified clickable Markdown links (`[label](file:///...)`) — never bare unclickable paths or redundant uploads.

### 3.5 HARD STOP after submission (ALL platforms)
Once an authorized submit/schedule click is dispatched — or a ready composer is handed to the creator — **STOP interacting with that destination for the submitted work immediately**:
- **Do NOT** reload result pages, browse published posts to verify them, poll creator dashboards, take post-publish screenshots, or retry an uncertain submission.
- Record status as `submitted, creator review pending` or `ready for user submission` (or report uncertainty for the creator to decide).
- Record final published URLs, work IDs, or G7 offline receipts ONLY from evidence supplied by the creator when asked.

## 4. Verified archive lifecycle (`release-candidate` → `archive`)

Read `archive_root` from `<CODEX_HOME>/skills/science-video-production/config/video-storage.local.json`:
- **Pending publication:** G5-accepted finals stay in `<archive_root>/release-candidate/` (including `-feed916` and `-textless` variants with SHA-256). Scheduled or moderation-pending works stay in `release-candidate/`.
- **After user confirms publication:** Move the confirmed published version/edition into `<archive_root>/archive/` (archive confirmed editions independently of pending ones; user confirmation suffices without a separate G7 request).
- **Verify every move:** Never overwrite another work/version. Across volumes, copy to a temporary partial file in the destination directory, read back size and SHA-256, rename to the final filename, and delete the source only after confirming both destination integrity and unchanged source identity. If storage is unavailable or verification fails, keep the source and log a pending move.
- To validate a moved final offline against an episode record, pass `--stored-video`:

    python -X utf8 "<CODEX_HOME>/skills/science-video-production/scripts/check_episode.py" <episode.json> --stage publish_ready --stored-video <absolute-stored-video> --report <new-receipt.json>

Record release settings and moves in [release-handoff-template.md](assets/release-handoff-template.md).

## 5. Post-publish data retrospective (on demand)

When the user commissions a platform performance review or supplies exported backend analytics, load [platform-retrospective.md](references/platform-retrospective.md) (and optionally run `platform_evidence.py` for exact-time curve alignment and comment deduplication). Close with a concise `next_production_brief` to feed back into `science-video-topic-selection` and `science-video-production`.
