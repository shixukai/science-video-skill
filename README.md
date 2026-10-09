# science-video-skill

面向普通大众自然现象与生活科学的引用式制作Skill。真实锚点是合法连续实拍/观测视频，原理为纯2D；规范采用不代表任何成片已通过或可发布。

- [入口与阶段路由](skills/science-video-production/SKILL.md)
- [视觉设计系统](skills/science-video-production/references/visual-system.md)
- [美术与画质记录模板](skills/science-video-production/assets/art-direction-template.md)
- [当前系列配置](skills/science-video-production/config/series-profile.json)
- [外部视频Skill选型与许可证](skills/science-video-production/references/video-skills-curation.md)
- [中文语音调用与听验](skills/science-video-production/references/voice-reference.md)
- [规则唯一归属](skills/science-video-production/indexes/rule-owners.json)
- [待拍纸上示例](examples/blue-sky/brief.md)，不是已完成视频

本版在七份责任参考中落实完整制作规范，以G1–G7记录、H/D策略、实际视听与内部解释审查区分阶段放行。项目数值与通用原则分开。私有设计板、媒体、账户和反馈不入公仓；公仓提供解释配方和可编辑技术示例；完整成品美术资产与设计板仍由项目按实际版本提供，不自动安装至全局。

验证：`python -m unittest discover -s tests`（Python3.11+、ffmpeg/ffprobe），包括既有包、引用结构及阶段证据回归。检查器拒绝缺失/冲突/过期记录，不会自动判断艺术、科学、听感或授权真实性；仍须实际媒体审查。旧计划可用于草排，旧交付须补齐当前要求。

从仓库根目录检查并保存本地回执：

```bash
python3 skills/science-video-production/scripts/check_episode.py /path/to/episode.json --stage plan --report /path/to/plan-check-001.json
```

回执记录输入与检查资源摘要、错误和未验提示；目标必须是新文件，父目录须存在。它不改QA或签成片通过。G2/G3回执绑定实际草排/代表段媒体；使用旧版上下文的记录须按当前媒体重新核对，不能仅刷新哈希沿用旧结论。

视觉制作包含风险代表样与同镜L2/L3校准、明度/边缘/细节主次、目的性留白、整片色彩与构图编排、主体分步精修、科学色义与光影分开控制、母版及最终编码细节对照。方法进入现有G2/G3/G5/G6记录，不新增审批或通用审美数值。

当前默认画风已固定为 [精细2D绘画式自然插画](skills/science-video-production/references/visual-system.md#已确认画风的视觉锚点)，随Skill携带仅作外观比较的参考图和 [三类美术任务规格](skills/science-video-production/assets/style/bright-nature.art-direction.json)。正式风格候选在交付前实际看图、并排对照和美术回查；配色参数与未批准标签都不代替主体、光影和材质完成度。G3还实际核对本地设计板文件及哈希，拒绝只填写两个一致的声明值。

已有真实秒数分镜与媒体时，可生成静态审片页：

```bash
python3 skills/science-video-production/scripts/build_visual_review.py /path/to/episode.json --media renders/candidate.mp4 --output reviews/visual-v1
```

媒体及相对输出路径均以单集目录为根，输出必须是新目录。生成完整画幅抽帧、HTML、带版本摘要的manifest与逐文件证据列表；详见 [工具用法与限制](skills/science-video-production/references/shotbook.md#整片视觉抽帧工具)。生成材料不代表实际审看，也不替代连续声画或平台检查。
