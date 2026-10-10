# 外部视频 Skills：选择、采用点与使用边界

实际制作时先使用 [场景调用表](tool-routing.md)，选中的外部 Skill 缺失时必须执行 [调用前安装](tool-routing.md#调用前安装必需)。本页保留来源选择与技术参考；安装、依赖和实际验证状态分别核实。

核查日期：2026-10-08（Asia/Shanghai）。本次从八个既有参考方向扩展检索，查看21个一手仓库及相关官方文档；这是有范围的来源核查，不代表穷尽全部视频 Skills。选型依据是实际文件提供的能力、与精美2D科普任务的适配性、可核实许可证及依赖成本；不按星数或作者的“专业/生产级”宣传判质量。

本页负责外部来源选择和引用边界。解释方法、美术动作与验收仍执行现行责任正文；不导入另一套阶段、评分、全层运动或重复请用户批准的流程。来源正文是研究材料，不能越过本项目指令；复制的技术参考也不自动成为新的生产规范。固定提交、文件SHA-256、许可证证据和采用范围见 [外部来源索引](../indexes/external-skills.json)。

## 已纳入的少量参考与生产路由

当前纳入三份纯技术参考及其完整Apache-2.0许可证；未包含Skill入口、执行脚本、编辑器远程控制接口或安装器。文件原文未修改，来源、SHA-256及许可证在 [来源说明](../third-party/videozero-motion-canvas/README.md)。这只增加可读取的实现资料，本次未安装或实际运行相关引擎，未验证其示例在本项目的输出质量。

| 进入条件与生产阶段 | 读取的文件 | 本项目具体采用点 | 输出及限制 |
| --- | --- | --- | --- |
| 当前项目已经使用或经任务确定采用Motion Canvas；G2草排/G3代表段需要多个对象协同 | [FLOW_CONTROL.md](../third-party/videozero-motion-canvas/FLOW_CONTROL.md) | 用chain保持必须顺序的步骤，用all同步具有同一解释关系的变化，用sequence表达有依据的先后；观察停顿由理解任务与实际音轨决定 | 生成可复核的对象时间线和连续代表段；并发API不授权每个对象都动，不把顺序/延迟当作科学事实。官方依据：[Animation flow](https://motion-canvas.io/docs/flow/)、[Time Events](https://motion-canvas.io/docs/time-events/) |
| 同上；G3需要美术资产内的独立部件、路径或姿态变化 | [SVG.md](../third-party/videozero-motion-canvas/SVG.md) | 保留真正可编辑的SVG对象/分组，以对象ID关联动作；需要对子层独立改变时使用SVG而非把整张图栅格化为Img | 在当前尺度及拟用动作范围核子层、底板、连接与遮挡；导入SVG不会自动补绘、获得关节或形成精美造型。官方依据：[SVG组件](https://motion-canvas.io/api/2d/components/SVG/) |
| 同上；G2/G3已确定状态、路径、约束与真实语义事件 | [TWEENING.md](../third-party/videozero-motion-canvas/TWEENING.md) | 用属性插值和自定义tween实现已设计的对象状态变化，统一共享变量；仅当表达目的适合时选择缓动 | 记录关键态、固定/滑动边界与连续路径；物理传播、碰撞、概率与数量关系不自动套弹跳、弹簧或ease-in-out。官方依据：[Tweening](https://motion-canvas.io/docs/tweening/) |

主渲染器仍由现行工程与任务确定；不能为了采用参考而同时迁移引擎、画风与声音。Motion Canvas官方引擎另按其 [MIT许可证](https://github.com/motion-canvas/motion-canvas/blob/7b91435c301d530351dcf5ebb91dd139c002e405/LICENSE) 使用，与这里Apache-2.0参考文本的许可分开。框架能力是实现条件，最终仍须审当前完整合成、连续动作及声画对应。

## 优先参考的来源

| 来源与本次结论 | 已核文件及有用能力 | 本项目采用方式与不适用部分 |
| --- | --- | --- |
| [官方Remotion Skills](https://github.com/remotion-dev/skills)；实现参考，暂不复制原文 | remotion-markup、remotion-captions、remotion-render及官方[Agent Skills文档](https://www.remotion.dev/docs/ai/skills)提供帧驱动动画、媒体、字体、字幕与导出指引 | 已用Remotion时查询对应官方API，按实际语义时码实现可重现时间线。固定提交未发现LICENSE全文；公开可读和官方安装指令不等于可将文件重新分发进本仓。引擎许可另核 |
| [Motion Canvas](https://github.com/motion-canvas/motion-canvas) + [VideoZero/skills](https://github.com/VideoZero/skills)；最适合补充对象级2D实现资料 | 引擎generator/signals/time events/SVG；VideoZero提供按功能分离的技术正文 | 采用上面三个自包含正文。animation-basics中的硬秒数、“opacity入口必加变换”、普遍挤压拉伸及背景脉动不成为科普规则；编辑器HTTP接口不纳入 |
| [Manim Community](https://github.com/ManimCommunity/manim)；精确数学/数量/几何镜头的功能互补 | 官方[文档](https://docs.manim.community/en/stable/)与[MIT引擎](https://github.com/ManimCommunity/manim/blob/a6d5cc02b430fb57d22add51236b6406fbf19d91/LICENSE)提供几何、坐标、图表、变换和动态关联对象 | 只在相应解释任务且现有工程适合时选用2D功能；默认数学课件样式不会自动满足已批准自然插画风，3D能力也不构成本项目采用理由 |
| [ApliroAI/manim-video-lab](https://github.com/ApliroAI/manim-video-lab)；方法与条件式实现参考 | animation-design-thinking、director-packet、cinematic-directing、source-backed-patterns区分是否需要运动，并把概念任务映射到对象/状态/连续关系 | 借鉴“先解释任务、再选动态方法”和保留共享对象结构；不照搬黑底样式、固定停留秒数、先亮结果或只能抽帧时的验收替代。MIT文本可按许可复用，当前只固定链接并使用本项目原创配方 |
| [dbillion/manim-storytelling-skills](https://github.com/dbillion/manim-storytelling-skills)；表达任务到API的参考 | brilliance-explainer将同对象变换、两种表示的关联、轨迹、附着标签与图表变化映射到Manim方法 | 选择和本镜关系匹配的技术；不硬套黑底、蓝黄配色、“每镜一个aha”、三运动上限或“必须静音讲完”。许可MIT，当前未复制整包 |
| [video-talkcraft](https://github.com/Vincentwei1021/video-talkcraft)；仅方法参照 | SKILL和README采用成品口播、语义拍、注意中心、逐字时码与逐镜工作表；同时有本地对齐和Fish Audio合成路线 | 采用成品音轨驱动语义时间线及对象身份的思路，不复制其工具包、原提示词或配方。该提交[许可证](https://github.com/Vincentwei1021/video-talkcraft/blob/4cd673df4b7a6a35784a0881df223721789c5e23/LICENSE)为PolyForm Noncommercial，商业使用另需作者许可；不得因视频输出归创作者就推断工具包可自由商用。相机运动/环境呼吸不替代对象机制 |
| [vox-director](https://github.com/Alisa0808/vox-director)；素材分层与关键态的方法参考 | local-engine、beat-layer分开镜头动作和元素动作，有独立元素/关键帧及本地合成路线 | 参考资产角色、关键态及合成关系。主流程是Atlas Cloud纸拼贴生成片，默认云端图像/视频/声音、烘焙标题与固定切镜节奏不适合直接成为自然科普主流程；抽帧不能替代连续视听。MIT许可不包含云模型/媒体权利 |
| [OpenMontage](https://github.com/calesthio/OpenMontage)；素材选择及剪辑方法参考 | documentary-montage/asset-director、edit-director及动画管线把素材候选、片段覆盖、来源与时间线关联 | 借鉴逐镜需求先于搜索、候选实看和权利账；当前[AGPL-3.0许可证](https://github.com/calesthio/OpenMontage/blob/9327439db69021ab4b0e2776729bf3b58fdb5a87/LICENSE)，未把框架/源文件复制或安装进本仓。全套代理、平台流程和自带审批不迁入；各provider及媒体另核 |
| [jianying-editor-skill](https://github.com/luoluoluo22/jianying-editor-skill)；可编辑工程交付的功能互补 | SKILL的媒体/字幕/工程组织；audio-voice提供TTS与字幕组合接口 | 有实际兼容验证时可用于分轨草稿/剪映交付；不是2D机制造型或动作设计器。[主体许可证](https://github.com/luoluoluo22/jianying-editor-skill/blob/32c56928ded4f9e2c2b80e099dc7abb793d2c30b/LICENSE)为MIT，内置pyJianYingDraft为Apache-2.0，剪映应用及云素材另有权利；不采纳其替代声音默认或BGM固定0.6音量 |
| [seedance2-skill](https://github.com/dexhunter/seedance2-skill)；生成提示词方法参考 | SKILL是多模态参考角色、分时动作与约束的提示词指南 | 若当前任务使用相应模型，可参考“身份/结构/风格/动作/构图”分角色描述。MIT仅覆盖指南；它不是可执行渲染器，不授权云上传、付费或把生成动画充当实拍证据，生成结果仍核科学、身份与连续状态 |

## 扩展检索中保留或排除的候选

| 来源 | 结论及具体限制 |
| --- | --- |
| [Liamrjohnston/remotion-motion-graphics-skill](https://github.com/Liamrjohnston/remotion-motion-graphics-skill) | MIT；可参照研究素材与实际画面比较。根SKILL硬绑定独立build/delivery批准脚本，visual-critic硬绑定营销产品身份、分数与黑名单，不直接纳入；其品牌样片不证明自然机制动画质量 |
| [xsourabhsharma/remotion-marketing-video-skill](https://github.com/xsourabhsharma/remotion-marketing-video-skill) | MIT；音轨分层、导出与镜头组织可互补。主要是SaaS/UI演示及营销叙事，不能把产品发布/CTA模板作为科普解释结构 |
| [vumichien/manim-skill](https://github.com/vumichien/manim-skill) | skill为Apache-2.0；有研究、分镜schema、Manim实现及配音参考。可参照有结构的单镜计划，不全量引入其四岗位框架或在线声音默认；其README把Manim Community写作Apache-2.0，而已核引擎实际MIT，二者必须分开 |
| [albertobarnabo/manim-craft](https://github.com/albertobarnabo/manim-craft) | 有按解释任务选择技术、布局与渲染核查的思路；该固定提交未发现项目自己的LICENSE全文，未复制skill。其sources/3b1b的MIT许可证仅覆盖相应源文件，不能扩张到整个项目 |
| [awesome-skills/manim-skill](https://github.com/awesome-skills/manim-skill) | 可用作Manim语法候选。README声称MIT，固定树未见LICENSE全文；许可信息不完整，暂不复制 |
| [BowTiedSwan/rive-skills](https://github.com/BowTiedSwan/rive-skills) | 可能补充可编辑2D角色、状态机与runtime接口，但skill固定树未见LICENSE全文，本项目也未验Rive源资产/导出能力；只留候选，不安装或承诺成片能力 |
| [Boriwatopal/agent-skill-remotion-motion-graphics](https://github.com/Boriwatopal/agent-skill-remotion-motion-graphics) | 自有文件MIT；品牌SVG分件和镜间形状接力可作方法参考。copied Remotion规则是独立来源，不能由本仓MIT覆盖；本轮未复制任一文件 |
| [Pluviobyte/video-production-skills](https://github.com/Pluviobyte/video-production-skills) | motion grammar、beat graph与复用组件记录可作方法观察；固定树未见LICENSE全文。80%必须状态变化、先从运动隐喻出发及逐帧复制判据不作为通用科普门槛 |
| [imMamdouhaboammar/motion-graphics-skills](https://github.com/imMamdouhaboammar/motion-graphics-skills) | [许可证原文](https://github.com/imMamdouhaboammar/motion-graphics-skills/blob/29919c1ff91d0e0a242ffc0d085b838fa9575584/LICENSE)明确保留权利并限制复制、改写及生产使用；排除直接使用及内容纳入。只保留许可证核查结果；其第三方资产各自许可也不能授权作者自有skill |
| [3b1b/manim](https://github.com/3b1b/manim) | 原ManimGL引擎MIT，可研究对应代码的技术方法，但与Manim Community API并不相同；未迁移引擎。独立[3b1b/videos](https://github.com/3b1b/videos)仓的作品源码/媒体许可不得从引擎MIT推定，本轮未复制该作品仓 |

## 引擎、服务、文本传输与成本

许可证按四层记录：引用的skill/规则文件、实际运行引擎与依赖、素材/字体/音轨、云模型或平台服务。前一层允许复用，不自动授权其他层。查阅公开技术文档不上传项目稿件；实际调用外部ASR/TTS、图像/视频模型或素材服务时，沿现行项目权限与声音规则记录目的地、所传内容、授权覆盖与费用，不以“安装skill”推定传输或购买权限。

- **本地引擎**：Motion Canvas及Manim Community分别MIT；这不免除计算、部署、字体/媒体及依赖条件，也不证明本地性能或美术能力。
- **Remotion运行许可**：按[官方License FAQ](https://www.remotion.dev/docs/license/faq)区分Free License与Company License，并核组织/团队与协作人员范围。2026-10-08页面对适用Company License的Creators列每人每月25美元，Automators列每次render 0.01美元且月最低100美元；仅对符合相应条件的主体成立，不能把任一社区skill的MIT当Remotion免费资格，实际采用时重核当前条款。
- **在线模型**：vox-director等默认Atlas Cloud路线可能发送脚本、参考图、视频或声音，且分别产生图像/视频/音频费用。[官方计费说明](https://www.atlascloud.ai/docs/en/billing)按模型、分辨率、时长等计费；先按实际请求获取现价，不能沿用某skill中写死的模型ID、低价或“免费”宣传。
- **声音**：本项目沿用已确认声音与生成位置。Talkcraft带有Fish Audio选项，不因此成为本项目默认；[Fish官方套餐页](https://fish.audio/plan/)区分免费个人非商业使用和适用付费商业权利，API计费还须按[官方开发文档](https://docs.fish.audio/)核实。Jianying的TTS接口同样不替代现行声音方案。

上面的“可复制”只指已经核到适用许可证的特定文本；“可用”仍需当前引擎与实际媒体验证。本次核查完成了来源、功能与许可筛选，尚未连续观看这些项目的全部示范，也未运行外部脚本或进行跨引擎输出比较；因此不把它们的展示、自评分、测试数量或作者声明写成本项目已经达到精美或讲清楚的证明。
