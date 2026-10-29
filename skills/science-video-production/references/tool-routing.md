# 按制作场景调用工具

先按下表确定主制作工具，再补本次实际缺少的辅助能力。复用已有模型、Blender与MoneyPrinterTurbo工程。

外部工具的固定来源、版本与许可见[外部来源索引](../indexes/external-skills.json)；实际安装与运行能力在当前宿主核查。

## 按成片风格锁定主制作工具

从用户要求及当前项目记录确定成片风格，不按题材分流：

| 成片风格 | 必须采用的主制作工具 | 具体职责与边界 |
| --- | --- | --- |
| 写实风格（实拍观感，含AI写实与有权用户自拍） | **MoneyPrinterTurbo** | 使用已有仓库完成实际素材编排或已核合成入口，结合已确认旁白、字幕与画幅导出。需要生成镜头时，本地视频模型提供素材；模型本身、FFmpeg拼接或Blender渲染不能替代MoneyPrinterTurbo制作环节。详见[写实制作流程](ai-generated-video.md)。 |
| 3D动画风格（可控三维场景与动画，含拟真材质的3D） | **Blender** | 在Blender完成主体建模/资产复用、材质灯光、相机、动画与实际渲染；配音、字幕、混音和编码可用已有辅助工具。不能用AI生成的“3D观感”视频或MoneyPrinterTurbo混剪替代Blender制作。详见[3D制作流程](engineering-blender.md)。 |

未指定风格且现有上下文没有选择时，沿系列写实默认值使用MoneyPrinterTurbo，不凭工程题材自动选Blender。上下文已有明确风格时直接执行，不重复问工具。用户后续明确改变本期风格或工具时，以其最新要求为准并记录具体范围；执行者不能借缺工具、生成困难、旧偏好或内部小样比较自行换路。必需工具不可用时说明具体缺口，继续不依赖它的研究、脚本与设计。

仅在已明确的混合风格范围内分段采用两条路线，写实段与3D动画段分别登记对应工程和镜号；字幕、箭头等辅助层不构成另一种成片风格，也不触发第二套主制作工程。封面与独立3D资产任务按各自委托执行，不因视频分流强迫封面通过MoneyPrinterTurbo。

在简报、逐镜设计和 `execution` 记录风格、主工具、工程版本及实际输入/输出：写实片保留MoneyPrinterTurbo调用与合成产物，3D片保留Blender源工程/构建代码与渲染记录。G1核路线，G2/G3核样段，G5核最终产物；配置中的工具名不能代替实际运行。

## 本地执行、最少传输与吞吐

Prefer the user's local computer for work it can perform at the required quality: asset preparation, model inference, rendering, editing, encoding, transcription/alignment, media probing and validation. Actively use available local capacity to shorten time to a qualified result. Apply these defaults within the selected production route and existing authorization:

