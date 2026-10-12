"""Synthetic numeric/pixel regressions; not acceptance of any production film."""
import io
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_visual_review import ReviewError, build_review, json_bytes, sha256
from render_evidence_checks import axis_aligned_coverage, clamp_alpha

try:
    from PIL import Image
except ImportError:
    Image = None


class NumericChecks(unittest.TestCase):
    def test_alpha_endpoints_and_floating_neighbors(self):
        for value in (0, 1, .25, math.nextafter(0, -1), math.nextafter(0, 1),
                      math.nextafter(1, 0), math.nextafter(1, 2), -1e100, 1e100):
            with self.subTest(value=value):
                self.assertTrue(0 <= clamp_alpha(value) <= 1)
                self.assertTrue(math.isfinite(clamp_alpha(value)))
        self.assertEqual(clamp_alpha(0), 0)
        self.assertEqual(clamp_alpha(1), 1)
        self.assertEqual(clamp_alpha(.25), .25)

    def test_quintic_overshoot_is_clamped_at_final_assignment(self):
        u = math.nextafter(1, 0)
        smooth = u*u*u*(u*(u*6-15)+10)
        self.assertGreater(smooth, 1)
        self.assertLess(1-smooth, 0)
        self.assertEqual(clamp_alpha(1-smooth), 0)
        self.assertEqual(clamp_alpha(smooth), 1)

    def test_invalid_alpha_is_not_silently_coerced(self):
        for value in (float("nan"), float("inf"), -float("inf"), True, False,
                      "0.5", None, [], 10**1000):
            with self.subTest(value=str(value)):
                with self.assertRaises(ReviewError):
                    clamp_alpha(value)

    def test_all_four_translation_extrema(self):
        for tx in (-30, 0):
            for ty in (-20, 0):
                result = axis_aligned_coverage(100, 60, 130, 80, tx, ty)
                self.assertTrue(result["covers_canvas"])
                self.assertEqual(result["translation_limits"], {"x": [-30, 0], "y": [-20, 0]})
        self.assertTrue(axis_aligned_coverage(100, 60, 100, 60, 0, 0)["covers_canvas"])

    def test_each_exposed_edge_fails_even_if_other_edges_cover(self):
        for edge, tx, ty in (("left", .001, -10), ("top", -15, .001),
                             ("right", -30.001, -10), ("bottom", -15, -20.001)):
            result = axis_aligned_coverage(100, 60, 130, 80, tx, ty)
            self.assertFalse(result["covers_canvas"], edge)
            self.assertFalse(result["covered_edges"][edge])
            self.assertEqual(sum(result["covered_edges"].values()), 3)

    def test_undersized_and_invalid_rectangles(self):
        result = axis_aligned_coverage(100, 60, 99, 60, 0, 0)
        self.assertFalse(result["covers_canvas"])
        self.assertIsNone(result["translation_limits"])
        for index in range(6):
            for value in (float("nan"), float("inf"), True, None):
                args = [100, 60, 130, 80, 0, 0]
                args[index] = value
                with self.assertRaises(ReviewError):
                    axis_aligned_coverage(*args)
        for size in (0, -1):
            with self.assertRaises(ReviewError):
                axis_aligned_coverage(100, 60, size, 80, 0, 0)
        with self.assertRaises(ReviewError):
            axis_aligned_coverage(100, 60, 1e308, 80, 1e308, 0)

    @unittest.skipUnless(shutil.which("node"), "optional installed Canvas runtime absent")
    def test_installed_canvas_negative_alpha_and_rectangle_extrema_pixels(self):
        check = subprocess.run(["node", "-e", "require.resolve('@napi-rs/canvas')"],
                               capture_output=True, timeout=10)
        if check.returncode:
            self.skipTest("optional @napi-rs/canvas absent; nothing installed")
        # Actual installed Canvas implementation, not a mocked setter. This only
        # tests the negative-alpha failure, not browser conformance in general.
        js = """
        const {createCanvas}=require('@napi-rs/canvas');
        const ctx=createCanvas(1,1).getContext('2d');
        const u=1-Number.EPSILON/2;
        const raw=1-u*u*u*(u*(u*6-15)+10);
        ctx.globalAlpha=1; ctx.globalAlpha=raw;
        const retained=ctx.globalAlpha;
        ctx.fillStyle='white'; ctx.fillRect(0,0,1,1);
        const oldPixel=Array.from(ctx.getImageData(0,0,1,1).data);
        ctx.clearRect(0,0,1,1);
        ctx.globalAlpha=Math.max(0,Math.min(1,raw)); ctx.fillRect(0,0,1,1);
        const coverage=[];
        for (const tx of [-30,0]) for (const ty of [-20,0]) {
          const c=createCanvas(100,60).getContext('2d');
          c.fillRect(tx,ty,130,80);
          const pixels=c.getImageData(0,0,100,60).data;
          coverage.push(Array.from(pixels).filter((_,i)=>i%4===3).every(v=>v===255));
        }
        const rotated=createCanvas(100,60).getContext('2d');
        rotated.translate(50,30); rotated.rotate(Math.PI/4); rotated.fillRect(-50,-30,100,60);
        console.log(JSON.stringify({raw,retained,oldPixel,coverage,
          rotatedCornerAlpha:rotated.getImageData(0,0,1,1).data[3],
          newPixel:Array.from(ctx.getImageData(0,0,1,1).data)}));
        """
        result = subprocess.run(["node", "-e", js], capture_output=True, text=True,
                                check=True, timeout=20)
        data = json.loads(result.stdout)
        self.assertLess(data["raw"], 0)
        self.assertEqual(data["retained"], 1)
        self.assertEqual(data["oldPixel"], [255, 255, 255, 255])
        self.assertEqual(data["newPixel"], [0, 0, 0, 0])
        self.assertEqual(data["coverage"], [True]*4)
        # Its enclosing bbox covers the canvas, but rotation leaves real corners
        # empty: never pass an arbitrary rotated bbox as an opaque rectangle.
        side = (100+60)/math.sqrt(2)
        self.assertTrue(axis_aligned_coverage(100, 60, side, side, (100-side)/2, (60-side)/2)["covers_canvas"])
        self.assertEqual(data["rotatedCornerAlpha"], 0)


