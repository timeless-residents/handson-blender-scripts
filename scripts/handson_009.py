import bpy
import math
import os

def clear_scene():
    """シーン内の全オブジェクトを削除"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def setup_camera_and_light():
    """カメラとライトを配置する"""
    # カメラの追加：地形全体が収まるように配置
    bpy.ops.object.camera_add(location=(15, -15, 15))
    cam = bpy.context.active_object
    # カメラを原点（地形中心）に向けるため回転を設定
    cam.rotation_euler = (math.radians(60), 0, math.radians(45))
    bpy.context.scene.camera = cam

    # サンライトの追加
    bpy.ops.object.light_add(type='SUN', location=(10, 10, 20))
    light = bpy.context.active_object
    light.data.energy = 3.0

def create_procedural_terrain():
    """
    プロシージャルな地形を生成する
      - primitive_grid_add() を利用してグリッド（地形のベース）を作成
      - Displace モディファイアと Musgrave テクスチャで高さ変動を与える
      - 簡単なマテリアルを設定
    """
    # x, y方向に 256 分割された 10 単位サイズのグリッドを作成
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=256, y_subdivisions=256, size=10, location=(0, 0, 0))
    terrain = bpy.context.active_object
    terrain.name = "ProceduralTerrain"

    # Displace モディファイアを追加
    disp_mod = terrain.modifiers.new(name="Displace", type='DISPLACE')
    # Musgrave テクスチャの生成
    tex = bpy.data.textures.new("TerrainTexture", type='MUSGRAVE')
    tex.musgrave_type = 'FBM'
    tex.noise_scale = 2.0   # ノイズの大きさ
    tex.octaves = 4         # 細かさ
    tex.lacunarity = 2.0    # lacunarity（繰り返しの間隔）
    # Blender 4.0 では、dimension または musgrave_dimension 属性は存在しないので設定しない
    disp_mod.texture = tex
    disp_mod.strength = 2.0  # 変位の強さ

    # シンプルな地形用マテリアルを追加
    mat = bpy.data.materials.new("TerrainMaterial")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        # 緑がかった土や草をイメージした色に設定
        bsdf.inputs["Base Color"].default_value = (0.2, 0.5, 0.2, 1)
        bsdf.inputs["Roughness"].default_value = 0.8
    terrain.data.materials.append(mat)
    
    return terrain

def render_image():
    """シーンをレンダリングして画像として保存する"""
    scene = bpy.context.scene

    # Blender ファイルのあるディレクトリまたはカレントディレクトリを基準に output フォルダを作成
    current_dir = os.path.dirname(bpy.data.filepath)
    if current_dir == "":
        current_dir = os.getcwd()
    output_dir = os.path.join(current_dir, "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 出力ファイルパスの設定（PNG 形式）
    scene.render.filepath = os.path.join(output_dir, "procedural_terrain.png")
    scene.render.image_settings.file_format = 'PNG'

    bpy.ops.render.render(write_still=True)
    print("Rendered image saved to", scene.render.filepath)

def main():
    clear_scene()
    setup_camera_and_light()
    create_procedural_terrain()
    render_image()
    print("プロシージャルな地形生成が完了しました。")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Error:", e)
