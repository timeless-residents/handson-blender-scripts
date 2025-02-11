import math
import random

import bpy


def setup_camera():
    # カメラを追加
    bpy.ops.object.camera_add(location=(10, -10, 10))
    camera = bpy.context.active_object
    camera.rotation_euler = (math.radians(60), 0, math.radians(45))

    # このカメラをシーンのアクティブカメラとして設定
    bpy.context.scene.camera = camera
    return camera


def setup_light():
    # サン（太陽光）を追加
    bpy.ops.object.light_add(type="SUN", location=(5, 5, 10))
    sun = bpy.context.active_object
    sun.data.energy = 5.0  # 光の強さを設定

    # エリアライトを追加して補助光として使用
    bpy.ops.object.light_add(type="AREA", location=(-5, -5, 5))
    area = bpy.context.active_object
    area.data.energy = 300.0  # エリアライトの強さを設定
    return sun, area


def main():
    # Blenderの初期化（既存のオブジェクトを削除）
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    # カメラとライトのセットアップ
    camera = setup_camera()
    sun, area = setup_light()

    # キューブを5個生成
    for i in range(5):
        # ランダムな位置を生成
        x = random.uniform(-5, 5)
        y = random.uniform(-5, 5)
        z = random.uniform(0, 5)

        # キューブを追加
        bpy.ops.mesh.primitive_cube_add(location=(x, y, z))

        # 現在のキューブの名前を設定
        current_cube = bpy.context.active_object
        current_cube.name = f"RandomCube_{i+1}"

        # ランダムなスケールを設定
        scale = random.uniform(0.5, 2.0)
        current_cube.scale = (scale, scale, scale)

    # レンダリング設定
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.context.scene.render.filepath = ".//output//handson_001.png"

    # レンダリングエンジンをCyclesに設定（より良い品質のため）
    bpy.context.scene.render.engine = "CYCLES"
    bpy.context.scene.cycles.samples = 128  # レンダリングサンプル数

    # レンダリングを実行
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    try:
        main()
        print("ランダムな位置にキューブを生成し、レンダリングが完了しました。")
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
