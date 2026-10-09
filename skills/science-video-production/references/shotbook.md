# 从成品音轨到可复核的逐镜记录

把方法落实到 `shots[].shotbook`，不要再堆一份与制作脱节的口号清单。计划阶段可待补；成片交付必须完整。旧的计划包仍可读取，旧的交付包须补齐这些记录才能重新验收。

## 音频先行，但不牺牲画面

先用当前成品级解说划分语义拍，再排镜头，不从估算字数或固定4–6秒切镜反推。每拍明确注意力任务及主次，不机械限制对象数量，写清口播触发词、实际音轨时点、相关对象的动作、状态或需观察的关系。对象需要先被认识；静止观察可以是合理动作，不为显得活泼而漂浮、抖动或硬推拉。

`start`、`end`、`beats[].at` 均为成片时间轴上的秒数。镜头按序、互不重叠；叠化属于镜内合成。没有解说的纯观察镜填 `beats: []` 并用 `silence_reason` 说明停顿作用；语义拍只覆盖实际解说事件，不必伪造词句填满静默。每镜填 `subject`（对象）、`action`（动作）、`framing`（景别/取景）、`claim_support`（本镜如何支持所列主张；无主张则解释叙事作用）、`motion_purpose`（变化怎样帮助理解或为何保持静止）。

将当前解说文件 SHA-256 写入 `narration.audio_sha256`。换录音、裁剪、变速或重排后，重新听并对齐全部受影响语义拍；更新校验值不能代替重听。检查器只查时间及版本一致性，不会识别词义、判断听感，也不自动批准画面。

## 先静帧完成度，再分层动作

先按 [视觉系统](visual-system.md) 引用当前设计基准，再把每镜关键帧做到可独立审看的成品级。按质量验收记录 `keyframe_review` 的当前文件、SHA-256、实际结论和具体观察。纯2D分层后，用确定性时间线控制揭示、遮罩、标注及必要的状态改变。动画不能掩盖底图粗糙或错误；无需为了采用流程额外安装引擎，也不做3D桥接。

因果/过程的动作卡在现有分镜中记稳定锚点、初态、触发、过程/终态、轨迹、停顿和理解目的；约束、数量、概率或证据类记录参照、条件、比较/呈现顺序及推导，不为字段捏造运动；每次切镜/模型变化记录前后镜号/时点和桥接。动作规则与阶段门槛由 [生产检查点](production-checkpoints.md) 负责，实际验收由 [质量正文](quality-acceptance.md) 负责，不另造平行台账。将这次实际声画审看记入 `qa.shotbook`，`reviewed_sha256` 使用检查器的 `shotbook_sha256(data)` 返回值。任一镜头、素材台账或音轨版本改变都会使该签收过期。每项本地素材的 `assets[].sha256` 也须与当前文件一致，换素材后重审，不能只刷新摘要。哈希只防止沿用旧声明，不能证明真的看过，也不替代整片验收。

## 整片视觉抽帧工具

已有实际对齐媒体的 `shotbook.start/end` 秒数时，可用 [build_visual_review.py](../scripts/build_visual_review.py) 生成静态审片材料。从Skill目录运行：

```bash
python3 scripts/build_visual_review.py /path/to/episode.json --media renders/candidate-v3.mp4 --output reviews/G5-v3
```

需要Python3.11+及本地ffmpeg/ffprobe，不自动安装、联网或修改episode/QA。`--media` 和相对 `--output` 均以episode所在目录为根，媒体与输出须在该目录内；输出必须是新目录，已有目录不覆盖。工具限定本地自包含视频容器，拒绝播放列表；非方形像素或非默认显示变换须先在制作软件输出已校正的审查副本，不能静默当作普通方形像素画面。无真实秒数的 `relative_plan`、null、非有限数、重叠/乱序或超出视频时长的镜头会失败，不能用估算时点冒充实际对齐。静帧诊断不要求视频自带音频，也不证明G2及后关的真实音轨条件已满足。

