# 外部视频 Skills：采用点与许可

按[工具路由](tool-routing.md)选本次所需能力，按[准备与安装](tool-routing.md#调用前准备与安装)运行。固定提交、阅读文件、许可证据和候选状态保存在[外部来源索引](../indexes/external-skills.json)；本页只列可直接采用的方法及限制。

## 已纳入的少量参考与生产路由

包内保留三份Apache-2.0技术参考，原文、SHA-256与完整许可证见[来源说明](../third-party/videozero-motion-canvas/README.md)。仅在已有Motion Canvas工程或获准2D范围需要相应能力时读取；不因引用迁移主工具。

| 进入条件与生产阶段 | 读取的文件 | 本项目具体采用点 | 输出及限制 |
| --- | --- | --- | --- |
| 当前项目已经使用或经任务确定采用Motion Canvas；G2草排/G3代表段需要多个对象协同 | [FLOW_CONTROL.md](../third-party/videozero-motion-canvas/FLOW_CONTROL.md) | 用chain保持必须顺序的步骤，用all同步具有同一解释关系的变化，用sequence表达有依据的先后；观察停顿由理解任务与实际音轨决定 | 生成可复核的对象时间线和连续代表段；并发API不授权每个对象都动，不把顺序/延迟当作科学事实。官方依据：[Animation flow](https://motion-canvas.io/docs/flow/)、[Time Events](https://motion-canvas.io/docs/time-events/) |
| 同上；G3需要美术资产内的独立部件、路径或姿态变化 | [SVG.md](../third-party/videozero-motion-canvas/SVG.md) | 保留真正可编辑的SVG对象/分组，以对象ID关联动作；需要对子层独立改变时使用SVG而非把整张图栅格化为Img | 在当前尺度及拟用动作范围核子层、底板、连接与遮挡；导入SVG不会自动补绘、获得关节或形成精美造型。官方依据：[SVG组件](https://motion-canvas.io/api/2d/components/SVG/) |
| 同上；G2/G3已确定状态、路径、约束与真实语义事件 | [TWEENING.md](../third-party/videozero-motion-canvas/TWEENING.md) | 用属性插值和自定义tween实现已设计的对象状态变化，统一共享变量；仅当表达目的适合时选择缓动 | 记录关键态、固定/滑动边界与连续路径；物理传播、碰撞、概率与数量关系不自动套弹跳、弹簧或ease-in-out。官方依据：[Tweening](https://motion-canvas.io/docs/tweening/) |

Motion Canvas引擎另按[MIT许可证](https://github.com/motion-canvas/motion-canvas/blob/7b91435c301d530351dcf5ebb91dd139c002e405/LICENSE)核验；参考文本的Apache-2.0不覆盖引擎、素材或服务。

## 优先参考的来源

仅为本镜缺少的具体方法读取下表；固定文件与许可证据查来源索引。

| 来源 | 实际采用点与许可限制 |
| --- | --- |
| [Remotion官方Skills](https://github.com/remotion-dev/skills) | 已有React工程的帧驱动动画、字幕与导出。所核提交未见独立LICENSE，不复制原文；引擎运行许可另核。 |
| [Motion Canvas](https://github.com/motion-canvas/motion-canvas) / [VideoZero](https://github.com/VideoZero/skills) | 采用上表三份对象时间线、SVG子层与插值参考；不引入固定秒数、背景脉动或编辑器远程接口。 |
| [Manim Community](https://github.com/ManimCommunity/manim) | 已有或获准2D工程需要几何、数量与动态图表时查官方API；引擎MIT，默认样式按本期美术重做。 |
| [manim-video-lab](https://github.com/ApliroAI/manim-video-lab) / [manim-storytelling-skills](https://github.com/dbillion/manim-storytelling-skills) | 参考解释任务到对象/状态/共享关系的映射；所核文本MIT，不采用固定停留秒数、黑底色板或替代实际审看的方法。 |
| [video-talkcraft](https://github.com/Vincentwei1021/video-talkcraft) | 参考成品音轨驱动语义时间线；所核文本PolyForm Noncommercial，商业使用另需许可，不复制工具包或切换为其Fish Audio默认声音。 |
| [vox-director](https://github.com/Alisa0808/vox-director) | 参考素材分层、独立元素与关键态；文本MIT不覆盖其默认云模型和媒体权利，不迁入Atlas Cloud全流程。 |
| [OpenMontage](https://github.com/calesthio/OpenMontage) | 参考逐镜需求、素材覆盖、来源与剪辑时间线的关联；所核框架AGPL-3.0，本包未复制/安装。 |
| [jianying-editor-skill](https://github.com/luoluoluo22/jianying-editor-skill) | 仅需剪映分轨工程交付时核实际兼容性；主体MIT、内置pyJianYingDraft Apache-2.0，应用/云素材另核。不替换本期声音。 |
| [seedance2-skill](https://github.com/dexhunter/seedance2-skill) | 参考身份/结构/风格/动作/构图分角色提示；MIT指南不是可执行模型或渲染器。 |

## 扩展检索中保留或排除的候选

完整候选及排除理由查[来源索引](../indexes/external-skills.json)的 `classification`、`limitations` 和 `license`。许可缺失/不完整不复制；明确禁止生产使用的来源不采用。需要新能力时再核当前版本与适用文件，不把检索目录当安装清单。

## 引擎、服务、文本传输与成本

分开核所引用文本、实际引擎/依赖、素材/字体/音轨和云服务条款。现有声音及本期主工具不因参考指南的默认项而改变。

- Remotion采用前核[当前运行许可](https://www.remotion.dev/docs/license/faq)，按组织及实际用途判断，不沿用旧价格或社区Skill许可。
- 在线ASR/TTS、图像/视频及素材服务先核目的地、实际上传内容、已有授权和当前计费；只读文档不上传项目稿件，安装Skill不自动授权传输或购买。
- 复制可分发文件时保留其许可；来源核验不代替本期运行及实际声画审查。
