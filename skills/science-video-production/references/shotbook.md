# 从成品音轨到可复核的逐镜记录

逐镜记录写入 `shots[].shotbook`；计划阶段允许实际缺项，申请成片交付前补齐当前版本。

## 音频先行，但不牺牲画面

以 `narration.script_file` 保存的连续完整讲解稿为口播正文，先按理解任务分成完整语义段，再排分镜和语义拍；每镜 `narration_exact_text` 对应该稿的原文片段，不能各写一篇再拼成解说。用当前真实音轨确定时点，不从估算字数或固定4–6秒切镜反推。每拍明确注意力任务及主次，不机械限制对象数量，写清口播触发词、实际音轨时点、相关对象的动作、状态或需观察的关系。对象需要先被认识；静止观察可以是合理动作，不为显得活泼而漂浮、抖动或硬推拉。

G2 将各镜 `narration_exact_text` 按镜头顺序拼回完整稿，仅忽略排版空白；无口播镜写空字符串。这只核文本结构一致，不代表解释逻辑通过。

`start`、`end`、`beats[].at` 均为成片时间轴上的秒数。镜头按序、互不重叠；叠化属于镜内合成。没有解说的纯观察镜填 `beats: []` 并用 `silence_reason` 说明停顿作用；语义拍只覆盖实际解说事件，不必伪造词句填满静默。每镜填 `subject`（对象）、`action`（动作）、`framing`（景别/取景）、`claim_support`（本镜如何支持所列主张；无主张则解释叙事作用）、`motion_purpose`（变化怎样帮助理解或为何保持静止）。

将当前解说文件 SHA-256 写入 `narration.audio_sha256`。换录音、裁剪、变速或重排后，重新听并对齐全部受影响语义拍；更新校验值不能代替重听。

## 先设计状态，再精绘关键态与分层动作

