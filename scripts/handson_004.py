import bpy
import math
import random

def clear_scene():
    """シーン内の全オブジェクトを削除"""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

def assign_random_color_material(obj):
    """
    指定オブジェクトにランダムなBase Colorを持つマテリアルを適用する。
    ※メッシュオブジェクト向け。ライトやカメラは対象外です。
    """
    if not hasattr(obj.data, "materials"):
        return
    mat = bpy.data.materials.new(name=f"{obj.name}_Mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (
            random.random(), random.random(), random.random(), 1.0)
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

def assign_ground_material(obj):
    """
    床用のマテリアルを設定します。
    グレーではなく、落ち着いたグリーン系（例：草や土）に設定しています。
    """
    if not hasattr(obj.data, "materials"):
        return
    mat = bpy.data.materials.new(name=f"{obj.name}_Mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        # 例：グリーン系の色 (RGB: 0.2, 0.5, 0.2)
        bsdf.inputs["Base Color"].default_value = (0.2, 0.5, 0.2, 1.0)
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

def assign_particle_instance_material(obj):
    """
    パーティクルインスタンス用のマテリアルを設定します。
    Particle Info ノードと ColorRamp を利用して、各パーティクルに対して
    異なる色を生成します（例：赤～緑～青のグラデーション）。
    """
    if not hasattr(obj.data, "materials"):
        return
    mat = bpy.data.materials.new(name=f"{obj.name}_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # 既存のノードをすべて削除
    for node in nodes:
        nodes.remove(node)

    # Material Output ノード
    output_node = nodes.new(type="ShaderNodeOutputMaterial")
    output_node.location = (400, 0)

    # Principled BSDF ノード
    principled_node = nodes.new(type="ShaderNodeBsdfPrincipled")
    principled_node.location = (200, 0)

    # Particle Info ノード
    particle_info = nodes.new(type="ShaderNodeParticleInfo")
    particle_info.location = (0, 0)

    # ColorRamp ノード
    color_ramp = nodes.new(type="ShaderNodeValToRGB")
    color_ramp.location = (100, 0)
    # 左端を赤、右端を青、中央を緑に設定
    color_ramp.color_ramp.elements[0].color = (1, 0, 0, 1)    # 赤
    color_ramp.color_ramp.elements[1].color = (0, 0, 1, 1)    # 青
    mid_elem = color_ramp.color_ramp.elements.new(0.5)
    mid_elem.color = (0, 1, 0, 1)                             # 緑

    # ノード接続
    links.new(particle_info.outputs["Random"], color_ramp.inputs["Fac"])
    links.new(color_ramp.outputs["Color"], principled_node.inputs["Base Color"])
    links.new(principled_node.outputs["BSDF"], output_node.inputs["Surface"])

    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

def setup_camera():
    """カメラを配置してシーンのアクティブカメラに設定"""
    bpy.ops.object.camera_add(location=(10, -10, 10))
    camera = bpy.context.active_object
    camera.rotation_euler = (math.radians(60), 0, math.radians(45))
    bpy.context.scene.camera = camera
    return camera

def setup_light():
    """サンライトを追加してシーンを照らす"""
    bpy.ops.object.light_add(type="SUN", location=(10, 10, 15))
    sun = bpy.context.active_object
    sun.data.energy = 3.0
    return sun

def setup_world():
    """ワールド背景の色を設定して、グレーではなく空をイメージしたブルー系に変更"""
    world = bpy.context.scene.world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        # 例：空色（RGB: 0.1, 0.4, 0.7）
        bg.inputs[0].default_value = (0.1, 0.4, 0.7, 1.0)
        bg.inputs[1].default_value = 1.0

def create_ground():
    """床用の平面を作成し、固定のグリーン系マテリアルを適用"""
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "Ground"
    assign_ground_material(ground)
    return ground

def create_emitter():
    """
    パーティクルを発生させるエミッタ（小さな平面）を作成し、
    エミッタにパーティクルシステムを設定します。
    各パーティクルは、Particle Instance 用の大きめの小球オブジェクトをインスタンスとして表示します。
    """
    # エミッタ作成
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0.1))
    emitter = bpy.context.active_object
    emitter.name = "Emitter"
    assign_random_color_material(emitter)

    # エミッタにパーティクルシステムを追加
    ps_mod = emitter.modifiers.new("ParticleSystem", type='PARTICLE_SYSTEM')
    psys = ps_mod.particle_system
    p_settings = psys.settings

    # パーティクル設定（フォンタン効果）
    p_settings.count = 500            # 発生するパーティクル数
    p_settings.frame_start = 1        # 発生開始フレーム
    p_settings.frame_end = 1          # 一括発生
    p_settings.lifetime = 50          # パーティクルの寿命（フレーム）
    p_settings.emit_from = 'FACE'
    p_settings.physics_type = 'NEWTON'
    p_settings.normal_factor = 5.0    # 上方向への初速度
    p_settings.factor_random = 0.5    # ランダム性を付与
    p_settings.use_dynamic_rotation = True
    p_settings.rotation_mode = 'GLOB_X'

    # パーティクル表示用のインスタンスオブジェクト（大きめの小球）作成
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(100, 100, 100))
    particle_obj = bpy.context.active_object
    particle_obj.name = "ParticleInstance"
    assign_particle_instance_material(particle_obj)
    
    # パーティクルレンダリング設定：オブジェクトとしてインスタンス化
    p_settings.render_type = 'OBJECT'
    p_settings.instance_object = particle_obj

    return emitter, particle_obj

def setup_scene_for_speed_and_color():
    """レンダリング設定を調整して、カラフルかつ高速に出力"""
    scene = bpy.context.scene
    # 高速レンダリングのため Eevee を利用（必要に応じて Cycles への変更も可）
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_percentage = 100
    # Simplify 設定で不要な負荷を軽減
    scene.render.use_simplify = True
    scene.render.simplify_subdivision = 1
    scene.render.simplify_child_particles = 0

    # 画像出力設定（RGBA で出力）
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    # カラーマネージメントの設定例
    scene.view_settings.view_transform = 'Filmic'
    scene.view_settings.look = 'None'

def main():
    # シーン初期化と各要素の配置
    clear_scene()
    setup_camera()
    setup_light()
    setup_world()
    create_ground()
    create_emitter()

    # アニメーションのフレーム設定
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end   = 50

    # レンダリング設定（カラフルな出力と高速レンダリングのため）
    setup_scene_for_speed_and_color()
    
    # 出力先パス（連番PNGとして保存）
    scene.render.filepath = ".//output//particle_fountain_"
    
    # アニメーションレンダリング実行
    bpy.ops.render.render(animation=True)
    print("アニメーションレンダリングが完了しました。")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"エラーが発生しました: {e}")
