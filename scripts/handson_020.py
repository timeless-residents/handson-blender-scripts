#!/usr/bin/env python3
"""
Blender 4.0.2 (M2 Mac Studio) 用のバックグラウンドレンダリングスクリプトです。

要件:
- 開始から終了まで概ね3秒、最長10秒を目標とする
- レンダリング工程を含み、結果を output/ フォルダに出力する
- 同一ファイルが存在する場合はバックアップしてから新規作成する
- bpy ライブラリを利用して実装する
- カメラは低い位置に配置し、見上げる構図でオブジェクトを巨大に見せる
- 照明・露出・マテリアルを調整して暗くなりすぎるのを防ぐ
"""

import bpy
import os
import datetime


def clear_scene() -> None:
    """
    現在のシーン内の全オブジェクトを削除します。
    """
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def backup_existing_file(filepath: str) -> None:
    """
    指定されたファイルが存在する場合、タイムスタンプ付きでリネーム（退避）します。

    Args:
        filepath: 退避対象のファイルパス
    """
    if os.path.exists(filepath):
        base, ext = os.path.splitext(filepath)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filepath = f"{base}_backup_{timestamp}{ext}"
        os.rename(filepath, backup_filepath)


def setup_scene() -> None:
    """
    シーンにSuzanneオブジェクト、カメラ、ライトを追加し、
    カメラがオブジェクトを注視するように設定します。
    さらに、明るいマテリアルやライトを追加し、暗くなりすぎないように調整します。
    """
    # Suzanne（モンキー）オブジェクトを追加し、サイズを拡大して巨大に見せる
    bpy.ops.mesh.primitive_monkey_add(size=1.0, location=(0, 1, 0))
    monkey = bpy.context.active_object
    monkey.scale = (2, 2, 2)

    # カメラを低い位置に追加（オブジェクトより下に配置）
    camera_location = (0, -2, -1)
    bpy.ops.object.camera_add(location=camera_location)
    camera = bpy.context.active_object

    # カメラが常にモンキーを注視するよう、トラック制約を設定
    track_constraint = camera.constraints.new(type="TRACK_TO")
    track_constraint.target = monkey
    track_constraint.track_axis = "TRACK_NEGATIVE_Z"
    track_constraint.up_axis = "UP_Y"

    # 照明としてサンライトを上部に追加し、強度を上げる
    bpy.ops.object.light_add(type="SUN", location=(0, 0, 10))
    sun_light = bpy.context.active_object
    sun_light.data.energy = 5.0  # シーンが暗い場合はさらに上げてもOK

    # 追加のエリアライトを正面に配置して、モンキーの形状を分かりやすくする
    bpy.ops.object.light_add(type="AREA", location=(0, -1, 1))
    area_light = bpy.context.active_object
    area_light.data.energy = 50.0
    area_light.data.size = 2.0

    # シーンのアクティブカメラとして設定
    bpy.context.scene.camera = camera

    # モンキーに明るめのマテリアルを付与
    bright_mat = bpy.data.materials.new(name="BrightMaterial")
    bright_mat.diffuse_color = (1.0, 0.8, 0.2, 1.0)  # オレンジ系で少し明るい色
    monkey.data.materials.append(bright_mat)

    # カラーマネジメントを調整（露出を上げ、AgX - High Contrast を設定）
    bpy.context.scene.view_settings.exposure = 1.0
    # ここを "AgX - High Contrast" に変更
    bpy.context.scene.view_settings.look = "AgX - High Contrast"


def setup_render(output_filepath: str) -> None:
    """
    レンダリング設定を行います。

    Args:
        output_filepath: レンダリング結果の出力先ファイルパス
    """
    scene = bpy.context.scene
    # 高速レンダリングのため Eevee を使用
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = output_filepath
    # 解像度は高速レンダリングを考慮して控えめに設定
    scene.render.resolution_x = 800
    scene.render.resolution_y = 600
    scene.render.resolution_percentage = 100


def render_scene() -> None:
    """
    シーンをレンダリングし、結果をファイルに書き出します。
    """
    bpy.ops.render.render(write_still=True)


def main() -> None:
    """
    メイン処理:
    - シーンの初期化、オブジェクト配置
    - 出力先ディレクトリの作成と既存ファイルの退避
    - レンダリング実行
    """
    clear_scene()
    setup_scene()

    # 出力先ディレクトリ（output/）のパスを設定
    output_dir = os.path.join(os.getcwd(), "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_file = os.path.join(output_dir, "render.png")
    backup_existing_file(output_file)
    setup_render(output_file)
    render_scene()


if __name__ == "__main__":
    main()
