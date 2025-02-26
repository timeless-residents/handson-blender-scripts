#!/usr/bin/env python3
"""
handson_024.py

Blender 4.3.2 用バックグラウンド実行スクリプト。
- 円柱にリングカットを入れ、各リングを上下にスライドして凹凸パターンを作成
- カメラを対象中央に配置し、明るめのライティング・マテリアルを設定してレンダリング
- 出力は output/ フォルダへ保存。既存ファイルはバックアップします。
"""

import bpy
import bmesh
import math
import os
import shutil
import datetime
import mathutils


def main() -> None:
    """
    メイン処理。
    シーン初期化、円柱作成・編集、マテリアル設定、カメラ・ライト配置、ワールド設定、
    レンダリング・出力ファイルのバックアップを実施する。
    """
    print("処理を開始します...")
    # シーン内の全オブジェクトを削除
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    print("環境設定完了")

    # 円柱の作成 (32頂点, 半径1, 深さ2)
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=32,
        radius=1,
        depth=2,
        end_fill_type='NGON',
        location=(0, 0, 0)
    )
    cylinder = bpy.context.active_object
    bpy.context.view_layer.objects.active = cylinder
    print("円柱の作成完了")

    # 編集モードに切替え、bmeshでリングカット用に側面のみサブディビジョン
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(cylinder.data)
    side_faces = [face for face in bm.faces if abs(face.normal.z) < 0.1]
    for face in bm.faces:
        face.select = False
    for face in side_faces:
        face.select = True
    bpy.ops.mesh.subdivide(number_cuts=3, smoothness=0)
    bmesh.update_edit_mesh(cylinder.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    print("リングカット追加完了")

    # 各頂点にサイン波で凹凸パターンを付与（上下スライド）
    amplitude: float = 0.2
    height: float = 2.0
    z_bottom: float = -1.0
    z_top: float = 1.0
    for vertex in cylinder.data.vertices:
        if abs(vertex.co.z - z_top) < 1e-3 or abs(vertex.co.z - z_bottom) < 1e-3:
            continue
        factor: float = (vertex.co.z - z_bottom) / height
        displacement: float = amplitude * math.sin(math.pi * factor)
        vertex.co.z += displacement
    print("凹凸パターン作成完了")

    # マテリアルの設定 (明るめにして形状が見やすいようにする)
    mat = bpy.data.materials.new(name="BrightMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    principled = nodes.get("Principled BSDF")
    if principled:
        # ベースカラーを薄いグレーに (R=G=B=0.8)
        principled.inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1.0)
        # 少しだけ Roughness を下げてハイライトを出やすくする (0.4 程度)
        principled.inputs["Roughness"].default_value = 0.4

    # 円柱にマテリアルを割り当て
    if len(cylinder.data.materials) == 0:
        cylinder.data.materials.append(mat)
    else:
        cylinder.data.materials[0] = mat
    print("マテリアル設定完了")

    # カメラの配置: (0, -4, 1) から原点を注視
    bpy.ops.object.camera_add(location=(0, -4, 1))
    camera = bpy.context.active_object
    direction = (0 - camera.location.x, 0 - camera.location.y, 0 - camera.location.z)
    camera.rotation_euler = direction_to_euler(direction)
    bpy.context.scene.camera = camera  # アクティブカメラに設定
    print("カメラの配置完了")

    # サンライトの追加（照明を強めに設定）
    bpy.ops.object.light_add(type='SUN', location=(0, 0, 4))
    light = bpy.context.active_object
    light.data.energy = 5.0  # 強度を上げる
    print("ライト設定完了")

    # ワールド(背景)の設定: 少し明るめの背景に
    world = bpy.data.worlds["World"]
    world.use_nodes = True
    bg_node = world.node_tree.nodes["Background"]
    bg_node.inputs[0].default_value = (0.7, 0.7, 0.7, 1.0)  # やや明るいグレー
    bg_node.inputs[1].default_value = 1.0  # 強度
    print("ワールド背景設定完了")

    # レンダリング設定
    scene = bpy.context.scene
    # Blender 4.3.2 では 'BLENDER_EEVEE' がないため 'BLENDER_EEVEE_NEXT' を利用
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
    scene.render.resolution_x = 800
    scene.render.resolution_y = 600

    # カラーマネジメント: 露出を上げたい場合はここで設定 (例: 1.0)
    scene.view_settings.exposure = 0.0

    # 出力先
    scene.render.filepath = get_output_filepath("cylinder_pattern.png")

    # レンダリング実行
    bpy.ops.render.render(write_still=True)
    print(f"レンダリング完了: {scene.render.filepath}")
    print("全ての処理が完了しました")


def direction_to_euler(direction: tuple) -> mathutils.Euler:
    """
    カメラが -Z 軸方向を注視軸とする前提で、指定方向へ向く回転角 (Euler) を返す。
    :param direction: 注視先へのベクトル (x, y, z)
    :return: カメラの回転 (Euler角)
    """
    vec: mathutils.Vector = mathutils.Vector(direction).normalized()
    default: mathutils.Vector = mathutils.Vector((0, 0, -1))
    quat: mathutils.Quaternion = default.rotation_difference(vec)
    return quat.to_euler()


def get_output_filepath(filename: str) -> str:
    """
    出力先フォルダ output/ 内の filepath を生成。
    同名ファイルが存在する場合はタイムスタンプ付きでバックアップします。
    :param filename: 出力ファイル名
    :return: 出力先の完全なファイルパス
    """
    output_dir: str = os.path.join(os.getcwd(), "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    filepath: str = os.path.join(output_dir, filename)
    if os.path.exists(filepath):
        timestamp: str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filepath: str = os.path.join(
            output_dir,
            f"cylinder_pattern_{timestamp}.png"
        )
        shutil.move(filepath, backup_filepath)
        print("既存ファイルを退避しました: " + backup_filepath)

    return filepath


if __name__ == "__main__":
    main()
