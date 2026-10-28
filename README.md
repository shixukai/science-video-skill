# science-video-skill

面向自然、生活、工程科学与工业制造的科普视频制作 Skill。当前版本1.6.9；具体修订以Git提交为准。

- **写实 → MoneyPrinterTurbo，3D动画 → Blender**。主体风格决定主工具；模型生成、字幕和编码作为辅助环节。
- **只有一个全局生产安装**。项目只保存数据和规则哈希锁，不复制Skill；维护源码不作生产入口。续做先读全局差异并显式迁移，保留旧执行记录。
- **开场先有情境和观看理由**。从正文第一观察倒推开场，成对设计末句/末画面与正文首句/首画面，连续审看到第一观察兑现。主题与路线可自然合句，不为时间字段硬拆。
- **工程制造讲完整链路**。输入、原理、关键过程、结果和验证按题目范围分章，真实讲解及观察需要决定片长。
- **先样后片**。实际播放节奏验证主体、动作、声音和接缝；低帧率布局代理限内部使用。整片仍完整看听。
- **精密标注与独立封面**。标注区分定位、方向和范围，尖箭头头杆连续且杆不穿尖；封面按本次所需比例独立构图并看手机缩略。
- **声音可修可验**。复用认可声音，先试听开场与难句；错读、拖慢、断句及接缝按原因修复，源音轨与最终混音分别听验。
- **当前系列原创视觉来源**。自行生成、建模/渲染、设计或已核实授权的用户自拍；第三方视频、论文影像仅供研究参考。

本轮统一开场、转场、画面、声音的制作动作和退回条件，删去重复解释、工具百科和无操作用途文字；修正旧2D、旧冻结版本及题材偏置。正文和脚本契约保持对应，实际媒体结果仍由对应看听记录确认。

## 使用入口

从[SKILL.md](skills/science-video-production/SKILL.md)按本次委托读取所需正文。新作默认1920×1080；历史2D与竖版参数仅用于明确适用的范围。视频交付止于G5；平台准备和发布仅在任务覆盖时进入G6/G7。

| 要解决的问题 | 正文 |
| --- | --- |
| 原题、全链路与开场 | [主题契约](skills/science-video-production/references/topic-contract.md)、[开场与转场](skills/science-video-production/references/viewer-retention-design.md) |
| 实际工具与执行阶段 | [工具路由](skills/science-video-production/references/tool-routing.md)、[制作检查点](skills/science-video-production/references/production-checkpoints.md) |
| 画面、标注与封面 | [视觉系统](skills/science-video-production/references/visual-system.md)、[精密标注](skills/science-video-production/references/annotation-style.md) |
| 声音 | [语音与听验](skills/science-video-production/references/voice-reference.md) |
| 失败和验收 | [质量验收](skills/science-video-production/references/quality-acceptance.md) |
| 3D资产复用 | [Blender与素材库](skills/science-video-production/references/engineering-blender.md) |

脚本从全局安装调用。`render_gate.py lock/run` 拒绝非全局生产入口；`roughcut`用于G2，`sample`生成待审代表段，`full`才要求G3通过。新回执不用旧文件名，不刷新旧哈希冒充新版通过。私有媒体、账号和审查记录不提交本仓。

## 维护检查

从维护仓库根目录运行，Python3.11+；涉及媒体的测试需要ffmpeg/ffprobe。按改动范围选择回归。

```bash
python -X utf8 skills/science-video-production/scripts/rebuild_standard_index.py
python -X utf8 skills/science-video-production/scripts/check_reference_system.py skills/science-video-production
python -X utf8 -m unittest discover -s tests -t .
python -X utf8 -m unittest discover -s skills/science-video-production/scripts/tests
```

章节索引只维护正文链接、摘要和锚点。`scripts/bounded_blender`、`scripts/bounded_i2v`的README维护各自有限执行范围和恢复方法；`third-party`保留原许可和固定版本来源。历史纸面例子与`references/learning-candidates`是待核研究记录，不作为当前制作许可或通过证据；历次变更见Git历史。
