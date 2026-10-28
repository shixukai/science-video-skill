---
name: science-video-production
description: 策划、制作、审查或修改自然、生活与工程科普视频、封面及3D资产。写实风格视频使用 MoneyPrinterTurbo，3D动画风格视频使用 Blender；制作与发布按委托范围分别执行。
---

# 科普视频制作

从一个具体问题出发，用有依据的画面、连续中文讲解和同步字幕逐步给出答案。严格按[成片风格选择主制作工具](references/tool-routing.md#按成片风格锁定主制作工具)：写实风格使用 MoneyPrinterTurbo，3D动画风格使用 Blender；不再按工程/自然题材分流。AI模型可为写实路线生成素材，不能代替MoneyPrinterTurbo制作环节。

## 范围与规则优先级

先遵循宿主指令、工具和权限约束，再落实用户当前明确请求及仍有效的授权。新要求覆盖与它冲突的旧偏好，已有授权不重复询问。正文负责规则，配置负责默认参数，单集记录负责本次范围和证据；模板、示例和索引不产生额外门槛。

本 Skill 未指定风格时沿系列写实默认值使用MoneyPrinterTurbo；用户已选3D动画时直接使用Blender，无须再为3D路线索要批准。中文旁白、声音、画幅和封面配置沿适用基准；历史2D参考不能覆盖本期风格。混合风格及额外全幅2D按明确委托范围处理，不能借辅助层静默改变主体风格。科学真实、权利和如实审看仍须满足；趣味、工具偏好和数值起点不能推翻明确委托。用户指定基础题目时保留原题，设计适合其受众的解释。

| 本次委托 | 执行范围与入口 |
| --- | --- |
| 整理 Skill | 检查正文、配置、模板、脚本与适当回归；不调用模型、恢复制作或发布 |
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

- **开场**：完整新片先建立[整体情境与观看理由](references/viewer-retention-design.md#先建立情境和看点再进入解释)，让观众认出对象、用途或真实难点，再收束到原题与第一步解释；不从定义、公式或工序名直接开讲，也不靠空泛片头拖延。明确要求直接答案或局部片段时按委托范围处理。
- **片长与全链路**：视频可按解释需要做得更长。工程科学、工业生产和高端制造优先讲清本题从原理与输入、关键过程到结果和验证的[完整链路](references/topic-contract.md#工程与制造题材的全链路和片长)，按章节组织，再由实际讲解与演示确定时长。
- **画面**：写实主镜按[写实制作契约](references/realistic-production.md)，3D动画按[Blender制作要求](references/engineering-blender.md)，实际看适用参考并确定逐镜主体、关系、动作、注意对象和观众所得。AI/3D不是实拍或科学观测；静图推拉、字幕变化和装饰运动不替代所讲过程。观察停顿按[主体动态](references/quality-acceptance.md#主体动态与长静帧)实审，不为凑秒数捏造动作。
- **Blender场景背景**：按[场景背景与空间完成度](references/engineering-blender.md#blender-场景背景与空间完成度)设计有依据的使用环境、空间层次、材质灯光与跨镜变化；整体镜头不能长期以同一底色/地台代替环境，局部简化须有明确解释用途。开工先检索共享库中的模型、环境、材质与灯光资产，复用前核版本、依赖和本片适用性。
- **指示信息**：按已确认的[精密技术标注](references/annotation-style.md)统一标签、定位线、方向箭头与范围强调，读取独立横版参数；箭头须尖端清楚、头杆连续，不能圆头穿尖。实际核目标绑定、遮挡、小屏和连续运动，风格复用不等于媒体验收。
- **封面**：按[封面成品标准](references/visual-system.md#封面成品标准与工程制造题材)独立制作系列精细插画封面，明确大主体、左上主题名与短问题。工程主体核结构和材质，长片封面对应全链路的核心承诺；本次所需比例独立构图，实际看原图、手机缩略与系列对照后交付。
- **可观看短样**：先用真实播放节奏的开场及关键过程验证应用情境、语速、主体细节与连续动作，再扩展整片。低帧率抽帧代理只供内部查布局，不能作为用户判断观感的唯一样段；已知粗糙、卡顿或无吸引力不能只标“草排/待审”后转给用户。
- **首次试制**：有认可成片时复用；没有时，用已实际查看的适用参考和明确设计制作候选，记录 `design.approved_film_reference.kind=initial_style_reference`，不伪造历史认可。扩片仍须新样连续声画及独立审查。
- **声音**：先写完整讲解再拆镜，复用已确认完整声音。调用Qwen前从上下文和已有工程确定位置，确实缺位置才询问；整理或策划不触发询问，不自动下载权重或另建语音环境。方法见[中文声音](references/voice-reference.md)。
- **来源与模态**：逐镜记录主要画面来源：`controlled_3d`、`ai_generated`、`real_footage` 或获准的 `pure_2d`；混合层分别登记资产。科学依据、风格参考和使用权分开核查。当前系列交付视觉遵循[原创视觉来源契约](references/science-and-rights.md#原创视觉来源契约)，只用自行生成、自建模/渲染、自设计或已核实授权的用户自拍；第三方公开视频、CC/Commons和论文影像仅供研究参考，不能转作填充镜。
- **执行**：复用已有环境；成片级有声草排、代表段与整片通过[执行入口](references/production-checkpoints.md#开工锁定与真实渲染入口)固定规则、设计、输入和输出。无声模型镜头和静态技术试验属于中间资产，记录真实任务和版本，不强迫每个底层操作带音轨或先有G3。
- **工具**：按[场景调用表](references/tool-routing.md)补缺，只读所选工具正文。已有同版环境验证可复用。缺工具先查安装与已有授权；Skill不预授未来安装、云传输、费用或外发权限。相同失败无新依据时停止依赖步骤，继续独立工作。需要有界执行时读[Blender执行核心](scripts/bounded_blender/README.md)或[I2V执行核心](scripts/bounded_i2v/README.md)，保留身份核验、唯一任务与恢复保护；GPU利用率只供观测，不单独设准入门槛。
- **画内标识**：必要字幕、科学标注保留；新增署名、水印、AI标识按[具体范围同意](references/visual-system.md#画内标识须有具体同意)处理。默认在平台字段和简介披露AI/模拟；实际义务需要片内标识时核依据及已有同意，不隐瞒或未经同意加字。
- **证据与反馈**：技术检测、哈希、静帧、连续样段、整片看听、平台结果分别成立。缺能力保持未验，已知失败修后实审；[反馈](references/quality-acceptance.md#用户意见逐项登记与维度隔离)按原媒体、范围和维度保存。独审需真实独立过程和对应感知能力，换名字不算独审。
- **版本**：已发布、取消或禁止版本不自动恢复。更新Skill不热切正在运行的任务；下次续做从全局入口核差异，显式记录迁移并重核受影响依赖。历史锁与归档只供取证，不从冻结副本继续执行，也不能把旧回执改成新版执行。

## 按需读取责任正文

| 问题 | 正文 |
| --- | --- |
| 原题、受众、开场、范围和答案 | [主题契约](references/topic-contract.md) |
| 科学、来源、权利和披露 | [科学与素材](references/science-and-rights.md) |
| 写实主镜和首样 | [写实制作契约](references/realistic-production.md) |
| 写实视频的MoneyPrinterTurbo制作与模型素材 | [写实制作流程](references/ai-generated-video.md) |
| 3D动画、精确结构、连续定位与3D库 | [Blender制作](references/engineering-blender.md)；[只读素材检索](scripts/find_3d_assets.py) |
| 阶段、解释顺序、实际调用、平台动作 | [制作检查点](references/production-checkpoints.md) |
| 画风、构图、文字、封面、接口连接 | [视觉系统](references/visual-system.md)；主要动画再读[场景设计](references/animation-scene-design.md) |
| 旁白生成、连续性和审听 | [中文声音](references/voice-reference.md) |
| 分镜、素材、版本和动作记录 | [逐镜记录](references/shotbook.md) |
| 验收、未验、失败和修复 | [质量验收](references/quality-acceptance.md) |
| 工具与可选方法 | [工具路由](references/tool-routing.md) |
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

回执用新文件名；退出码0为本地检查通过、1为记录阻塞、2为输入/执行错误。脚本不授予审美、科学、权利、听感或发布批准；如实交付待审材料不等于验收通过。
