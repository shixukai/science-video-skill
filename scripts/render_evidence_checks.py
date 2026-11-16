"""Pure numeric rendering boundary checks; never media or QA approval."""
from build_visual_review import ReviewError, number


def clamp_alpha(value):
    """Clamp a finite real value, rejecting invalid input instead of stale state."""
    if not number(value):
        raise ReviewError("alpha must be a finite, non-boolean number")
    return max(0.0, min(1.0, value))


def axis_aligned_coverage(canvas_width, canvas_height, drawn_width, drawn_height, tx, ty):
    """Only an opaque, unmasked, axis-aligned rectangle in final canvas coordinates.

    drawn_width/height already include positive scaling; tx/ty are its top-left.
    This checks geometry, not actual alpha, antialiasing or exported pixels.
    """
    sizes = (canvas_width, canvas_height, drawn_width, drawn_height)
    if any(not number(v) or v <= 0 for v in sizes) or any(not number(v) for v in (tx, ty)):
        raise ReviewError("dimensions must be positive finite numbers; translations must be finite")
    right, bottom = tx + drawn_width, ty + drawn_height
    if not number(right) or not number(bottom):
        raise ReviewError("transformed edges overflowed")
    edges = {"left": tx <= 0, "top": ty <= 0,
             "right": right >= canvas_width, "bottom": bottom >= canvas_height}
    feasible = drawn_width >= canvas_width and drawn_height >= canvas_height
    return {"bounds": [tx, ty, right, bottom], "covered_edges": edges,
            "covers_canvas": all(edges.values()),
            "translation_limits": {"x": [canvas_width - drawn_width, 0],
                                   "y": [canvas_height - drawn_height, 0]} if feasible else None}
