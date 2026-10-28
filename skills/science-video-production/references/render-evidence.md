# 渲染边界与取证副本

处理透明度闪现、平移露边与审查图压缩问题时使用；取证绑定本次实际编码和时点。

## 透明度：最后赋值前检查

[Canvas标准](https://html.spec.whatwg.org/multipage/canvas.html#dom-context-2d-globalalpha) 规定：NaN、无穷和超出0–1的globalAlpha赋值会被忽略，原状态保留。理论上已落在0–1的缓动式，浮点运算仍可能越界；只夹紧输入进度不足以保证最终透明度合法。

在实际渲染入口对最终透明度做有限值检查，再夹紧。不要依靠Canvas自动修正，也不要把非有限值悄悄变成0：应定位计算错误，阻断该次渲染或使用项目明确记录的处理。示意实现：

    function checkedAlpha(value) {
      if (typeof value !== 'number' || !Number.isFinite(value)) {
        throw new Error('non-finite alpha');
      }
      return Math.max(0, Math.min(1, value));
    }
    context.globalAlpha = checkedAlpha(finalAlpha);

`scripts/render_evidence_checks.py` 的 `clamp_alpha` 提供Python数值检查。修复须接入实际渲染入口的最后一次赋值，核层叠状态并重渲。

对实际淡入/淡出区间，按当前帧时轴、缓动与合成风险检查端点、浮点邻值和邻近采样；检查最终alpha均为有限0–1。保留原异常和处理结果，不能只测试理想端点。邻近帧范围由实际故障/变化确定，不固定帧数；再从当前编码导出核相关密序帧和连续片段，防止旧alpha残留、闪现或错误图层仍可见。

## 平移：分别核四边

只有完整不透明、无裁剪/遮罩、无旋转/斜切、正缩放后的轴对齐矩形，才可直接用以下几何条件。画布尺寸为W、H，最终绘制矩形尺寸为Dw、Dh，最终左上坐标为tx、ty：

- 左、上：tx ≤ 0，ty ≤ 0
- 右、下：tx + Dw ≥ W，ty + Dh ≥ H
- 可行平移范围：W − Dw ≤ tx ≤ 0，H − Dh ≤ ty ≤ 0；Dw < W或Dh < H时，仅平移无法全覆盖

使用已合并实际锚点、缩放及变换顺序的画布坐标，不把源图尺寸直接当绘制尺寸。`axis_aligned_coverage(W, H, Dw, Dh, tx, ty)`返回四边分别结果、全覆盖结果与可行范围；它不改镜头，也不判断素材真的满足前提。逐帧轨迹与所有四边极值均需核，不能只测中心或起终点。

旋转、遮罩、透明边缘、非矩形素材和实际抗锯齿覆盖须检查变换后的实际像素/alpha，不能借外包矩形公式宣称全画布覆盖。无论公式是否通过，都在最终编码检查镜头极值和接点；黑边也可能来自素材本身。缺边时修素材覆盖或镜头轨迹，不用模糊/贴色掩盖。

## 从现有抽帧生成目标尺寸PNG

优先复用 [现有抽帧工具](shotbook.md#整片视觉抽帧工具)。`build_visual_review.py` 已从指定编码媒体按实际解码帧号抽取原尺寸PNG，并绑定媒体SHA、帧号和时间；它的start/mid/end样本不自动覆盖全部运动极值、透明度风险或中间瞬态。

需要目标观看尺寸的审查图时，先确认源文件就是本次实际审查的最终编码版本，并用既有命令生成新目录：

    python scripts/build_visual_review.py path/to/episode.json --media final.mp4 --output review-new

保留并核该次 `review-new/manifest.json` 的SHA-256、媒体SHA、实际帧号/时间及原PNG哈希。在当前项目既有的受控取证流程中，将对应原尺寸PNG按实际观看尺寸等比缩放，并仍保存PNG；可用已装FFmpeg或Pillow，不另加文件派生工具。记录实际目标宽高、像素取整方法、工具/版本、缩放滤波、输出格式和PNG哈希，并保留到原帧的身份链。不能仅改扩展名，也不能拿渲染源截图代替最终编码帧。

目标尺寸按实际观看场景选择，等比缩放；不同画幅独立设计/审查。保留源图，输出到已核路径的新文件；取证期间不要并发移动或替换源媒体。

审查图优先PNG，避免额外JPEG伪影；必须用JPEG时保存质量设置，并与同帧同尺寸PNG对照。缩略图不能恢复原视频细节；HDR或色彩问题须另核色调映射及实际显示。

## 回归与结论范围

修改数值检查或抽帧工具后运行：

    python -m unittest discover -s scripts/tests -p 'test_render_evidence_checks.py' -v

套件检查alpha端点/非法值、四边覆盖及编码抽帧；可选Canvas、FFmpeg/Pillow依赖缺失时如实记skip。工具回归后仍从当前重渲媒体复查故障时段与连续片段。
