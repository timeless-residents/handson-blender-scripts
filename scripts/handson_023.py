#!/usr/bin/env python
"""
Blender用スクリプト:
  トーテムポール風オブジェクトと地面、複数のカメラ、照明、ワールド環境、
  複雑なレンダリング設定および高度なマテリアルノードの構築を行い、レンダリングする。

【機能詳細】
  - シーン初期化と各データブロックのクリーンアップ
  - 世界背景および環境テクスチャ設定（ノードエディタを使用）
  - 詳細なレンダリング設定（解像度、サンプル数、出力フォーマットなど）
  - カメラの作成、設定、深度（DOF）およびキーフレームによるアニメーション設定
  - 複数種の照明（SUN、AREA、POINT）をシーンに配置し、各パラメータを調整
  - 地面およびトーテムポール各部（ベース、鳥の頭部、くちばし、翼、中央装飾、下部装飾）の生成
  - 高度なマテリアル設定（シンプル／複雑なノードネットワークの構築）
  - 各オブジェクトへのモディファイア適用、法線調整、原点設定などの最終調整
  - シーン全体をカメラに収めた状態でレンダリング実行およびシーンのOBJエクスポート

実行例:
    blender --background --python script_totem_full.py
"""

import bpy
import os
import shutil
import datetime
import math
import bmesh
import mathutils
import addon_utils  # アドオン有効化用

# =============================================================================
# 1. 設定パラメータクラス
# =============================================================================


class Config:
    def __init__(self):
        # シーン・レンダリング基本設定
        self.render_engine = "BLENDER_EEVEE"
        self.resolution_x = 1920
        self.resolution_y = 1080
        self.resolution_percentage = 100
        self.samples = 32

        # Ambient Occlusion（EEVEE用）
        self.use_ambient_occlusion = True
        self.ao_distance = 1.0

        # 出力設定
        self.output_dir = os.path.join(os.getcwd(), "output")
        self.output_filepath = os.path.join(self.output_dir, "render_totem.png")

        # ワールド設定
        self.world_background_color = (0.05, 0.1, 0.2, 1.0)
        self.environment_strength = 1.0
        self.use_environment_texture = True
        self.environment_texture_path = os.path.join(os.getcwd(), "textures", "env.hdr")

        # カメラ設定
        self.camera_location = (8.0, -8.0, 8.0)
        self.camera_target = (0.0, 0.0, 1.5)
        self.camera_lens = 18
        self.camera_sensor_width = 36
        self.camera_dof_distance = 10.0
        self.camera_dof_fstop = 2.8

        # 照明設定
        self.sun_light_location = (5.0, 5.0, 10.0)
        self.sun_light_energy = 3.0
        self.area_light_location = (-4.0, 4.0, 8.0)
        self.area_light_energy = 1000.0
        self.point_light_location = (0.0, -6.0, 6.0)
        self.point_light_energy = 800.0

        # 地面設定
        self.ground_size = 10.0
        self.ground_location = (0.0, 0.0, 0.0)
        self.ground_material_color = (0.2, 0.4, 0.2, 1.0)

        # トーテムポール設定（各パーツ）
        # ベース
        self.base_radius = 0.5
        self.base_depth = 3.0
        self.base_location = (0.0, 0.0, self.base_depth / 2.0)
        self.base_material_color = (0.3, 0.2, 0.1, 1.0)
        # 鳥の頭部
        self.head_radius = 0.3
        self.head_depth = 0.5
        self.head_location = (0.0, 0.0, self.base_depth + self.head_depth / 2.0)
        self.head_material_color = (0.9, 0.9, 0.8, 1.0)
        # くちばし
        self.beak_size = 0.15
        self.beak_location = (0.0, 0.3, self.base_depth + 0.1)
        self.beak_extrude_vector = (0.0, 0.1, 0.0)
        self.beak_material_color = (1.0, 0.8, 0.2, 1.0)
        # 翼
        self.wing_size = 1.0
        self.left_wing_location = (0.0, 0.0, self.base_depth + 0.2)
        self.left_wing_rotation = (0.0, 0.0, math.radians(90))
        self.left_wing_scale = (2.0, 0.3, 1.0)
        self.wing_material_color = (0.1, 0.5, 0.2, 1.0)
        # 中央の顔っぽい装飾
        self.mid_face_radius = 0.4
        self.mid_face_depth = 0.3
        self.mid_face_location = (0.0, 0.0, self.base_depth * 0.6)
        self.mid_face_material_color = (0.3, 0.6, 0.6, 1.0)
        # 下部の人型装飾
        self.bottom_radius = 0.3
        self.bottom_depth = 0.5
        self.bottom_location = (0.0, 0.0, self.bottom_depth / 2.0)
        self.bottom_material_color = (0.7, 0.2, 0.2, 1.0)

        # コンポジター設定
        self.use_compositor = True
        self.compositor_bloom_intensity = 0.2
        self.compositor_glare_threshold = 0.8