按[动画场景设计](animation-scene-design.md#开工顺序动作意图先于精绘)先定状态变化、持续/新增/分离结构与镜间关系，再做关键态和资产。关键态按本期媒介及[视觉基准](visual-system.md)审看，在 `keyframe_review` 记文件、SHA-256、结论与观察。写实由MoneyPrinterTurbo主制，3D动画由Blender主制；2D仅用于已明确范围，不能以终态图推拉或揭幕代替过程动画。

切镜时成对设计前镜 `final_state` 与后镜 `initial_state`，`transition_reason` 写前后镜号/时点、沿用结论与下一任务；用 `object_ids/spatial_anchor` 和视角保留可认对应。动作卡字段见下文，不重复建台账。实际声画审查记 `qa.shotbook`，`reviewed_sha256=shotbook_sha256(data)`；镜头、素材或音轨变更后重审受影响内容，素材 `assets[].sha256` 绑定当前文件。

## 整片视觉抽帧工具

已有与媒体对齐的 `shotbook.start/end` 时，用[build_visual_review.py](../scripts/build_visual_review.py)生成静态审片材料。从Skill目录运行：

```bash
python3 scripts/build_visual_review.py /path/to/episode.json --media renders/candidate-v3.mp4 --output reviews/G5-v3
```

需Python3.11+和本地ffmpeg/ffprobe。`--media` 与相对 `--output` 以episode目录为根，均须位于该目录；输出为新目录，不修改episode/QA。只收本地自包含视频，拒绝播放列表；非方形像素或特殊显示变换先在制作软件导出校正副本。`relative_plan`、空/非有限时点、重叠/乱序或越界镜头会失败。

输出 `index.html`、每镜首/中/末PNG、`manifest.json` 和 `gate-evidence.json`。总览保留完整画幅并列出覆盖/未覆盖区间；末样取镜尾边界前实际帧。manifest记录请求时点和实际帧时间，短镜或低帧率可能重复帧；关键机制、接缝或极值未抽到时另补。

manifest保存episode快照、源视频、HTML/PNG摘要与工具版本；帧路径相对抽帧目录，媒体/episode路径相对单集目录。`timeline_sha256`只绑定镜号及start/end；只改QA会改变快照哈希，媒体/时点/内容变化则需新目录重建并重审受影响范围。

`gate-evidence.json` 是可按实际审查范围复制到 `qa.gates.<stage>.evidence` 的文件列表，路径以单集目录为根，直接列出manifest、HTML和所有PNG及其SHA-256，不包含列表自身。记录观察、对照母版或补充片段时须另列这些文件；只引用该列表或manifest不会让阶段检查递归绑定图片，详见 [阶段证据](quality-acceptance.md#美术方法的阶段证据)。

该页用于[整片编排](visual-system.md#整片色彩与构图缩略带)及静态定位；色彩保真、小屏/平台显示、运动与完整声画另实际审查。

## 设计和资产引用绑定

写实新作的模板包含design.visual_intent和逐镜shotbook.realism，按实际实现填写；默认空值不是获准。G1仅绑定文字意义与用途，坐标/时段变化在后续布局和媒体阶段复核；不能因局部移动标签重做未变的选题。首样基准、roughcut/sample/full回执见[制作入口](production-checkpoints.md#开工锁定与真实渲染入口)。

简报固定Skill提交、series-profile和tokens版本/哈希、私有设计板ID/哈希及批准范围。真实使用的设计图、组件、视频和音轨在现有 `assets` 中按实际kind、来源/权利、版本说明与 `sha256`登记，通过 `shots[].asset_ids` 关联；配置参数或索引本身不假报为实拍。复制到项目的配置/设计证据版本与位置留简报及 `qa.visual_frames.note`，不能写“使用最新版”或仅凭公开tokens认设计板通过。

设计板、配置与画面一致性按质量正文实看；公开索引校验不覆盖私有媒体。

仅采用具体获准的历史2D画风时，将Skill内 [参考图](../assets/style/accepted-style-reference.png) 和 [美术规格](../assets/style/bright-nature.art-direction.json) 的固定版本/哈希登记到简报引用清单；实际看图与本镜采用点写在美术记录，不能用文案推定已看。以其生成项目设计板时，`design.board_reference/board_sha256` 仍指当前实际设计板；参考的外观认可与新设计板的实际审查范围分开，不能把系列参考哈希填成新板批准。需要阶段冻结时，把所用参考副本、规格及实际对照文件分别列入既有gate evidence，不从后续安装版本反推旧项目使用内容。

## 逐镜结构与方向图形记录

在 `shotbook.visual_logic` 保存本镜实际导出的检查，不另建脱离分镜的台账：

- `review_scope`：实际检查当前最终导出后才填 `final_export`；计划/短样不能代签
- `orientation`：`applicable` 为布尔值。涉及对象结构或方向时填 true，记录 `status`、`reference`（事实参考定位）、`frame_mapping`（对象自身左右、画面左右与正/侧/背视角）、`structures`（关键结构观察）、`transforms`（镜像/翻转/换视角及跨镜一致性）、`evidence`（实际帧/连续片段与时间点）。明确无相关结构/方向时才填 false 并写 `reason`，不能用不适用绕过已知缺陷
- `graphics`：逐个可见箭头或无向引线登记唯一 `id`、`kind=arrow/leader`、本镜 `asset_id`、`component_reference`（组件来源与版本）、`license_evidence`（与素材台账一致的许可/原创依据）。无此类图形填空列表并用 `no_graphics_reason` 说明
- 每个图形的 `checks` 按项记录 `status`、具体 `note`、实际导出 `evidence`。箭头项为 `tip`（尖端）、`shaft_join`（杆头连接）、`visibility`（缩放/裁切/遮挡）、`direction`（含义）、`endpoints`（起终点）、`motion_extrema`（动画极值/连续性）；引线只需 `visibility`、`endpoints`、`motion_extrema`，在 endpoints 说明连接标签与对象、无方向含义。静态图形也记录最终尺寸/裁切状态且明确无动画

逐镜清点实际导出的全部有关对象和图形，失败、漏记或未验先修；不能改“不适用”或将箭头改名为引线隐藏缺陷。组件、镜像、镜头或导出变更后重审，并绑定当前素材、shotbook及导出摘要。

逐镜来源在 `shotbook.origin`，资产来源在 `assets[].origin`，字段、证据与研究/交付闭包边界统一按 [原创视觉来源契约](science-and-rights.md#逐镜来源证据)。既有模态、权利和审看记录保留，不把新增来源字段当批准或追溯改写旧结果。

## 素材选择要能复核

先写对象、动作、景别、时长及支持陈述，再实际查看候选对应片段，比较对象正确性、动作覆盖、清晰度、构图余量和权利；搜索缩略图不能代实看。

`candidates` 保存来源、`viewing_note` 与取舍；主要候选 `asset_id` 必须属于本镜，辅助层另记 `asset_ids`。`source_interval` 写原片入出点和时间基准；仅静态参考/原创图可填 `still/full`，照片推拉不算实拍。只有一个合法候选时用 `alternatives_note` 说明。来源、创作者、权利证据、范围和署名沿素材台账保留。

## 可选工作方式

可编辑剪辑工程可按解说、字幕、音乐/音效、画面、图内标注分别建轨，以便替换和复核。只有实际导出并在目标编辑器打开验证，才能称为可编辑工程已交付；当前规则不承诺特定剪辑器兼容。

生成参考各注明对象身份、结构事实、风格、动作或构图职责；按时段写动作及须保持的关系，输出逐镜审查。

外部方法的来源、许可、固定版本及实际采用点见[外部技能选型](video-skills-curation.md)。

## 动作卡、镜头配方与事件复核

实际过程类的动作卡八项落实在现有shotbook：对象/锚点、初态、触发、关键变化、终态、轨迹、快慢/观察停顿、观众学到什么；补物理条件、教学简化、关键姿态、口播事件和实际音轨hash。不同机制不套万能弹性曲线；路径、方向、约束、遮挡或观察条件变化可以是实质机制，不强求形变。关键图另说明视角、注意中心、动作路径、字幕区和比例变化。

复用配方记录问题类型、条件、镜头骨架、资产、动作卡、口播事件、科学风险与正反例：整体→局部→整体需同一对象回程；前态→触发→后态保留中间变化；同条件对照只改有关变量；传播→响应核起因/方向/延迟，波前不冒作物质飞出；剖面先建立外形和剖切关系再恢复整体。无声网页演示/相对时间只是候选，不能抵G3，也不能预填未生成音轨的绝对时码。

定位/标签、尺度切换、观察停顿等D时序见制作策略，按任务校准，不机械统一。语义事件实际音频时点与画面时点差超过150ms先标复核警告；提前预备/反应镜头写理由并实际看，不自动判错或自动忽略。

保存可恢复的简报、来源、稿件、分镜、设计/资产、原声/混音分轨、时码、字幕、各媒体版本、审查及授权/平台回执。文件名区分集/剪辑/音轨/画幅版本，字幕/封面/文案独立hash；变更后按[受影响依赖](quality-acceptance.md#失败后的处理)复查，不沿用旧签收。

### 按动作类别补充信息

仅对本镜实际采用的类别填写 `shotbook.action_class`（去重列表）与 `action_class_details`（按类别键组织），复用已有对象、锚点、trigger/key_states/trajectory等字段，不要求每镜全填五类：
- localization_and_label（定位与标签）：appearance_condition（出现条件）、follow_target（跟随目标）、hold_duration（停留）
- scale_transition（尺度切换）：original_object、spatial_anchor、local_frame（局部取景框及坐标基准）、return_location；明确同一对象进出关系
- deformation（对象形变）：topology_states（可对应的同拓扑关键态）、fixed_boundary、sliding_boundary、trajectory；逐机制设计，不把所有对象统一弹跳，也不为工具限制改变科学机制
- propagation_and_change（传播与变化）：cause、origin、direction、delay、end_state；解释动画与实拍一样，若作教学慢放，从第一次使用就清楚提示时间缩放，不等结尾补说明
- observation（观察停顿）：learning_task与duration，实际停留由理解任务决定

`timing_basis.mode`单独说明real_audio（实际音轨ID/hash及语义时点）或relative_plan（无音轨时只记相对阶段）；正式动作方案还记录note说明其语义依据；它不等于speed_and_pause。路径、快慢停顿及音画事件分别记录，不能只用trajectory代替完整动作时序。正文定位/标签合类160–320ms与tokens细分attention160–280、label180–320是同一D的不同粒度，实际可读性和语义优先，不是硬物理时长。

库版本在 `design.library_reference` 固定ID/版本/hash，风格版本仍为design.style_version，不假定二者相等。`design.new_asset_ids`只列本期需新建的资产ID，其他资产按实际复用及变更记录处理；不能将整个资产列表都当新建。

按[入口路由](../SKILL.md#按需读取责任正文)读取当前阶段所需正文与实际配置；`design.library_reference` 记录库的id/version/manifest hash及adoption（采用/仅参考），不混同风格版本。

如果采用雷声机制配方，另读 [条件式完整示例](../assets/examples/thunder-brief.md)，保留其具体禁画、首次慢放即披露和未制作状态；其他题材不因此强制讲雷声，也不恢复被取消题材。

实际依赖统一按资产ID解析：design.font_asset_id和design.render_asset_ids是代表段及成片共用依赖，逐镜asset_ids保留该镜范围，deliverable_asset_ids按产物记录列表。代表段连同其字幕与三尺度设计实际依赖参与权利检查及版本绑定；未使用的后续素材不使当前代表段过期。所有依赖必须类型正确且能解析，不能将非法字段当空列表略过。
### 无音轨的 G1 纸面计划

`plan` / G1 可用 `timing_basis.mode=relative_plan`，填写具体的 `relative_phases` 和 `note`，说明先后语义阶段、观察任务以及真实时点尚待音轨确定。`start`、`end` 留 null 或省略；若有计划语义拍，`beats[].at` 留 null，另写具体 `phase`、拟用触发词、注意对象和动作，也可暂用空 `beats`。不要把尚未合成的拟用口播标成无声镜。

未取得媒体时 `candidates=[]`，`alternatives_note` 写待选对象与缺项，删除未实看的示例候选。G2前取得实际工作音轨，把相对阶段转为真实时点，对齐语义拍并补素材实看；`relative_plan` 不通过G2及后续。

计划包的 `assets` 可登记明确需要、尚待制作/取得的素材需求，再由镜头 `asset_ids` 引用稳定ID：`source` 写计划取得方式及用途，`creator` 如实记待确定，`file` 留空，`rights.status=pending`。这类记录不代表已有素材；`candidates` 只记录真正查看过的候选，两者不混用。`kind` 按拟用媒介选，图解/模拟仍如实填所需 `disclosure`；取得后才补实际原源、作者、文件与权利证据。若连素材需求尚未确定，先交简报，不为结构检查编造素材或科学来源。

## 解释设计与实际镜头的绑定

沿用 `topic_alignment.coverage` 的范围和镜头引用，将 [解释类型与难点方案](production-checkpoints.md#e02e07精制作前的解释设计) 绑定实际镜头及语义拍。类型化关系路径使用 `explanation_steps` 的逐步 `relation_type`，旧范围级 `explanation_type` 兼容读取，历史因果记录可读取 `causal_steps`，同一范围不填写两套竞争结构。每步保留必要前提、关键关系、推导、边界、指代到表现对象的映射、镜头ID、承接及动态适用性；因果步骤另记前态/变化/后态。`prerequisites` 用 `knowledge` 和 `source=audience_prior/step` 绑定具体沿用结论，来源为步骤时填写 `step_id`；受众前提、呈现顺序及旧字符串迁移按 [前提来源规则](production-checkpoints.md#2-把解释关系变成可见表达) 执行。无动态需求须说明为什么静态关系足够，而不是用不适用掩盖缺失过程。

计划路径与实际证据按同一步骤ID衔接。实际表达检查记录作品中看见/听见的关系和推导依据，而非复制设计意图。换镜、剖面、放大或教学扫描的时间/尺度定位及声画语义配合，执行 [E09–E10](quality-acceptance.md#自主解释与表达审查)；静音定位不是静音独立理解全部逻辑，逐字时间同步也不代替及时形成语义对应。

字段以[单集模板](../assets/episode-template.json)为准：`relation_type=causal/spatial/structure_function/comparison/propagation/quantitative/probability/evidence`；按实际类型补空间参照、结构连接、传播路径、共同尺度/分母、概率范围或证据限制。

当前 qa.explanation_review 与 qa.expression_review 可引用同一详细观察证据；旧 `qa.comprehension.internal_review` 兼容绑定当前上下文与最终声画范围，分别保存解释和表达职责、答案/关系/小变化或区分/边界四目标以及每步实际观察证据。能力、所审文件和范围须真实，不能用模板文本制造已看已听事实；当前关尚无实际作品时保留未验，按阶段范围继续草稿而不签成片通过。
制作前纸稿逻辑审查使用 qa.explanation_logic，旧 `qa.comprehension.logic_review` 可兼容读取，明确 `basis=paper_logic` 并绑定G1上下文；它不复用最终声画签收。当前每步 key_difficulty 标识实际关键难点，topic_alignment.expression_cards 覆盖该集合；旧 `brief.difficult_step_ids` 与四项难点卡兼容读取而非强求每个铺垫步骤一张卡；确无专项难点时给具体理由。旧 `causal_steps` 兼容读取不代表旧包可以跳过当前G1解释设计或G5实际审查。

主体动态的定义、长静帧上限、ROI筛查、语义段记录与G2/G3/G5失败门槛统一见 [质量责任正文](quality-acceptance.md#主体动态与长静帧)；逐镜静态方向认可不替代对应动态证据。

逐镜文字用途清单引用 [文字责任正文](visual-system.md#可见文字用途与制作辩解)，分镜语音承接证据引用 [声音责任正文](voice-reference.md#整期旁白连续性)；单镜听感不能代整期连续性。
