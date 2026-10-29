---
name: science-video-production
description: 策划、制作、审查或修改自然、生活与工程科普视频、封面及3D资产。写实风格视频使用 MoneyPrinterTurbo，3D动画风格视频使用 Blender；制作与发布按委托范围分别执行。
---

# 科普视频制作

从一个具体问题出发，用有依据的画面、连续中文讲解和同步字幕逐步给出答案。严格按[成片风格选择主制作工具](references/tool-routing.md#按成片风格锁定主制作工具)：写实风格使用 MoneyPrinterTurbo，3D动画风格使用 Blender；不再按工程/自然题材分流。AI模型可为写实路线生成素材，不能代替MoneyPrinterTurbo制作环节。

## 范围与规则优先级

先遵循宿主指令、工具和权限约束，再落实用户当前明确请求及仍有效的授权。新要求覆盖与它冲突的旧偏好，已有授权不重复询问。正文负责规则，配置负责默认参数，单集记录负责本次范围和证据；模板、示例和索引不产生额外门槛。

未指定风格沿系列写实默认值；已选3D动画直接用Blender。混合风格按明确范围执行，历史2D仅在明确获准的2D范围或独立封面使用。用户指定题目时保留原题，按其受众设计解释。

| 本次委托 | 执行范围与入口 |
| --- | --- |
| 整理 Skill | 删除重复和无制作用途的说明，核正文、配置、模板、脚本及适当回归；不调用模型、恢复制作或发布 |
| 只策划 | 读[主题契约](references/topic-contract.md)、[科学与素材](references/science-and-rights.md)、[解释设计](references/production-checkpoints.md)；可交明确待研究的草案，不编来源、音轨或秒数。`plan`是已有主源的结构检查，不是所有草案的必需验收 |
| 仅3D模型、静态预览、检索或入库 | 读[资产任务](references/engineering-blender.md#仅做资产时的任务范围)；核模型、科学关系、依赖和归档，不造音轨、整期episode或G3。完整视频中的中间建模仍保留后续视频义务 |
| 新片或续做视频 | 原包优先；G1解释设计 → G2有声草排 → G3代表段 → G4完整候选 → G5成片质量。先验适用范围的样片，再扩制 |
| 局部修复 | 读取当前媒体、原请求、最新反馈；保留稳定ID及仍有效资产/声音，按[受影响依赖](references/quality-acceptance.md#失败后的处理)复查。纯布局修复不重做选题；新整片仍需完整看听 |
| 只交视频，不做封面 | 记录 `delivery_scope=video_only` 及 `delivery_scope_note`，止于G5；旁白、字幕、科学与整片审查照常，不造封面或平台授权 |
| 封面或完整发布包 | 读[封面设计](references/visual-system.md#两种封面各自设计)。系列发布包默认 `delivery_scope=release_package`，含独立排版的3:4和4:3封面；封面单独用 `--stage covers` |
| 平台预览或发布 | 仅在请求覆盖相应动作时执行G6发布准备、G7发布读回。交付不等于授权上传或公开发布 |

## 唯一全局入口

只使用[一个全局安装](references/global-skill-installation.md)，项目不复制整套Skill，也不从项目冻结副本或维护源码运行生产任务。开始及续做先读取全局规则与用户最新要求；项目只保存制作数据、实际运行证据及规则哈希锁。全局变化后显式迁移，旧锁不能覆盖新要求或自动延续审查。

## 制作关键约束

| 制作项 | 必须落实的动作 | 实审与失败处理 |
| --- | --- | --- |
| 开场与转场 | 先定正文第一项观察，再写能引出它的整体情境、用途或难点；将开场末句/末画面与正文首句/首画面成对设计。[方法与示例](references/viewer-retention-design.md) | 正常速从首帧看到第一项观察成立；无观看理由、铺垫无进展或切入失联，先改情境/问题/定位。直接答案或局部片段按明确委托处理 |
| 解释与片长 | 工程/工业/高端制造讲清本题从输入、原理、关键过程到结果及验证的[完整链路](references/topic-contract.md#工程与制造题材的全链路和片长)；先完整稿后拆镜，实际讲解和观察需要决定片长 | 删支线与重复，不为固定时长加速或省略必要过程 |
| 画面 | 先按当前媒介检索可复用工程/素材；3D资产按[共享素材库](references/engineering-blender.md#查找与选择已有素材)查找。逐镜写主体、关系、驱动/交互、起态/变化/终态及观众所得；按[写实](references/realistic-production.md)或[Blender](references/engineering-blender.md)制作 | 在实际景别和小屏核结构、背景、关键状态；连续看动作与接缝。静图推拉、字幕变化不代替承诺过程；有目的观察按[主体动态](references/quality-acceptance.md#主体动态与长静帧)审 |
| 正文文字 | 禁止左上角、右上角场景/工序说明；仅为当前观察所必需的对象、数值或关系使用辅助文字，按[用途与停留](references/visual-system.md#正文辅助文字的使用与停留)安排完整稳定阅读时间 | 最终编码正常速、小屏读完并认回目标；角落抬头、闪现或须暂停才能理解，修后重审 |
| 标注 | 复用已确认[精密技术标注](references/annotation-style.md)及横版参数；区分定位引线、方向箭头和范围强调 | 尖端清楚、头杆连续且杆不穿尖；在实际缩放/遮挡/运动极值和小屏核目标绑定 |
| 声音 | 按[中文声音](references/voice-reference.md)优先复用仍有效的认可主轨；新增合成按连续讲述，稳定音色与自然音区，起音清楚、句尾利落，先连听基准段、难句与接缝再扩合成 | 源轨与最终混音分别实听；语速认可不代音调连续通过。漂移或拖沓先修稿件、合成单元及处理链，不以统一响度或反复倍速掩盖 |
| 封面 | 仅按委托制作，按[封面标准](references/visual-system.md#封面成品标准与工程制造题材)独立排版本次所需比例 | 原图、手机缩略及系列对照核主体、结构、标题和真实观看承诺 |
| 先样后片 | 先以正常帧率的低成本连续预演核开场/转场，再做最终引擎细节样段；G2检查整期解释，G3核正式代表段后扩制。[Blender执行与复用](references/blender-execution.md)，局部动态修复按[完整周期](references/blender-execution.md#complete-a-repair-cycle-before-expanding)验证开合与接缝 | 先修已知粗糙、卡顿、失焦和慢旁白；低帧率布局代理不作为用户判断观感的唯一样段；新整片仍完整看听 |



- **制作基准**：有适用认可成片就复用；首次试制用实际查看的适用参考，记 `design.approved_film_reference.kind=initial_style_reference`。按[场景背景](references/engineering-blender.md#blender-场景背景与空间完成度)设计有依据的环境、层次和跨镜变化；局部简化须服务解释。
- **来源与标识**：逐镜记录 `controlled_3d/ai_generated/real_footage/pure_2d`，混合层分别登记；科学依据、风格参考和使用权分开；当前系列执行[原创视觉来源契约](references/science-and-rights.md#原创视觉来源契约)，只用自行生成、建模/渲染、设计或已核实授权的用户自拍，第三方影像仅供研究参考。字幕/科学标注保留；新增署名、水印或片内AI标识按[具体范围同意](references/visual-system.md#画内标识须有具体同意)处理。
- **本地优先与性能**：能在本机完成的制作、素材处理与检测优先在本机执行；按[本地执行、最少传输与吞吐](references/tool-routing.md#本地执行最少传输与吞吐)复用本地数据、最小化跨端传输，画质优先，积极并行利用CPU、GPU与缓存，在系统保持响应和稳定的前提下提高有效吞吐；资源争用时调整本任务并发，不设任意利用率上限。
- **执行与复用**：复用现有环境；调用Qwen前查上下文和已有工程，确缺位置才问，不自动下载或另建环境。有声草排、样段与整片走[执行入口](references/production-checkpoints.md#开工锁定与真实渲染入口)；无声镜头/静态测试按中间资产保存实际版本。工具补缺按[路由](references/tool-routing.md)及已有授权，连续相同失败无新依据时停止该依赖。有界候选按[Blender](scripts/bounded_blender/README.md)或[I2V](scripts/bounded_i2v/README.md)核心执行，保留身份、唯一任务与恢复保护。 Resource refusals and device fallback follow the [current-evidence rule](references/production-checkpoints.md#静态证据条件复用与动态新鲜检查); generated launchers cannot invent admission thresholds.
- **审查与版本**：技术检测、静帧、连续声画和平台结果分别记录；按[审片传输](references/tool-routing.md#review-media-without-repeated-uploads)本地筛选、按需传图和去重，不把整段序列逐张回传。独立审查须有独立过程及实际感知能力。[反馈](references/quality-acceptance.md#用户意见逐项登记与维度隔离)按媒体/范围/维度保留，缺能力未验、已知失败修后重审。规则更新不热切运行任务，也不恢复已发布、取消或禁止版本；续做显式迁移，不改写旧锁和旧回执。

## 按需读取责任正文

| 问题 | 正文 |
| --- | --- |
| 原题、受众、开场、范围和答案 | [主题契约](references/topic-contract.md) |
| 科学、来源、权利和披露 | [科学与素材](references/science-and-rights.md) |
| 写实主镜和首样 | [写实制作契约](references/realistic-production.md) |
| 写实视频的MoneyPrinterTurbo制作与模型素材 | [写实制作流程](references/ai-generated-video.md) |
| 3D动画、精确结构、连续定位与3D库 | [Blender制作](references/engineering-blender.md)、[爆炸图与剖切](references/engineering-blender.md#爆炸图与剖切的选择)；[只读素材检索](scripts/find_3d_assets.py) |
| 人物绑定、动捕、操作与口型 | [人物表演](references/engineering-blender.md#人物绑定动捕与口型)；按需启用可编辑3D或视频后处理，先核实际难点 |
| 阶段、解释顺序、实际调用、平台动作 | [制作检查点](references/production-checkpoints.md) |
| 画风、构图、文字、封面、接口连接 | [视觉系统](references/visual-system.md)；主要动画再读[场景设计](references/animation-scene-design.md) |
| 旁白生成、连续性和审听 | [中文声音](references/voice-reference.md) |
| 分镜、素材、版本和动作记录 | [逐镜记录](references/shotbook.md) |
| 验收、未验、失败和修复 | [质量验收](references/quality-acceptance.md) |
| 工具与可选方法 | [工具路由](references/tool-routing.md) |
| 复杂任务分工、调用与独立审查 | [子代理协作](references/subagent-orchestration.md)：主代理统筹，复杂制作/返工按独立任务实际委派适用角色，分别核角色载入、原生/备用调用与产物；小修改直接完成 |
| 留存编排或透明度/画幅故障 | 按需读[持续观看](references/viewer-retention-design.md)或[渲染取证](references/render-evidence.md) |

[责任索引](indexes/rule-owners.json)和[章节覆盖索引](indexes/standard-coverage.json)只用于导航和维护，不复制规则或充当逐集检查单。历史案例与 `references/learning-candidates/` 中的未验证经验候选不是所有题材的固定镜头、阈值或通过证据。

## 配置、记录与校验

新作采用[系列配置](config/series-profile.json)的1920×1080横版默认值；旧竖版字幕修订只作用于指定旧项目。写实项目绑定适用参考；随包[历史插画](assets/style/accepted-style-reference.png)、[美术规格](assets/style/bright-nature.art-direction.json)和[色彩参数](assets/style/bright-nature.tokens.json)只在适用2D/封面范围使用。科学本色优先。质量和可校准起点见[制作策略](config/production-policy.json)，配置状态不代表实审通过或行动授权。

按交付深度使用[简报](assets/brief-template.md)、[单集记录](assets/episode-template.json)、[原题锚点](assets/topic-anchor-template.json)。模板是空记录结构，不是预先认可；删除不适用示例，缺证据保持未验。单集文件放用户工作目录；相对媒体/证据路径以 `episode.json` 所在目录为根。

从使用中的Skill目录运行；`python`替换为已有可用解释器，Windows不使用应用商店占位：

    python -X utf8 scripts/check_reference_system.py .
    python -X utf8 scripts/render_gate.py lock <单集绝对路径>/skill-lock.json
    python -X utf8 scripts/render_gate.py run <episode.json> --phase roughcut --shot-ids SH1,SH2 --output roughcut-001.mp4 --receipt roughcut-run-001.json
    python -X utf8 scripts/render_gate.py run <episode.json> --phase sample --shot-ids SH1 --output sample-001.mp4 --receipt sample-run-001.json
    python -X utf8 scripts/check_episode.py <episode.json> --stage G3 --report <新回执.json>
    python -X utf8 scripts/check_episode.py <episode.json> --stage delivery --report <新交付回执.json>

按实际阶段选命令，不照抄镜号。`roughcut`用于G2整期有声草排，`sample`用于待审代表段；两者不要求已有G3，`full`才要求当前G3后扩片。已有匹配规则锁可复用，不每次制造新锁。`plan`不晋级；G1–G7按适用阶段核证据；`delivery`检查本地成片至G5，`publish_ready`检查至G6，`covers`只验封面。发布仍需实际动作和G7读回。

回执用新文件名；退出码0为本地检查通过、1为记录阻塞、2为输入/执行错误。结构检查后，按对应阶段完成实际审查并记录缺项。
