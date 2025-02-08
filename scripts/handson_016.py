import bpy
import os
import time
import datetime
import random

# 出力ディレクトリ
output_dir = "output"

# 出力ファイルのベース名
output_base = "starry_sky_vertex"

# レンダリング設定
cycles_samples = 32 # ある程度品質を保つため
resolution_x = 800
resolution_y = 600

# 星のパラメータ
num_stars = 5000  # 星の数（頂点数）
star_size = 2.0   # 星の大きさ（平面の大きさに関連）
min_brightness = 0.2  # 星の最小輝度
max_brightness = 1.0  # 星の最大輝度
color_variation = 0.1 # 星の色のばらつき（0で白、1で完全にランダム）

def ensure_output_dir():
    """出力ディレクトリが存在しない場合は作成する"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

def backup_existing_file(filepath):
    """同名ファイルが存在する場合は退避する"""
    if os.path.exists(filepath):
        base, ext = os.path.splitext(filepath)
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        backup_filepath = f"{base}_{timestamp}{ext}"
        os.rename(filepath, backup_filepath)
        print(f"Existing file backed up to: {backup_filepath}")

def create_starry_sky():
    """頂点カラーを使って星空のようなシーンを作成・レンダリングする"""

    # 既存のオブジェクトを削除
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # Worldを設定 (背景色を黒に)
    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    if "Background" not in world.node_tree.nodes:
        bg_node = world.node_tree.nodes.new(type='ShaderNodeBackground')
    else:
        bg_node = world.node_tree.nodes["Background"]
    bg_node.inputs["Color"].default_value = (0, 0, 0, 1)
    bg_node.inputs["Strength"].default_value = 0.0

    # 高密度の平面を作成（細分化）
    bpy.ops.mesh.primitive_plane_add(size=star_size, enter_editmode=True, location=(0, 0, 0))
    bpy.ops.mesh.subdivide(number_cuts=int((num_stars)**0.5 -1)) # 頂点数がnum_starsに近くなるように
    bpy.ops.object.mode_set(mode='OBJECT')  # オブジェクトモードに戻る
    plane = bpy.context.object
    
    # 頂点カラーレイヤーを追加
    if not plane.data.vertex_colors:
        color_layer = plane.data.vertex_colors.new()
    else:
        color_layer = plane.data.vertex_colors.active

     # 各頂点にランダムな頂点カラーを設定
    loop_index = 0
    for poly in plane.data.polygons:
        for loop_index_in_poly in poly.loop_indices:
            brightness = random.uniform(min_brightness, max_brightness)
             # 色のばらつきを追加
            r = max(0, min(1, brightness + random.uniform(-color_variation, color_variation)))
            g = max(0, min(1, brightness + random.uniform(-color_variation, color_variation)))
            b = max(0, min(1, brightness + random.uniform(-color_variation, color_variation)))
            color_layer.data[loop_index].color = (r, g, b, 1.0)
            loop_index += 1
    
    # マテリアルを作成
    material = bpy.data.materials.new(name="StarMaterial")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()

    # Emissionノード
    emission_node = nodes.new(type='ShaderNodeEmission')
    emission_node.location = (200, 0)

    # Material Outputノード
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    output_node.location = (400, 0)
    
    # Attributeノード (頂点カラーを取得)
    attribute_node = nodes.new(type="ShaderNodeAttribute")
    attribute_node.attribute_name = color_layer.name # 頂点カラーレイヤーの名前
    attribute_node.location = (0, 0)

    # ノードを接続
    material.node_tree.links.new(attribute_node.outputs["Color"], emission_node.inputs["Color"])
    material.node_tree.links.new(attribute_node.outputs["Color"], emission_node.inputs["Strength"]) # 明るさも頂点カラーで制御
    material.node_tree.links.new(emission_node.outputs['Emission'], output_node.inputs['Surface'])
    
    # プレーンにマテリアルを割り当て
    if len(plane.data.materials):
        plane.data.materials[0] = material
    else:
        plane.data.materials.append(material)

     # 頂点をランダムに少しだけ上下に動かす（オプション）
    for vert in plane.data.vertices:
        vert.co.z += random.uniform(-0.1, 0.1) * star_size /10.0

    # カメラを設定
    bpy.ops.object.camera_add(location=(0, 0, star_size * 2.5), rotation=(0, 0, 0))
    camera = bpy.context.object
    bpy.context.scene.camera = camera

    # レンダリング設定
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = cycles_samples
    scene.render.resolution_x = resolution_x
    scene.render.resolution_y = resolution_y
    scene.render.filepath = os.path.join(output_dir, output_base + ".png")
    scene.render.image_settings.file_format = 'PNG'

    # レンダリング前にファイルを保存
    bpy.ops.wm.save_mainfile(filepath="temp.blend")

    # レンダリング
    start_time = time.time()
    bpy.ops.render.render(write_still=True)
    end_time = time.time()

    print(f"Rendering took {end_time - start_time:.2f} seconds")

    # 一時ファイルの削除
    os.remove("temp.blend")



if __name__ == "__main__":
    ensure_output_dir()
    output_path = os.path.join(output_dir, output_base + ".png")
    backup_existing_file(output_path)
    create_starry_sky()