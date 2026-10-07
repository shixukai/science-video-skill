# science-video-skill

面向普通大众自然现象与生活科学的引用式制作Skill。真实锚点是合法连续实拍/观测视频，原理为纯2D；规范采用不代表任何成片已通过或可发布。

- [入口与阶段路由](skills/science-video-production/SKILL.md)
- [视觉设计系统](skills/science-video-production/references/visual-system.md)
- [当前系列配置](skills/science-video-production/config/series-profile.json)
- [规则唯一归属](skills/science-video-production/indexes/rule-owners.json)
- [待拍纸上示例](examples/blue-sky/brief.md)，不是已完成视频

本版采用引用式第一版：保留七份责任参考和三个项目模板，项目数值与通用原则分开。私有设计板、媒体、账户和反馈不入公仓；公仓不包含完整艺术素材库，也不自动安装至全局。

验证：`python tests/test_check_episode.py`（Python3.11+、ffmpeg/ffprobe）；`python tests/test_reference_system.py`。前者145项既有包回归，后者验证引用/配置/索引；均不能代替美术、听觉、理解、权利或平台实测。
