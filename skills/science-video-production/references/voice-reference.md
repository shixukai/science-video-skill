# 中文解说：确认千问调用位置与实际听验

声音方案以 [系列配置](../config/series-profile.json) 为准：官方 Qwen CustomVoice 权重、Serena、Chinese 与项目口语指令。已有认可且仍与稿件匹配的音轨优先复用；采用默认配置不代表任何样片或成片已通过。

## 调用位置与确认

实际需要合成千问语音时，先检查当前及前文上下文是否已经指定千问工程、运行环境或服务位置。上下文已经明确指定时直接使用并记录对应上下文，不重复询问，也不要求本轮重新确认；只有上下文没有指定时才向用户询问。仅发现目录、缓存或配置不能当作指定调用位置。等待答复期间继续独立的稿件与分镜工作；位置未明确前不执行合成、创建环境、安装依赖或下载模型。仅整理Skill或编写纸面计划时不需要询问具体调用位置。

优先使用已确认工程的现有入口、运行环境、权重和参数，或已确认服务的接口。通用Skill不写入固定工程路径、Python路径、缓存路径或服务地址；这些位置留在当期私有记录。自带 [本地适配器](../scripts/synthesize_voice.py) 仅在明确选择它时使用，并非所有千问调用的必经入口。[官方使用说明](https://github.com/QwenLM/Qwen3-TTS#custom-voice-generate) 提供本地 CustomVoice 接口及 Serena 音色；适配器用官方参数合并方法记录有效参数。

当明确选择本地适配器时，系列配置的 audio.local_adapter_example 提供可调整的加载起点；已有工程沿用自己的已验证参数。该示例固定官方模型提交 `0c0e3051f131929182e2c023b9537f8b1c68adfe`，来源为 [官方模型 API](https://huggingface.co/api/models/Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice)，不同修订必须按实际记录；本地适配器核完整提交和文件清单哈希。服务或既有工程未暴露完整权重修订时，在 model_version_reference 写真实模型标识、版本证据及未提供的范围，不发明提交或清单，也不因此另下权重。

## 可选本地适配器

仅在用户已经确认本地工程，并明确选用本适配器时调用它。先核现有环境能否加载所需官方接口；路径、依赖和缓存来自本次确认的工程。确需新增环境、依赖或权重时，先说明具体缺项并取得相应指示，再按所选工程方式准备；不把新建Python环境当默认步骤。本适配器将依赖初始化与推理放在可清理的隔离工作目录，结束后恢复cwd，避免依赖会话文件污染工程。

适配器需要兼容的 `qwen-tts`、soundfile及huggingface_hub，版本按实际环境核实并记录；官方 [包定义](https://github.com/QwenLM/Qwen3-TTS/blob/main/pyproject.toml) 可作依赖依据。已确认工程具有自己的千问入口时优先调用该入口，无需迁移到此适配器。

准备私有 UTF-8 稿件 `script-v1.txt` 后，用新的输出文件名运行。正文不做隐式删改或逐句拆分，先按完整语义选择一段；长稿超过实际能力时按完整段落分次生成并逐段记录。

以下变量均由本次确认的实际工程提供，不是默认位置；命令从Skill目录运行。

```sh
"${QWEN_PYTHON}" scripts/synthesize_voice.py \
  --execution-reference "${QWEN_CONFIRMATION_REFERENCE}" \
  --project-dir "${QWEN_PROJECT_DIR}" \
  --cache-dir "${QWEN_MODEL_CACHE}" \
  --text-file "${QWEN_SCRIPT_FILE}" \
  --output "${QWEN_OUTPUT_WAV}" \
  --record "${QWEN_GENERATION_RECORD}"
```

本地适配器默认离线读取显式指定且已存在的模型缓存；缺模型时明确失败。只有本次指示覆盖权重下载时，才使用 --allow-model-download，从官方仓库下载选定修订到已确认缓存。--execution-reference、--project-dir、--cache-dir 均必填，缺确认引用或路径时在加载运行库、创建输出目录前失败。依赖安装、模型下载与实际调用分别按当前指示执行；脚本不会覆盖已有WAV或记录，也不会切换工程、缓存、设备或服务来重试。

输出是模型原生采样率的单声道 FLOAT WAV，保留源波形，不自动变速、变调、归一化或转 MP3。`peak_sample` 超出常规满幅时先测量和听验，再决定处理。返回空、全静默或含非有限样本的波形会失败；接口返回及文件写成只支持“已生成”，`listening` 始终保持待审。

## 运行记录与音轨绑定

私有生成记录保存真实后端、供应方、模型标识、运行参数、稿件及输出哈希，并用 execution 记录 status=confirmed、mode=local_project/service、location 与 confirmation_reference。本地工程另记实际Python、模型位置和可得的修订/清单；服务另记接口与实际响应版本证据，不含凭据。完整权重修订无法取得时保存真实 model_version_reference 说明。成功状态为 generated，不是声音验收通过；失败不生成成功记录，也不擅自换调用位置。

当期 narration.execution 保存已确认的调用方式、位置和确认来源；生成记录中的 execution 四个共同字段须逐字匹配。将实际记录以 narration.generation_record={file,sha256} 绑定到单集，config_reference 定位同次运行；input.sha256 对应 narration.script_sha256，未后处理时 output.sha256 对应 narration.audio_sha256。exact_model_revision_reference 只引用真正取得的版本证据。音轨仍由 narration.asset_id 解析对应 assets[].id，不取数组首项，不把配置当音频。

裁剪、重排、转码、响度处理、拼接或变速均另建音轨版本与 `narration.postprocess_record={file,sha256}`。后处理记录采用 `schema_version=1`、`status=processed`，`source={file,sha256}` 对应合成记录的输出，`output={file,sha256}` 对应当前音轨；`steps` 记录实际工具、版本与执行参数。未形成连续来源链时不以旧生成记录证明当前文件。可试用的响度/编码起点见系列配置 `audio.postprocess_example`，先实测并试听，不把起点当通用响度标准，也不用处理或音乐掩盖生硬语调。

已有实际认可且仍匹配当前稿件的音轨，可用 `narration.reuse_record` 记录 `status=previously_accepted`、真实认可/来源记录 `reference` 和当前 `audio_sha256`，优先复用，不为补新模板重生成。旧音轨没有精确修订时如实写未定位，不发明版本；复用仍须核当前声画和字幕，并保留听验范围。

## 源音轨与最终混音分别听验

源样本或独立音轨在 `narration.source_listen_review` 记录自己的 file/hash、scope、实际所听区间/方法/能力和证据；设备按实际范围记录。首次样本认可只覆盖所听版本和范围，不能代填长稿或整片通过；声音实质变化时重新试听短样。私有样本、反馈和认可记录留在项目，通用 Skill 不保存私人素材。

沿用项目确认的音色与口语指令，每段核稿件一致、漏词/重复/跑词、术语、数字、单位、多音字、断句和拼接处。主题、因果动词与结论有自然重音，给定位和变化留观察停顿；长句先改稿，不统一放慢成机械讲述。异常时长或疑似文本偏离先核查，不直接装片、不猜模型根因；完整解码、合理时长或 ASR 对齐不能代替文本正确性与实际听感检查。每条有中文解说；缺能力交明确待补录版本，字幕与配乐不代配音。

最终混音在 `qa.audio.listening` 正常速度完整听当前导出，按 [制作策略](../config/production-policy.json) 完成耳机与手机外放检查，记录设备、区间和问题时码；缺哪项就哪项未验。平台另核关键段。核心术语错读、因果词吞漏、断句改义、拼接突变、持续底噪/失真和音乐遮解释均退回。配音、配乐、环境和音效分轨，人声优先，逐段/跨段核突刺、削波与突断；不用 whoosh 或警报掩盖问题，不每次切镜默认加音效，设计音效不冒充原声记录。

剪接、补录、改词、停顿或语速变化后，重新核实际时码、字幕、关键动作及当前完整混音。混音、语速与最终编码 D 起点见 [制作策略](../config/production-policy.json)；已有认可配置和匹配音轨优先，不为起点强制变声、变速或重生成。最终编码实测响度和峰值，不称平台官方要求，也不代听验。音轨存在、ASR、波形、响度和技术解码都不等于听过；未实际听验的项目保持待审，不用短样认可填 `qa.narration` 的整片通过。

## 整期旁白连续性

整期旁白先按同一次连续讲述组织稿件，统一可感知的语气、节奏、语速和音量关系；不是要求每句同样重音，也不是切镜就重启一段播报。优先生成或取得能连续叙述的音轨，再按解释节拍剪接画面；沿用同一Serena、seed、模型参数或响度数值只能提供制作一致性起点，解码/ASR正确不证明跨段听起来连续。不能用统一加速、变声、强归一化或音乐掩盖语气突变。

长篇超出实际技术能力时可分段，按已验证的当前入口记录具体限制、可用方法、能力证据和上下文承接；不硬定模型一定支持长篇、提示拼接、参考声或某个未验证方案。分段稿件须保留前后论述、指代、因果与自然句尾/句首的承接，不按每个分镜机械独立生成。实际分段输入/输出版本与承接上下文可核，接缝仍在最终混音中正常速度连续听验；纸面上下文一致不能代替听感。

`narration.delivery_plan` 固定 mode（continuous_first 或 context_preserving_segments）和 target 的 tone/rhythm/speech_rate/loudness，以具体自然语言记录整期方向，不发明通用音质数值门槛。分段另有 technical_limit/verified_method/capability_evidence/context_handoff，并逐段记录 id、script与audio的file/hash、context_before/context_after、handoff_evidence，相邻段承接对应同一论述。引用现有工程或生成记录，不因为补字段重装模型或改运行环境。

G2完整有声草排、G3实际代表段和G5最终整期混音分别在 `qa.audio.continuity.<stage>` 记录 status、context_sha256、media_sha256、audio_sha256、plan_sha256、method=normal_speed_continuous_listening、actually_heard、reviewer/capability/evidence 与完整 ranges。criteria 的 tone/rhythm/speech_rate/loudness/joins 各有 status/observation/evidence；逐分镜衔接 transitions 记 from_shot/to_shot、当前媒体时码at、确实跨越该点的listen_range、status/observation/evidence。at必须对齐当前实际媒体分镜边界：G2/G5用实际对齐的有序shots[].shotbook.start/end；G3在既有qa.visual_frames.animation.shot_intervals按代表段本地时码记shot_id/start/end，覆盖当前完整代表段及所选镜头并绑定G3摘要。时间轴不得缺段、重叠或漏镜；自报at与listen_range不能替代边界，成片改变后重新对齐。连续音轨没有拼接也要听相邻画面之间的叙述承接，G3只覆盖所选片段，不能代整期通过；G5仍完成耳机与手机外放完整听检。

用户已反馈语气不一致、接缝突变或明显分段播报时，沿既有 `qa.visual_frames.failures` 记 scope=audio 的开放失败及原版本/时码/反馈定位，`qa.audio` 与对应连续性项保持fail/needs_changes；不以同声线、技术测试或其他高分抵消。局部新样可核修复范围，不能关闭整期声音否定；只有当前完整混音的连续复听、各接缝实际证据及匹配版本的完整复查才能解决该失败。缺实际听觉能力保持未验，测试通过不签视频或声音合格。

## 来源与传输范围

按本次已确认位置记录传输范围。本地工程与本适配器不向远程合成服务发送稿件；服务方式按实际接收者、文本类别、用途和已有授权执行，当前或前文上下文中明确指定的工程或服务位置可直接作为调用依据。缺少所传内容的授权时补足，不把文字范围扩大到视频或参考声纹。声音方向不代传输授权；不擅自克隆真人，合成声音按实际声明与必要披露执行。

服务、配额或资源失败报告具体阻塞，保留当前方案；不轮换账户、换镜像规避限制，不自动购买额度。模型许可、服务条款与具体用途分别核实，不在台账或仓库存入凭据、令牌或参考声纹。

## 适配器验证边界

适配器单元测试使用模拟模型，验证调用确认、显式路径、来源记录、失败退出与临时目录清理；不代表某个已有工程、服务或本次真实语音已可用。每次实际调用按已确认目标验证接口与运行结果，生成后实际听验；导入、文件存在或技术检查不能替代语音正确性和听感。
