---
name: science-video-production
description: 为普通大众制作自然现象与生活科学视频，使用有权真实动态视频与纯2D解释；按引用式标准规划、制作、审查或修改单集及发布包，不用于自动发布或普通问答。
---

# 自然科普视频制作

先让人认出观察现象，再讲清原问题。实际结果按媒介、版本与审查范围分别成立，目录、参数、技术测试和局部认可不能代替成片。

## 核心边界

- 明确主问题及必要的从属问题与联系；用户明确改方向时更新当前范围，局部修复不擅改题；主图、口播、必要图内字须共同解释
- 原理用纯2D；真实锚点用合法连续实拍/观测视频，照片运动或AI不得顶替
- 每条有中文解说及同步字幕；沿用项目已确认声音，不能用纯字幕配乐冒充完成
- 静态方向、组件、连续样段、整片理解、声音、平台与发布分别验；已知失败不得带病放行
- 已发布、明确取消或禁止的版本不自动重做/恢复；本Skill写入或升级本身不提供制作恢复、外传或发布权限

## 阶段路由：逐项执行适用的责任正文

| 阶段/问题 | 唯一责任正文 | 产物 |
| --- | --- | --- |
| 原题、开场、局部范围和答案 | [主题契约](references/topic-contract.md) | 原题锚点与覆盖证据 |
| 科学、视频原源、权利与两类素材索引 | [科学与素材](references/science-and-rights.md) | 主张/来源/权利及候选 |
| 解释设计、前提、关系类型、整期草排与交付发布 | [制作检查点](references/production-checkpoints.md) | 整期计划、有声代表段、发布回执 |
| 系列画风、三尺度、色与字、布局和封面 | [视觉设计系统](references/visual-system.md) | 当前设计板引用与实现版本 |
| 音轨生成、传输边界与实际听验 | [中文声音](references/voice-reference.md) | 成品音轨及审听范围 |
| 语义拍、候选、动作卡、方向图形与版本绑定 | [逐镜记录](references/shotbook.md) | episode.json与私有证据 |
| 检查对象、证据、失败/未验和反馈复查 | [质量验收](references/quality-acceptance.md) | 分项实际验收记录 |

同一规则仅在对应正文展开；模板只记录结果，其他章节用链接调用。规则归属与阶段见 [责任索引](indexes/rule-owners.json)，它不创建第二套规则。[完整条款覆盖索引](indexes/standard-coverage.json) 逐项指向责任正文，配套字段重复不算新增独立门槛。

## 当前系列实现基准

- [完整制作策略](config/production-policy.json)：G1–G7、H/D区分、评分、自主解释审查及产能/复盘起点；缺实际能力记未满足
- [系列配置](config/series-profile.json)：明亮自然方向、纯2D、Qwen/Serena、画幅/字幕与交付默认值
- [视觉参数](assets/style/bright-nature.tokens.json)：色角色、可调配比、字阶/线条起点；科学本色优先
- 项目在私有工作包提供已确认设计板及批准范围；公开仓不包含其原图或私有链接
- 采用本版完整标准及参数只确定工作基准，未自动批准新动作、科学机制、平台布局或整片；按当前任务范围推进，不从配置状态推断复工

先读取配置和所需正文，再复制 [简报](assets/brief-template.md)、[单集记录](assets/episode-template.json) 和 [原题锚点](assets/topic-anchor-template.json)。逐镜实际使用的基准/资产版本与哈希记入私有单集，不以“最新版”代替固定引用。

## 检查与交付

从本Skill目录运行：

    python scripts/check_reference_system.py .
    python scripts/check_episode.py path/to/episode.json --stage plan
    python scripts/check_episode.py path/to/episode.json --stage G3
    python scripts/check_episode.py path/to/episode.json --stage delivery

第一项只核规则归属、参数与公共索引结构/哈希；阶段检查必须在对应推进前调用并保存回执，plan不晋级，G1–G7逐关核证据，delivery含G6。范围与限制见 [技术检查](references/quality-acceptance.md#记录与技术检查)。通过命令不等于科学、权利、美术、听觉、理解或发布通过。缺实际视听时按质量正文保持未验，可交明确待审材料，不能包装成验收完成。

所有适用标准逐项执行，基本素材仅作参考；现行具体项目配置优先。只整理Skill时，不动媒体；用户明确要求完成整理后恢复制作时，先核版本发布/读回结果，再在原授权范围进入对应阶段。任何新的暂停、取消或版本限制优先。