@unittest.skipUnless(Image and shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "Pillow and existing FFmpeg tools required; nothing installed")
class ViewingCopyChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.media = self.root / "final.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-f", "lavfi", "-i",
                        "testsrc2=size=96x64:rate=6:duration=1", "-c:v", "mpeg4", "-q:v", "4",
                        "-pix_fmt", "yuv420p", str(self.media)], check=True, timeout=30)
        self.episode = self.root / "episode.json"
        self.episode.write_bytes(json_bytes({"shots": [{"id": "synthetic",
                                   "shotbook": {"start": 0, "end": 1}}]}))
        build_review(self.episode, "final.mp4", "review")
        self.manifest = self.root / "review/manifest.json"
        self.data = json.loads(self.manifest.read_text())
        self.original_hashes = {p: sha256(p) for p in self.root.rglob("*") if p.is_file()}

    def test_existing_extractor_final_frame_identity_and_lossless_resize(self):
        decoded = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-i", str(self.media),
                                  "-map", "0:v:0", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"],
                                 capture_output=True, check=True, timeout=30).stdout
        samples = self.data["shots"][0]["samples"]
        self.assertEqual([f["frame_index"] for f in samples], [0, 3, 5])
        self.assertEqual([f["frame_seconds"] for f in samples], [0, .5, .833333])
        self.assertEqual(self.data["media"]["sha256"], sha256(self.media))
        for sample in samples:
            source = self.root / "review" / sample["file"]
            self.assertEqual(sha256(source), sample["sha256"])
            with Image.open(source) as image:
                self.assertEqual(image.format, "PNG")
                self.assertEqual(image.size, (96, 64))
                i = sample["frame_index"]
                self.assertEqual(image.tobytes(), decoded[i*96*64*3:(i+1)*96*64*3])
                expected = image.resize((48, 32), Image.Resampling.LANCZOS)
                png = io.BytesIO()
                expected.save(png, format="PNG")
                with Image.open(io.BytesIO(png.getvalue())) as actual:
                    self.assertEqual(actual.format, "PNG")
                    self.assertEqual(actual.size, (48, 32))
                    self.assertEqual(actual.tobytes(), expected.tobytes())
                jpeg = io.BytesIO()
                expected.save(jpeg, format="JPEG", quality=40)
                with Image.open(io.BytesIO(jpeg.getvalue())) as lossy:
                    self.assertNotEqual(lossy.tobytes(), expected.tobytes())
        for path, digest in self.original_hashes.items():
            self.assertEqual(sha256(path), digest, str(path))
        self.assertEqual(self.data["status"], "generated_for_review")

    def test_existing_extractor_refuses_overwrite_or_escaping_media(self):
        for media, output in (("final.mp4", "review"), (str(self.media), "new-review"),
                              ("../outside.mp4", "new-review")):
            with self.assertRaises(ReviewError):
                build_review(self.episode, media, output)
        for path, digest in self.original_hashes.items():
            self.assertEqual(sha256(path), digest, str(path))


if __name__ == "__main__":
    unittest.main()
