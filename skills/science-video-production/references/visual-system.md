# 视觉设计系统

本页负责美术制作与实现；实际验收见[质量验收](quality-acceptance.md)，开场与原题见[主题契约](topic-contract.md)，事实与权利见[素材规则](science-and-rights.md)。

按当前任务读取：[设计基准](#当前基准与引用)、[实际资产落地](#已批准设计的实际落地)、[文字与布局](#文字居中与运动)、[可动画资产](#三尺度造型与制作细节)、[精美定义](#2d精美的正向完成标准)、[静态完成度](#静态画面-a01a10)、[连续动作](#连续动作-d01d08)、[整片整合](#整片整合-i01i05)。

## 明亮风格与高级材质

写实与Blender默认以有效布光形成明亮、清晰、精细的主体，保留真实本色、必要阴影、暗部结构与高光层次；背景明度独立选择，深色/黑色背景也可成立，不以浅底或整帧均值判断明亮。按[专业美术编排](art-direction.md)确定颜色角色、明暗主次、前后景、材质反射与跨镜光色，并逐类处理雪花感。历史参考按原适用范围复用，背景深色本身不构成风格不合格；参数或色板不等于实际样段认可。G3/G5沿现有美术失败记录核当前实际媒体，用户审片只给本地路径。

## 当前基准与引用

按[成片风格](tool-routing.md#按成片风格锁定主制作工具)选路线：写实使用MoneyPrinterTurbo，3D动画使用Blender。下文2D绘画、卡通亲和化及纯2D条款仅用于已明确获准的2D范围或独立封面；写实/3D主镜采用本期对象和场景的适用参考。

采用[系列配置](../config/series-profile.json)的适用默认值；[明亮自然参数](../assets/style/bright-nature.tokens.json)仅为历史2D/封面的起点。实际打开参考，在本片需要的整景、对象中景和机制近景中对照轮廓、光色、材质、字图及空间。参数与目标外观不符时修实际画面。

项目设计板记录版本、哈希和认可范围，私有原图及反馈留在项目。复用已有适用的风格认可，新结构、动作和合成按本期实际输出检查。

### 已确认画风的视觉锚点

历史2D参考采用**结构可信、光影细腻、材质通透的精细2D绘画式自然插画**。查看[已确认外观参考](../assets/style/accepted-style-reference.png)，按[美术规格](../assets/style/bright-nature.art-direction.json)安排对象、整景与机制任务。沿用已认可的外观方向；参考不作为入片素材。忽略查看器背景、侧栏、选框和截图裁切，科学内部结构另查可靠资料。

| 固定的风格关系 | 在新题材上的实现 | 明确偏离 |
| --- | --- | --- |
| 具象造型与结构 | 人物有可信比例、姿态和手足；动物、植物、器物按实际身份建立轮廓与结构。曲面、转折和受力形态有区分 | 将自然主体退成默认图标、圆团、折线或几何占位，仅靠标签说明身份 |
| 有组织的体积明暗 | 用2D色面、笔触和渐变沿形体转折组织受光、半影、暗面；局部遮挡/接触增强结构可信度 | 全物体同一平涂、随意贴亮边或统一渐变；靠辉光/全局锐化弥补弱造型 |
| 材质彼此不同 | 布料褶皱沿关节与受力方向，装备有部件和厚薄；透明、金属、岩土或生物表面按本题需要表现对应特征 | 把同样高光、纸纹或圆角套给所有物体；不区分柔软、坚硬、透明与不透明 |
| 边缘与笔触有主次 | 焦点结构较清楚，次要边缘和远景适度收敛；色块与绘画边缘共同定义形体 | 全轮廓同样粗硬，所有区域同样清晰或同样堆细节；粗主体嵌在精背景中 |
| 自然光色与空气层次 | 按场景建立明确光向、环境映色和远近关系；可用暖光与冷空气形成层次，科学本色优先 | 仅复制蓝绿黄色号而没有明暗/空间关系；无依据把夜景、海洋或机制一律染成同一日照场景 |
| 整景、主体与机制同一完成度 | 整景有空间组织，主体细看有结构，机制近景保留对象身份、材质和形体完成度；示意线与对象分开 | 外景精细、内部原理突然切换成粗圆细线课件；用装饰替代关键结构 |

这些关系适用于各题材，固定的是制作完成度与绘画语言，不是黄色衣服、登山者、山谷、树叶或水滴。科学图形、坐标和路径可按功能简化；主体有必要时可透明、剖切或抽象表示，须保留准确对应和相同美术完成度，不为了写实感编造结构。纯2D允许绘画体积及反光，不引入3D模型或伪3D渲染。

### 从视觉锚点到实际资产

1. 打开适用参考和美术规格，给执行者可访问的图像、认可范围和本镜职责。先写对象结构依据、构图焦点、光向材质、禁画关系、动作所需独立层与文字区。
2. 在已锁定媒介中生成、绘制或复用有权资产。支持参考图的工具传入实际图像和本镜要求；科学路径、箭头、数值及正式文字保留为可控制的独立层。
3. 将当前完整合成与参考并排看，按下文A01–A10找出最大的造型、光影、材质或构图差距。先修该差距，再重看受影响画面。仅验证布局的占位稿留在技术草排；正式外观候选须呈现目标完成度。
4. 制作端修好明显偏离后，再交独立美术审查。真正需要选择画风时提供完成度相当的候选；工具达不到要求时，在当前路线内调整资产方法并记录仍缺的具体能力。

观察记录沿用[美术记录](../assets/art-direction-template.md)及现有QA，资产绑定见[逐镜记录](shotbook.md#设计和资产引用绑定)。

### 从封面完成度到可控动态场景

将封面的主体、材质、光色和场景完成度延续到正片，构图随解释任务重新设计。先选本片最容易从具象对象退成图解的代表段，在现有G2/G3与动作卡内完成：

1. **确定闭合范围**：包含整体定位、关键关系及可见结果；因果题可用“现象→局部→机制→结果”，比较或结构题按自身关系组织。只做孤立膜片、箭头或漂亮外景不能覆盖这项风险。
2. **先让关系可辨**：每镜写主体、固定/改变/比较项、结果及整体回接。在目标手机尺寸确定景别与注意中心；必要接触、差异和结构清楚后再安排背景及文字。
3. **按动作准备资产**：制作所需关键态，补齐运动后露出的隐藏面，按独立运动/遮挡拆主体、底板与材质层，固定坐标根、锚点和mask。无需运动的背景可不拆；跨态保持身份、光向、材质及alpha。
4. **让对象兑现讲解**：按已锁定媒介制作连续状态。可控实现共用相关几何与状态参数；AI输出逐项实看。数量、强弱或重复性主张须有对应对象结果与共同尺度/条件，示意不冒充实测。整图推拉、标签更新、背景粒子不能替代主体变化。
5. **接入已有旁白试放**：按真实语义安排动作、桥接和观察停顿。看完整合成、关键态/运动极值及正常速度有声段，在手机尺寸核结果可辨，再按[阶段证据](quality-acceptance.md#美术方法的阶段证据)记录问题与修复。
6. **按覆盖范围扩制**：新对象、新尺度或不同关系补相应样段；全片检查抽象段能否认回现象，以及光色、材质、声音和动作接缝。最终完整看听当前编码。

跨尺度保留同一对象的轮廓、位置、朝向或局部特征。关键机制至少让人完整观察一次必要条件、对象变化与结果；按实际先后/并行关系表达，不制造时延。输入输出需比较时可同场并置，必要文字说明条件和单位。

在已获准的huashu工程中保留原引擎与时间线，精绘素材置于单集目录，用对象局部变换/mask合成，科学几何与事件表保持可审查。沿用资产ID、动作卡与 `qa.visual_frames`，依赖见[工具路由](tool-routing.md#huashu-art-motion-执行)。观察停顿及简化背景按解释需要安排。

若主体在手机上小到无法辨认接触/选侧，或长段只剩膜片、波形与标签，先重做景别和整体—局部联系，再精修纹理。

### 已批准设计的实际落地

把当前资产渲染出的完整合成帧与批准设计板并排看：核轮廓比例、空间、光向明暗、材质边缘、色彩及文字。按[引用绑定](shotbook.md#设计和资产引用绑定)固定资产与设计板版本，在 `qa.visual_frames.note` 记录具体差距和对照图。

造型语言已偏离时退回资产制作；不要只调色、叠纹理或加光效。可见资产/合成改变后重看受影响范围，连续动作另按[动作验收](quality-acceptance.md#可检查项目)检查。

## 保持识别，允许题材呼吸

易引发不适的对象可用克制构图、光线和细节呈现，保留科学身份及必要风险；写实主镜不自动改成卡通。温和、可爱的精细2D风格只在本期已获准2D范围或独立封面使用，不能删除机制所需结构或把有害对象暗示为无害。

适用的2D/封面方向是清新明亮、通透、色彩鲜明的自然整景：清澈蓝天、暖光、鲜活植物色、自然物体本色与前中后景。人物、环境、机制和文字如同一作者完成；近景可简化，不退回另一套黑底细线课件。不把深色旧组件简单换浅色，不以荧光、全局光晕、粗糙几何或满屏纹理冒充明亮。

颜色按角色使用：环境/空气、主体、结构/阴影、焦点与文字。具体hex/字阶/线宽在参数文件，不在正文维护第二套数值。白昼45/35/15/5只是可调视觉面积起点，不是原图像素统计，也不强套夜景、海洋或不同题材。科学本色、物种特征、光谱顺序、变量色义优先；必要时用形状、线型/文字辅助，不能只靠颜色区分。

按[三尺度精修](#三尺度造型与制作细节)处理实际资产，用[同镜对照](#代表样与-l2l3-校准)检查差距；动作关系与节拍见[制作检查点](production-checkpoints.md#2-把解释关系变成可见表达)。

## 纯2D解释与真实素材

在 `pure_2d` 模态下，原理用纯2D插画/动画，不用3D模型或伪3D渲染替代。纯2D约束制作方式，不要求对象平涂；可用二维绘画、矢量明暗、边缘与材质表现体积、透明、反光及环境映色，效果服从科学条件和当前已确认画风。用户已锁 `ai_generated` 时，原理/现象连续画面按 [AI生成视频](ai-generated-video.md) 推进，仍须可核对的科学简化与披露，且不得冒充实拍。实拍连续视频仅作 `real_footage` 观察锚点；2D可承担标注、放大、剖面或不可见机制；只有用户具体批准相应范围时才可做完整2D解释；不得据本段替代写实主画面。真实视频的获取、默认开场与处理边界由 [素材规则](science-and-rights.md#制作声明的最小内容) 负责。示意不能伪装科学证据，参考图/封面用途不抵实拍缺口。

全景、中景、机制近景分别设计，身份和科学关系连续，不是同一图反复放大。轻纹理/渐变/阴影仅服务空间与识别，不以无依据体积光效掩盖造型。科学色、比例、时间或路径被简化/处理时按素材规则明确边界。

解释镜头先按 [空间关系与声画对应](production-checkpoints.md#逐段声画与图内文字对应) 确定必要对象、参照与注意中心，再选景别、视角和背景。已批准画风约束造型与表现体系，不要求保留同一张整景的构图；必要时重构侧视、局部或简化环境，让背景细节与对比服从关系识别，同时保持对象身份和科学对应。简化可减少本镜不需要的信息；按重构后的景别与对象职责维持当前已确认画风的完成度，不能以简化为由把主体退为粗糙占位图形。不能为保留漂亮风景，把解释对象缩成难认的点线后叠标签，也不能靠整体缩小、堆字或无关系的装饰补救。

## 竖屏画幅与构图

本节标题及9:16示例保留供既有竖版恢复；通用构图原则同样用于当前16:9横版，后续默认与独立布局见下文“后续横版与适度亲和化”。

9:16以完整画幅组织场景，画面边缘纳入构图；天空、水面、纯色环境和其他有目的的低细节区域均可成为场景的一部分。负空间用于隔开对象、容纳视线或动作、突出机制、安排必要文字，不因空白而补装饰。须能说明它与主体及解释任务的关系；缺失场景、无依据边框和闲置的大标题板不能冒充留白。真实宇宙/阴影暗区与人为黑边区分。

居中、偏置、对角、上下分区或对照构图按本镜对象关系选择，不把几何中线当质量标准，也不为变化而强套构图法则。结合主体轮廓与光学重心，安排视线、运动方向、接触位置及相邻镜头的注意中心；只在选择不明时用粗缩略图比较。主图、图内标签、字幕与平台覆盖分别布局，不能为躲UI把整幅缩小/左上移；审片辅助线不入成片。

不为铺满画幅拉伸、裁掉科学主体/脚点/接触或补造影像。素材无法安全重构就换符合 [原创视觉来源契约](science-and-rights.md#原创视觉来源契约) 的自产片段或在获准范围做自设计示意，仍不假称实拍已满足。标题、字幕与必要局部背板随场景组织；背景细节服从主体，不用粒子、纹理或扩大底板填满每块空白。

### 整片色彩与构图缩略带

将分镜的必要关键态按顺序排成缩略带，标出每段职责、主体尺度、注意中心、背景明度、强调色和细节密度，包含实际使用的各模态与接缝。删掉没有新增观察的重复镜头；景别和密度变化服务定位、解释、比较或回归，不套固定远—中—近循环。

科学对象、变量色义及条件跨镜保持一致，光色起伏通过环境与非语义明暗安排。应用段展示具体对象和有据结果，结尾回到原问题。随后在有声草排中检查时长、注意力接续和转场，缩略带只用于定位问题。

## 后续横版与适度亲和化

后续新制作默认1920×1080、16:9高清横版；当前明确要求改为横版的工作包按该范围重新设计。沿解释关系独立安排主体、景别、字幕和安全区，不能交换宽高、拉伸画面或按高度缩放旧竖版字幕坐标。`series-profile.json` 的 `captions` 保留旧竖版修订用于恢复，横版读取 `landscape_captions` 并在当前实际帧核布局。已批准或已发布竖版作品保留原画幅、身份、媒体与批准，不因默认值改变自动重导。

已获准的2D范围或独立封面保持成熟、精细的造型与可信结构，不用玩具比例、大圆眼或低细节图标替代主体。易引发不适的对象可适度亲和化，但保留识别结构、机制和真实风险。写实主镜以构图、光线和取景控制观感，不改成卡通。

## 文字、居中与运动

Use the approved font/weight, consistent alignment and margins, and clear space around the observation target. Necessary text must remain readable at phone size; tiny, ultra-thin or low-contrast type is not refinement. Improve placement and contrast first, adding restrained backing only when needed for permitted text. Captions normally use 1–2 semantic lines in the lower readable area; do not split terms or numbers from units.

Render editable overlay glyphs at delivery resolution after scene resizing, separately from raw 3D frames, so text revisions require recomposition only. Export evaluated anchors and visibility for tracked labels and check them against the current camera. Do not enlarge text baked into a proxy. Physical markings that belong to a scene surface may stay in the asset; when the explanation requires reading them, frame and hold them accordingly. Design covers separately.

字幕背景由实际字体、字号、行距、描边字形外缘加必要padding生成，不按字数估算，不固定大横框；短行不套两行大框。字层锚点/末行基线稳定，背景变宽高不拖动字层；同一句可缓存布局，不能逐帧重算抖动。超宽先断行/分句，不缩字号硬塞或侵入平台安全区。

当前项目基线/增量与一次应用修订标识只存 [系列配置](../config/series-profile.json)；它是历史1080×1920修订设置，不是永久通用Y或平台安全区。恢复时从已应用标识读取目标，不能再次扣同一增量；同画幅其他分辨率按高度比例换算并记录舍入，改画幅另排。只平移字幕及紧背景；与必要标签碰撞先做删除测试，再局部避让并保留指向/字号/时段，不整体挪主图。额外重排要如实记录，不能称纯像素平移。已发及已批准待发版本不因此追改。

视频对象标签、定位线、方向箭头及范围强调统一按[精密技术标注](annotation-style.md)设计；默认值读取[独立横版标注参数](../assets/style/precision-annotations.tokens.json)，不沿用历史竖版标签字号或圆角底板。已确认风格可复用，实际锚点、尖端和动态仍逐项实看。[矢量示例](../assets/style/leader-and-arrow.svg)是可编辑构造例，不是成片通过证据。图层仍按主体、必要强调、引线/箭头、标签、字幕的职责组织；修改参数不自动重染既有素材，须改实际源文件、重渲并更新引用。

### 正文辅助文字的使用与停留

**No upper-left or upper-right scene descriptions in body shots.** This includes shot names, scene summaries, two-line headings, process-stage tags and recurring chapter headings. Do not move the same heading to another corner or restyle it as a capsule. Establish location and progression through the picture, narration and transition. A necessary chapter title or route overview belongs in a dedicated transition/overview composition and leaves before the body resumes; do not insert a title card for every shot. Process diagrams must preserve actual branches, repetitions and order.

Before adding an explanatory sentence, try to show its content through the subject's action/state, framing, a motivated scale transition or a meaningful comparison. Generic captions describing the view or model, such as "local arrangement illustration", normally leave the image. If removing them makes the mechanism unclear, repair the visible event or the [shot relationship](viewer-retention-design.md#用镜头关系表达按需使用蒙太奇) instead of restyling the same explanation as a label. Preserve necessary qualifiers/conditions in synchronized narration or other existing appropriate channels; do not remove scientific uncertainty along with graphic text. Necessary short object labels, quantities/units, captions and required notices remain subject to their actual purpose and existing rules.

Use auxiliary text only when removing it would lose information needed for the current observation:

- Identify a specific part or state that the viewer must locate or distinguish; place its short label beside the feature or bind it with a precise leader. A detached scene heading does not become an object label by renaming it.
- Show a necessary number/unit, scale, comparison, symbol/legend or concise relationship that cannot be read from the picture and synchronized captions alone.
- State a scientific condition needed to interpret the current result, using the shortest accurate wording. Attribution and disclosures follow their existing placement/permission rules.

Do not repeat the spoken sentence as a second caption, label an obvious scene, fill empty space, or replace a visible mechanism with prose. Use one short phrase or sentence, not a paragraph. Present one auxiliary reading task at a time; a necessary comparison may form one group. If it competes with the caption or a new visual event, sequence the information or rewrite the narration. Keep ordinary subtitles synchronized as complete semantic units; these auxiliary-label floors do not apply to each subtitle word.

Read the short-label and explanation/comparison minimums in `audience_text.auxiliary_reading` in [production policy](../config/production-policy.json). They are editorial floors, not a guarantee of comprehension or a fixed shot length. Extend for unfamiliar terms, multiple values, locating the referent and actual phone-size reading.

- Count only one **continuous, fully legible, stable reading interval**. Entrance/exit animation, occlusion, low-contrast frames and moving/reflowing text do not count. Target motion is acceptable while the text remains stable and the binding clear. Separate flashes cannot be added together; a substantive text change starts a new reading interval.
- Plan the complete text, referent, entrance, stable interval and exit in the existing action card/timeline before rendering. Keep the text visible through the relevant observation after the minimum. Live values may update under a stable descriptor; hold the important result long enough to read and compare, rather than freezing each intermediate digit.
- If a shot or visible target cannot support the reading interval, shorten/remove the auxiliary text, use the narration, or extend/replan the observation. Never leave a label pointing at an absent target merely to reach a duration. Do not compress a sentence into a brief flash to preserve a cut.

Review the final encode at normal speed and phone viewing size with the actual narration/captions: the viewer must read the text and find its referent without pausing or rewinding. In the existing overlay evidence/QA observation, record each auxiliary item's stable readable start/end and the reading/locating result; appearance timestamps alone do not establish dwell. A forbidden corner heading, a subminimum reading interval, or text understood only after pausing is a failure. Fix and recheck the affected sequence; metadata checks and still frames cannot approve temporal readability.

## 观众画面与交付记录

对画内文字做删除测试：隐藏后，观众是否会丢失必要的对象身份、关系、条件、单位或中文可访问性？有具体损失则保留短准确文字并安排时段；没有则删除或移入配套。必要署名/标识另核实际条款要求的位置。

在下节 `presentation_text` 统一记录决定；不为每句口播另加标签，不把制作过程、工具限制、版本和QA状态写入观众画面。

### 可见文字用途与制作辩解

On-screen, caption, voiceover and cover text must serve the topic, object/mechanism, accessibility, scientific conditions or necessary attribution/license information; one item may have several real purposes. Shot-list names, working titles, generic scene-description captions, production-status notes, material defects, tool limits and internal QA belong in private records or appropriate companion material, not body-shot overlays, even briefly. Apply the deletion test before styling a label. When a real object/state needs identification, use the shortest accurate term. If a qualification is necessary to avoid mistaking a teaching model for a specific real object, preserve that meaning in a concise cue at the first relevant point and wherever later understanding requires it; do not merely rename or conceal the limitation. AI/simulation production disclosures default to platform fields and companion material, with specific on-frame consent handled below. No keyword, including a word meaning “illustration” or “model,” is automatically forbidden.

Edit defensive narration by purpose: remove material with no audience value, express a needed distinction as a direct positive explanation, and keep a genuinely necessary scientific condition where it is needed to understand the claim. For a structural tour followed by production, a clear transition such as “先看部件怎样组成整体，再沿制造过程看它怎样成形” can establish the viewing order. Do not automatically move discarded sentences into tiny corner notes; companion material is appropriate only when the information need not accompany the observation.

例如“素材不足只能这样画”“本片验收已通过”属于制作辩解，改写措辞或移到口播/封面仍删除。素材无原声时不添加虚构原声；科学任务需要声音比较时取得适配素材或调整有依据的表达。

删除不等于隐瞒科学与权利。必要来源署名、许可信息，以及确有科学意义的时间缩放、实验条件和结论限制，分别核其内容义务与呈现位置；AI制作披露默认留平台字段及配套，画内冲突按下文具体同意规则处理；允许由配套说明履行的署名不因此进入画面、字幕、口播或封面。科学模型的适用条件按scientific_condition连接文字一致、有科学依据的保护项；关键词命中时，在该item的 `cue_review` 记录 `status=pass`、`interpretation=scientific_condition`、与保护项basis一致的 `scientific_basis`、具体 `audience_task` 和判断 `note`。有依据的科学条件不因含“因此用”等因果措辞就被否决；缺判断或判断失败保持未通过。素材缺陷、制作工具限制、制作选择和QA状态不能靠保护用途标签或判断声明豁免。具体署名/许可和披露事实依 [权利责任正文](science-and-rights.md)，不由本规则授予使用权。

单集 `presentation_text` 维护唯一用途清单：`channels` 明确 frame/caption/voiceover/cover 的 present/absent 与 note；`items` 按正式文字顺序记录 id、surface、text、purposes、necessity、removal_loss。`required_notices` 保留 id/purpose/text/basis，另明确 `placement=audience/companion` 与 `placement_basis`，未知位置不得默认为上屏。audience以item的notice_id连接保护项；companion记录 `companion_destination` 作为配套落点，不强制生成媒体item。purposes使用topic/mechanism/accessibility/scientific_condition/attribution/license/ai_simulation/watermark；watermark仅本次明确请求并有具体同意时适用，material_defect/internal_qa/production_excuse/production_meta为禁止类别。AI披露默认companion；有已核义务或本次明确需求且有内容/位置/时段具体同意时，可用audience及同notice_id的item，仍核实际输出。实际素材以 `assets[].required_notice_ids` 引用同一保护项，改变位置或删除媒体文字不免除义务。没有字的通道也说明实际无字与核查范围，不默认把遗漏记为空。

G1核计划用途和保护项；G2/G3/G5分别在 `qa.presentation_text.<stage>` 记录实际所审版本、context_sha256、media_sha256、inventory_sha256、actual_media_inspected、各通道 channel_reviews（status/item_ids/observation/evidence）、protected_notices_review 与总 evidence。G2/G3核实际画面、字幕和口播，G5再完整核本次要求的封面；G3只签代表段范围。sources.voiceover/caption 用 file/hash 固定相应正式UTF-8稿件/字幕；G3使用所审片段的正式稿，G2/G5绑定本期正式稿，字幕依对应阶段源文件。口播和字幕的完整正文须按原顺序纳入用途清单，不得只挑好句；字幕txt/srt/vtt/ass由检查器提取正文，其他格式先转为受支持的正式字幕格式，再绑定版本并实际检查，不冒称原格式已自动核验。G5 cover_files固定本次要求的实际封面版本，无封面为[]。源文件筛查、词模式和OCR只辅助；各通道仍须实际看/听当前媒体，保护项缺失、漏分类、禁止用途或未实际检查都阻断，不能换个允许类别冒充用途。

配套位置在G1只核义务、位置依据及预期落点，不要求伪造已完成文件。G2/G3/G5的上述阶段记录另用 `companion_notices` 列出 `notice_id/file/sha256/status/observation`，绑定该阶段实际UTF-8配套文本；文件须含必要标识文字并经实际位置审查。G2可使用当时真实配套草稿，G5核当前交付配套；G3只核代表段实际所用素材引用的配套义务。文件存在和字面匹配只证明记录绑定，不证明授权、实际发布或许可合规。

### 画内标识须有具体同意

未经用户对具体标识内容、位置和显示时段的明确同意，不得在视频、字幕、封面或图内资产烧录AI模拟标识、水印、制作说明、内部验收记录或其他制作标识；工具默认、模板惯例、许可名称或笼统制作授权均不是同意。必要科学标签、图例、比例/时间/实验条件及正常同步字幕不属于此禁令，不额外要求逐字审批。

AI合规优先使用平台声明字段及简介/配套说明，并核实具体义务。若具体平台规则或素材许可确实要求画内保留标识，先向用户说明实际条款、拟用内容、位置与时段并取得具体同意；未同意则暂停相关素材/输出、改选可合规的素材或渠道，不能自行加标，也不能去掉法定或许可要求后悄然违约发布。制作辩解和内部验收状态仍禁止入片；AI制作披露及本次明确要求的水印按上述真实同意执行，不能只填一个approval布尔值。实际义务与请求冲突时先说明具体冲突，不假定任一方已获豁免。

标识项沿用 `presentation_text.items`，另填实际 `position`、`time_range=[start_seconds,end_seconds]`；静态封面用约定区间 `[0,1]` 表示整张。必要真实署名/许可证也须核此同意，不从许可要求推导用户同意。图形标识以 `kind=marking`、可辨识内容说明 `text`、`graphic_sha256` 及 `graphic_source={file,sha256}` 固定实际图形来源，不以没有文字逃过检查。`user_approval.scope` 精确复制 text/surface/position/time_range/graphic_sha256（无图形填null），另填 `user_message_ref`、`user_quote` 和 `evidence={file,sha256}`，指向用户原始同意文本及逐字引文；bool=true、制作端自签、旧版本笼统批准或改变内容/位置/时段后沿用均不合格。G1只核已有计划及同意，不要求尚未制作的成片。来源引用、引文和哈希只能绑定记录，原始消息真实性与同意语义仍须实际核实，不能伪造或由代理补签。

G2/G3/G5输出前在现有文字审查记录绑定 `overlay_evidence={file,sha256}`，按 [标识与来源证据模板](../assets/overlay-evidence-template.json) 和 [标识权限门禁](../scripts/label_permission_guard.py) 核当前导出媒体、用途清单、renderer/字幕/栅格字层/素材来源、实际可见文字与图形标识；角落、片头片尾、字幕、图内和主体区都须实看，含无字区及瞬时overlay。G3核完整代表段，G2/G5核完整当前导出，G5另绑定本次要求的实际封面。每项实际观察连接用途item、来源、精确内容/位置/时段；来源文件和证据均须当前SHA-256。未知/未列明overlay、无来源、未授权标识、与同意范围不符或过期证据一律阻断；不能把未知记为空、把标识改叫科学字幕或仅扫源代码就签通过。该增量不替代既有用途、实际声画、OCR/全时域文字检查；机器只能验证证据结构/绑定和已知词句，完整来源捕获、实际看图及授权真伪仍依真实审查。词模式只辅助筛查。AI本身是科学研究对象时，实际语义复核后可在item.cue_review记status=pass、interpretation=scientific_subject、reviewer/scientific_basis/audience_task/note、关联现有claim_ids、当前text_sha256及evidence={file,sha256}；该例外只解除关键词误报，不授予制作标识或水印权限。生产AI披露仍用ai_simulation及具体同意，不能改叫科学主题绕过。

## 两种封面各自设计

封面独立呈现大主体、短主题名和正片确实回答的问题。可复用符合原创视觉来源契约的自产视频帧或已认可自产资产，但重新组织构图；不拿带字幕截图、机制说明页或裁边后的细字小主体充数。已发布作品以当前真实发布正文和对应成片核主题，旧候选仅辅助；版本冲突先核实，不用相邻知识点替换原题。

本系列沿用精细2D插画、左上主题名与短问题；需要3:4和4:3时分别安排标题、主体与留白。按下表完成后交付。

### 封面成品标准与工程制造题材

封面先让观众认出本片对象、主题与观看理由。工程科学、工业生产和高端制造沿用系列精细插画的完成度与识别方式，主体按本题选真实设备、产品、材料或关键工序，不因“自然插画”这个历史名称而添加无关自然景物。正片采用3D不要求封面改成黑底模型展示；可以用自建3D作为造型、光影或构图依据，再完成符合系列身份的封面。

| 项目 | 制作与实看标准 |
| --- | --- |
| 内容承诺 | 对应当前正片的主问题和实际回答范围。写“怎么制造”“全流程”或“从原料到成品”前核正片是否覆盖该承诺；工艺参数、精度、性能、先进程度或比较结论有对应依据，不用无法兑现的夸大标题。长片封面突出核心对象和关键疑问，不把全链路压成工序清单。 |
| 主体与取景 | 以一眼可认的大主体建立焦点，保留识别所需轮廓与特征。工程题材核整机/部件身份、装配关系、方向和相对尺度；需要局部或剖切时，让观众仍能理解它与整体的关系。辅体只为比较或关键关系服务，不堆多个等权小图。 |
| 材质与科学外观 | 金属、陶瓷、玻璃、复合材料等按实际对象体现表面与受光差别；体积、边缘、明暗和细节有主次。核重复零件、孔道、刀具接触、加工状态等本题关键处，修掉穿插、融化、重复错位及无依据发光。示意剖切或颜色表达保持科学含义，不冒充实拍或实测。 |
| 标题与问题 | 沿系列左上大主题名与短问题安排层级，语义直接、与正片一致。用合法字体独立排中文，保留字层；不采用生成图中的乱码文字。标题不压关键结构，不靠缩小字、堆副标题或厚重描边塞满画面。 |
| 色光与背景 | 对照本次已实际查看的适用封面/风格参考的色光和细致程度，主体与背景在明度、色彩或清晰度上有可辨分离。工业场景、工具和环境只提供必要语境，避免背景纹理或灯效抢主体；科学本色优先，不用任意霓虹色制造所谓科技感。 |
| 比例与导出 | 按本次请求交付；完整系列包默认3:4和4:3，明确只要一种时只做该比例。两种比例分别重排标题、主体和留白，不能拉伸或机械裁切；常用输出尺寸与手机代理宽度见下列流程，不冒称平台硬标准。原图保持有效细节，检查导出后的裁切、锯齿、重影、压缩糊字和字体缺失。 |
| 缩略识别与一致性 | 实看每个导出的原图、手机缩略预览及与本次适用基准的并排对照。缩小时仍能认出对象、读清主题和问题、分清视觉重点；与正片开场保持同一对象与题意。任一比例存在错误主体、看不清的字或关键结构遮挡，修复后重看该版本。 |
| 交付材料 | 交本次所需成品和可追溯的无字背景、可编辑字层/合成源、字体与参数、来源/制作记录、手机预览、对照图及实际审查引用。沿已有 `qa.covers` 绑定版本，不重复建立一套批准表，也不以文件齐全或自动检测替代美术实看。 |

现有记录中的 `style=detailed_2d_nature` 是系列插画风格的兼容标识，`observations.large_natural_subject` 用于记录本题大主体的识别、尺度和造型观察；工程主体同样使用这两个既有字段，不把它们解释为“只能画自然对象”。各项实际观察分别写入既有 `style_match`、`scientific_appearance`、`independent_composition`、`mobile_readability` 等记录，未看保持pending。

### 制作流程

1. **定科学外观**：写明主体身份、轮廓、结构/材质依据、可用剖切及禁画项。问题与正片范围一致，比喻不画成错误事实。
2. **先图后字**：打开适用参考，以主体位置/尺度、背景主次、光向、材质、留字区和禁画项制作无字背景；正式中文用合法字体另排，保留可编辑字层和合成源。
3. **各比例重排**：需要两种比例时共用身份与主要素材，分别安排标题、主体及留白。当前常用1080×1440与1440×1080，平台有实际要求时再适配。
4. **实际看原图和缩略图**：可从270px宽竖图、360px宽横图试查，再按实际播放场景校准。核对象识别、标题/问题可读、关键轮廓无遮挡及科学外观；修复后独立审查当前导出。
5. **固定交付版本**：保存成品、无字背景、字层/合成源、字体参数、手机预览、对照及摘要，按下节绑定。批量重做逐项核作品身份与新旧版本；平台替换另按本次授权执行。

### 封面实图绑定与放行

沿用 `qa.covers`，将[封面审查模板](../assets/cover-review-template.json)的真实记录以visual_review={file,sha256}绑定。已有认可封面时用baseline.kind=approved_cover并绑定图、原认可及范围；首张封面没有旧认可时可用kind=initial_style_reference、scope=cover_appearance、实际image、selection_reason、actually_opened及observation，不伪造旧批准。两条路径都须独立实看当前成品和小屏对照；参数、哈希不代审美。真实媒体与反馈留私有工作包。

本次要求的各比例分别绑定当前导出与 `qa.reviewed_sha256`，保存手机预览及基准/新封面并排对照图；预览注明实际显示宽度、`phone_thumbnail` 场景及来源导出哈希，对照图绑定基准、导出和预览哈希。实际打开原图、预览与对照，逐项记录画风完成度、可识别的大主体、左上大标题与短问题、独立构图、科学外观、小屏可读和禁用布局是否存在；任一未看、未验、失败、源文件缺失或哈希过期均阻断。已有封面若未留上述证据，可补做真实对照，不能补签未进行的观看；只修封面无需重审无关片段。

制作/交付前运行 `python scripts/check_episode.py path/to/episode.json --stage covers --report path/to/new-cover-check.json`，再完成实际美术审查。单独封面任务只查封面；包含封面的G5及后续阶段复核同一记录，`video_only`不补造封面。未实际打开或缺能力记pending；已认可的适用风格无需重复批准。

### 已认可封面的可迁移做法

- **间歇泉**：低矮矿物锥、地表与大幅白色喷流水滴/凝结雾共同建立身份，主要喷流在右侧，左上留清晰标题区；蓝天与暖赭色地表形成层次。标题“间歇泉”，短问题“为什么 / 喷喷停停？”。不用地下剖面、岩浆、路径箭头或来源不明的测绘暗示替代现象。
- **爆米花**：小颗完整金黄玉米与大颗完整蓬松爆米花形成清楚对照；白色厚实、不规则泡沫褶皱与少量附着外皮保留真实身份，背景收敛。标题“爆米花”，短问题“为什么 / 突然开花？”。“开花”只是提问比喻，不能画成薄片花瓣、放射花朵、两半切口或剖面蜂窝。

迁移这两例的大主体、短问题、可信外观及小屏审看方法；按新题名字形和比例重排，不固定旧字号、蓝天背景或右侧主体位置。

## 声音质感

声音采用 [中文声音](voice-reference.md) 的唯一正文与系列配置；合成声明、自然口语、真实时码和完整听验均不能由画面参数代替。

## 三尺度造型与制作细节

视觉规范页用整体场景、对象中景、机制近景说明尺度适配，按 [代表样与同镜对照](#代表样与-l2l3-校准) 选择实际适用的实例，展示轮廓、形状语言、空间层次、光向、材质、细节密度、人物比例、字体层级、语义配色和字幕。缺实例记待做，未实际审看记候选，有范围/版本/证据才作生产基准。轮廓和材质服从同一已确认体系，主体不能比环境粗糙，近景不能把中景SVG无限放大。有依据的科学几何与解释符号可简化，按A01核身份、关系及条件；比例、边缘、空间与色彩组织仍须达到当前目标完成度，不能仅凭形状名称判合格或不合格。

精修按“主体轮廓与比例 → 结构、接触与支承 → 明暗与边缘组织 → 必要材质”推进，前项问题不能靠后项堆细节补偿；这是一种修图顺序，不是另设关卡。自然对象保留有依据的非完全对称结构，不给所有物体同样圆角或脸。先用简化色面比较主体与负空间，再补所需结构和接触；建立主要明度关系后分配边缘清晰度，最后只添加有助识别的材质。特定物种/物理形状须另研究建变体，通用标本不是科学图谱。按背景、主体、结构、引导、标签、字幕及实际动作需要分层，不把复杂可变对象压成不可编辑位图。

对本镜需要独立显隐、移动或形变的对象，按所需动作保留独立可编辑层与干净底板；逐一隐藏，并在当前拟用范围做轻微位移，实际查看完整合成与接触/边缘细节。保存所检图层、位移范围和结果；底板中的烘焙副本、空洞、双轮廓、矩形接缝或接触关系失效须修复后复核，不能把批准整图贴回去再叠层冒充已分离。位图绘画层可用，静态环境不必强拆；完整人物或植物群独立一层也不证明关节、枝叶或隐藏部位足以支持所需动作，必要时继续分件与补绘。隐藏/小位移只证明所检范围的分离与合成，动态证据按 [质量验收](quality-acceptance.md#可检查项目) 另验。

远景减细节、中景保识别、近景增真正支持解释的内部信息。把明度反差、边缘清晰度和细节密度共同分配给注意中心；次要环境可降低其中相应强度，不把所有轮廓同样加粗、所有表面同样画满，也不以模糊遮掉必要结构。线宽按参数起点和实际缩放复核。材质可关闭、对象内裁剪、帧间稳定，不覆盖字、不每帧随机；排线不能误作流线/力线。统一示意光向须记录，真实叙事光源出现时服从场景，不用塑料高光/全局辉光救造型。前中后景服务定位，不到处视差漂移。

昼夜/近景可换主题环境，但字体、角色比例、边缘和动作语言保持；科学事实色＞本镜变量色义＞主题色＞装饰色。制作时分开控制科学变量的色义与造型光影：变量色、图例和必要标识保留稳定对应，明暗、投影与材质变化不使变量被误认换值或换类；必要时用独立标记、形状或线型补充。教学热色不冒充真实发光，亮面不暗示数值升高。变量确需换义时重新建立图例；整片调色不得静默改变语义编码。源sRGB、工作空间与SDR/Rec.709输出分别记，HDR/广色域转SDR另核，写标签不等于正确转换。

最终字幕与标签为可编辑字层，不由生成模型画字；字体须合法取得并固定实际版本，不附字体文件，不把系统fallback当像素一致。正常字重与字形优先，不伪粗/重描边补错字。字幕沿当前画幅的字幕配置，历史候选56px/1.25、12–14汉字仅在原适用范围试排；图内标注读取[独立参数](../assets/style/precision-annotations.tokens.json)，不将字幕字号、描边或底板套给标签。实际字宽、观看尺度与停留优先。正文对实际动态底的对比度目标4.5:1，按未舍入值与最坏帧检查，紧背板可用，不声称WCAG整片认证。重要非语言声音信息也用必要字幕提示。

平台遮罩初始provisional，实际设备/界面/版本/日期/覆盖几何/证据齐全后才确认；旧1390字幕框不覆盖当前系列1615/1690基线。标题和封面沿各自适用参数，机制标签按[标注标准](annotation-style.md)及小屏实际可读性校准；变体记录理由，不能悄悄漂移。

手绘质感按轮廓、关键态和连续动作对照，不以纸纹叠加判定。历史插画字重、圆角及padding只在原范围使用；新视频标注读取独立参数，字幕与封面保持各自基准。

`design.board_reference`指向当前项目内的实际设计板文件，G3读取该文件并核对所记SHA-256；路径和哈希只能证明版本绑定。实际批准依据单独在 `design.approval.actual_feedback_ref` 引用真实反馈/批准记录，并绑定所认可的board哈希、审查者和分维度范围。三尺度图通过不能覆盖明确风格否定，视觉风格批准也不自动包含动作、音轨、整片或发布。可复用仍适用的既有批准，不重复索取同一决定。

### 最终编码的细节保留

制作端用同一镜头的工作母版与实际最终编码对照，优先选细线/小字、柔和渐变、低对比结构和运动中的材质等本片真实风险。先在目标播放尺度和正常速度看，再放大定位：细线是否消失或跳变、边缘是否发虚或生出光圈、渐变是否断层、纹理是否游移，关键结构和语义色是否仍可辨。放大图用于找原因，不能据局部放大效果代替实际观看尺寸的判断。

发现损失后先定位源图、缩放合成、色彩转换或编码环节，再改受影响的线宽、局部明度关系、纹理尺度、重采样或有依据的编码设置；不默认给全片锐化、增饱和或堆码率。用修后实际编码重新比较，平台转码仅在具备实际访问条件时另看；未取得平台成品不能声称已保留其细节。版本证据和实际验收仍归 [质量验收](quality-acceptance.md#记录与技术检查)。

## 2D精美的正向完成标准

按当前适用参考，在实际景别、目标屏幕和连续播放中检查下列A/D/I项目。身份、结构、构图、色义、接触、节奏与连贯性同样用于写实和3D；绘画分层、clip、底板和种子仅用于相应可控实现，不要求把写实素材拆层或改成2D。基础可用之外，L3须能指出造型、构图、空间、材质和节奏达到参照完成度的实际位置。

断线、穿插、抖动、遮字等客观缺陷先修；参照差距指出具体区域/时段；不同审美取向沿用本期已确认方向。缺参照时制作候选，不把候选自记为已批准。

### 动画场景设计与执行

主要动画由可识别实体/介质的状态或关系承担，辅助图形解释不可见关系，不能替代主体结果。按[场景设计](animation-scene-design.md)确定观察任务、状态序列、构图与资产拆分，再做代表段；[雪花示例](snow-crystal-scene-example.md)供已获准2D范围参考。证据沿用[既有阶段](quality-acceptance.md#美术方法的阶段证据)。

### 画面充实与精细场景表达

画面空洞时，先核口播的必要关系有没有落到主体变化、有效细节或同条件对照。关键区域太小则重取景；缺结果则补状态；已有结果不显著则调整参照、明度和观察窗口。局部放大须新增解释所需信息并保留整体定位，不只放大滑条、计数器或粗组件。

完整合成中核视点、相对尺度、遮挡、光向与环境映色，再看对应近景和相机极值。精细资产像拼贴时修空间关系；纹理、粒子或光圈不能补回它。必要留白、深色背景和时间轴按本镜用途保留，不为填满而添物。

具体操作见[空洞诊断与修复](animation-scene-design.md#先诊断空在哪里)，将观察写入现有动作卡与A03/A08、D01/D07、I01/I04。

### 代表样与 L2/L3 校准

从本期分镜选择实际高风险段：如密集说明、精细机制、留白构图、媒介或跨尺度接缝；可由同一代表段覆盖多项风险。

需要判断L2/L3差距时，优先用真实修订前后在同内容、同景别下对照；动态比较保持相应声画条件。逐项指出轮廓比例、结构接触、空间、边缘、细节及节奏的改变，写明适用范围与未覆盖项。无现成对照才做候选，不为每镜制造差稿；L3仍绑定实际认可及当前证据。

### 静态画面 A01–A10

| 编号 / 项目 | L3需要实际呈现的完成度 | 制作与检查方法 |
| --- | --- | --- |
| A01 轮廓与形状语言 | 主体有清楚且符合身份的轮廓，比例、曲直、大小节奏有意图；必要结构不用通用圆角替代 | 在拟用景别及手机代理检查轮廓、比例和关键关系。按对象职责设计：实体与环境核结构及造型参照，科学结构与解释符号核所表示的对象、关系和简化条件；各类元素均须达到本片目标完成度，识别正确不能代替造型推敲 |
| A02 结构与连接 | 内部结构、接触、连接和支承可信，近景揭示真实需要的信息，主体与环境完成度相当 | 核关节/连接点及负空间；分别看关键结构与完整合成，避免断开、粘连、漂浮或无依据的拓扑 |
| A03 构图与视觉优先级 | 主问题、关系和注意中心首先可见；主体尺度、负空间、视线、运动方向及标签位置共同支持解释 | 按对象关系选择居中或其他构图，在实际画幅及小屏核注意中心；明度、边缘和细节共同建立主次。留白须有作用，不以填满或默认居中代替设计 |
| A04 色彩与明暗 | 主体、环境、变量和文字各有色角色，重要关系可分辨；科学色义不被光影或整片调色改变 | 比较前景/背景的实际动态对比，分开控制变量色层与造型光影；灰度只诊断明度，形状/线型可补充等明度色，不能据灰度一票否定颜色方案 |
| A05 空间与遮挡 | 前中后景、接触与遮挡能帮助定位，同一物体跨镜空间身份连续，层次足够且不混乱 | 检查支承、遮挡顺序和视角桥；只增加本题需要的空间层，不强制每景三层或持续视差 |
| A06 线条与边缘 | 线宽、转角、路径接合与裁剪在最终尺寸稳定，关键结构清楚，边缘强弱服从主次 | 查看转角、端点、mask边缘、半透明交叠及最小尺度；在实际最终编码核细线和边缘保留，修接缝与异常光圈，不给所有对象统一粗黑框或锐化 |
| A07 材质与光向 | 用到的阴影、纹理或排线附着于对象，尺度和光向一致，运动中稳定，能增强识别 | 开关材质层对照；按对象clip并保持种子固定，检查变形与遮挡。没有纹理也可达L3，不能用纸纹、辉光掩盖造型 |
| A08 细节密度 | 关键结构有足够信息，背景与远景主动简化，细节聚集与留白有节奏 | 标出必须看见的信息，随主体层级分配细节，删除无功能细节再比较；近景新增必要信息，避免一律满画或一律几何占位，运动材质在最终编码中仍稳定 |
| A09 景别与尺度适配 | 本片用到的远/中/近景各自设计，同一对象身份和科学关系连续 | G3的 `design.keyframe_scales.whole_scene/object_midshot/mechanism_closeup` 各绑定实际图、摘要、观察note及pass；用本片对象的整景、中景和局部结构/关键关系作设计验证，不要求成片新增三镜。换尺度核线宽、细节、标签及定位，避免无限放大中景资产 |
| A10 字体与图形标注 | 正式字形、字号、字重、行距、紧背板及引线与画面统一，必要文字可读且就近对应 | 用真实字体量字形边界，核最长/最密句及动态底；文字可编辑，依法取得字体；不靠模型画字或装饰性长文补解释 |

### 连续动作 D01–D08

| 编号 / 项目 | L3需要实际呈现的完成度 | 制作与检查方法 |
| --- | --- | --- |
| D01 表达实际关系 | 动作、约束、路径、比较或有目的的静止直接建立本题关系，起点、过程和结果可追踪 | 连续看关键解释段，指出实际发生在哪个对象及怎样支持结论；有用途的draw-on/显隐/平移可用，不能以手法名称判断质量 |
| D02 时间分配 | 认识、变化、比较、观察停顿和收束各得到相应时间；画面密度与动作强弱有节奏且跟随实际口播 | 用整期缩略带定位持续均匀用力或突兀变化，再在有声草排和正常速连续段中调整；必要变化后留看清的时间，不套固定镜长、景别循环或每秒新增物体 |
| D03 间距与路径 | 每帧位置/姿态的间距、速度及路径与机制和动作意图相符，起止不突兀，极值不失真 | 复核关键帧间轨迹、速度峰值与到达状态。匀速传播可以保持匀速；不统一加ease或弹簧，不凭曲线漂亮改变科学机制 |
| D04 锚点与接触 | 应固定的支点、关节、地面和连接保持稳定，需要滑动或分离时关系清楚 | 检查运动极值、遮挡处及接触点；刚体不必形变，软体与关节按本题约束处理，不能用整层旋转替代必要连接 |
| D05 中间态与连续性 | 中间形状、身份、拓扑、边缘、颜色和图层关系连续，状态转变自然且可辨 | 看首/中/末、极值及完整播放；查旧层残留、鬼影、穿插、接缝和闪烁；首尾正确不能证明过程正确 |
| D06 主次动作 | 需要的预备、跟随、回弹或次级动作增加生命感并服从机制，次级运动晚于或弱于主要解释 | 明确主动作和辅助动作的作用；无必要时可不适用，不能给粒子、光线和刚体强制形变/回弹 |
| D07 镜头与桥接 | 推拉、取景、尺度、视角和转场有解释用途，变化前后能认回同一对象和关系 | 切换前定位，切换后保持身份/方向线索，局部返回能认回原处；不用不断推拉或叠化掩盖对象关系缺失 |
| D08 注意力编排 | 主要事件、必要标签、字幕和声音按语义顺序共同引导注意，不同时争抢 | 按真实音轨逐段核开始、重点、停顿和结束；同一时段允许多个对象，只限制同时引入的新重要关系 |

### 整片整合 I01–I05

| 编号 / 项目 | L3需要实际呈现的完成度 | 制作与检查方法 |
| --- | --- | --- |
| I01 解释闭合 | 原问题、前提、关键关系、局部说明和最后答案组成完整理解路径，条件和简化清楚 | 只依据作品实际呈现的信息做解释及表达内审，指出每个结论的支持位置，不让术语、类比或局部效果代替关系 |
| I02 声音与画面节奏 | 解说自然、轻重与动作重点相合，音乐/音效支持理解，接缝和静默有意图 | 完整正常速实际看听，分别耳机与手机外放听最终混音；音量、ASR和事件表只能帮助定位，不能代听 |
| I03 通道分工 | 主图建立对象/关系，图内字补必要条件和数值，解说推进推理，字幕提供中文可访问性 | 对文字按当前理解任务逐项删除测试；保留必要科学边界、单位与限定，署名/披露按已核实的位置落实，避免三处长文重复 |
| I04 全片一致性 | 不同场景、昼夜、景别与密度维持同一造型、字体、边缘、材质及动作语言，色彩和构图的变化形成有目的的整体 | 以整期缩略带辅助定位重复、过渡和收束，实际连续看实拍/2D接缝及风险代表段；逐镜漂亮或缩略带协调不能给整片代签 |
| I05 可编辑资产与合成 | 本片需要独立动作的层有完整隐藏部分、干净底板和稳定合成，工程可恢复实际使用版本 | 对所需独立层做隐藏及拟用位移，查看边缘、接触和底板；记录源文件/依赖版本。静态背景无须强拆，无此需求时说明不适用 |

### 可复用的表达骨架与实现选择

[解释配方](../assets/explanation-recipes.json) 提供八类关系的具体固定项、改变项、展示顺序和常见误导。先把本题关系填实，再设计同体系的对象与动作。配方和代码框架减少重复劳动；成品造型、时序、科学条件与实际连续审查看本题。

[外部技能选型](video-skills-curation.md) 按原始仓库、许可证和功能选择实现参考。Remotion、Motion Canvas、Manim等可用于具体获准的2D范围及辅助图层；引擎选择须服从已锁定媒介和当前适用的认可资产，不能凭框架支持动画就替代写实主画面。不以安装更多Skill替代美术设计或真实音轨，也不根据代码示例承诺已经达到L3。

### 连接拓扑与接口连续性

出现管道、线缆、连杆等连接件时，先设计正确对象/端口角色与连接拓扑，明确管径或截面变化、实体接头、中心线与接合/插入深度、遮挡层次，以及运动全程和跨镜的端点身份。连接不连续、接错端口、无合理实体接头的突变、悬浮断口或仅视觉搭桥均失败；按连接类型判断，不能机械要求所有线等粗。

端口功能须按可靠型号资料、结构图、可验证实物观察或明示教学模型定义确认，不能仅凭颜色、外形或就近位置指定进出口。接口还须核末端切线/中心线同轴关系、套入与固定结构；缺型号或用途依据时先核实，不给未知口补签正确。

沿用每镜 `shotbook.connections`：先判断是否有需要核查的跨部件连接。无连接场景只写 `applicable=false`、真实的 `not_applicable_reason` 与空 `links`，不编接头、粗细数值或虚构审查。存在连接时按稳定ID逐条记录类型、两端对象/端口及功能角色、截面/变径设计、接合几何、遮挡和动态/跨镜连续性。变径须有符合对象的实体过渡；线缆粗细或连杆截面可不同，但须解释其结构，不能靠背景遮盖突变。相同连接ID换端点或角色须有明确设计理由；科学过程本来包含拆接时明确展示拆接状态，不把真实断开错判为事故，也不允许无说明换接。

候选实际连续看听时，逐条对照设计与观察到的端点角色，并查看全景、接口近景和运动/切镜关键态。检查中心线、端面贴合/插入深度、管口/接头是否真正相接；弯曲、缩放、遮挡或切镜后，不能出现断口、穿帮、粗细跳变、前后层次互换或假接。允许复用同一张清晰关键态对照页，不强制固定截图数量或同一管径。仍有接口问题须修相应连接或镜头并重看，不能用字幕解释、粗线覆盖或其它镜头通过抵扣。

`sample`渲染入口先检查所选镜头的连接设计，不要求未来候选审查；G3在既有 `qa.visual_frames.animation.connection_review` 绑定当前样稿及设计，G5–G7在 `qa.visual_frames.connection_review` 绑定实际整片。沿用本阶段连续视听记录中的审查人/媒体，不另建审批链；有连接的每镜每条连接都需实观察，记录端点、五类观察、未解决问题和全景/接口/关键态图像引用。缺实看、设计/媒体/图像哈希过期、观察端口与设计不符或任何未修问题阻断相应关。代码只核声明、图像和绑定，物理合理性、真实拓扑和视觉质量仍须实际审查；N/A不能用来隐藏画面中存在的连接件。项目图片和审片意见留私有工作包，不收入公共Skill。

连接记录字段：`links[]` 使用 `id/kind/from/to/diameter_and_transition/joint_geometry/occlusion/continuity`；两端各含 `object_id/port_id/role/role_basis`，有意换接另记 `topology_change_reason`。实际 `connection_review` 使用 `status/actually_inspected/media_sha256/plan_sha256/reviewer/links`；每个结果含 `shot_id/connection_id/from/to/status/issues`、五类 `observations`（`topology_and_ports/diameter_and_transition/joint_geometry/occlusion/continuity`）及 `views`。视图各含 `kind/file/sha256/source_media_sha256/actually_opened/observation`，kind覆盖 `overview/joint_closeup/motion_or_cut_key_states`；plan_sha256由 `connection_guard.plan_sha256(episode, shot_ids)` 计算，不由审查人编造。
