import bpy
import math
import os

def clear_scene():
    """シーン内の全オブジェクトを削除"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def setup_camera_and_light():
    """カメラとライトを配置する"""
    # カメラの追加
    bpy.ops.object.camera_add(location=(10, -10, 10))
    cam = bpy.context.active_object
    cam.rotation_euler = (math.radians(60), 0, math.radians(45))
    bpy.context.scene.camera = cam

    # サンライトの追加
    bpy.ops.object.light_add(type='SUN', location=(10, 10, 10))
    light = bpy.context.active_object
    light.data.energy = 3.0

def create_base_object():
    """基底オブジェクトとして立方体を作成する"""
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = "BaseCube"
    return obj

def add_array_modifier(obj, modifier_name, count, offset, axis=(1, 0, 0)):
    """
    指定オブジェクトに Array モディファイアを追加する関数
      - obj: 対象オブジェクト
      - modifier_name: モディファイアの名前
      - count: 複製数
      - offset: 複製間のオフセット値（倍率）
      - axis: 複製方向（デフォルトは X 軸方向）
    """
    mod = obj.modifiers.new(name=modifier_name, type='ARRAY')
    mod.count = count
    mod.use_relative_offset = True
    # relative_offset_displace は各軸ごとに倍率を指定する（デフォルトは X 軸に 1.0）
    mod.relative_offset_displace[0] = offset * axis[0]
    mod.relative_offset_displace[1] = offset * axis[1]
    mod.relative_offset_displace[2] = offset * axis[2]
    return mod

def render_image():
    """シーンをレンダリングして画像として保存する"""
    scene = bpy.context.scene

    # 現在の Blender ファイルのあるディレクトリを基準に output フォルダを作成
    current_dir = os.path.dirname(bpy.data.filepath)
    if current_dir == "":
        # Blender ファイルが保存されていない場合はカレントディレクトリを利用
        current_dir = os.getcwd()
    output_dir = os.path.join(current_dir, "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 出力ファイルパスの設定
    scene.render.filepath = os.path.join(output_dir, "handson_008.png")
    scene.render.image_settings.file_format = 'PNG'

    bpy.ops.render.render(write_still=True)
    print("Rendered image saved to", scene.render.filepath)

def main():
    clear_scene()
    setup_camera_and_light()
    
    # 基底オブジェクト（立方体）の作成
    base_obj = create_base_object()
    
    # 1. X 軸方向に 8 個の複製（オフセット 1.5）を生成
    add_array_modifier(base_obj, modifier_name="Array_X", count=8, offset=1.5, axis=(1, 0, 0))
    
    # 2. Y 軸方向にも複製するため、2 番目の Array モディファイアを追加
    #    ※2 番目のモディファイアは既存の X 軸配列に対して重ね合わせる形になる
    add_array_modifier(base_obj, modifier_name="Array_Y", count=4, offset=1.5, axis=(0, 1, 0))
    
    # 必要に応じて、Z 軸方向への配列なども追加可能です

    # 配列生成結果を確認するためレンダリング実行
    render_image()
    
    print("自動配列生成が完了しました。")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Error:", e)