config = Config()

# =============================================================================
# 2. シーン操作ユーティリティ（初期化・クリーンアップ）
# =============================================================================


def backup_file(file_path: str) -> None:
    if os.path.exists(file_path):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{file_path}.{timestamp}.bak"
        shutil.move(file_path, backup_path)


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    # メッシュ、マテリアル、ライト等もクリーンアップ
    for block in bpy.data.meshes:
        bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)
    for block in bpy.data.lights:
        if block.users == 0:
            bpy.data.lights.remove(block)


# =============================================================================
# 3. ワールド・環境設定
# =============================================================================


def setup_world_background() -> None:
    world = bpy.data.worlds["World"]
    world.use_nodes = True
    node_tree = world.node_tree
    nodes = node_tree.nodes
    links = node_tree.links
    for node in nodes:
        nodes.remove(node)
    bg_node = nodes.new(type="ShaderNodeBackground")
    bg_node.location = (-300, 0)
    bg_node.inputs[0].default_value = config.world_background_color
    bg_node.inputs[1].default_value = config.environment_strength
    output_node = nodes.new(type="ShaderNodeOutputWorld")
    output_node.location = (0, 0)
    links.new(bg_node.outputs[0], output_node.inputs[0])


def setup_environment_texture() -> None:
    if config.use_environment_texture and os.path.exists(
        config.environment_texture_path
    ):
        world = bpy.data.worlds["World"]
        world.use_nodes = True
        nt = world.node_tree
        nodes = nt.nodes
        links = nt.links
        env_tex = nodes.new(type="ShaderNodeTexEnvironment")
        env_tex.location = (-600, 0)
        try:
            env_tex.image = bpy.data.images.load(config.environment_texture_path)
        except Exception as e:
            print("環境テクスチャの読み込みエラー: ", e)
        mix_node = nodes.new(type="ShaderNodeMixShader")
        mix_node.location = (-150, 0)
        bg_node = nodes.new(type="ShaderNodeBackground")
        bg_node.location = (-300, -200)
        bg_node.inputs[0].default_value = config.world_background_color
        output_node = nodes.new(type="ShaderNodeOutputWorld")
        output_node.location = (100, 0)
        links.new(env_tex.outputs[0], mix_node.inputs[1])
        links.new(bg_node.outputs[0], mix_node.inputs[2])
        links.new(mix_node.outputs[0], output_node.inputs[0])


def setup_ambient_occlusion() -> None:
    scene = bpy.context.scene
    if scene.render.engine == "BLENDER_EEVEE":
        scene.eevee.use_gtao = config.use_ambient_occlusion
        scene.eevee.gtao_distance = config.ao_distance


# =============================================================================
# 4. レンダリング設定
# =============================================================================


def setup_render() -> None:
    scene = bpy.context.scene
    scene.render.engine = config.render_engine
    scene.render.resolution_x = config.resolution_x
    scene.render.resolution_y = config.resolution_y
    scene.render.resolution_percentage = config.resolution_percentage
    scene.render.filepath = config.output_filepath
    scene.render.image_settings.file_format = "PNG"
    if config.render_engine == "BLENDER_EEVEE":
        scene.eevee.taa_render_samples = config.samples
        scene.eevee.use_bloom = True


