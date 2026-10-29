# 3D动画制作：Blender 与 3D 素材复用

3D动画风格视频必须使用Blender，覆盖自然、生活、工程、工业与制造题材；主体资产、动画、材质灯光、相机与实际渲染在Blender完成。复用已有工程与3D素材，登记`controlled_3d`，不必先试视频模型。拟真3D也属于本路线，不能由AI生成的3D外观或MoneyPrinterTurbo混剪替代；写实风格则按[风格分流](tool-routing.md#按成片风格锁定主制作工具)使用MoneyPrinterTurbo，工程题材不自动触发Blender。

工程示例仅检查本题适用部件；配音、字幕、混音和编码复用辅助工具，不改变Blender主制作路线。

工程视频先按[全链路与片长](topic-contract.md#工程与制造题材的全链路和片长)组织完整解释，再安排3D整体、局部与工序镜头；局部建模精细度不能代替上下游、制造过程或系统结果的交代。

## 仅做资产时的任务范围

仅委托模型、静态预览、检索或入库时，交对应可编辑资产和检查/归档结果：核源模型、科学结构、连接方位、所需视图及依赖，仅在涉及运动时查动作。无音轨用途不造旁白、整期分镜或G3。完整视频中的建模仍是中间步骤，后续声画制作与验收继续执行。

## 先认得出真实对象，再解释内部

- 研究公开实物照片、剖视图和可信技术资料，先核轮廓、关键部件、相对尺度与空间关系。现代客机发动机的识别不能只靠一个圆筒和重复叶片；按本题需要保留风扇、短舱、旁通与核心流道等关系，再做局部精细化。不为所有题材强制同一机型、级数或部件清单。
- 公开产品资料可指导外形，不能由此声称自建模型是厂商官方 CAD、精确维修图或已验证的流场。外观接近、教学几何和工程仿真分别说明，来源、权利与适用限制留在 [科学与素材记录](science-and-rights.md)。
- Check necessary structures in whole-object, medium and mechanism close-ups before surface polish. Give pipes, cables and passages real endpoints and interfaces. Distinguish materials through appropriate roughness and reflection response. For metallic mechanisms, controlled broad reflections can reveal curvature, edges and separations; adjust light size and direction so glare does not erase the interfaces being explained. Check these relationships at the target viewing size. Surface detail cannot conceal missing structural connections.

## Blender 场景背景与空间完成度

背景是本镜的空间、用途和观察条件的一部分，按与主体一致的成品标准设计。完整视频不能默认让所有对象悬浮在同一纯色/渐变底、无边地台或通用暗棚里，再只换相机、底色和字幕。先在既有场景设计卡中选定本段所需环境、参考依据、可复用资产和由整体进入局部的方式，不以“高级感”代替可制作的场景方案。

- **建立具体情境**：应用、整体或工序镜头呈现与本题相符的空间、承载/支承、配套对象与尺度参照，使观众看得出东西在哪里、怎样使用。工程场景可按事实采用工位、厂房、试验台或安装环境，自然/生活场景选择其实际载体与观察条件；不能把通用厂房或任意管道当成所有设备的工作环境。没有依据的设备连接、人员操作、洁净条件和工艺状态不为装饰添加。
- **组织可读的空间层次**：按取景安排主体、邻近参照与远处环境的距离、遮挡、透视和明暗层次，必要时加入有用途的前景。镜头移动时核真实视差与空间连续性；不强制每帧凑满前中后三层，也不靠一张背景图冒充需绕行或交互的3D空间。接触、支承、阴影和反射随对象与环境成立，避免漂浮、无限重复地砖和空旷舞台感。
- **环境本身有完成度**：按实际可见尺度补必要的建筑/设施结构、接缝、边缘、材质差异与适当使用痕迹；复用模块时调整布置、比例和用途。主光、环境光与反射共同说明空间，保持主体清楚、背景层级安静；HDRI、雾、景深、噪声或彩色灯不能替代场景内容，也不能遮掩主体和背景的粗糙。
- **简化有明确范围**：机制近景、剖切、微观示意和必要对照可使用克制背景，保留其解释需要的材料边界、载体或位置线索；进入与离开时能认回所属整体。单独资产检视、隔离展示和用户明确要求的极简片段按其用途处理。局部允许简洁不等于整片可省略环境设计，丰富也不等于堆满物件或添加无关运动。
- **变化服从内容**：按应用→装配/工位→局部机制→结果的实际叙事需要设计背景与景别变化；同一场景可复用，不设固定场景数量。换工序/尺度时改变真正相关的空间或观察关系，保持同一环境的方向、光照与设备身份；不能用随意换背景掩盖空间断裂。
- **沿现有关卡实审**：代表段在目标画幅看完整合成、必要局部和正常速连续画面；整片缩略带检查是否长期同底同构图、场景重复而无叙事用途，再回到实际镜头核细节、遮挡、流畅度和字幕/标注。G3正式样段缺乏必要情境、背景明显占位或已知粗糙时先修复，不扩制；G5复核当前最终编码。纯色面积、物件数量或环境资产已入库不能自动签通过，背景完成也不抵扣主体或科学问题。

示例：讲设备整体用途，可先在有依据的安装/试验环境建立尺度，再进入仍有定位线索的结构近景；讲制造过程，可用适配的工位及真实输入/输出衔接工序，再在局部剖切中减弱外围；讲微观材料，可先交代宏观应用与载体，再用有边界的材料空间解释。示例是选择方法，不是固定片头或必须添加的设施清单。

## 人物绑定、动捕与口型

Enable this branch when a character's performance helps demonstrate an operation, interaction or explanation. Reuse a suitable local character, rig, actions and facial controls before building new ones. Choose the required output first: editable 3D performance belongs in Blender; generated face-video postprocessing produces a video layer. Follow the selected [production route](tool-routing.md#按成片风格锁定主制作工具) and the actual [source/usage requirements](science-and-rights.md); an available tool or animation library does not expand the allowed asset origins or external uploads.

1. **Define the performance.** In the existing action card, name the character, target, gaze, action, contact/release events and resulting object response. Plan only the body, hands and facial detail visible at the closest shot. Reuse the same character identity and performance across camera cuts; a presenter need not speak or gesture continuously.
2. **Rig and skin separately.** Check mesh topology, scale, axes, transforms and rest pose. Fit joint positions, create or correct the skeleton, bind deformation weights, and test the actual bending/turning/grasping poses. Skeleton generation alone is not skinning. Correct collapsing shoulders/hips, elbow/knee twisting, disconnected clothing and hand/object penetration before rendering; preserve the editable source rig and mesh.
3. **Retarget and clean motion.** Map source/target bones, rest poses, units and root movement. Preserve the source fps, time origin and resampling map rather than silently treating every capture as 30 fps. Keep source motion separate from cleaned actions; correct foot sliding, ground contact, balance and held-object constraints. Body-motion recovery does not automatically supply reliable fingers, face or device operation. Bake the required actions/constraints for the actual batch-render path and test a different frame order when random-access evaluation is used.
4. **Animate speech from the approved audio.** Reuse the current [voice track](voice-reference.md), then map audio-relative mouth cues to facial bones/visemes or relative shape keys at the project fps and offset. Use a language-compatible aligner or manually corrected cues; Chinese characters/subtitle timings are not one-to-one mouth shapes. Keep curves editable, blend neighboring mouth shapes, preserve pauses/closed lips, and combine jaw, lips, expression and gaze without double deformation. Audio or edit changes invalidate the affected alignment, not automatically the entire rig.
5. **Test the real difficulty.** Use the existing G2/G3 sample to cover the planned close-up and difficult turn, occlusion, grasp/release or speech transition. Check deformation/contact in motion, watch normal-speed with the actual audio for synchronization, and inspect mouth/teeth/tongue clipping, identity, edge stability and silent sections. An idle pose, a walk cycle or one frontal talking still cannot validate these harder uses. Record actual observations and unreviewed ranges in the existing QA; tool completion is not performance approval.

### 按需选择人物工具

These are capability candidates, not preinstalled or production-validated claims. Select only what the shot needs, verify the current release and loaded dependencies, and run its representative use before expansion.

| Need | Candidate and handoff | Selection detail |
| --- | --- | --- |
| Editable local rig | Blender [Rigify](https://docs.blender.org/manual/en/4.0/addons/rigging/rigify/basics.html), or [UniRig](https://github.com/VAST-AI-Research/UniRig#usage) for suitable meshes | Fit/generate the rig and bind/test skinning. UniRig separates skeleton and skin-weight prediction; check the actual release/checkpoint supports the required stages. |
| Recover body motion from video | [GVHMR](https://github.com/zju3dv/GVHMR) → body parameters → conversion/retargeting to the character | Not a ready target-character FBX, finger or lip-sync service. Its [repository license](https://github.com/zju3dv/GVHMR/blob/main/LICENSE) limits use to educational/research/nonprofit purposes; required SMPL/SMPL-X and other models have their own terms. Choose a use-compatible alternative when these do not fit. |
| External humanoid auto-rig/actions | [Mixamo](https://helpx.adobe.com/creative-cloud/faq/mixamo-faq.html) → rigged character/action → Blender | External upload service, restricted to supported humanoids; confirm account availability, current usage/source rules and upload scope. It is not a local default. |
| Rough audio-driven mouth cues | [Rhubarb](https://github.com/DanielSWolf/rhubarb-lip-sync#recognizers) → timestamped cues → character-specific mouth shapes | Default recognizer is English; language-independent `phonetic` can be tried for Chinese but has lower accuracy. Validate and correct it instead of claiming Chinese-specific alignment. |
| Face-video animation or lip redraw | [LivePortrait](https://github.com/KlingAIResearch/LivePortrait#3-inference-) for image/video + driving performance; [LatentSync](https://github.com/bytedance/LatentSync) for video + audio | Outputs generated video, not an editable Blender facial rig or viseme curves. Record the generated layer and inspect identity, mouth, occlusions and temporal continuity. Check the exact weights/detector terms, not only the code license: bundled InsightFace model restrictions and version-specific capacity can affect use. |


## 同一几何与方位基准

- 为需跨镜复用的实件保留一份几何来源，装配镜、抽离镜、剖切镜和结尾镜引用同一资产或同一组构建函数；不要分别重建“看起来差不多”的替身。
- 在建模与动作前说明本对象适用的局部轴、接口、运动轴和观察视点。叶片等气动部件另核上下游、前缘/后缘、叶根/叶尖与凹凸面，需要时用剖面和弦线检查弯度、安装姿态及气流关系，再从最终相机复核；不向其他机构强加叶片术语。
- **安装转角不能修复叶型弯度的镜像。** 收到“反了”反馈时，区分几何手性、迎流关系、装配姿态、旋向和相机视角；先定位是哪一项，再改共同几何与受影响镜头，不能仅旋转特写或反向箭头。
- 同级同类重复件可共享几何；邻近的转子、导向叶片和不同级应按各自作用、旋向与速度关系检查，不能把一片叶型或一个倾角复制到全机。凹面朝向、转向和弯度参数都不是跨机型通则。
- 同轴旋转叶排可沿实际旋转轴投影已求值网格，利用保守轴向包络检查相邻排在整个旋转相位的分离；要包含叶根锁件、盘缘、端壁和倒角等真实最外沿，不只看名义弦长或某一角度。正间隙仅支持该教学模型的几何关系，不能换算为厂商运行、热膨胀或制造公差。
- 橙/蓝等示意色只表示本片已说明的变量；流线朝向仍须由实际坐标关系支持。区分静止坐标系的绝对流与叶片坐标系的相对流，不能把二者无变换地连成一条“已验证”路径。示意曲线、粒子和颜色不是 CFD 或实测证据。

## 从整体连续进入局部

- Locate the target within the whole before moving closer. When exposing internals, choose a local cutaway, shell removal or selective transparency that reveals the needed region while retaining enough silhouette, adjacent structure and interfaces to recognize its original position. Keep relevant wall thickness and cut edges readable. Preserve recognizable features across shots; a matching name, hard cut or dissolve alone does not establish component identity.
- 过桥动作从装配场景在实际起始帧求得的世界变换出发，并对齐目标近景的结束姿态、相机与光照。注意父级变换、动画求值、单位及缩放，避免抽离时对象突然翻面、跳位或替换。
- 按实际场景先解除遮挡、让对象离开相邻几何，再旋转至便于观察的姿态；检查起点、障碍最近处、旋转极值和跨镜边界，也实看中间运动。教学性的分离、剖开或抽出不冒称真实维护拆装流程。
- 局部检视先核遮挡件的角色；随移去外壳才成立的支撑、紧固件应在适用的检查显示组中一起处理，避免留下遮住主体、无接合关系的粗杆。用命名视图或显示层保存检视状态，同时保留默认完整资产；不为画面清爽一概删除仍需解释的支承。
- 壳体、内部结构和孔口共用同一形状定义。移开壳体后，原壳上的孔列、后缘出口及主体轮廓应仍能对应；不能用薄片遮住错误连接，或以镜头切换隐藏几何不连续。

### 爆炸图与剖切的选择

Use an exploded view to explain component order, interfaces and assembly relationships; use a cutaway to reveal a path or mechanism that must remain connected. Select the view for the observation task, rather than cutting and rejoining an object repeatedly to create motion.

For a moving cutaway, design the complete opening/hold/closing cycle with the final camera path. A finite Boolean box is not an infinite plane: verify its intended cutting face and all other faces across the entire swept volume, including thin end plates, rollers and caps. Derive camera clearance and visibility from the final evaluated scene state, not a cached base camera or an isolated endpoint. Keep the physical liquid/material state separate from the observation cut so the reveal does not imply draining or removal. If one patch creates another cut-face/occlusion defect, validate the shared geometry/state representation through the [complete repair cycle](blender-execution.md#complete-a-repair-cycle-before-expanding) before adding more local offsets or wrapper overrides.

- Start from the recognizable assembled object and keep a fixed reference part. In the existing action card, name the component groups, assembly axis/axes, separation vectors, reveal order and interfaces the viewer must see. A layered stack usually reads clearly along one principal axis; choose other paths when its actual topology requires them.
- Separate each group once along an intentional path, preserving orientation during that move. A translation-only plan is `M_i(t) = T(e(t) * d_i) * M_i(0)`, with initial evaluated world transform `M_i(0)`, planned world-space offset `d_i` and smooth non-overshooting progress `e(t)`. Convert to the actual parent space; avoid applying the offset to both a parent and its children. Rotation, when needed for inspection, is a separate readable phase.
- Stage **assembled recognition → separation → interface observation → reassembly or matched handoff**. Reassembly is useful only when the next explanation needs it. Space parts enough to expose their connections at phone size; preserve necessary fasteners, supports and connector identity. Keep camera movement quiet while the layers become distinguishable.
- Check start, intermediate, fully separated and handoff states, then normal-speed playback: the same parts remain recognizable, paths do not intersect accidentally, and the exposed interfaces answer the question. Explain the transition from a structural tour to a manufacturing sequence through the narration/edit; display order does not establish real production or servicing order.

## 冷却与管道机制的可见连接

- 流道、分隔壁、进出口、孔道与表面气膜应从共同几何/表面函数取位置和方向，修改叶型后联动更新；不能只搬外壳而把内部通路或风线留在旧坐标。
- 分别核入口是否真正连入空腔、转弯处是否通、隔壁是否意外贯穿、出口是否实际开孔。贴在金属上的线、相碰的圆柱或发光点不能代替流体通路。
- 气膜从已存在的孔口出发，贴着相应叶面向该坐标系下的下游展开；不要因画面漂亮让冷却流穿过实体或迎着解释方向倒流。网格与可见帧检查各有范围，不能用无明显穿模替代隐藏拓扑或流场验证。

## 有界试制与可靠复用

Use the existing G2/G3 workflow in three production passes; these are work products, not extra approvals:

| Pass | Produce and check | Keep costly work out until |
| --- | --- | --- |
| Continuous motion preview | Use existing assets or adequate placeholders at normal playback fps. Include the opening context, transition and first topic observation; check camera path, object identity, occlusion, attention and timing with the available narration. Lower spatial/shading cost, not temporal sampling. | The route and adjacent-shot handoff work in continuous playback. Do not wait for polished geometry to discover a weak transition. |
| Final-engine look development | Check representative final-resolution frames and a short continuous risk segment for structure, reflections, transparency, cut edges, fibers and temporal noise. Use the approved final engine and closest planned viewing scale. | The actual material/geometry risks are covered. Preview-engine success alone does not establish final appearance. |
| Shot render and edit | Render only affected shots/ranges to original image sequences, then assemble with separate text/caption layers and the accepted voice track. Check the resulting joints and complete applicable audiovisual scope. | Existing G3 conditions are met before expansion; final quality still requires actual viewing/listening. |

Keep one reusable asset source and a stable shot driver; store shot-specific camera, animation and frame parameters in the project. Build/import scenes once per process and update their states per frame. Repeated parts can share meshes/instances; retain required structure at the actual closest shot. Do not recreate whole assets or launch scripts for every label, camera or duration revision.

Use the [global sequence executor](blender-execution.md) for suitable local intermediate frames: immutable input jobs, native frame ranges, exact-device selection, per-frame hashes, resumable output and separate build/render timing. Reuse an existing compatible executor where it already implements these behaviors. Existing task-specific safeguards remain applicable. A saved procedural scene must be baked or supplied with its actual state driver before background/farm rendering.

Determine rerender scope from changed dependencies: common geometry/material changes affect referencing shots; camera changes affect the shot and its junctions; screen-text or audio changes normally require recomposition, not 3D rendering. Validate reused raw frames against their original scene/input/settings and frame hashes. Keep captions/titles/screen labels editable outside the raw 3D sequence; export actual object-anchor projections and visibility for [dynamic annotations](annotation-style.md#动态与对象绑定). Physical lettering or labels that must participate in scene lighting/occlusion can remain in 3D.

Freeze code, assets, engine/settings and frame mapping before a batch. A changed source creates a new version; a retry with identical inputs verifies and resumes the original job. Keep historical outputs and failed attempts. Review unchanged evidence within its original scope instead of redoing it for bookkeeping; use the [context comparison](production-checkpoints.md#记录整理与增量复查) for triage. Newly exposed geometry, changed meaning, known failures and changed audiovisual joins still need the affected checks.

Reuse the accepted continuous narration; place necessary observation pauses at semantic breaks and update picture, captions and annotations together. Measure preparation, scene build, render/write, edit and review separately. Technical frame/geometry checks do not certify actual appearance, science or hearing, and an optimization is not a measured speedup until comparable work has been timed.

## 3D 正片与系列封面分别设计

3D正片的封面仍按[系列封面标准](visual-system.md#封面成品标准与工程制造题材)独立设计。可用本题模型作造型/光影依据，不直接交工程预览或带字幕截图；多个比例分别构图，实际看原图与手机缩略。

## 使用过的 3D 素材统一归档

共享库根目录读取[系列配置](../config/series-profile.json)的 `shared_3d_library`，按下节检索并核新用途。

### 素材库归档的持续授权

读取本地 `shared_3d_library.standing_authorization`。已有授权且 `target_root` 与实际库根一致时，直接执行授权内的复制、版本目录、索引和回读校验，不因换集、跨会话或重试重复询问。同步维护代码须保留本机有效授权；公共默认配置不代表其他用户授权。

保留源文件和已有版本，新增版本归档；清单核对后复制并从目标读回摘要。目标暂不可达时记待同步及原因，在原授权内恢复。改目标、删源、覆盖旧版或外传按实际新授权处理；授权撤销或范围变化以最新要求为准。

### 查找与选择已有素材

开工先查共享总目录，按题材、对象、用途、场景及同义词检索模型和素材，分别查看 `reusable`、`pending` 和适用的历史条目。有适配且可用于本次目的的对象或场景时，优先链接、附加或修改已有资产，不重新建同一个模型；确实找不到、依赖缺失或新用途不适配时，在既有记录写明具体缺口后再补建。普通搜索未命中时继续按别名及 `--include-supporting` 查看历史候选；待审候选先核范围、依赖及本片画面，不因未完成旧审查就默认重新建模。失败/诊断反例只作修复或取证参考，不当作默认可用版本。

总目录按SHA-256合并相同文件，保留所有来源、原版本和审查范围；`reusable` 仅表示目录所列范围可作为复用起点，不是对新片整体声画、科学或发布的批准。`pending` 是缺少足够审查或依赖证据；`failed` 是有记录的失败版本/诊断反例，具体原因与范围随条目保存。若同一文件在不同上下文有冲突结果，保留各项记录并列为待审。目标库真实文件及依赖仍须在采用前核查，不以索引存在代替可用性。


用只读 [find_3d_assets.py](../scripts/find_3d_assets.py) 查询结构化 `asset-index.json`，而不是从 `INDEX.md` 第一条或文件名挑模型：

    python -X utf8 scripts/find_3d_assets.py --kind engine
    python -X utf8 scripts/find_3d_assets.py --kind cooled-blade
    python -X utf8 scripts/find_3d_assets.py --root /absolute/authorized/library --kind bridge

支持旧整机/叶片/桥接角色，以及通用 `current_asset`、`assets` 列表；用 `--kind environment`、`--kind material`、`--kind lighting` 或实际类别检索，也可用 `--query` 检索名称与关键词。先记录本片所需资产、实际查询、选用/改造/不采用原因及缺口，再补建；不因检索只覆盖旧类别就认定没有素材。明确非默认的历史、失败资产及重建中间件、基础源、封面机位仅在显式 `--include-supporting` 时列出；普通待审候选可检索但不能当作已通过。按 `--status reusable`、`--status pending`、`--status failed` 筛选，后两者会显示非默认历史项；均保留各自角色和限制。`current_engine` 仅表示所在版本索引的当前入口；有多个版本时返回候选，不按修改时间或版本名自动宣称全库最新/通过。旧桥接与新整机分别核身份、变换及依赖，不能由同库归档推断已适配。

脚本只检索小型元数据，不打开、执行或哈希模型；返回的预期摘要、审查引用与文件存在状态不是当前完整性或质量通过。选中少量候选后，再核实际文件摘要、预览、单位/轴、所用相机、权利与新用途。源索引坏损、未知格式和不安全路径需显式报出；NAS不可达或当前不可见与“已读取且零匹配”分开，前者在既有授权内核路径和访问权限，不误判为空库或另造一套素材。

- 归档范围含主体/部件、可复用场景与环境模块、程序材质/贴图、灯光/相机方案、动画/节点及实际构建依赖。用通用索引登记类别、名字、关键词、预览、来源版本、依赖与状态；历史保存、目标完整性已核和可用于新片是三个不同结论。核“是否全部收齐”要给出已扫描项目、实际文件清单、去重方法、缺失/待同步/依赖未核项及时间，不能只看NAS目录存在或某一包成功。
- 按类别、资产名与版本建立可查目录，例如 `<类别>/<资产名>/<版本>/`，保留可编辑 `.blend` 与实际使用的构建脚本、贴图、链接库等必要依赖。归档用复制，保留单集源文件；已有版本不静默覆盖，修订另存版本并标清替代关系。
- 说明用途、单位/尺度、局部轴和原点、关键对象/集合名、装配接口、支持的剖切或动作、Blender/渲染器版本及外部依赖。给出能辨认实件的缩略预览；视频抽帧只能标为预览，不能冒充独立资产源。
- 随素材保留来源/作者、原创或第三方事实、许可证及必要署名、使用限制、实际修改和科学示意边界。公开参考图、厂商 CAD 与自建教学模型分开；不因可下载就认为可再分发，也不替原创资产擅自指定开放许可。
- 以文件清单与 SHA-256 绑定实际归档内容，标明正式采用、失败、未审及已知限制；失败旧版本不要混成默认可用项。系统字体、权重、凭据、缓存帧及与复用无关的发布/配音文件不混入3D素材库；单独 ZIP 可辅助携带，不能替代可编辑源与依赖说明。
- 复制后从目标目录回读文件、核数量/摘要和必要依赖，再记已归档。目标暂不可达时，先完成可迁移的本地暂存与清单，记录待同步目标和失败原因；不能把“本地已准备”写成“NAS 已保存”。复用时仍按新片实际用途核科学关系、权利与输出，不把存档状态当作质量或发布批准。
