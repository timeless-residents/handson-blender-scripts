import bpy
import math
import mathutils
import random
import os

# グローバル変数：対象オブジェクト（高詳細モデル）と生成したLODオブジェクトのリスト
TARGET = None
# LOD_OBJECTS は (lod_obj, threshold_distance) のタプルのリスト
LOD_OBJECTS = []

def clear_scene():
    """シーン内の全オブジェクトを削除"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def setup_camera_and_light():
    """カメラとサンライトを配置する"""
    bpy.ops.object.camera_add(location=(10, -10, 10))
    cam = bpy.context.active_object
    cam.rotation_euler = (math.radians(60), 0, math.radians(45))
    bpy.context.scene.camera = cam

    bpy.ops.object.light_add(type='SUN', location=(10, 10, 10))
    light = bpy.context.active_object
    light.data.energy = 3.0

def duplicate_with_decimation(original, ratio):
    """
    対象オブジェクトを複製し、Decimate モディファイアを適用して
    指定の比率 (ratio) でポリゴン数を削減したオブジェクトを返す。
    """
    bpy.ops.object.select_all(action='DESELECT')
    original.select_set(True)
    bpy.context.view_layer.objects.active = original
    bpy.ops.object.duplicate()
    dup_obj = bpy.context.active_object
    dup_obj.name = f"{original.name}_LOD_{int(ratio*100)}"

    # Decimate モディファイアの追加と適用
    mod = dup_obj.modifiers.new(name="Decimate", type='DECIMATE')
    mod.ratio = ratio
    bpy.ops.object.modifier_apply(modifier=mod.name)

    return dup_obj

def generate_lod_levels(target, lod_settings):
    """
    対象オブジェクト (target) に対して、LOD用の複製オブジェクトを生成する。
    lod_settings は (decimation_ratio, 切替距離) のタプルリスト。
    例: [(0.5, 10.0), (0.25, 20.0), (0.1, 40.0)]
    """
    global LOD_OBJECTS
    for (ratio, distance) in lod_settings:
        lod_obj = duplicate_with_decimation(target, ratio)
        LOD_OBJECTS.append((lod_obj, distance))
        print(f"Generated LOD: {lod_obj.name} with ratio {ratio} at threshold {distance}")

def update_lod():
    """
    カメラと対象オブジェクトの距離に応じて、表示するLODモデルを切り替える。
    ここでは、距離が小さい場合は高詳細（TARGET）、距離が大きくなるにつれて
    低詳細のLODオブジェクトを表示し、他は非表示にします。
    """
    scene = bpy.context.scene
    cam = scene.camera
    if not cam:
        return
    cam_loc = cam.matrix_world.translation
    global TARGET, LOD_OBJECTS
    if TARGET is None:
        return
    target_loc = TARGET.matrix_world.translation
    distance = (cam_loc - target_loc).length

    # 統合リスト：(オブジェクト, threshold)
    # ※高詳細モデルは閾値0.0 とする
    lod_levels = [(TARGET, 0.0)] + LOD_OBJECTS
    # 表示するオブジェクトは、距離 >= threshold となるうちで、最も高い閾値を持つもの
    chosen = TARGET
    for lod_obj, threshold in sorted(lod_levels, key=lambda x: x[1]):
        if distance >= threshold:
            chosen = lod_obj

    # 全てのオブジェクトを非表示にし、選ばれたオブジェクトのみ表示
    TARGET.hide_viewport = True
    TARGET.hide_render = True
    for lod_obj, _ in LOD_OBJECTS:
        lod_obj.hide_viewport = True
        lod_obj.hide_render = True
    chosen.hide_viewport = False
    chosen.hide_render = False

    print(f"Camera distance: {distance:.2f} | Using LOD: {chosen.name}")

def render_image():
    """シーンをレンダリングして画像として保存する"""
    scene = bpy.context.scene

    # Blender ファイルのあるディレクトリを基準に output フォルダを作成
    current_dir = os.path.dirname(bpy.data.filepath)
    if current_dir == "":
        # Blender ファイルが保存されていない場合はカレントディレクトリを利用
        current_dir = os.getcwd()
    output_dir = os.path.join(current_dir, "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 出力ファイルパスの設定
    scene.render.filepath = os.path.join(output_dir, "auto_lod.png")
    scene.render.image_settings.file_format = 'PNG'

    bpy.ops.render.render(write_still=True)
    print("Rendered image saved to", scene.render.filepath)

def main():
    global TARGET, LOD_OBJECTS
    clear_scene()
    setup_camera_and_light()

    # 対象オブジェクトの作成（例として UV スフィア）
    bpy.ops.mesh.primitive_uv_sphere_add(location=(0, 0, 0))
    TARGET = bpy.context.active_object
    TARGET.name = "LOD_Target"
    print("Created target object:", TARGET.name)

    # LOD 設定リスト： (decimation_ratio, 切替距離)
    # 例: 50% のディテールを距離10以上、25% を距離20以上、10% を距離40以上で表示
    lod_settings = [(0.5, 10.0), (0.25, 20.0), (0.1, 40.0)]
    generate_lod_levels(TARGET, lod_settings)

    # 更新して適切なLODモデルを表示する（カメラ位置が固定の場合）
    update_lod()

    # レンダリング実行して画像を出力
    render_image()

    print("Automatic LOD generation and dynamic switching completed.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Error:", e)
