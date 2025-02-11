import bpy
import os
import time
from datetime import datetime

# 出力ディレクトリ
output_dir = "output"

# 出力ファイルのベース名
output_base = "handson_015"

# 同一ファイルが存在する場合の退避処理
def backup_existing_file(filepath):
    if os.path.exists(filepath):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_filepath = f"{filepath}_{timestamp}"
        os.rename(filepath, backup_filepath)
        print(f"Existing file '{filepath}' backed up to '{backup_filepath}'")

# シーンの初期化 (既存のオブジェクトを削除)
def clear_scene():
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj)
    for material in bpy.data.materials:
        bpy.data.materials.remove(material)


def create_wireframe_object():

    # デフォルトの立方体を作成 (必要に応じて他のオブジェクトに変更可能)
    bpy.ops.mesh.primitive_cube_add(size=1, enter_editmode=False, location=(0, 0, 0), rotation=(0, 0.2, 0))
    cube = bpy.context.object

    # ワイヤーフレームモディファイアを追加
    modifier = cube.modifiers.new(name="Wireframe", type='WIREFRAME')
    modifier.use_replace = True  # 元のメッシュを非表示にする
    modifier.thickness = 0.02      # ワイヤーの太さ

    # マテリアルをシンプルに設定 (今回は特に変更不要)
    material = bpy.data.materials.new(name="WireframeMaterial")
    material.use_nodes = True

    # ノードツリーの取得とノードのクリア
    node_tree = material.node_tree
    for node in node_tree.nodes:
        node_tree.nodes.remove(node)

    # Principled BSDF ノードの追加
    principled_bsdf = node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
    principled_bsdf.inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1.0) # 白っぽい色
    principled_bsdf.inputs["Metallic"].default_value = 0.0
    principled_bsdf.inputs["Roughness"].default_value = 0.4

    # Material Output ノードの追加
    material_output = node_tree.nodes.new(type='ShaderNodeOutputMaterial')

    # ノードのリンク
    node_tree.links.new(principled_bsdf.outputs["BSDF"], material_output.inputs["Surface"])

    cube.data.materials.append(material)

    # ライティング (シンプルな3点照明)
    bpy.ops.object.light_add(type='POINT', radius=1, location=(2, 2, 3))
    light1 = bpy.context.selected_objects[0]
    light1.data.energy = 500

    bpy.ops.object.light_add(type='POINT', radius=1, location=(-2, -2, 3))
    light2 = bpy.context.selected_objects[0]
    light2.data.energy = 300

    bpy.ops.object.light_add(type='POINT', radius=1, location=(-2, 2, -2))
    light3 = bpy.context.selected_objects[0]
    light3.data.energy = 200

    # カメラの設定
    bpy.ops.object.camera_add(location=(2, -2, 1.0), rotation=(1.2, 0, 0.785))
    camera = bpy.context.object
    bpy.context.scene.camera = camera
    camera.data.lens = 25  # 焦点距離

def setup_render_settings(output_filepath):

    # レンダリング設定
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'  # Cyclesレンダーエンジンを使用
    scene.cycles.samples = 128
    scene.cycles.max_bounces = 4

    scene.render.resolution_x = 800
    scene.render.resolution_y = 600
    scene.render.filepath = output_filepath
    scene.render.image_settings.file_format = 'PNG'


def main():
    start_time = time.time()

    # 出力ディレクトリの作成
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 出力ファイルパス
    output_filepath = os.path.join(output_dir, output_base + ".png")

    # 既存ファイルのバックアップ
    backup_existing_file(output_filepath)

    # シーンのクリア
    clear_scene()

    # ワイヤーフレームオブジェクトの作成
    create_wireframe_object()

    # レンダリング設定
    setup_render_settings(output_filepath)

    # レンダリング実行
    bpy.ops.render.render(write_still=True)

    end_time = time.time()
    print(f"Total execution time: {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    main()