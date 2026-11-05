"""Offline appearance guard behavior; these fixtures do not prove visual quality."""
from contextlib import contextmanager
import json
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch
import zlib

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE if (HERE / "blender_batch.py").is_file() else HERE.parent))
import blender_batch as batch


class Pointer:
    def as_pointer(self):
        return id(self)


class Polygons:
    def __init__(self, indices=(0,)):
        self.indices = list(indices)
        self.bulk_reads = 0

    def __len__(self):
        return len(self.indices)

    def foreach_get(self, name, values):
        assert name == "material_index"
        self.bulk_reads += 1
        for index, value in enumerate(self.indices):
            values[index] = value


class Material(Pointer):
    def __init__(self, name="Material", channel="Surface", nodes=True, target="ALL", muted=False):
        self.name = self.name_full = name
        self.use_nodes = nodes
        output = NS(mute=muted, inputs={key: NS(is_linked=key == channel)
                                       for key in ("Surface", "Volume")})
        self.output = output
        self.node_tree = NS(get_output_node=Mock(side_effect=lambda renderer:
                            output if target in ("ALL", renderer) else None))


class Object(Pointer):
    def __init__(self, name="Object", materials=None, indices=(0,), kind="MESH", hidden=False):
        self.name = self.name_full = name
        self.type = kind
        self.hide_render = hidden
        self.hide_viewport = False
        self.original = self
        self.evaluated = None
        self.material_slots = [NS(material=material) for material in (materials or [])]
        self.data = Pointer()
        self.data.polygons = Polygons(indices)
        self.data.body = "A"
        self.data.splines = Polygons((0,))
        self.data.body_format = Polygons((0,))
        self.data.curves = [NS()]
        self.data.points = [NS()]

    def evaluated_get(self, graph):
        return self.evaluated or self


def branch(objects=(), children=(), hidden=False, excluded=False):
    return NS(exclude=excluded, collection=NS(hide_render=hidden, objects=list(objects)),
              children=list(children))


def layer(name="Layer", objects=(), children=(), enabled=True):
    return NS(name=name, use=enabled, layer_collection=branch(objects, children), update=Mock())


class Context:
    def __init__(self, layers):
        self.view_layer = layers[0]
        self.graphs = {id(item): NS(object_instances=[], update=Mock()) for item in layers}

    @contextmanager
    def temp_override(self, scene, view_layer):
        old = self.view_layer
        self.view_layer = view_layer
        try:
            yield
        finally:
            self.view_layer = old

    def evaluated_depsgraph_get(self):
        return self.graphs[id(self.view_layer)]


def fixture(objects=(), layers=None, engine="CYCLES"):
    layers = layers or [layer(objects=objects)]
    scene = NS(render=NS(engine=engine, use_single_layer=False), view_layers=layers, frame_set=Mock())
    bpy = NS(context=Context(layers), app=NS(version_string="fixture", build_hash=b"fixture"),
             data=NS(materials=[]))
    return scene, bpy


def instance(obj, parent, visible=True):
    return NS(is_instance=True, show_self=visible, object=obj, parent=parent)


def png(path, width=8, height=6):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) +
                     chunk(b"IDAT", zlib.compress((b"\0" + b"\x44\x88\xcc" * width) * height)) + chunk(b"IEND", b""))


