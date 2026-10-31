# 动画场景设计：从实体状态到完整镜头

主要动画及静态资产转动画时，先设计主体、情境、可见变化与镜头接续，再精制资产。结果写入现有动作卡及[美术记录](../assets/art-direction-template.md#动画场景设计卡)；写实主画面执行[写实制作契约](realistic-production.md)，2D实现仅用于已确定范围及辅助层。

## 先诊断空在哪里

| 实际症状 | 优先判断 | 优先改法 | 不能据此直接下结论 |
| --- | --- | --- | --- |
| 物体精细，但像一张标本贴在底色上 | 缺观察情境或必要参照 | 确定观察尺度、环境/载体及关系；纯标本展示有明确用途时可以保留 | 不因背景简洁就判失败，也不强加地面、植物或人 |
| 主体只旋转、推近，讲解已进入生长/变化 | 对象没有发生所讲的状态变化 | 设计连续中间态、变化区域和累积结果 | 相机运动、材质闪动不是生长证据 |
| 东西很多，却不知道看哪里 | 关系层级混乱 | 让当前关系取得明度、边缘与动作优先级；删除竞争事件 | 图层数、运动量、满屏率不证明丰富 |
| 特写比全景更大，却没有新信息 | 景别没有发现任务 | 增加真实需要的结构/状态，或取消这次特写 | 增添无依据微结构不算精细 |
| 每镜都漂亮，接起来仍单薄 | 没有信息递进与状态记忆 | 保留前镜已建立的状态，用新视角/对照推进原问题 | 切得更多、更快不自动改善 |
| 只有放大截图才看得出改动 | 关键差异低于实际观看可辨程度 | 改取景、形状差异、局部明度或观察时机 | 代码数值变化、像素帧差不能代替正常观看 |

区分必要留白与缺失内容：先说出空白区域承担的观察、运动、对照或文字空间，再检查它是否真的有用。可以有安静的大背景；只要主体、当前关系和观察回报已经成立，不必填满。Blender完整视频同时执行[场景背景与空间完成度](engineering-blender.md#blender-场景背景与空间完成度)：局部留白与极简检视不授权整片省略环境、使用相同底色或地台。

### 先区分缺失与不显著

检查现有作品时，先逐项标为“已有且清楚 / 已有但不显著 / 缺失 / 未验”，再选修复方法。主体已经生长、已有近景、已有双对象差异时，不能继续开出“增加生长、特写、对照”的泛泛任务。记录准确时点、保留的结构、实际变化和所用观察方式；稀疏抽帧看不出变化时，先补关键态或连续观察，不把“未看清”写成“没有”。

材质和透明边缘已成立而关键新增区域太小时，保留有效资产，优先修取景、参照与状态表达。

## 开工顺序：动作意图先于精绘

先写本镜的可见关系和状态序列，再决定需要精绘哪些关键态、遮挡面及独立部件。成品级静帧是外观检查，不是“先生成一张漂亮整图，再设法让它漂动”的生产顺序。

1. 从当前解释分镜摘出本镜观察任务、必要条件、主对象及与前后镜的联系。先用名词和具体变化写成一句可执行指令。
2. 画低成本状态草图：变化前、关系最关键的中间态、结果；比较/结构类选择能呈现差异的状态，不硬造过程。标出保留、新生、消失、变形与遮挡的部分。
3. 同时设计构图、状态变化和资产拆分。先判断关键关系在目标播放尺寸能否看清，再精绘轮廓、结构、受光与材质。
4. 在原时间线制作连续代表段。用实际语义和音轨确定事件、观察停顿和切镜；纸面示例里的秒数不能当同步证据。
5. 先看当前完整合成，再用局部/去叠图诊断问题，修复后回到原构图连续复查。G2/G3/G5的原证据要求继续适用。

### 手调曲线先分清停驻与持续接触

需要保持姿态/位置的停驻，明确保留起止状态，检查插值是否在停驻期间偷偷漂移；正在持续运动的接触，则让约束、接触点与对象响应沿所需轨迹连续，不能在每个接触键附近自动缓入缓出造成脚滑、脱离或无依据减速。仅对受影响的控制器和区间调整插值、切线或分段，不对整条动画一键平滑/简化；已有求解、缓存或实测速率依其真实条件处理，不统一改成线性或Bezier。复查实际完整动作和接缝，曲线好看本身不证明接触或因果正确。

## 镜头内容的四种职责

这四项是设计问题，不是强制四个图层，也不要求四种内容每帧同屏。

| 职责 | 设计时要写清的内容 | 对画面产生的作用 |
| --- | --- | --- |
| 主体 | 具体对象、可识别结构、当前状态、这次真正改变的部位 | 让观众认得出并持续追踪同一对象 |
| 情境 | 在哪里、什么尺度、必要环境/载体/观察条件；哪些可以留在画外 | 让对象有处境，建立相对大小、空间或条件 |
| 关系 | 接触、生长、传递、比较、约束或结构怎样从画面中成立 | 让细节支持解释，不只展示相关物体 |
| 发现 | 本镜增加了什么观察信息，结果怎样留下，下一镜为何需要它 | 使时间和镜头推进带来实际收获 |

环境必须承担具体职责，例如界定尺度、提供光色与遮挡、表示经过核实的条件或承接动作。无依据的风、雾、碰撞、融化不能为画面热闹而添加。科学机制不需要外部环境时，允许做干净的局部场；其构图、材质和关系仍要完成。

## 场景设计检查

在[视觉系统A/D/I标准](visual-system.md#静态画面-a01a10)内检查下列项目；本页补充状态与动作的制作方法，不重复维护美术等级表。

| 制作对象 | 先做什么 | 正常速检查什么 | 对应项目 |
| --- | --- | --- | --- |
| 主体、场景与细节 | 按识别结构、实际尺度、支承/遮挡建立构图；先主形，再接触与材质 | 目标尺寸能认出对象和关键特征，近景提供新信息 | A01–A09 |
| 主动作与状态记忆 | 写初态→中间态→结果及保留/新增/移除部分，参数控制真实对象变化 | 旧结构稳定、变化有因、结果留下；无整图缩放或字幕更新冒充过程 | D01/D04/D05 |
| 时间与辅助运动 | 依机制分配认识、变化、比较和观察停顿；难点时降低次级运动 | 不乱加弹性、回弹或漂移，所讲变化能在本镜看完 | D02/D03/D06 |
| 镜头、接续与声音 | 每次换景说明新观察任务，用对象特征/方向/状态衔接，事件对齐语义 | 不丢对象身份；主要动作、必要标签和字幕不争抢 | D07/D08/I01–I03 |
| 合成与输出 | 共用几何/锚点，补隐藏面和底板，材质贴附对象 | 无滑皮、鬼影、抖动、穿插，最终编码保住关键间隙和边缘 | A06/A07/D05/I04/I05 |

## 把已有变化变成可读的证据

以下方法用于“做了，但看不清”的镜头，沿用上表的构图、主动作、状态记忆、镜头与叙事标准，不另设质量等级。

| 问题 | 制作动作 | 验收观察 |
| --- | --- | --- |
| 主体很大，实际变化只在细小末端 | 先圈出支持本镜结论的最小特征，如一个新分叉、边界位移或接触点；按此特征决定景别，同时保留必要旧结构。降低无关纹理与背景边缘的竞争 | 在目标播放尺寸的完整画面里能定位该特征；不能只报主体占屏比例，或靠审片时临时裁大才看见 |
| 生长与镜头移动混在一起 | 让关键关系出现时有稳定观察窗口；保留旧分叉、接触面等参照。需要运镜时共同变换对象与参照，离开近景前交代结果 | 能区分对象实际改变与相机缩放/平移；固定相机只作诊断，正式镜头仍需正常速复查 |
| 对照已有差别，但第一眼读不出 | 写出具体判别特征，例如侧枝形成位置、宽窄或疏密；固定与结论无关的初态、尺度、视角、光照和观察时点。必要时让两边同类局部对齐 | 看见的是所选条件造成的目标差异，而非随机纹理、亮暗或比例差；形态不能为增强对比而超出科学依据 |
| 已承诺的条件变化只由一句话宣布 | 为确需解释的条件变化设置可读节点，并将该节点与对象后续变化对应。不可见条件可用必要标签或明确示意；结果落到主体结构上 | 能追踪“条件改变 → 哪些部位响应 → 留下什么结果”；装饰性变色、雾量或粒子流不冒充测量与机制 |
| 多次返回相近全景，没有新的观察收获 | 在分镜上注明本次返回要认回的局部、同时比较的区域或累积结果；用前镜身份与状态接回全景。没有新增证据则合并或缩短 | 每次回全景都能指出新结论对应的位置；不只换标题，不凭材质闪动宣布共同生长 |

比较“何时开始变化”时，应统一观察时刻、显示各自变化节点，不能又强行统一变化后的持续时间。比较“同样持续时间后的结果”时则相反。先声明比较什么，再选择要固定的时间参照；不能把所有变量不同的两个自然个体当作受控实验。

若解释的是持续共享的条件，展示同一情境、对应区域与相似结果即可，不强制新增条件变化节点。

定位标记可以短暂出现并退去，帮助找到对象结果；不能让高亮本身充当新增物质。相同阶段的多个区域需要对应时，标记的顺序仅表示讲解顺序，不暗示它们依次发生。标签仍可承担必要身份、条件与数值；检验目标是文字与可见证据相互对应，不是强求无字也能理解所有机制。

### 工艺动作要留下可观察的结果

For a process explanation, show the workpiece before the operation, the interaction at the active region, and the resulting changed material/structure. Equipment travel alone does not demonstrate what happened to the workpiece.

Drive interacting objects from one process state or event timeline. Specify the driver/trigger, when contact or a constraint becomes valid, which objects respond, and what result accumulates or remains. Derive tool travel, workpiece deformation/removal, carried material, instrument feedback and necessary effects from those relationships, rather than unrelated keyframe tracks. A practical implementation is a shared `process_state(t)` consumed by geometry, rigs, overlays and sound-event markers; use explicit event dependencies when continuous functions are unsuitable. Select the actual scientific model first. Controlled geometry is sufficient when it preserves the required relationship; use simulation where its dynamics are necessary, with applicable assumptions and validation.

Give the important explanation a consequential event to follow: establish a goal or constraint, show an action taking effect, expose the developing change, then let the viewer inspect the result. Choose whole/close-up/section/result views for those discoveries, retaining the same object and state at handoffs. Keep the camera quiet when the critical interaction needs attention; vary pacing around anticipation, action and observation using the real narration. Sound cues follow actual depicted events, not every pan or cut. Structure inspection can remain calm; no fixed action count, camera-move quota or simulation requirement applies to every shot.

| Example | Shared state and visible sequence | Production result to check |
| --- | --- | --- |
| Probe test | `probe_z/contact/test_state/result`: align → make contact → acquire/classify → add the result to the map → lift and move | Each displayed result follows its test and remains in the accumulated map; data is measured, simulated or clearly illustrative as appropriate. A lowered probe followed by a long unchanged image is insufficient. |
| Material removal | Tool/exposed interface, protected region and removed volume share the chosen process state; removal progresses at the active interface while unaffected material stays | The changed boundary and intermediate structure are visible. Do not shrink the entire workpiece or reveal an already completed cavity; select the actual etching/machining mechanism. |
| Character operating a fixture | Gaze/reach → valid grasp → workpiece follows hand → seating contact → release/clamp in the order required by the actual support → inspection feedback | Hand, workpiece and fixture share contact/release events; held objects do not drift, jump parents or move before grasping. Body mocap alone does not establish fingers, grip or correct operation. |

Choose the actual mechanism before adding effects. ALD, for example, uses sequential surface reactions and can coat complex topography; generic downward particle rain can misrepresent it. [Lam Research's ALD explanation](https://newsroom.lamresearch.com/Tech-Brief-A-Look-at-Atomic-Layer-Deposition-ALD) is an example of a process-specific visual basis. Likewise, an optical-path graphic must follow the selected system: [ASML's EUV description](https://www.asml.com/en/products/euv-lithography-systems) uses reflective reticles and mirrors. An illustrative ray path must not imply that invisible radiation is an ordinary visible beam. These examples guide verification, not a particle/beam preset for every manufacturing video.

## 把动作写到可以制作

“雪花慢慢形成”“水流自然”“镜头有电影感”都不足以执行。动作指令至少要能回答：

> 在哪个可见区域，哪个对象从什么状态变为什么状态；哪些结构或参照保持不变；中间怎样连接；结果在哪里看见；镜头和辅助运动如何让人看清。

按题材选择状态模型：

| 关系 | 主要可控状态 | 有意义的视觉变化 | 典型错误 |
| --- | --- | --- | --- |
| 边界沉积型生长（如雪晶；其他生长另选相应模型） | 生长边界、分支连接、新增区域、随时间保留的形态 | 已有结构延续，边界附近新增实体 | 从中心揭开最终图；整图放大；分支整齐逐根点亮冒充同时生长 |
| Material processing | Active surface/boundary, supplied or removed material, protected region and endpoint | Show deposition, reaction, removal or filling progressing at the correct interface; retain the workpiece reference and resulting structure | Reveal an already finished layer; shrink a whole solid to fake etching; use decorative particles with no corresponding material change |
| Test and classification | Test location, stimulus/contact, acquisition, decision and accumulated result | Distinguish untested, testing and classified states; update a map/table from actual measurements, the chosen simulation or clearly illustrative data, with symbols/text as well as color | Hold a probe still while narration alone describes results; random red/green flashing presented as real yield |
| Multiple transfer paths | Each carrier/quantity, source, interfaces, destination and any relevant return path | Establish each route in one coherent section/view, then compare them with stable color/line meaning | Repeatedly jump between shell and section; assume different carriers must travel in opposite directions |
| 形变/受力 | 支点、接触、约束与局部形状 | 约束不变处保持，受影响区域发生相应变化 | 全层摇摆；硬物强加果冻回弹 |
| 传递/传播 | 载体局部状态、传播位置、前后响应 | 区分局部对象运动与传播范围 | 所有物体同向平移；波纹循环却没有响应 |
| 条件比较 | 共同初态/尺度/参照、改变条件、结果差异 | 区分被比较的状态，差异落在主体上 | 两幅图各自好看却尺度、光照和条件全变 |
| 结构/空间/证据 | 组成、位置/约束、显示顺序、推论边界 | 用揭示、定位或并列让关系可检查 | 为满足“动态”硬造物理过程 |

遮罩、显隐和draw-on可以揭示真实状态模型，也可以用于明确的教学定位；单纯按时间擦出一张最终成图，不证明对象经历了生长。优先审状态序列和可见结果，再审实现手法。可用静止观察完整形态，但它不能替代当前所承诺的变化过程。

## 可交给制作 Agent 的任务写法

直接填写[动画场景设计卡](../assets/art-direction-template.md#动画场景设计卡)，引用当前分镜、科学依据和该阶段实际音轨/时间线，不再复制一份表。

委托须给可访问的适用参考图和本镜初态、关键中间态、结果、稳定参照、可辨特征及接续对象。执行者先确定状态与构图，再精制资产。所选工具做不出变化时，在已锁定媒介内修输入或改实现；能力仍缺则记录具体缺口，继续独立工作，不能退成符号后靠背景装饰补救。

## 制作端如何检查

沿现有G2/G3/G5检查，而非要求外部观众反馈：

- **设计时**：对照原题和科学依据，核本镜有没有观察任务、状态联系、情境用途和下一镜回报。删掉一个元素若不损失识别、解释、构图或必要观察条件，可考虑删掉。
- **静态时**：看关键态完整合成及当前批准参照。先看主形、关系和焦点，再看材质。纯技术占位与正式风格候选分开。
- **连续时**：正常速看实际导出，记录主动作发生位置、能否察觉、结果是否留下、相邻镜是否连得上；再带声核语义。不能只挑最清楚一帧证明整段成立。
- **有疑点时**：临时固定相机、隐藏装饰/辅助叠图，或比较同条件前后状态，定位问题来源；这些诊断不替代恢复正式层后的完整审查。
- **记录时**：写具体时点、所见差异、对应A/D/I、修复与未验范围；区分已有且清楚、已有但不显著、缺失、未验。静帧证据只支持该状态的观察；没有连续观看能力时保留动作、节奏及声画待验，不宣称连续效果已改善或L3通过。

如果只在调色、纹理或背景上更精致，而主体结果、观察情境和信息递进仍缺失，返回状态与分镜设计。不要开始批量制作同类镜头。

## 雪花案例的使用方式

见[雪花生长设计示例](snow-crystal-scene-example.md)：在已获准的2D范围内，将状态、情境、近景和资产职责写成制作任务；其他题材按自己的科学关系改写。