产物包含 `index.html`、每镜首/中/末PNG、`manifest.json` 及 `gate-evidence.json`。总览只代表所列镜头；页面显示源视频时长、所列区间及未覆盖区间，局部输入不冒充整期。保留完整画幅，网页仅缩放显示；按解码帧时间选取相应时点实际显示的帧，末样严格取结束边界前的帧，避免抽到下一镜或EOF。manifest同时记录请求秒数与实际帧时间，短镜/低帧率可能重复同一帧，实际帧起始时点也可能早于请求时点；这不证明剪辑点或分镜标注准确。关键机制状态、接缝和运动极值未命中时另补证据。

manifest记录生成时episode原字节SHA-256、源视频摘要、工具版本、各帧时点及HTML/PNG摘要；输出条目路径以抽帧目录为根，媒体与episode路径以单集目录为根。`timeline_sha256` 只绑定有序镜号及start/end，不覆盖画面、动作描述或全部QA。只改QA会改变episode快照哈希，不能据此认定视频变了；反过来也不能凭时间轴相同沿用已改变媒体/关键状态的观察。换媒体、时点或相关内容后使用新输出目录重建并重审实际影响范围。

`gate-evidence.json` 是可按实际审查范围复制到 `qa.gates.<stage>.evidence` 的文件列表，路径以单集目录为根，直接列出manifest、HTML和所有PNG及其SHA-256，不包含列表自身。记录观察、对照母版或补充片段时须另列这些文件；只引用该列表或manifest不会让阶段检查递归绑定图片，详见 [阶段证据](quality-acceptance.md#美术方法的阶段证据)。

该页辅助 [整片编排](visual-system.md#整片色彩与构图缩略带) 和静态定位；自动抽帧不代替工作软件的色彩管理、母版/最终编码保真对照、实际小屏或平台显示检查。它没有测量审美，也不能凭固定三帧确认中间动作、字幕持续可读、完整声画或L3；是否看过及看见什么仍由审查者如实记录。

## 设计和资产引用绑定

简报固定Skill提交、series-profile和tokens版本/哈希、私有设计板ID/哈希及批准范围。真实使用的设计图、组件、视频和音轨在现有 `assets` 中按实际kind、来源/权利、版本说明与 `sha256`登记，通过 `shots[].asset_ids` 关联；配置参数或索引本身不假报为实拍。复制到项目的配置/设计证据版本与位置留简报及 `qa.visual_frames.note`，不能写“使用最新版”或仅凭公开tokens认设计板通过。

当前 `episode.json` 字段不增加一套平行审批状态。素材/语义拍/文件hash由现有检查器绑定；设计板、配置引用与实际画面是否一致按质量正文实看。本仓索引检查只验证公开组件哈希，不能验证私有媒体或批准的真实性。

采用当前系列画风时，将Skill内 [参考图](../assets/style/accepted-style-reference.png) 和 [美术规格](../assets/style/bright-nature.art-direction.json) 的固定版本/哈希登记到简报引用清单；实际看图与本镜采用点写在美术记录，不能用文案推定已看。以其生成项目设计板时，`design.board_reference/board_sha256` 仍指当前实际设计板；参考的外观认可与新设计板的实际审查范围分开，不能把系列参考哈希填成新板批准。需要阶段冻结时，把所用参考副本、规格及实际对照文件分别列入既有gate evidence，不从后续安装版本反推旧项目使用内容。

## 逐镜结构与方向图形记录

在 `shotbook.visual_logic` 保存本镜实际导出的检查，不另建脱离分镜的台账：

- `review_scope`：实际检查当前最终导出后才填 `final_export`；计划/短样不能代签
- `orientation`：`applicable` 为布尔值。涉及对象结构或方向时填 true，记录 `status`、`reference`（事实参考定位）、`frame_mapping`（对象自身左右、画面左右与正/侧/背视角）、`structures`（关键结构观察）、`transforms`（镜像/翻转/换视角及跨镜一致性）、`evidence`（实际帧/连续片段与时间点）。明确无相关结构/方向时才填 false 并写 `reason`，不能用不适用绕过已知缺陷
- `graphics`：逐个可见箭头或无向引线登记唯一 `id`、`kind=arrow/leader`、本镜 `asset_id`、`component_reference`（组件来源与版本）、`license_evidence`（与素材台账一致的许可/原创依据）。无此类图形填空列表并用 `no_graphics_reason` 说明
- 每个图形的 `checks` 按项记录 `status`、具体 `note`、实际导出 `evidence`。箭头项为 `tip`（尖端）、`shaft_join`（杆头连接）、`visibility`（缩放/裁切/遮挡）、`direction`（含义）、`endpoints`（起终点）、`motion_extrema`（动画极值/连续性）；引线只需 `visibility`、`endpoints`、`motion_extrema`，在 endpoints 说明连接标签与对象、无方向含义。静态图形也记录最终尺寸/裁切状态且明确无动画

逐镜清点实际导出中的全部有关对象和图形，不能只检查模板示例或挑好看的箭头。任一失败、漏记、未验即退回；不能仅改成“不适用”或把箭头改名为引线来隐藏已知缺陷，修复并实际复核后才更新结论；镜像、组件、镜头或导出修改后重审。现有素材 SHA-256、shotbook 摘要与最终导出哈希共同绑定版本；只刷新哈希不算复查。检查器只拦记录结构异常、失败、无效引用和旧版本，不识别左右手、不数实际画面箭头、不判断视觉正确或美观；是否漏项仍须实际逐镜审看。

## 素材选择要能复核

先明确本镜对象、动作、景别、所需时长与支持陈述，再找候选。实际查看多个候选的对应片段，比较对象正确性、动作覆盖、清晰度、构图余量及可用权利；不要只凭搜索缩略图、标题或平台总称选中。

在 `candidates` 保留来源、`viewing_note` 与取舍理由。指定一个主要候选，所选 `asset_id` 必须属于本镜；辅助层仍通过 `asset_ids` 单独记账。`source_interval` 写原素材入点/出点及时间基准，只有非真实视频锚点的静态参考/原创图才写 `still`/`full`；真实视频锚点必须给所用原片连续入出点及实际观看记录，不能因文件已封装成视频就把照片推拉填成实拍。此字段是人工可追溯声明，检查器只查非空，不会自动验证原素材时长或区间真实性。如确实只有一个合法可用候选，用 `alternatives_note` 解释限制，不伪造看过多个候选。每项素材已有的来源、创作者、权利证据、使用范围和署名仍必须独立齐全；搜索命中和候选入选都不授予使用权。

## 可选工作方式与参考边界

可编辑剪辑工程可按解说、字幕、音乐/音效、画面、图内标注分别建轨，以便替换和复核。只有实际导出并在目标编辑器打开验证，才能称为可编辑工程已交付；当前规则不承诺特定剪辑器兼容。

使用参考图/视频辅助生成时，为每份参考明确“对象身份、结构事实、风格、动作或构图”的角色，按时间段写对象动作及保持不变的关系。参考角色不能混用，生成结果仍逐镜审查。不要把任何示例中的健康/科学断言或某模型当时的时长、分辨率、价格写成永久制作规则。

以下是工作方法来源，本文及检查逻辑为本项目独立编写。逐项许可、固定版本、实际采用点及条件式技术引用见 [外部技能选型](video-skills-curation.md)；这些链接不授予不受限的复制或素材使用权：

- [Talkcraft](https://github.com/Vincentwei1021/video-talkcraft/blob/main/SKILL.md)：关注成品音频、语义拍及注意力对象
- [Vox Director](https://github.com/Alisa0808/vox-director/blob/main/SKILL.md)：关注先关键帧后分层运动
- OpenMontage [素材选择](https://github.com/calesthio/OpenMontage/blob/main/skills/pipelines/documentary-montage/asset-director.md)与[剪辑组织](https://github.com/calesthio/OpenMontage/blob/main/skills/pipelines/documentary-montage/edit-director.md)：关注逐镜需求、候选实看和素材可追溯性
- [剪映编辑技能](https://github.com/luoluoluo22/jianying-editor-skill)：仅参考可编辑分轨交付思路，未作兼容性验证
- [Seedance 技能](https://github.com/dexhunter/seedance2-skill)：仅参考素材角色与分时段动作描述

## 动作卡、镜头配方与事件复核

实际过程类的动作卡八项落实在现有shotbook：对象/锚点、初态、触发、关键变化、终态、轨迹、快慢/观察停顿、观众学到什么；补物理条件、教学简化、关键姿态、口播事件和实际音轨hash。不同机制不套万能弹性曲线；路径、方向、约束、遮挡或观察条件变化可以是实质机制，不强求形变。关键图另说明视角、注意中心、动作路径、字幕区和比例变化。

复用配方记录问题类型、条件、镜头骨架、资产、动作卡、口播事件、科学风险与正反例：整体→局部→整体需同一对象回程；前态→触发→后态保留中间变化；同条件对照只改有关变量；传播→响应核起因/方向/延迟，波前不冒作物质飞出；剖面先建立外形和剖切关系再恢复整体。无声网页演示/相对时间只是候选，不能抵G3，也不能预填未生成音轨的绝对时码。

定位/标签、尺度切换、观察停顿等D时序见制作策略，按任务校准，不机械统一。语义事件实际音频时点与画面时点差超过150ms先标复核警告；提前预备/反应镜头写理由并实际看，不自动判错或自动忽略。

每片保存可恢复的简报、来源、脚本、分镜、设计/资产、原声/混音分轨、事件时码、字幕、样片/候选/发布版、审查、授权/平台回执与反馈。目录可适配现项目，信息不能漏。命名含集/剪辑/音轨/画幅版本，不用final_final_latest；字幕、封面、文案独立hash。改稿使事实/理解/旁白/字幕/相关镜头失效，改音轨使听检/同步/完整片失效，改布局使视觉/字幕/平台失效，改封面文案使包装和相关授权失效。视频任何字节变动需重新绑定并重审相关最终项目。

### 按动作类别补充信息

仅对本镜实际采用的类别填写 `shotbook.action_class`（去重列表）与 `action_class_details`（按类别键组织），复用已有对象、锚点、trigger/key_states/trajectory等字段，不要求每镜全填五类：
- localization_and_label（定位与标签）：appearance_condition（出现条件）、follow_target（跟随目标）、hold_duration（停留）
- scale_transition（尺度切换）：original_object、spatial_anchor、local_frame（局部取景框及坐标基准）、return_location；明确同一对象进出关系
- deformation（对象形变）：topology_states（可对应的同拓扑关键态）、fixed_boundary、sliding_boundary、trajectory；逐机制设计，不把所有对象统一弹跳，也不为工具限制改变科学机制
- propagation_and_change（传播与变化）：cause、origin、direction、delay、end_state；解释动画与实拍一样，若作教学慢放，从第一次使用就清楚提示时间缩放，不等结尾补说明
- observation（观察停顿）：learning_task与duration，实际停留由理解任务决定

`timing_basis.mode`单独说明real_audio（实际音轨ID/hash及语义时点）或relative_plan（无音轨时只记相对阶段）；正式动作方案还记录note说明其语义依据；它不等于speed_and_pause。路径、快慢停顿及音画事件分别记录，不能只用trajectory代替完整动作时序。正文定位/标签合类160–320ms与tokens细分attention160–280、label180–320是同一D的不同粒度，实际可读性和语义优先，不是硬物理时长。

库版本在 `design.library_reference` 固定ID/版本/hash，风格版本仍为design.style_version，不假定二者相等。`design.new_asset_ids`只列本期需新建的资产ID，其他资产按实际复用及变更记录处理；不能将整个资产列表都当新建。

开工先按 [入口路由](../SKILL.md#阶段路由逐项执行适用的责任正文) 阅读当前阶段适用的责任章节、固定版本配置/tokens与实际资产清单，再登记本片引用；推进阶段时补读新增适用章节，不遗漏其约束。固定引用记录不替代先读规则。库的id/version/manifest hash及adoption（已采用或仅参考）记design.library_reference；不要把风格版本、原资料包版本或当期允许库版本当同一个值。

如果采用雷声机制配方，另读 [条件式完整示例](../assets/examples/thunder-brief.md)，保留其具体禁画、首次慢放即披露和未制作状态；其他题材不因此强制讲雷声，也不恢复被取消题材。

实际依赖统一按资产ID解析：design.font_asset_id和design.render_asset_ids是代表段及成片共用依赖，逐镜asset_ids保留该镜范围，deliverable_asset_ids按产物记录列表。代表段连同其字幕与三尺度设计实际依赖参与权利检查及版本绑定；未使用的后续素材不使当前代表段过期。所有依赖必须类型正确且能解析，不能将非法字段当空列表略过。
### 无音轨的 G1 纸面计划

`plan` / G1 可用 `timing_basis.mode=relative_plan`，填写具体的 `relative_phases` 和 `note`，说明先后语义阶段、观察任务以及真实时点尚待音轨确定。`start`、`end` 留 null 或省略；若有计划语义拍，`beats[].at` 留 null，另写具体 `phase`、拟用触发词、注意对象和动作，也可暂用空 `beats`。不要把尚未合成的拟用口播标成无声镜。

尚未制作或取得媒体时，`candidates=[]` 并在 `alternatives_note` 写具体待选需求和当前缺项；模板候选仅是字段示例，未查看时应删除，不能填写虚构的观看或入选记录。这些计划不证明媒体、声音、权利或视觉质量通过。进入 G2 前须取得实际工作音轨，将相对阶段转为实际秒数、对齐语义拍并完成素材实看记录；`relative_plan` 不能通过 G2 及后续阶段。

计划包的 `assets` 可登记明确需要、尚待制作/取得的素材需求，再由镜头 `asset_ids` 引用稳定ID：`source` 写计划取得方式及用途，`creator` 如实记待确定，`file` 留空，`rights.status=pending`。这类记录不代表已有素材；`candidates` 只记录真正查看过的候选，两者不混用。`kind` 按拟用媒介选，图解/模拟仍如实填所需 `disclosure`；取得后才补实际原源、作者、文件与权利证据。若连素材需求尚未确定，先交简报，不为结构检查编造素材或科学来源。

## 解释设计与实际镜头的绑定

沿用 `topic_alignment.coverage` 的范围和镜头引用，将 [解释类型与难点方案](production-checkpoints.md#e02e07精制作前的解释设计) 绑定实际镜头及语义拍。类型化关系路径使用 `explanation_steps` 的逐步 `relation_type`，旧范围级 `explanation_type` 兼容读取，历史因果记录可读取 `causal_steps`，同一范围不填写两套竞争结构。每步保留必要前提、关键关系、推导、边界、指代到表现对象的映射、镜头ID及动态适用性；因果步骤才同时保留前态/变化/后态/承接。无动态需求须说明为什么静态关系足够，而不是用不适用掩盖缺失过程。

计划路径与实际证据按同一步骤ID衔接。实际表达检查记录作品中看见/听见的关系和推导依据，而非复制设计意图。换镜、剖面、放大或教学扫描的时间/尺度定位及声画语义配合，执行 [E09–E10](quality-acceptance.md#自主解释与表达审查)；静音定位不是静音独立理解全部逻辑，逐字时间同步也不代替及时形成语义对应。

类型路径的记录字段以 [单集模板](../assets/episode-template.json) 为准：`relation_type` 使用 causal、spatial、structure_function、comparison、propagation、quantitative、probability 或 evidence；旧 explanation_type 按责任正文映射。共享步骤记录前提、关系、推导、边界、指代映射与镜头引用；所选类型补充实际所需的空间参照/结构连接/传播路径/共同尺度分母/概率范围/证据限制。字段只核记录完整，不能自动证明推理真实有效。

当前 qa.explanation_review 与 qa.expression_review 可引用同一详细观察证据；旧 `qa.comprehension.internal_review` 兼容绑定当前上下文与最终声画范围，分别保存解释和表达职责、答案/关系/小变化或区分/边界四目标以及每步实际观察证据。能力、所审文件和范围须真实，不能用模板文本制造已看已听事实；当前关尚无实际作品时保留未验，按阶段范围继续草稿而不签成片通过。
制作前纸稿逻辑审查使用 qa.explanation_logic，旧 `qa.comprehension.logic_review` 可兼容读取，明确 `basis=paper_logic` 并绑定G1上下文；它不复用最终声画签收。当前每步 key_difficulty 标识实际关键难点，topic_alignment.expression_cards 覆盖该集合；旧 `brief.difficult_step_ids` 与四项难点卡兼容读取而非强求每个铺垫步骤一张卡；确无专项难点时给具体理由。旧 `causal_steps` 兼容读取不代表旧包可以跳过当前G1解释设计或G5实际审查。