class AppearanceTests(unittest.TestCase):
    def setUp(self):
        self.spec = {"schema_version": 1, "job_id": "appearance-fixture", "purpose": "appearance",
                     "driver": "scene.py", "blender_executable": "fixture.exe", "inputs": [],
                     "output_dir": "frames", "frames": "1:2",
                     "render": {"engine": "CYCLES", "device": "CPU", "samples": 2,
                                "width": 8, "height": 6, "fps": 25}}

    def audit(self, objects=(), **kwargs):
        scene, bpy = fixture(objects, **kwargs)
        return batch.audit_appearance_bindings(self.spec, scene, bpy)

    def test_appearance_workbench_rejected_upfront_and_prepare_writes_no_job(self):
        self.spec["render"]["engine"] = "BLENDER_WORKBENCH"
        with self.assertRaisesRegex(ValueError, "Appearance jobs require Cycles or EEVEE"):
            batch.validate_spec(self.spec)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "spec.json").write_text(json.dumps(self.spec), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Appearance jobs require"):
                batch.prepare(root / "spec.json", root / "job.json")
            self.assertFalse((root / "job.json").exists())
            self.assertFalse((root / "frames").exists())

    def test_appearance_supported_final_engines(self):
        for engine in ("CYCLES", "BLENDER_EEVEE_NEXT"):
            with self.subTest(engine=engine):
                self.spec["render"]["engine"] = engine
                self.assertEqual(batch.validate_spec(self.spec), [1, 2])

    def test_legacy_workbench_purposes_keep_declared_behavior(self):
        self.spec["render"]["engine"] = "BLENDER_WORKBENCH"
        for purpose in ("motion_preview", "lookdev", "shot_frames", "patch"):
            with self.subTest(purpose=purpose):
                self.spec["purpose"] = purpose
                self.assertEqual(batch.validate_spec(self.spec), [1, 2])
                self.assertIsNone(batch.audit_appearance_bindings(self.spec, None, None))

    def test_actual_workbench_engine_also_rejected(self):
        with self.assertRaisesRegex(ValueError, "Actual appearance renderer"):
            self.audit(engine="BLENDER_WORKBENCH")

    def test_unused_library_pbr_does_not_supply_actual_binding(self):
        scene, bpy = fixture([Object(materials=[Material(nodes=False)])])
        bpy.data.materials = [Material("UnusedPBR")]
        with self.assertRaisesRegex(ValueError, "missing node material"):
            batch.audit_appearance_bindings(self.spec, scene, bpy)
        self.assertEqual(bpy.data.materials[0].node_tree.get_output_node.call_count, 0)

    def test_evaluated_binding_wins_over_original_in_both_directions(self):
        source = Object(materials=[Material("Original")])
        source.evaluated = Object("Evaluated", [Material("Evaluated", nodes=False)])
        source.evaluated.original = source
        with self.assertRaisesRegex(ValueError, "missing node material"):
            self.audit([source])
        source.material_slots[0].material.use_nodes = False
        source.evaluated.material_slots[0].material.use_nodes = True
        self.assertEqual(self.audit([source])["materials"], 1)

    def test_missing_material_assignment_rejected(self):
        for materials in ([], [None]):
            with self.subTest(materials=materials), self.assertRaisesRegex(ValueError, "material"):
                self.audit([Object(materials=materials)])

    def test_disconnected_muted_and_wrong_renderer_outputs_rejected(self):
        for material in (Material(channel=None), Material(muted=True), Material(target="EEVEE")):
            with self.subTest(material=material), self.assertRaisesRegex(ValueError, "output"):
                self.audit([Object(materials=[material])])

    def test_correct_renderer_specific_active_output_is_selected(self):
        material = Material(target="EEVEE")
        self.assertEqual(self.audit([Object(materials=[material])], engine="BLENDER_EEVEE_NEXT")["materials"], 1)
        material.node_tree.get_output_node.assert_called_once_with("EEVEE")

    def test_connected_non_principled_surface_and_volume_graphs_are_accepted(self):
        for kind, channel in (("Emission", "Surface"), ("Transparent", "Surface"),
                              ("Holdout", "Surface"), ("Volume", "Volume")):
            with self.subTest(kind=kind):
                result = self.audit([Object(materials=[Material(kind, channel=channel)])])
                self.assertEqual(result["status"], "bindings_checked")
                self.assertEqual(result["quality"], "unreviewed")
                self.assertEqual(len(result["binding_sha256"]), 64)
                self.assertNotIn("approved", result)

    def test_only_used_mesh_slots_are_audited_with_native_bulk_read(self):
        obj = Object(materials=[Material(), None], indices=(0, 0, 0))
        self.assertEqual(self.audit([obj])["bindings"], 1)
        self.assertEqual(obj.data.polygons.bulk_reads, 1)
        obj.data.polygons.indices.append(1)
        with self.assertRaisesRegex(ValueError, "slot 1"):
            self.audit([obj])

    def test_out_of_range_used_slot_rejected_even_when_one_slot_exists(self):
        with self.assertRaisesRegex(ValueError, "slot 4"):
            self.audit([Object(materials=[Material()], indices=(4,))])

    def test_empty_geometry_does_not_demand_a_material(self):
        mesh = Object(indices=())
        font = Object(kind="FONT"); font.data.body = ""
        curve = Object(kind="CURVE"); curve.data.splines = Polygons(())
        self.assertEqual(self.audit([mesh, font, curve])["surface_objects"], 0)

    def test_curve_surface_and_font_ignore_unused_disconnected_material_slot(self):
        for kind in ("CURVE", "SURFACE", "FONT"):
            with self.subTest(kind=kind):
                obj = Object(kind=kind, materials=[Material(), Material(channel=None)])
                self.assertEqual(self.audit([obj])["bindings"], 1)
                indexed = obj.data.body_format if kind == "FONT" else obj.data.splines
                indexed.indices[0] = 1
                with self.assertRaisesRegex(ValueError, "slot 1"):
                    self.audit([obj])

    def test_render_hidden_and_excluded_paths_do_not_require_materials(self):
        children = [branch([Object("HiddenCollection")], hidden=True),
                    branch([Object("ExcludedCollection")], excluded=True)]
        render_layer = layer(objects=[Object("HiddenObject", hidden=True)], children=children)
        self.assertEqual(self.audit(layers=[render_layer])["surface_objects"], 0)

    def test_render_visible_path_wins_for_multiply_linked_object(self):
        obj = Object(materials=[Material(nodes=False)])
        render_layer = layer(children=[branch([obj], hidden=True), branch([obj])])
        with self.assertRaisesRegex(ValueError, "missing node material"):
            self.audit(layers=[render_layer])

    def test_viewport_hiding_is_not_render_hiding(self):
        obj = Object(materials=[Material(nodes=False)])
        obj.hide_viewport = True
        with self.assertRaisesRegex(ValueError, "missing node material"):
            self.audit([obj])

    def test_evaluated_instance_not_unused_source_library_is_audited(self):
        emitter = Object("Instancer", kind="EMPTY")
        source = Object("InstanceMesh", [Material(nodes=False)])
        scene, bpy = fixture([emitter])
        bpy.context.evaluated_depsgraph_get().object_instances = [instance(source, emitter)]
        with self.assertRaisesRegex(ValueError, "InstanceMesh"):
            batch.audit_appearance_bindings(self.spec, scene, bpy)

    def test_repeated_instances_deduplicate_objects_materials_and_mesh_scans(self):
        emitter = Object("Instancer", kind="EMPTY")
        material = Material()
        source = Object("InstanceMesh", [material])
        scene, bpy = fixture([emitter])
        bpy.context.evaluated_depsgraph_get().object_instances = [instance(source, emitter) for _ in range(8)]
        result = batch.audit_appearance_bindings(self.spec, scene, bpy)
        self.assertEqual((result["surface_objects"], result["materials"], result["evaluated_instances"]), (1, 1, 8))
        self.assertEqual(source.data.polygons.bulk_reads, 8)  # ephemeral RNA must be read per instance
        self.assertEqual(material.node_tree.get_output_node.call_count, 1)

    def test_hidden_instancer_and_nonrendering_instance_are_skipped(self):
        for hidden, visible in ((True, True), (False, False)):
            with self.subTest(hidden=hidden, visible=visible):
                emitter = Object("Instancer", kind="EMPTY", hidden=hidden)
                scene, bpy = fixture([emitter])
                bpy.context.evaluated_depsgraph_get().object_instances = [instance(Object(), emitter, visible)]
                self.assertEqual(batch.audit_appearance_bindings(self.spec, scene, bpy)["surface_objects"], 0)

    def test_hidden_instancer_surface_still_audits_its_rendered_instances(self):
        emitter = Object("Instancer", materials=[Material(nodes=False)])
        emitter.is_instancer = True
        emitter.show_instancer_for_render = False
        material = Material("InstanceMaterial")
        scene, bpy = fixture([emitter])
        bpy.context.evaluated_depsgraph_get().object_instances = [instance(Object("Child", [material]), emitter)]
        self.assertEqual(batch.audit_appearance_bindings(self.spec, scene, bpy)["materials"], 1)
        material.use_nodes = False
        with self.assertRaisesRegex(ValueError, "Child"):
            batch.audit_appearance_bindings(self.spec, scene, bpy)

    def test_object_and_collection_holdouts_do_not_need_surface_material(self):
        obj = Object(); obj.is_holdout = True
        collection = branch([Object("CollectionHoldout")]); collection.holdout = True
        result = self.audit(layers=[layer(objects=[obj], children=[collection])])
        self.assertEqual(result["holdout_objects"], 2)
        self.assertEqual(result["bindings"], 0)

    def test_actual_layer_material_override_is_audited(self):
        render_layer = layer(objects=[Object()])
        render_layer.material_override = Material("Override")
        self.assertEqual(self.audit(layers=[render_layer])["materials"], 1)
        render_layer.material_override.use_nodes = False
        with self.assertRaisesRegex(ValueError, "missing node material"):
            self.audit(layers=[render_layer])

    def test_hair_curves_and_pointclouds_are_checked_and_special_types_disclosed(self):
        for kind in ("CURVES", "POINTCLOUD"):
            with self.subTest(kind=kind):
                with self.assertRaisesRegex(ValueError, "no assigned material"):
                    self.audit([Object(kind=kind)])
                self.assertEqual(self.audit([Object(kind=kind, materials=[Material()])])["materials"], 1)
        result = self.audit([Object(kind="GREASEPENCIL")])
        self.assertEqual(result["unassessed_object_types"], ["GREASEPENCIL"])

    def test_all_enabled_render_layers_checked_and_context_restored(self):
        first = layer("First", [Object(materials=[Material()])])
        second = layer("Second", [Object(materials=[Material(nodes=False)])])
        scene, bpy = fixture(layers=[first, second])
        with self.assertRaisesRegex(ValueError, "Second"):
            batch.audit_appearance_bindings(self.spec, scene, bpy)
        self.assertIs(bpy.context.view_layer, first)
        bpy.context.graphs[id(second)].update.assert_called_once()
        second.use = False
        self.assertEqual(batch.audit_appearance_bindings(self.spec, scene, bpy)["view_layers"], ["First"])
        second.use = True
        scene.render.use_single_layer = True
        self.assertEqual(batch.audit_appearance_bindings(self.spec, scene, bpy)["view_layers"], ["First"])

    def test_shared_material_checked_once_each_frame_without_stale_cache(self):
        material = Material()
        scene, bpy = fixture([Object("First", [material]), Object("Second", [material])])
        batch.audit_appearance_bindings(self.spec, scene, bpy)
        self.assertEqual(material.node_tree.get_output_node.call_count, 1)
        material.output.inputs["Surface"].is_linked = False
        with self.assertRaisesRegex(ValueError, "no connected Surface or Volume"):
            batch.audit_appearance_bindings(self.spec, scene, bpy)
        self.assertEqual(material.node_tree.get_output_node.call_count, 2)

    def test_driver_frame_mutation_fails_before_second_frame_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "scene.py").write_text("# declared synthetic fixture\n", encoding="utf-8")
            (root / "fixture.exe").write_bytes(b"non-executable fixture")
            (root / "spec.json").write_text(json.dumps(self.spec), encoding="utf-8")
            job = batch.prepare(root / "spec.json", root / "job.json")
            material = Material()
            renderer = batch.BlenderRenderer()
            renderer.scene, renderer.bpy = fixture([Object(materials=[material])])
            renderer.build = Mock()
            rendered = []
            def set_frame(scene, frame, spec):
                renderer.frame = frame
                if frame == 2:
                    material.use_nodes = False
                return {"frame": frame}
            renderer.driver = NS(set_frame=set_frame)
            def render(path):
                rendered.append(renderer.frame)
                png(path)
            renderer.render = render
            with patch.object(batch, "configure", return_value={"engine": "CYCLES"}), \
                    patch.object(batch, "audit_blender_inputs") as dependency_audit:
                with self.assertRaisesRegex(ValueError, "missing node material"):
                    batch.execute(job, renderer)
            self.assertEqual(rendered, [1])
            self.assertEqual(dependency_audit.call_count, 2)
            first = batch.read(root / "frames" / "frame_000001.json")
            self.assertEqual(first["actual_render"]["appearance_binding_check"]["quality"], "unreviewed")
            self.assertFalse((root / "frames" / "frame_000002.png").exists())
            self.assertFalse((root / "frames" / "frame_000002.json").exists())
            self.assertEqual(batch.read(root / "frames" / "state.json")["status"], "failed")


