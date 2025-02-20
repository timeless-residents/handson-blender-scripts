#!/usr/bin/env python
"""
Blender 4.0.2 用スクリプト

- バンプマップを用いて波紋を表現した「水面」と、バスボム風の球体を配置
- 水面は粗さを下げて反射を強めにし、疑似的な「水らしさ」を演出
- 球体はスムーズシェード＋パステル調でバスボム感を演出
- レンダリング結果を output/render.png に保存（同名ファイルはタイムスタンプ付きで退避）
- Eevee で短時間レンダリング
"""

import bpy
import os
import shutil
from datetime import datetime


def cleanup_scene() -> None:
    """シーン内の全オブジェクトを削除する"""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def shade_smooth(obj: bpy.types.Object) -> None:
    """指定オブジェクトをスムーズシェード化"""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()


def create_water_plane() -> bpy.types.Object:
    """バンプマップ付きの水面Planeを作成する"""
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
    plane = bpy.context.active_object
    plane.name = "WaterPlane"

    # スムーズシェードを適用
    shade_smooth(plane)

    # 新規マテリアル作成
    mat = bpy.data.materials.new(name="WaterMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # 既定ノードを全削除
    for node in list(nodes):
        nodes.remove(node)

    # 必要なノードを作成
    output_node = nodes.new(type="ShaderNodeOutputMaterial")
    output_node.location = (400, 0)

    bsdf_node = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf_node.location = (0, 0)
    bsdf_node.inputs["Base Color"].default_value = (0.0, 0.3, 0.8, 1)
    # 粗さを小さめにして反射を強調
    bsdf_node.inputs["Roughness"].default_value = 0.05

    # もし "Specular" 入力が存在するなら値を設定する
    if "Specular" in bsdf_node.inputs:
        bsdf_node.inputs["Specular"].default_value = 0.8

    # ノイズテクスチャで細かな波紋を表現
    noise_node = nodes.new(type="ShaderNodeTexNoise")
    noise_node.location = (-400, 100)
    noise_node.inputs["Scale"].default_value = 50.0
    noise_node.inputs["Detail"].default_value = 8.0
    noise_node.inputs["Distortion"].default_value = 0.0

    bump_node = nodes.new(type="ShaderNodeBump")
    bump_node.location = (-200, 0)
    bump_node.inputs["Strength"].default_value = 0.15

    # ノード接続
    links.new(noise_node.outputs["Fac"], bump_node.inputs["Height"])
    links.new(bump_node.outputs["Normal"], bsdf_node.inputs["Normal"])
    links.new(bsdf_node.outputs["BSDF"], output_node.inputs["Surface"])

    plane.data.materials.append(mat)
    return plane


def create_sphere() -> bpy.types.Object:
    """水面上に配置する球体を作成する"""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0, 0, 1.0))
    sphere = bpy.context.active_object
    sphere.name = "BathBombSphere"

    # スムーズシェードを適用
    shade_smooth(sphere)

    # 球体用のシンプルなマテリアル作成
    mat = bpy.data.materials.new(name="SphereMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf is not None:
        # 少しパステル調のピンク系にしてバスボム感を演出
        bsdf.inputs["Base Color"].default_value = (1.0, 0.6, 0.8, 1)
        bsdf.inputs["Metallic"].default_value = 0.0
        bsdf.inputs["Roughness"].default_value = 0.3
    sphere.data.materials.append(mat)
    return sphere


def create_camera() -> bpy.types.Object:
    """シーンを撮影するカメラを作成する"""
    bpy.ops.object.camera_add(location=(5, -5, 5), rotation=(1.1, 0, 0.7854))
    camera = bpy.context.active_object
    camera.name = "Camera"
    bpy.context.scene.camera = camera
    return camera


def create_light() -> bpy.types.Object:
    """シーン照明用のSunランプを作成する"""
    bpy.ops.object.light_add(type="SUN", location=(0, 0, 10))
    light = bpy.context.active_object
    # 少し強めに
    light.data.energy = 5.0
    # 角度を少し大きめにして影を柔らかく
    light.data.angle = 15.0
    return light


def setup_render(output_filepath: str) -> None:
    """レンダリング設定を行い、出力先を指定する"""
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.render.resolution_x = 640
    scene.render.resolution_y = 480
    scene.render.resolution_percentage = 100
    scene.render.filepath = output_filepath

    # 背景を少し暗めのグレーに
    scene.world.color = (0.05, 0.05, 0.05)


def backup_existing_file(filepath: str) -> None:
    """出力先ファイルが存在する場合、タイムスタンプ付きで退避する"""
    if os.path.exists(filepath):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_filepath = f"{filepath}.{timestamp}.bak"
        shutil.move(filepath, backup_filepath)


def main() -> None:
    """メイン処理"""
    output_folder = "output"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    output_filepath = os.path.join(output_folder, "render.png")

    backup_existing_file(output_filepath)

    cleanup_scene()
    create_water_plane()
    create_sphere()
    create_camera()
    create_light()
    setup_render(output_filepath)

    # レンダリング実行（write_still=Trueで画像を保存）
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
