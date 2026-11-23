# Facts, asset rights and production statements

Read this page when verifying scientific claims, visual provenance, asset rights, or generated-content disclosures.

## Original visual provenance contract

Default mode is `origin_contract.mode=self_created_visuals`: all delivered video, samples, and covers must be AI-generated, modeled/staged/rendered/designed by this project, or verified authorized user-shot capture (plus verified native `licensed_3d_model` inputs on 3D routes).

- **Zero third-party finished footage/stills in production:** Public-domain, CC/Commons, institutional, stock, or paper videos/photos are **research/scientific/style references only**. Cropping watermarks, grading, reordering, AI-rewriting, or adding Chinese dubbing never converts third-party footage into original production.
- **Enforced across all stages:** Applies to rough cuts, samples, finals, and covers (validated structurally by `scripts/origin_guard.py`; real authorship still requires original evidence). Stop affected work immediately if unverified or third-party footage enters production, replace it, and recheck.

### Licensed 3D model inputs

On 3D routes, suitable open-licensed native 3D models (meshes, materials, textures, rigs under compatible license) may be adopted directly under [model reuse](engineering-blender.md#open-licensed-models-may-be-adopted-directly) — never promotional renders or stock stills.

Record `kind=model_3d`, `origin.category=licensed_3d_model`, `source`, `creator`, `file/sha256`, `rights.status=cleared` + `license_name/scope`, `origin.license_evidence {file, sha256}`, external `origin.dependencies [{file, sha256}]`, and `origin.review {file, sha256}` (no fabricated self-generation entrypoints). Downstream renders stay `self_rendered` referencing that model in `origin.inputs` with `origin_category=licensed_3d_model`.

### Per-shot provenance evidence

Bind provenance inside existing `episode.json` records (no parallel approval):
- `shots[].shotbook.origin`: `planned_method` (`self_generated`, `self_rendered`, `user_capture`), `design {file, sha256}`, `entrypoint {file, sha256}`, `entry_version`.
- `assets[].origin`: `category` (`self_generated`/`self_rendered`/`self_designed`/`user_capture`), `method/entry_version`, `entrypoint/design/output/review {file, sha256}`, upstream `inputs [{asset_id, file, sha256, origin_category}]`, and `frames [{file, sha256}]`. Never omit conditioning images or upstream models; `third_party_reference` never enters production inputs.
- `user_capture` requires readable `user_authorization {file, sha256}` proving capture authorship and usage permission.

### Original provenance does not lower delivery quality

Disclose AI realism (“AI生成，非实拍/观测”) and controlled 3D simulations accurately via platform controls and companion records by default (never burning unconsented on-frame notices under [marking consent](visual-system.md#in-picture-markings-require-specific-consent)). Provenance passes never replace normal-speed G3/G5 quality review.

## Scientific evidence

Bind every material claim to its ID, exact wording, conditions/units, and verified primary source (original papers, standards, or credible scientific institutions; never search summaries or unsourced LLM answers). Distinguish correlation vs causation, sample vs population, simulation vs measurement, and preserve genuine uncertainty. Remove or narrow unsupported claims; high-risk health/safety claims require appropriate verification. Viewing a webpage grants factual citation only — never screenshot/illustration reuse rights.

## Asset ledger

Register every entering visual, audio, music, SFX, and font asset once with: ID, type, source, creator, relative path + SHA-256, rights basis & evidence, permitted scope (commercial use, adaptation, attribution, platform, territory), actual processing, and required attribution/disclosure location. Follow exact license clauses (e.g., [CC BY 4.0 Section 3(a)](https://creativecommons.org/licenses/by/4.0/legalcode.en#s3a2)). For public distribution, default to commercial-safe toolchains and block `non_commercial_restricted` generators unless non-commercial scope is explicitly authorized.

## Two indexes and private storage

- [aesthetic-references.json](../indexes/aesthetic-references.json): style/motion inspiration only (`production_use="not_granted"`).
- [reusable-assets.json](../indexes/reusable-assets.json): versioned general reusable components (`candidate`/`in_review`/`approved`/`deprecated`/`blocked`; revocable when rights or facts change).
- Keep private media, design boards, credentials, account data, and user feedback strictly in private storage outside the public Skill repo.

## Minimum production statement

Production statements, source credits, and AI/simulation disclosures live in accompanying materials and platform controls by default (not burned into frames).
- When using a `real_footage` anchor, verify original user capture, authorization, third-party clearances, capture context, and actual source in/out points; watch continuously and disclose crop/speed/grade honestly. Never log AI clips or panned photos as `real_footage`.
- Honest example phrasing (only when factually true): “天空镜头为作者实拍；分子与光路为机制示意，非真实摄影、非按比例。” / “云内放电过程为 AI 生成连续画面，非实地拍摄或观测记录。”

## Fact cards and formal asset admission

Each fact card binds primary source location, conditions/units, and separates fact from teaching simplification or analogy (one strong authoritative source suffices for settled facts; add independent sources for disputed numbers or safety claims). Science review covers visual scale, colors, directions, forces, and timing — not narration alone.

One-off episode assets use `episode_original` (or `licensed_model_reuse` for one-time 3D models); use `assets[].catalog` ([production-asset.schema.json](../assets/production-asset.schema.json)) only when promoting an asset for formal library reuse. G3 checks only assets used by the representative segment; G4/G5 check the full used set.

## Actual publication steps for generated-content declarations

Declare AI-synthesized narration (including when visuals are authored in controlled 3D) and AI-generated imagery via active platform disclosure controls ([CAC labeling rules, articles 3, 6(4), 10](https://www.cac.gov.cn/2025-03/14/c_1743654684782215.htm); [Douyin labeling notice](https://trust.douyin.com/article/69831756697378034?channel=safety&enter_from=channel_page)). Platform submission controls are owned by the companion `science-video-publishing` Skill (`自主声明 → 内容由 AI 生成` in Douyin composer; Xiaohongshu creator handoff; see [prerelease declarations](production-checkpoints.md#declare-ai-generated-content-at-publication)).

In `qa.release.ai_disclosure`, derive `contains_generated_content` from the actual release closure (shots, covers, audio), set `platform_declaration_required` + `current_rule_reference` + `declaration_evidence`, and mark `platform_declaration_used=true` only after verifying the control pre-submit. On-frame disclosures still require explicit [specific consent](visual-system.md#in-picture-markings-require-specific-consent).

## Preserve claim meaning through production handoffs

Attach each conditional claim's fact-card ID to its script line, visual beat, and review note — stating both the **condition that must survive editing** and the **inference the evidence does NOT support**. Editing wording, colors, speed, or shot order must never turn a conditional effect into an unconditional claim or invent frequency through repeated identical shots; a caption cannot rescue a contradicting picture. Resolve cross-role factual conflicts by citing source evidence rather than seniority or visual drama.