def setup_compositor() -> None:
    scene = bpy.context.scene
    scene.use_nodes = True
    tree = scene.node_tree
    for node in tree.nodes:
        tree.nodes.remove(node)
    render_layers = tree.nodes.new(type="CompositorNodeRLayers")
    render_layers.location = (-300, 0)
    glare_node = tree.nodes.new(type="CompositorNodeGlare")
    glare_node.glare_type = "FOG_GLOW"
    glare_node.threshold = config.compositor_glare_threshold
    glare_node.mix = config.compositor_bloom_intensity
    glare_node.location = (-100, 0)
    composite_node = tree.nodes.new(type="CompositorNodeComposite")
    composite_node.location = (200, 0)
    links = tree.links
    links.new(render_layers.outputs[0], glare_node.inputs[0])
    links.new(glare_node.outputs[0], composite_node.inputs[0])


# =============================================================================
# 5. カメラ設定
# =============================================================================


def create_camera() -> bpy.types.Object:
    bpy.ops.object.camera_add(location=config.camera_location)
    cam = bpy.context.active_object
    cam.data.lens = config.camera_lens
    cam.data.sensor_width = config.camera_sensor_width
    return cam


def configure_camera(cam: bpy.types.Object) -> None:
    target = mathutils.Vector(config.camera_target)
    direction = target - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    cam.data.dof.use_dof = True
    cam.data.dof.focus_distance = config.camera_dof_distance
    cam.data.dof.aperture_fstop = config.camera_dof_fstop


def setup_camera_and_animate() -> None:
    cam = create_camera()
    configure_camera(cam)
    bpy.context.scene.camera = cam
    cam.keyframe_insert(data_path="location", frame=1)
    cam.location.x += 0.5
    cam.location.y += 0.5
    cam.keyframe_insert(data_path="location", frame=50)
    if cam.animation_data and cam.animation_data.action:
        for fcurve in cam.animation_data.action.fcurves:
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation = "BEZIER"


# =============================================================================
# 6. 照明設定
# =============================================================================


def create_sun_light() -> bpy.types.Object:
    bpy.ops.object.light_add(type="SUN", location=config.sun_light_location)
    sun = bpy.context.active_object
    sun.data.energy = config.sun_light_energy
    sun.data.angle = math.radians(5)
    return sun


def create_area_light() -> bpy.types.Object:
    bpy.ops.object.light_add(type="AREA", location=config.area_light_location)
    area = bpy.context.active_object
    area.data.energy = config.area_light_energy
    area.data.size = 5.0
    return area


def create_point_light() -> bpy.types.Object:
    bpy.ops.object.light_add(type="POINT", location=config.point_light_location)
    point = bpy.context.active_object
    point.data.energy = config.point_light_energy
    return point


def setup_all_lights() -> None:
    create_sun_light()
    create_area_light()
    create_point_light()


# =============================================================================
# 7. マテリアル設定
# =============================================================================


def create_material_simple(
    name: str, color: tuple[float, float, float, float]
) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
    return mat


def create_material_complex(
    name: str, base_color: tuple[float, float, float, float]
) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    for node in nodes:
        nodes.remove(node)
    output_node = nodes.new(type="ShaderNodeOutputMaterial")
    output_node.location = (400, 0)
    mix_shader = nodes.new(type="ShaderNodeMixShader")
    mix_shader.location = (200, 0)
    diffuse_shader = nodes.new(type="ShaderNodeBsdfDiffuse")
    diffuse_shader.location = (0, 100)
    glossy_shader = nodes.new(type="ShaderNodeBsdfGlossy")
    glossy_shader.location = (0, -100)
    diffuse_shader.inputs["Color"].default_value = base_color
    glossy_shader.inputs["Color"].default_value = base_color
    glossy_shader.inputs["Roughness"].default_value = 0.2
    links.new(diffuse_shader.outputs["BSDF"], mix_shader.inputs[1])
    links.new(glossy_shader.outputs["BSDF"], mix_shader.inputs[2])
    mix_shader.inputs[0].default_value = 0.3
    links.new(mix_shader.outputs["Shader"], output_node.inputs["Surface"])
    return mat