- **Keep processing near the data.** Reuse the installed tools, confirmed model locations, loaded models and verified assets. Run file searches, JSON/log filtering, hashes, measurements and report generation locally; return paths/IDs, concise results and relevant errors. Keep full logs, source media, weights and intermediate frame sequences locally instead of repeatedly sending them through the conversation or a remote runner.
- **Transfer only what the next step needs.** Prefer local review when the reviewer has actual access and perception capability; remote media review follows [selection and deduplication](#review-media-without-repeated-uploads). Remote processing is for an explicitly selected service, a demonstrated local capability/capacity gap, or a measured end-to-end benefit including transfer and queue time. Record the concrete reason and necessary payload in existing execution records; use existing permissions without adding a new approval form.
- **Reuse local working data.** Prefer an appropriate local fast disk for new active working sets and temporary media. Fetch missing assets from the approved library/NAS on demand, reuse verified local copies and archive changed files incrementally. Preserve originals, existing job-bound paths, version evidence and required backups; do not move a running job's inputs or repeatedly copy a whole library/project for a local change. Cache/reuse remains subject to the existing input-integrity checks.
- **Use CPU and GPU actively; preserve quality.** Select compatible GPU rendering/inference and hardware decode/encode when they meet the required quality. Overlap independent CPU preparation, analysis and post-processing with GPU work. Do not pre-emptively simplify materials, lighting, geometry or output quality because rendering might be expensive. Verify the actual selected backend and per-stage time; investigate idle gaps and inherited CPU/fixed-thread settings before treating low GPU utilization as a hardware limit.
- **Scale useful parallelism.** Coordinate worker count, threads per worker and batch size using current memory/VRAM demand, actual throughput and errors. Sustained high CPU/GPU usage is acceptable while the system remains responsive and stable. Increase useful concurrency when capacity remains; reuse a valid measured setup and put necessary calibration in the existing short sample, not a benchmark before every launch. The target is qualified output per unit time, not a utilization percentage.
- **Back off before system responsiveness is lost.** Use available current observations of memory/VRAM pressure, sustained paging or I/O stalls, desktop responsiveness and device/thermal errors. When resource contention causes slowdown or instability, reduce this task's workers, per-worker threads or batch size, or pause new submissions; preserve completed frames and resume at a demonstrated stable setting. Handle OOM/device faults in the affected job instead of repeatedly relaunching the same failing workload. Keep normal hardware/OS protections, job ownership, output locks and explicit host/user/task-specific limits; do not terminate unrelated tasks. Missing optional telemetry is not a new blocker. Resource admission follows the [current-evidence rule](production-checkpoints.md#静态证据条件复用与动态新鲜检查), without invented utilization caps, fixed reserve quotas or idle-wait gates.
- **Optimize the complete workflow.** Reuse initialized processes/scenes, batch compatible work, overlap independent stages and resume valid outputs. Re-render only affected ranges; text/audio-only changes normally recompose existing frames. Compare end-to-end time and qualified output throughput at the same quality, including transfer, loading and I/O. Keep the accepted resolution, motion sampling, geometry, voice and review requirements; high utilization alone is not proof of improvement. Use the existing [timing records](production-checkpoints.md#分段计时与受控服务复用) for measured configurations and results.

## Review media without repeated uploads

Local files do not imply local perception. Treat `view_image`, `emitImage` and image-bearing tool results sent to a remote model as media submissions. Local decoding, hashes, geometry checks and FFmpeg measurements can stay on the computer. A path or a successful playback command does not give an agent video/audio perception.

1. **Detect and select locally.** Run applicable frame-integrity, black/freeze/change, geometry/camera and audio checks locally; return compact findings and time ranges. These checks locate candidates for inspection, not aesthetic or scientific approval. Keep the original frames and full logs on disk. Do not loop image-view tools over a whole frame sequence as routine review, or send every intermediate render merely because it exists.
2. **Choose media for the question.** For motion and pacing, use a locally encoded, normal-frame-rate clip with the required sound and complete affected cycle/joins when the reviewer can actually perceive it. For static diagnosis, start with selected key states or a readable, labelled contact sheet, then request originals or contextual crops only where detail is unresolved. Preserve source identity, frame/time, crop and scale. Do not paginate the entire sequence into sheets to imitate playback. If continuous perception is unavailable, mark that coverage unreviewed; hundreds of still-image calls cannot supply it. Keep the existing normal-speed first-view and independent-context rules.
3. **Match the representation to the review.** Prepare lightweight review derivatives locally; do not change production masters. Use resolution/compression adequate for the actual question. Full-resolution text, fine geometry, texture, color or compression defects may need original frames and surrounding context. Proxy findings apply only to what remains observable; they do not replace required final-encode or full-film review. Choose a bounded batch for the current question rather than a universal frame/byte quota.
4. **Avoid duplicate submissions.** Assign one owner per review responsibility, media version and range; retain the separate G5 explanation and expression reviewers. In the existing work/review log, identify submitted media by content hash, frame/range or crop, purpose, recipient context and result status. Reuse observations for unchanged content in the same context; the parent receives paths, time-coded findings and only needed evidence, not another copy of every inspected frame. Repeat a submission only for a concrete reason such as missing detail, a new comparison or required independent review. A fresh reviewer must receive the media it needs without relying on the author's verdict; a shared path/hash is not a shared model cache. If a batch response is missing or oversized, inspect its status and resend only the missing needed items, not the whole batch automatically.
5. **Account honestly.** When diagnosing transfer cost, count actual media-submission events and repetitions, and record locally measured derivative sizes in the existing log. File bytes are an estimate of selected payload, not measured network traffic: encoding, resizing, cache behavior, retries and protocol overhead may differ. Report wire bytes only when actually measured and scoped. Do not upload more images to investigate an upload problem or print base64/full media logs into the conversation.

## 按需选择与应用证据

`tool_applications` 默认空，只登记实际选用的外部Skill：`need`、`selection_reason`、`source_id`、`usage_mode`（`method`/`runtime`）、`read_reference`（实际版本及文件）、`shot_ids`、`status`。方法参考须实际阅读并用于镜头；不因此安装整套框架。

`planned` 为待实施；`applied` 附 `artifact_evidence`（文件及SHA-256），在既有QA记录采用结果。`runtime` 另附 `installation_evidence` 和 `execution_evidence`；已有同版同环境证据可复用。

## 逐镜选择与同目标小样

先按上述风格分流锁定主制作工具；写实片执行[写实制作契约](realistic-production.md)，3D动画执行[Blender制作要求](engineering-blender.md)。下列2D工具只用于辅助层或明确委托的2D范围，不能替代两条路线的主体制作；绘图/代码动画也不能登记为视频模型调用。

- 写实氛围、环境建立与开场现象：通过MoneyPrinterTurbo制作；准备素材时复用当前已确认且有权可用的本地视频生成能力，也评估已核实用户自拍及用途授权的连续原片。第三方公开视频、CC/Commons及论文影像只能研究参考，不能因可下载或获许可变成填充镜。生成片只能作表现或示意，不能承担真实观测证据；科学论证仍须可核来源，引用论文不等于引入其视频画面；交付来源按 [原创视觉来源契约](science-and-rights.md#原创视觉来源契约)。
- 3D动画中依赖准确结构、接触次序、方向、拓扑或机构状态的过程：必须由Blender以同源几何与状态驱动整体、局部和过桥，无需先试视频模型。写实路线不能借这些要求静默换成Blender；两类输出都须核科学来源与实际连续状态。
- 已明确采用混合风格的镜头先分清每个产物的作用及对应主制作工具：例如生成环境与可控机制层分别登记来源，合成后检查对象身份、尺度、光影与前后状态；原有逐镜模态/资产台账保留，不能把合成结果误标实拍。
- 旁白、同步字幕、可核证据标注与必要图内字在后期以可编辑层合成，不依赖模型生成准确文字；它们不能补救错误主体动作或虚构证据。

同一路线内仍有素材、参数或表现方案待选时，才做同目标局部小样比较：固定必要主体、起终态、关键发现和观看条件。沿现有记录保存实际输入/版本、产物哈希、正常速审看差距、实测耗时与修复次数，未测项留未知；选定方案后继续现有阶段。只有一条可用路径时直接验证，不强制每镜比较。

### Blender-to-ComfyUI pipeline trials

Use a short paired trial when a neural redraw is a plausible improvement for the selected shot. It is optional, not a prerequisite for ordinary Blender production. Keep the [selected production route](#按成片风格锁定主制作工具); a trial does not make generated pixels equivalent to controlled geometry.

1. **Freeze a shared shot.** Use the same Blender scene, camera, objects, action, native frame range and viewing conditions. Define visible invariants such as component count, holes, interfaces, contact order and final state before rendering. Save the beauty sequence and the actual control input. Choose a frame count and resolution supported by the candidate model; keep both comparison clips at the same duration and fps. Identify native versus resized/interpolated outputs and any differing settings. This compares complete pipelines, not necessarily one isolated variable.
2. **Verify the actual control path.** Inspect the running node schema and saved graph: the full condition sequence must reach the video-control input, with the reference frame connected separately when used. First-frame I2V alone is not a controlled video-redraw test. A native-node example is `LoadVideo → GetVideoComponents.images → Canny → Wan22FunControlToVideo.control_video`, with the beauty first frame connected to `ref_image`, matched high/low-noise sampling, then VAE decode and encoding. Consult the [upstream template](https://github.com/Comfy-Org/workflow_templates/blob/main/templates/video_wan2_2_14B_fun_control.json), verifying the installed schema and model/accelerator pairing. Record actual versions, hashes, graph, seed, sampling, condition parameters and frame mapping. Depth, Mist, Normal and Canny are not interchangeable.
3. **Check preservation before appearance.** Inspect the encoded output for the required objects, openings, thin layers, motion and relationships; attractive texture cannot offset a lost part or changed mechanism. Record concrete defects by frame/time. Review continuous stability through the existing [actual viewing requirements](quality-acceptance.md#审片者与观看安全); stills can establish local defects but cannot prove smoothness or absence of flicker. Preserve a failing candidate and its repair cost. Full-frame neural output remains `ai_generated`; for masked redraw or compositing, record generated and retained controlled layers separately, with their actual Blender/control dependencies. Use controlled geometry for an explanation whose required relationships the redraw does not preserve.
4. **Measure time to a usable result.** Follow the existing [stage timing definitions](production-checkpoints.md#分段计时与受控服务复用). Report shared preparation once and each route's preparation/control export, startup, queue, loading, execution, encoding, repairs and actual review. The redraw route includes its required Blender work: if controls come from a beauty render, include that dependency; a cheap depth/clay-export alternative is a different trial. Separate first deployment/download costs from reusable work and state cache conditions. Measure route wall time; overlapping stages are not additive. Mark untimed work and unseparated stages instead of calling execution time the full total or pure inference.
5. **Adopt the demonstrated use, not the tool name.** A useful production method needs the required quality plus an observed quality or total-time benefit at comparable viewing conditions. A failed redraw still informs shot selection; it does not establish that all models fail. Keep unreviewed results as candidates. One short trial does not justify a series-wide engine/model change, universal speed claim, fixed low-VRAM setting, or replacing material/light work with automatic redraw.


工具或素材变更按[受影响依赖](quality-acceptance.md#失败后的处理)复查；续做按[全局迁移](global-skill-installation.md)核差异，不热切正在运行的任务。

## 调用前准备与安装

1. 查现有安装、可读入口、工程和依赖；会话列表未显示不等于没安装。复用已验证环境，不覆盖定制或为历史索引降级。
2. 缺必需runtime时，核来源/版本、依赖、本次安装授权和宿主权限；已有授权直接执行。仅阅读方法不安装框架；云传输、费用、账号及模型下载按各自授权处理。
3. 安装后读入口，核版本，做本次能力所需的最小运行并绑定真实产物。指定素材库归档沿[持续授权](engineering-blender.md#素材库归档的持续授权)执行。
4. 同类失败无新修复依据时停止该依赖，记录缺口并继续独立工作；不能静默替换锁定的主工具。未锁定辅助能力可用现有等效工具。

## 场景选择

| 当前任务 | 入口与产物 | 执行要点 |
| --- | --- | --- |
| 写实视频 | [MoneyPrinterTurbo流程](ai-generated-video.md) → 合成成片 | 显式素材顺序/裁切，复用完整旁白，核循环、字幕和发布副作用 |
| 3D动画或独立资产 | [Blender制作](engineering-blender.md)；[查库脚本](../scripts/find_3d_assets.py) → 源工程、渲染镜头或资产 | 先查库；独立资产任务不造整期音轨或G3 |
| 人物绑定、动捕与口型 | [人物表演](engineering-blender.md#人物绑定动捕与口型) → 可编辑角色/动作/面部曲线，或明确的生成视频层 | 按镜头需要启用，复用角色与音轨；骨架、蒙皮、重定向、接触及口型分别核，工具候选不等于已安装/实测 |
| AI写实连续素材 | 当前本地视频模型/ComfyUI工作流 → 视频与调用记录 | 核视频节点、权重及实际输出；图片模型不算视频生成 |
| 剪接、混音、转码、画幅 | `ffmpeg-skill` → 新媒体及检测结果 | 先核本机编码器/滤镜，保留源文件 |
| 中文识别、字幕对齐 | 已准备的本地ASR/对齐引擎 → SRT/字幕版 | 对齐最终时间线，核中文模型及字幕渲染能力 |
| 获准2D动画或辅助层 | 已有 `huashu-art-motion`、Motion Canvas、Manim或Remotion工程 → 可编辑层/画面轨 | 仅选与本镜关系相符的能力；不替代写实或3D主制作 |
| 现有HTML/React辅助层 | 已有HyperFrames或Remotion工程 → 图形轨 | 阅读对应入口，核实际依赖与运行许可，不为普通剪接迁移工程 |
| 首帧、背景、封面 | 现有合法资产或本期已选图片工具 → 静态资产 | 按宿主图像工具要求执行；静图不登记成视频 |
| 外语字幕或配音 | 本期获准字幕/声音工具 → 对齐字幕或新语言音轨 | 翻译字幕不等于配音；声音选择、上传与收费分别核实际授权 |

其他工具只在明确需求出现时查[来源与能力索引](../indexes/external-skills.json)，不照目录逐一安装。

复杂任务有可独立推进的工作或需要独立审查时，按[子代理协作](subagent-orchestration.md)委派；主代理保留整体叙事与交付责任，本地执行者协调实际作业。角色定义不改变风格路由、制作阶段或实际工具权限。

## 交给子工具的任务

交接主问题、镜头/语义段时码、前态与结束态、正式旁白及确认声音、适用画风/资产、画幅/fps、允许的文字和输出目录。产物回同一单集工程并接回完整旁白；镜头切换不重选声音或重新生成一句TTS。

工具检测复用到既有阶段记录；内容、画面与听感分别按责任正文审查。上游示例的色板、秒数、特效和默认声音不覆盖本期设计。

## huashu-art-motion 执行

仅在获准2D范围采用。读取其 `references/09-视频动画语法.md` 和本镜需要的语法卡，将 `scripts/engine/` 复制到单集新工程，固定上游提交与项目改动。参数化片段先核关系：例如 `y1` 的中心物/卫星节点不适合直接表示凝露，应用分层资产与场景代码表达杯壁、水汽和水滴。

优先复用已验证环境；以下为上游参数化入口，路径、内容、时长按本镜替换：

```sh
uv run --isolated --python python3 --with playwright --with pillow --with numpy python <单集工程>/render.py --spec <镜头.json> --out <新画面轨.mp4>
uv run --isolated --python python3 --with playwright --with pillow --with numpy python <huashu安装目录>/scripts/qa.py --spec <镜头.json> --out <新QA目录>
```

新环境及Chromium安装按已有授权和宿主权限执行。导出后用ffprobe核编码、尺寸、帧率、帧数与时长，再实际看抽帧和连续样段；沿用本期已确认声音及整条旁白。复杂人物/自然形体使用合法精细资产，代码负责可编辑动作与合成。

上游代码/文档为MIT，字体沿各自OFL，笔顺衍生数据沿Arphic许可；作者人物及相关帧只作示范，生产素材另核权利。

## 其他执行说明

- **FFmpeg与本地中文ASR**：读当前工具文档后调用 `probe.py`、处理脚本与 `check.py`。先剪辑，再用已准备的中文模型识别/对齐；默认英语模型不能当中文方案。完全离线先核权重在本机；缺 `subtitles`/`drawtext` 等能力时区分SRT、软字幕与烧录字幕，不能宣称未产出的字幕版已完成。
- **HyperFrames/Remotion**：只读所用能力的入口与依赖，复用现有工程和音轨。HyperFrames本地运行设置 `HYPERFRAMES_NO_TELEMETRY=1`，素材外传/反馈提交另按实际授权；Remotion的Skill许可和引擎运行许可分别核。Studio使用 `--no-open`，需要显示时用允许的浏览器工具打开。
- **browser-video-recording**：仅在确需操作演示时调用；它用截图状态合成，不是连续实录。显式配置 `cursor_asset`、`cursor_hotspot` 后运行 `scripts/render_browser_demo.py --config <配置> --output <新文件.mp4>`，避开默认全屏遮罩及系统光标抓取分支；无声轨接本期旁白。
- **模型/云服务候选**：先核准确入口、已准备模型/账号及实际授权；未核来源不猜命令。提示词指南不当可执行渲染器，字幕翻译器不当TTS，云转录不写成全本地处理。

## 来源识别

以[固定来源索引](../indexes/external-skills.json)中的真实仓库、文件与许可为准，不照搬帖子中重复或错配的链接。`video-dubbing` 未核实为可执行入口；`app-demo-agent`等同名候选须核真实来源。

逐镜状态与试验记录按[精确可控与高效迭代](production-checkpoints.md#精确可控与高效迭代)执行。
