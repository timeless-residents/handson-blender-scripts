import bpy
import os
import time

# 設定
OUTPUT_DIR = "output"
FILE_PREFIX = "handson_017"
FILE_EXTENSION = "png"
MAX_EXECUTION_TIME = 10  # 秒

def main():
    """メイン関数：Blenderシーンを設定し、レンダリングを実行する。"""
    start_time = time.time()

    # 出力ディレクトリの準備
    output_path = prepare_output_directory(OUTPUT_DIR, FILE_PREFIX, FILE_EXTENSION)
    if not output_path:
        print("Error: Failed to prepare output directory.")
        return

    # シーンの初期化
    scene = bpy.context.scene
    try:
        initialize_scene(scene)
        # オブジェクトの作成と配置 (例: 立方体)
        create_and_place_object(scene)

        # レンダリング設定
        setup_rendering(scene, output_path)

        # レンダリングの実行
        render_scene(scene)
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"スクリプト実行時間: {execution_time:.2f} 秒")

    if execution_time > MAX_EXECUTION_TIME:
        print(f"警告: スクリプト実行時間が{MAX_EXECUTION_TIME}秒を超えました。")


def prepare_output_directory(output_dir, file_prefix, file_extension):
    """出力ディレクトリを準備し、既存のファイルをバックアップする。"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    filepath = os.path.join(output_dir, f"{file_prefix}.{file_extension}")
    if os.path.exists(filepath):
        backup_filepath = os.path.join(output_dir, f"{file_prefix}_backup_{int(time.time())}.{file_extension}")
        os.rename(filepath, backup_filepath)
        print(f"既存のファイル {filepath} を {backup_filepath} にバックアップしました。")

    return filepath


def initialize_scene(scene):
    """シーンを初期化：既存のオブジェクトを削除し、ワールド設定を行う。カメラとライトは残す"""
    # 既存オブジェクトの削除 (カメラとライトは除く)
    for obj in bpy.context.scene.objects:
        if obj.type not in {'CAMERA', 'LIGHT'}:
            bpy.data.objects.remove(obj, do_unlink=True)

    # ワールド設定: 環境光を白に設定
    world = bpy.data.worlds['World']
    # よりニュートラルな環境光に
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.9, 0.9, 0.9, 1)  # グレー寄りに
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.5  # 強度を下げる

    # 床の追加
    if not bpy.data.objects.get("Plane"):
        bpy.ops.mesh.primitive_plane_add(size=200, enter_editmode=False, align='WORLD', location=(0, 0, -0.5))  # サイズを200に拡大
        plane = bpy.context.object
        
        # 床のマテリアルをより環境に溶け込む設定に
        mat = bpy.data.materials.new(name="InfiniteFloor")
        mat.use_nodes = True

        # Principled BSDFが存在するか確認
        if not mat.node_tree.nodes.get("Principled BSDF"):
             bsdf = mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
             bsdf.location = (200,0)

             material_output = mat.node_tree.nodes.get("Material Output")
             if not material_output:
                 material_output = mat.node_tree.nodes.new('ShaderNodeOutputMaterial')

             mat.node_tree.links.new(bsdf.outputs['BSDF'], material_output.inputs['Surface'])
        else:
            bsdf = mat.node_tree.nodes["Principled BSDF"]

        bsdf.inputs["Base Color"].default_value = (0.98, 0.98, 0.98, 1)  # わずかにオフホワイト
        bsdf.inputs["Roughness"].default_value = 0.2  # 適度な反射
        bsdf.inputs["Metallic"].default_value = 0.0  # 金属感なし

        plane.data.materials.append(mat)

    # カメラがなければ作成する
    if not bpy.data.objects.get("Camera"):
        bpy.ops.object.camera_add(align='WORLD', location=(0, -5, 1), rotation=(0.5, 0, 0))

    # 既存のライトを削除
    for obj in bpy.context.scene.objects:
        if obj.type == 'LIGHT':
            bpy.data.objects.remove(obj, do_unlink=True)
    
    # キーライト（主光源）
    key_light = bpy.data.lights.new(name="KeyLight", type='AREA')
    key_light.energy = 300  # より強い光量に
    key_light.size = 5
    
    # フィルライト（補助光）
    fill_light = bpy.data.lights.new(name="FillLight", type='AREA')
    fill_light.energy = 50  # 弱めの補助光
    fill_light.size = 10
    
    # キーライトの配置
    key_light_obj = bpy.data.objects.new(name="KeyLight", object_data=key_light)
    bpy.context.scene.collection.objects.link(key_light_obj)
    key_light_obj.location = (2, -2, 3)  # より強いコントラストのため位置調整
    key_light_obj.rotation_euler = (0.5, 0.4, 0)
    
    # フィルライトの配置
    fill_light_obj = bpy.data.objects.new(name="FillLight", object_data=fill_light)
    bpy.context.scene.collection.objects.link(fill_light_obj)
    fill_light_obj.location = (-1.5, 1, 2)
    fill_light_obj.rotation_euler = (0.3, -0.2, 0)


def create_and_place_object(scene):
    """オブジェクトを作成し、シーンに配置する。"""
    # 立方体の作成
    bpy.ops.mesh.primitive_cube_add(size=1, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    cube = bpy.context.object

    # マテリアルの作成と適用
    material = bpy.data.materials.new(name="WhiteMaterial")
    material.use_nodes = True

    bsdf = None
    if not material.node_tree.nodes.get("Principled BSDF"):
        bsdf = material.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.location = (200,0)

        material_output = material.node_tree.nodes.get("Material Output")
        if not material_output:
            material_output = material.node_tree.nodes.new('ShaderNodeOutputMaterial')

        material.node_tree.links.new(bsdf.outputs['BSDF'], material_output.inputs['Surface'])
    else:
        bsdf = material.node_tree.nodes["Principled BSDF"]

    if bsdf:
        bsdf.inputs["Base Color"].default_value = (1, 1, 1, 1)  # 白色

    cube.data.materials.append(material)


def setup_rendering(scene, output_path):
    """レンダリング設定を行う。"""
    scene.render.filepath = output_path
    scene.render.image_settings.file_format = 'PNG'
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.device = 'GPU'
    bpy.context.scene.cycles.samples = 64
    scene.view_settings.look = 'None'
    scene.render.film_transparent = False


def render_scene(scene):
    """シーンをレンダリングする。"""
    bpy.ops.render.render(write_still=True)

if __name__ == "__main__":
    main()