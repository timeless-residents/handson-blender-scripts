#!/usr/bin/env python3
"""
このスクリプトは、Blender上で以下の実験を行います:
- シーンを初期化し、床、キューブ、カメラ、スポットライトを作成
- スポットライトを「狙い撃ちライティング」用に、常にキューブを向くようにTrack Toコンストレイントを設定
- スポットライトの位置をアニメーション（開始～終了約3秒）で変化させる
- シーンをレンダリングし、output/フォルダ内にMP4動画として出力
- 出力先に同名ファイルが存在する場合は、タイムスタンプ付きでバックアップ

Usage:
    blender --background --python script.py
"""

import bpy
import os
import shutil
import datetime


def main():
    """メイン処理"""
    # シーン内の全オブジェクトを削除
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # 床 (Plane) を追加
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
    floor = bpy.context.active_object
    floor.name = "Floor"

    # キューブを追加（床上に配置）
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.5))
    cube = bpy.context.active_object
    cube.name = "Cube"

    # カメラを追加
    bpy.ops.object.camera_add(location=(3, -3, 3), rotation=(1.1, 0, 0.785398))
    camera = bpy.context.active_object
    camera.name = "Camera"
    bpy.context.scene.camera = camera

    # スポットライトを追加
    bpy.ops.object.light_add(type='SPOT', location=(0, -3, 3))
    light = bpy.context.active_object
    light.name = "Spotlight"
    light.data.energy = 1000
    light.data.spot_size = 0.785398  # 45° (ラジアン)
    light.data.use_shadow = True

    # スポットライトにTrack Toコンストレイントを設定し、常にキューブを向くようにする
    track_constraint = light.constraints.new(type='TRACK_TO')
    track_constraint.target = cube
    track_constraint.track_axis = 'TRACK_NEGATIVE_Z'
    track_constraint.up_axis = 'UP_Y'

    # シーンのフレーム設定（約3秒：24fpsの場合1～72フレーム）
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 72

    # スポットライトの位置アニメーション
    # フレーム1: 初期位置 (0, -3, 3)
    light.location = (0, -3, 3)
    light.keyframe_insert(data_path="location", frame=1)

    # フレーム36: 中間位置 (3, 0, 3)
    light.location = (3, 0, 3)
    light.keyframe_insert(data_path="location", frame=36)

    # フレーム72: 終了位置 (0, 3, 3)
    light.location = (0, 3, 3)
    light.keyframe_insert(data_path="location", frame=72)

    # 出力先フォルダ (output/) を作成（存在しない場合）
    output_dir = os.path.join(os.getcwd(), "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 出力ファイルパスを設定
    output_file = os.path.join(output_dir, "handson_018.mp4")
    if os.path.exists(output_file):
        # 既存ファイルがある場合は、タイムスタンプ付きで退避（リネーム）する
        base, ext = os.path.splitext(output_file)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{base}_{timestamp}{ext}"
        shutil.move(output_file, backup_file)

    # レンダリング設定
    render = scene.render
    render.image_settings.file_format = 'FFMPEG'
    render.ffmpeg.format = 'MPEG4'
    render.ffmpeg.codec = 'H264'
    render.ffmpeg.constant_rate_factor = 'HIGH'
    render.resolution_x = 1280
    render.resolution_y = 720
    render.fps = 24
    render.filepath = output_file

    # アニメーションレンダリング実行
    bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
