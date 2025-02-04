import bpy
import math


def setup_scene():
    # シーンをクリア
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    # カメラをセットアップ
    bpy.ops.object.camera_add(location=(0, -10, 5))
    camera = bpy.context.active_object
    camera.rotation_euler = (math.radians(75), 0, 0)
    bpy.context.scene.camera = camera

    # ライトをセットアップ
    bpy.ops.object.light_add(type="SUN", location=(5, -5, 10))
    sun = bpy.context.active_object
    sun.data.energy = 5.0

    # 地面となる平面を追加
    bpy.ops.mesh.primitive_plane_add(size=20)
    plane = bpy.context.active_object

    return camera, sun, plane


def create_text_material():
    material = bpy.data.materials.new(name="TextMaterial")
    material.use_nodes = True
    nodes = material.node_tree.nodes

    # ノードをクリア
    nodes.clear()

    # プリンシプルBSDFを追加
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.inputs["Base Color"].default_value = (0.8, 0.1, 0.1, 1)  # 赤色
    principled.inputs["Metallic"].default_value = 0.8
    principled.inputs["Roughness"].default_value = 0.2

    # マテリアル出力を追加
    output = nodes.new("ShaderNodeOutputMaterial")

    # ノードを接続
    material.node_tree.links.new(principled.outputs["BSDF"], output.inputs["Surface"])

    return material


def create_3d_text(text_string="BLENDER", extrude=0.2):
    # テキストオブジェクトを作成（最初から見える高さに配置）
    bpy.ops.object.text_add(location=(0, 0, 1))
    text_obj = bpy.context.active_object
    text_obj.data.body = text_string

    # テキストを整形
    text_obj.data.extrude = extrude
    text_obj.data.align_x = "CENTER"
    text_obj.data.align_y = "CENTER"

    # マテリアルを適用
    material = create_text_material()
    text_obj.data.materials.append(material)

    return text_obj


def create_text_animation(text_obj, frames=24):
    # アニメーションの開始フレームと終了フレームを設定
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = frames

    # 最初のキーフレーム（1フレーム目）
    bpy.context.scene.frame_set(1)
    text_obj.location = (0, 0, 1)
    text_obj.rotation_euler = (0, 0, 0)
    text_obj.keyframe_insert(data_path="location")
    text_obj.keyframe_insert(data_path="rotation_euler")

    # 中間キーフレーム
    bpy.context.scene.frame_set(frames // 2)
    text_obj.location = (0, 0, 2)
    text_obj.rotation_euler = (0, 0, math.pi)
    text_obj.keyframe_insert(data_path="location")
    text_obj.keyframe_insert(data_path="rotation_euler")

    # 最後のキーフレーム
    bpy.context.scene.frame_set(frames)
    text_obj.location = (0, 0, 1)
    text_obj.rotation_euler = (0, 0, math.pi * 2)
    text_obj.keyframe_insert(data_path="location")
    text_obj.keyframe_insert(data_path="rotation_euler")

    # アニメーションカーブをスムーズに
    for fc in text_obj.animation_data.action.fcurves:
        for kf in fc.keyframe_points:
            kf.interpolation = "BEZIER"
            kf.easing = "EASE_IN_OUT"


def main():
    # シーンのセットアップ
    camera, sun, plane = setup_scene()

    # 3Dテキストを作成
    text_obj = create_3d_text("BLENDER 3D")

    # アニメーションを作成
    create_text_animation(text_obj)

    # レンダリング設定
    bpy.context.scene.render.engine = "BLENDER_EEVEE"  # 正しいエンジン名に修正
    bpy.context.scene.render.resolution_x = 960
    bpy.context.scene.render.resolution_y = 540
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.context.scene.render.filepath = "//output//frame_"

    # アニメーションをレンダリング
    bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    try:
        main()
        print("3Dテキストアニメーションの生成とレンダリングが完了しました。")
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