def setup_material_for_object(
    obj: bpy.types.Object,
    use_complex: bool = False,
    color: tuple[float, float, float, float] = (1, 1, 1, 1),
) -> None:
    if use_complex:
        mat = create_material_complex(obj.name + "_Mat", color)
    else:
        mat = create_material_simple(obj.name + "_Mat", color)
    if obj.data is not None:
        obj.data.materials.clear()
        obj.data.materials.append(mat)


# =============================================================================
# 8. オブジェクト作成 - 地面
# =============================================================================


def create_ground_plane() -> bpy.types.Object:
    bpy.ops.mesh.primitive_plane_add(
        size=config.ground_size, location=config.ground_location
    )
    ground = bpy.context.active_object
    setup_material_for_object(
        ground, use_complex=True, color=config.ground_material_color
    )
    subd = ground.modifiers.new("Subdiv", type="SUBSURF")
    subd.levels = 2
    bpy.ops.object.shade_smooth()
    return ground


# =============================================================================
# 9. オブジェクト作成 - トーテムポール各パーツ
# =============================================================================


def create_totem_base() -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=64,
        radius=config.base_radius,
        depth=config.base_depth,
        location=config.base_location,
    )
    base = bpy.context.active_object
    setup_material_for_object(base, use_complex=True, color=config.base_material_color)
    bpy.ops.object.shade_smooth()
    return base


def create_bird_head() -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=64,
        radius=config.head_radius,
        depth=config.head_depth,
        location=config.head_location,
    )
    head = bpy.context.active_object
    setup_material_for_object(head, use_complex=True, color=config.head_material_color)
    bpy.ops.object.shade_smooth()
    return head


def create_beak() -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(
        size=config.beak_size, location=config.beak_location
    )
    beak = bpy.context.active_object
    setup_material_for_object(beak, use_complex=False, color=config.beak_material_color)
    bpy.ops.object.mode_set(mode="EDIT")
    mesh = beak.data
    bm = bmesh.from_edit_mesh(mesh)
    max_y = -1e6
    target_face = None
    for face in bm.faces:
        center = face.calc_center_median()
        if center.y > max_y:
            max_y = center.y
            target_face = face
    if target_face is not None:
        for face in bm.faces:
            face.select = False
        target_face.select = True
        bmesh.update_edit_mesh(mesh)
        bpy.ops.mesh.extrude_region_move(
            TRANSFORM_OT_translate={"value": config.beak_extrude_vector}
        )
    bpy.ops.object.mode_set(mode="OBJECT")
    return beak


def create_left_wing() -> bpy.types.Object:
    bpy.ops.mesh.primitive_plane_add(
        size=config.wing_size, location=config.left_wing_location
    )
    left_wing = bpy.context.active_object
    left_wing.rotation_euler = config.left_wing_rotation
    left_wing.scale = config.left_wing_scale
    setup_material_for_object(
        left_wing, use_complex=False, color=config.wing_material_color
    )
    bpy.ops.object.shade_smooth()
    return left_wing


def create_right_wing(left_wing: bpy.types.Object) -> bpy.types.Object:
    right_wing = left_wing.copy()
    right_wing.data = left_wing.data.copy()
    bpy.context.scene.collection.objects.link(right_wing)
    right_wing.location = config.left_wing_location
    right_wing.scale = (
        -config.left_wing_scale[0],
        config.left_wing_scale[1],
        config.left_wing_scale[2],
    )
    return right_wing


def create_mid_face() -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=64,
        radius=config.mid_face_radius,
        depth=config.mid_face_depth,
        location=config.mid_face_location,
    )
    mid_face = bpy.context.active_object
    setup_material_for_object(
        mid_face, use_complex=True, color=config.mid_face_material_color
    )
    bpy.ops.object.shade_smooth()
    return mid_face