class ExpiringObject:
    def __init__(self, target, alive):
        self._target, self._alive = target, alive
    def __getattr__(self, key):
        if not self._alive[0]:
            raise RuntimeError('evaluated instance RNA expired')
        return getattr(self._target, key)
    def as_pointer(self):
        if not self._alive[0]:
            raise RuntimeError('evaluated instance RNA expired')
        return self._target.as_pointer()

class EphemeralInstanceTests(unittest.TestCase):
    def check(self, missing):
        emitter = Object('Emitter', kind='EMPTY')
        material = [] if missing else [Material('Surface')]
        source = Object('TransientMesh', materials=material)
        scene, bpy = fixture([emitter])
        alive = [False]
        def instances():
            alive[0] = True
            yield instance(ExpiringObject(source, alive), emitter)
            alive[0] = False
        bpy.context.evaluated_depsgraph_get().object_instances = instances()
        return batch.audit_appearance_bindings({'purpose': 'appearance'}, scene, bpy)

    def test_transient_valid_instance_is_checked_before_expiry(self):
        result = self.check(False)
        self.assertEqual(result['evaluated_instances'], 1)
        self.assertEqual(result['surface_objects'], 1)

    def test_transient_missing_material_still_fails(self):
        with self.assertRaisesRegex(ValueError, 'TransientMesh: no assigned material'):
            self.check(True)

    def test_reused_ephemeral_mesh_address_does_not_reuse_stale_indices(self):
        emitter = Object('Emitter', kind='EMPTY')
        a = Object('First', materials=[Material()], indices=(0,))
        b = Object('Second', materials=[Material()], indices=(1,))
        a.data.as_pointer = lambda: 123456
        b.data.as_pointer = lambda: 123456
        scene, bpy = fixture([emitter])
        bpy.context.evaluated_depsgraph_get().object_instances = iter([
            instance(a, emitter), instance(b, emitter)])
        with self.assertRaisesRegex(ValueError, 'Second: slot 1: missing node material'):
            batch.audit_appearance_bindings({'purpose': 'appearance'}, scene, bpy)



if __name__ == "__main__":
    unittest.main()
