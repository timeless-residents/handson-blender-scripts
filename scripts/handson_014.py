import bpy
import random
import math
import os
from datetime import datetime
import bmesh # type: ignore
from mathutils import Vector, noise # type: ignore


def clear_scene():
    """シーンをクリアする"""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def create_camo_colors():
    """迷彩パターンの色を定義"""
    return [
        (0.22, 0.25, 0.15, 1.0),  # ダークオリーブ
        (0.35, 0.32, 0.18, 1.0),  # カーキ
        (0.15, 0.17, 0.12, 1.0),  # ディープグリーン
        (0.28, 0.24, 0.16, 1.0),  # ダークブラウン
    ]


def create_base_mesh(mesh_type="CUBE"):
    """ベースとなるメッシュを作成"""
    if mesh_type == "CUBE":
        bpy.ops.mesh.primitive_cube_add(size=4.0)
    elif mesh_type == "CYLINDER":
        bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=2.0)

    obj = bpy.context.active_object

    # サブディビジョンモディファイアを追加して細分化
    subdiv = obj.modifiers.new(name="Subdivision", type="SUBSURF")
    subdiv.levels = 8
    subdiv.render_levels = 8

    # モディファイアを適用
    bpy.ops.object.shade_smooth()
    bpy.ops.object.modifier_apply(modifier="Subdivision")

    return obj


def generate_noise_texture(scale=1.5):
    """ノイズテクスチャを生成"""

    def noise_at(x, y, z):
        # 3つのスケールの異なるノイズを合成
        vec1 = Vector((x * scale, y * scale, z * scale))
        vec2 = Vector((x * scale * 2, y * scale * 2, z * scale * 2))
        vec3 = Vector((x * scale * 4, y * scale * 4, z * scale * 4))

        n1 = noise.noise(vec1)  # 基本パターン
        n2 = noise.noise(vec2) * 0.5  # 中間的な詳細
        n3 = noise.noise(vec3) * 0.25  # 細かい詳細

        return (n1 + n2 + n3) / 1.5  # スケーリング調整

    return noise_at


def apply_vertex_paint(obj, colors):
    """頂点カラーを適用"""
    mesh = obj.data
    if not mesh.vertex_colors:
        mesh.vertex_colors.new()

    color_layer = mesh.vertex_colors.active
    noise_func = generate_noise_texture()

    # BMeshを使用して頂点の位置情報にアクセス
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()

    # 各頂点に色を適用
    for poly in mesh.polygons:
        for idx, loop_idx in enumerate(poly.loop_indices):
            vertex_idx = mesh.loops[loop_idx].vertex_index
            vertex = bm.verts[vertex_idx]

            # ノイズ値に基づいて色を選択
            noise_val = noise_func(vertex.co.x, vertex.co.y, vertex.co.z)
            color_idx = int((noise_val + 1) * len(colors) / 2) % len(colors)

            # 色をわずかにランダム化
            color = list(colors[color_idx])
            for i in range(3):
                color[i] += random.uniform(-0.05, 0.05)
                color[i] = max(0, min(1, color[i]))

            color_layer.data[loop_idx].color = color

    bm.free()


def setup_material(obj):
    """マテリアルをセットアップ"""
    mat = bpy.data.materials.new(name="CamoMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()

    # 頂点カラーノードを追加
    vertex_color = nodes.new("ShaderNodeVertexColor")
    vertex_color.layer_name = obj.data.vertex_colors.active.name

    # プリンシプルBSDFを追加
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.inputs["Roughness"].default_value = 0.7
    principled.inputs["Metallic"].default_value = 0.1

    # ノードを接続
    mat.node_tree.links.new(
        vertex_color.outputs["Color"], principled.inputs["Base Color"]
    )
    mat.node_tree.links.new(
        principled.outputs["BSDF"],
        nodes.new("ShaderNodeOutputMaterial").inputs["Surface"],
    )

    # マテリアルを適用
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)


def setup_lighting():
    """ライティングをセットアップ"""
    # HDRIライトを模したワールドライティング
    world = bpy.context.scene.world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    nodes.clear()

    # 背景ノードを追加（明るめのグレー）
    bg = nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = (0.8, 0.8, 0.8, 1.0)
    bg.inputs["Strength"].default_value = 0.5

    world.node_tree.links.new(
        bg.outputs["Background"], nodes.new("ShaderNodeOutputWorld").inputs["Surface"]
    )

    # キーライト（メイン照明）
    bpy.ops.object.light_add(type="AREA", location=(5, -5, 5))
    key_light = bpy.context.active_object
    key_light.data.energy = 400
    key_light.data.size = 5

    # フィルライト（影を柔らかく）
    bpy.ops.object.light_add(type="AREA", location=(-4, -2, 3))
    fill_light = bpy.context.active_object
    fill_light.data.energy = 200
    fill_light.data.size = 3

    # リムライト（輪郭を強調）
    bpy.ops.object.light_add(type="AREA", location=(0, 5, 2))
    rim_light = bpy.context.active_object
    rim_light.data.energy = 150
    rim_light.data.size = 2


def setup_camera():
    """カメラをセットアップ"""
    bpy.ops.object.camera_add(location=(5, -5, 4))
    camera = bpy.context.active_object
    camera.rotation_euler = (math.radians(60), 0, math.radians(45))
    bpy.context.scene.camera = camera


def setup_render():
    """レンダリング設定"""
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 64
    scene.render.resolution_x = 640
    scene.render.resolution_y = 480

    # デノイジングを有効化
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"

    # アダプティブサンプリングを有効化
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.01


def render_output():
    """レンダリング出力を実行"""
    scene = bpy.context.scene

    # 出力ディレクトリの作成
    output_dir = "//output"
    if not os.path.exists(bpy.path.abspath(output_dir)):
        os.makedirs(bpy.path.abspath(output_dir))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    scene.render.filepath = f"{output_dir}//camo_mesh_{timestamp}.png"

    # レンダリング実行
    bpy.ops.render.render(write_still=True)


def main():
    """メイン実行関数"""
    try:
        print("\n=== 迷彩パターン生成開始 ===")

        # シーンをクリア
        clear_scene()

        # メッシュを作成
        obj = create_base_mesh(mesh_type="CUBE")

        # 迷彩パターンを適用
        colors = create_camo_colors()
        apply_vertex_paint(obj, colors)

        # マテリアルとライティングをセットアップ
        setup_material(obj)
        setup_lighting()
        setup_camera()

        # レンダリング設定と出力
        setup_render()
        render_output()

        print("\n処理が完了しました。")
        print(f"出力ディレクトリ: {bpy.path.abspath('//output')}")
    except Exception as e:
        print(f"\nエラーが発生しました: {str(e)}")
        raise


if __name__ == "__main__":
    main()