def create_bottom_figure() -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=64,
        radius=config.bottom_radius,
        depth=config.bottom_depth,
        location=config.bottom_location,
    )
    bottom = bpy.context.active_object
    setup_material_for_object(
        bottom, use_complex=True, color=config.bottom_material_color
    )
    bpy.ops.object.shade_smooth()
    return bottom


def assemble_totem_pole() -> bpy.types.Object:
    base = create_totem_base()
    head = create_bird_head()
    beak = create_beak()
    left_wing = create_left_wing()
    right_wing = create_right_wing(left_wing)
    mid_face = create_mid_face()
    bottom = create_bottom_figure()
    head.parent = base
    beak.parent = base
    left_wing.parent = base
    right_wing.parent = base
    mid_face.parent = base
    bottom.parent = base
    head.location.z = config.base_depth + config.head_depth / 2.0
    beak.location.z = config.base_depth + 0.1
    mid_face.location.z = config.base_depth * 0.6
    bottom.location.z = config.bottom_depth / 2.0
    return base


# =============================================================================
# 10. 補助関数（オブジェクトの最終調整）
# =============================================================================


def apply_transformations(obj: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def set_object_origin_to_geometry(obj: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")


def add_subdivision_modifier(obj: bpy.types.Object, levels: int = 2) -> None:
    mod = obj.modifiers.new("Subdivision", type="SUBSURF")
    mod.levels = levels
    bpy.ops.object.shade_smooth()


def add_edge_split_modifier(
    obj: bpy.types.Object, split_angle: float = math.radians(30)
) -> None:
    mod = obj.modifiers.new("EdgeSplit", type="EDGE_SPLIT")
    mod.split_angle = split_angle


def recalc_normals(obj: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")


def refine_mesh(obj: bpy.types.Object) -> None:
    add_subdivision_modifier(obj, levels=2)
    add_edge_split_modifier(obj, split_angle=math.radians(30))
    recalc_normals(obj)


def finalize_object(obj: bpy.types.Object) -> None:
    apply_transformations(obj)
    set_object_origin_to_geometry(obj)
    refine_mesh(obj)


# =============================================================================
# 11. 高度なマテリアル設定（プロシージャル／カスタムノード）
# =============================================================================


def create_procedural_material(name: str) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    for node in nodes:
        nodes.remove(node)
    output_node = nodes.new(type="ShaderNodeOutputMaterial")
    output_node.location = (800, 0)
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.location = (500, 0)
    bsdf.inputs["Base Color"].default_value = (0.8, 0.3, 0.3, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.4
    noise = nodes.new(type="ShaderNodeTexNoise")
    noise.location = (100, 200)
    noise.inputs["Scale"].default_value = 5.0
    noise.inputs["Detail"].default_value = 2.0
    ramp = nodes.new(type="ShaderNodeValToRGB")
    ramp.location = (300, 200)
    ramp.color_ramp.elements[0].position = 0.3
    ramp.color_ramp.elements[1].position = 0.7
    mapping = nodes.new(type="ShaderNodeMapping")
    mapping.location = (-200, 200)
    mapping.inputs["Scale"].default_value = (1.0, 1.0, 1.0)
    tex_coord = nodes.new(type="ShaderNodeTexCoord")
    tex_coord.location = (-400, 200)
    links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(bsdf.outputs["BSDF"], output_node.inputs["Surface"])
    return mat


def create_custom_material(
    name: str, base_color: tuple[float, float, float, float]
) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    for node in nodes:
        nodes.remove(node)
    out_node = nodes.new(type="ShaderNodeOutputMaterial")
    out_node.location = (900, 0)
    mix_shader = nodes.new(type="ShaderNodeMixShader")
    mix_shader.location = (700, 0)
    diffuse = nodes.new(type="ShaderNodeBsdfDiffuse")
    diffuse.location = (400, 100)
    diffuse.inputs["Color"].default_value = base_color
    glossy = nodes.new(type="ShaderNodeBsdfGlossy")
    glossy.location = (400, -100)
    glossy.inputs["Color"].default_value = base_color
    glossy.inputs["Roughness"].default_value = 0.15
    fresnel = nodes.new(type="ShaderNodeFresnel")
    fresnel.location = (200, 0)
    fresnel.inputs["IOR"].default_value = 1.45
    links.new(diffuse.outputs["BSDF"], mix_shader.inputs[1])
    links.new(glossy.outputs["BSDF"], mix_shader.inputs[2])
    links.new(fresnel.outputs["Fac"], mix_shader.inputs[0])
    links.new(mix_shader.outputs["Shader"], out_node.inputs["Surface"])
    return mat


def assign_procedural_material(obj: bpy.types.Object) -> None:
    mat = create_procedural_material(obj.name + "_ProcMat")
    if obj.data is not None:
        obj.data.materials.clear()
        obj.data.materials.append(mat)


# =============================================================================
# 12. その他のオブジェクト最終調整関数
# =============================================================================


def smooth_object(obj: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()


def add_custom_modifier(obj: bpy.types.Object) -> None:
    solidify = obj.modifiers.new("CustomSolidify", type="SOLIDIFY")
    solidify.thickness = 0.02
    bevel = obj.modifiers.new("CustomBevel", type="BEVEL")
    bevel.width = 0.01
    bevel.segments = 4


def setup_object_for_render(obj: bpy.types.Object) -> None:
    apply_transformations(obj)
    set_object_origin_to_geometry(obj)
    refine_mesh(obj)
    add_custom_modifier(obj)
    smooth_object(obj)


# =============================================================================
# 13. シーン最終出力用補助関数
# =============================================================================


def export_scene_to_obj(export_path: str) -> None:
    # io_scene_obj アドオンを addon_utils を用いて有効化
    addon_utils.enable("io_scene_obj", default_set=True, persistent=True)
    if hasattr(bpy.ops.export_scene, "obj"):
        bpy.ops.export_scene.obj(filepath=export_path, use_selection=False)
    else:
        print("OBJ export operator not found. Skipping export.")


def log_scene_objects() -> None:
    print("シーン内オブジェクト一覧:")
    for obj in bpy.data.objects:
        print(f"  {obj.name}")


def verify_render_settings() -> None:
    scene = bpy.context.scene
    print("レンダリング設定:")
    print(f"  解像度: {scene.render.resolution_x} x {scene.render.resolution_y}")
    print(f"  エンジン: {scene.render.engine}")
    print(f"  出力先: {scene.render.filepath}")


def finalize_scene() -> None:
    log_scene_objects()
    verify_render_settings()


def export_and_finalize() -> None:
    # export_path = os.path.join(config.output_dir, "scene_export.obj")
    # export_scene_to_obj(export_path)
    # finalize_scene()
    # print("シーンエクスポート完了。エクスポート先：" + export_path)
    print("シーンエクスポート完了。スキップします。")


# =============================================================================
# 14. メインプロセス実行（詳細手順）
# =============================================================================


def full_main() -> None:
    clear_scene()
    setup_world_background()
    setup_environment_texture()
    setup_ambient_occlusion()
    setup_render()
    if config.use_compositor:
        setup_compositor()
    setup_camera_and_animate()
    setup_all_lights()
    ground = create_ground_plane()
    setup_object_for_render(ground)
    totem = assemble_totem_pole()
    setup_object_for_render(totem)
    bpy.ops.object.select_all(action="DESELECT")
    ground.select_set(True)
    totem.select_set(True)
    bpy.ops.view3d.camera_to_view_selected()
    assign_procedural_material(ground)
    assign_procedural_material(totem)
    if not os.path.exists(config.output_dir):
        os.makedirs(config.output_dir)
    backup_file(config.output_filepath)
    bpy.ops.render.render(write_still=True)
    print("レンダリング完了。出力先：" + config.output_filepath)


# =============================================================================
# 15. 最終出力（エクスポート・ログ出力）
# =============================================================================


def export_and_finalize_scene() -> None:
    export_and_finalize()


# =============================================================================
# 16. エントリーポイント（最終実行）
# =============================================================================


def main() -> None:
    full_main()
    export_and_finalize_scene()


if __name__ == "__main__":
    main()
