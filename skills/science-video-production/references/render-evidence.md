<a id="渲染边界与取证副本"></a>
# Render boundaries and evidence copies

Use this for alpha flashes, exposed pan edges and review-image compression. Bind evidence to the actual current encode/time.

<a id="透明度最后赋值前检查"></a>
## Alpha: check before the final assignment

The [Canvas standard](https://html.spec.whatwg.org/multipage/canvas.html#dom-context-2d-globalalpha) ignores NaN, infinite and out-of-0–1 globalAlpha assignments, retaining the previous state. Floating-point easing may overshoot even when theoretically bounded; clamping input progress alone does not guarantee valid final alpha.

At the actual render entrypoint, check final alpha is finite before clamping. Do not rely on Canvas correction or silently turn nonfinite values into 0: locate the computation error, stop that render or use the project's explicitly recorded handling. Example:

    function checkedAlpha(value) {
      if (typeof value !== 'number' || !Number.isFinite(value)) {
        throw new Error('non-finite alpha');
      }
      return Math.max(0, Math.min(1, value));
    }
    context.globalAlpha = checkedAlpha(finalAlpha);

`scripts/render_evidence_checks.py` provides Python numeric validation through `clamp_alpha`. Wire repairs into the actual render entrypoint's final assignment, check stacked state and rerender.

For actual fades, check endpoints, adjacent floating-point values and nearby samples according to the frame timeline, easing and compositing risks; all final alpha must be finite 0–1. Preserve original anomalies/results, not ideal-endpoint-only tests. Determine neighboring ranges from actual faults/changes, not fixed frame counts, then inspect relevant dense frames/continuous clips from current encoding for stale alpha, flashes or unwanted visible layers.

<a id="平移分别核四边"></a>
## Translation: check all four edges separately

Use these direct geometry conditions only for fully opaque, unclipped/unmasked, unrotated/unsheared, positively scaled axis-aligned rectangles. Canvas size is W,H; final drawn rectangle is Dw,Dh with top-left tx,ty:

- Left/top: tx ≤ 0, ty ≤ 0
- Right/bottom: tx + Dw ≥ W, ty + Dh ≥ H
- Feasible translation: W − Dw ≤ tx ≤ 0, H − Dh ≤ ty ≤ 0; translation alone cannot cover if Dw < W or Dh < H

Use canvas coordinates incorporating actual anchors, scaling and transform order; source size is not drawn size. `axis_aligned_coverage(W, H, Dw, Dh, tx, ty)` returns per-edge/full coverage and feasible ranges; it changes no camera and cannot establish the prerequisites. Check frame trajectories and all four edge extremes, not only center/endpoints.

Rotation, masks, transparent edges, irregular assets and antialias coverage require transformed actual pixels/alpha; bounding-box formulas do not establish full coverage. Regardless of formula result, inspect final-encode motion extremes/joins; black edges may be in the source. Repair coverage or motion, not blur/color concealment.

<a id="从现有抽帧生成目标尺寸png"></a>
## Create target-size PNGs from existing frame extracts

Prefer [existing extraction tools](shotbook.md#full-film-frame-extraction-helper). `build_visual_review.py` extracts native-size PNGs by actual decoded frame number and binds media SHA/frame/time. Its start/mid/end samples do not automatically cover motion extremes, alpha risks or transient states.

For target-view-size review images, verify the source is the current reviewed final encode, then use the existing command with a new directory:

    python scripts/build_visual_review.py path/to/episode.json --media final.mp4 --output review-new

Retain/check that run's `review-new/manifest.json` SHA-256, media SHA, real frame/time and original PNG hashes. In the project's existing controlled evidence workflow, proportionally resize corresponding native PNGs to actual viewing dimensions and retain PNG output using installed FFmpeg/Pillow, without another derivative-file tool. Record target dimensions, pixel rounding, tool/version, filter, format and PNG hash with identity chain to original frame. Renaming extensions or substituting render screenshots for final-encode frames is invalid.

Choose proportional target dimensions for actual viewing, designing/reviewing distinct aspects independently. Preserve originals and create new files at checked paths; do not concurrently move/replace source media during evidence preparation.

Prefer PNG to avoid added JPEG artifacts. If JPEG is necessary, retain quality settings and compare same-frame/same-size PNG. Thumbnails cannot restore video detail; HDR/color issues require separate tone-map/display checks.

<a id="回归与结论范围"></a>
## Regression and conclusion scope

After numeric-check/extraction-tool changes, run:

    python -m unittest discover -s scripts/tests -p 'test_render_evidence_checks.py' -v

The suite checks alpha endpoints/invalid values, four-edge coverage and encode extraction. Truthfully mark optional Canvas/FFmpeg/Pillow dependencies skipped when absent. After tool regression, recheck faulty intervals/continuous clips from current rerendered media.
