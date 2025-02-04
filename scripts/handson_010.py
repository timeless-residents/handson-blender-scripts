import bpy
import os
import math

def create_comparison_scene():
    """
    比較用のシーンを作成する
    - 2つのキューブ（通常マテリアルとエミッションマテリアル）
    - 床を追加
    - キューブを回転させて陰影を確認しやすく
    """
    # 既存のメッシュオブジェクトを削除
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            bpy.data.objects.remove(obj, do_unlink=True)
    
    # 床を作成
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, -1))
    floor = bpy.context.active_object
    floor.name = "Floor"
    
    # 通常マテリアルのキューブを作成
    bpy.ops.mesh.primitive_cube_add(location=(-2, 0, 0))
    normal_cube = bpy.context.active_object
    normal_cube.name = "NormalCube"
    normal_cube.rotation_euler = (math.radians(15), math.radians(45), 0)
    
    # 発光マテリアルのキューブを作成
    bpy.ops.mesh.primitive_cube_add(location=(2, 0, 0))
    emission_cube = bpy.context.active_object
    emission_cube.name = "EmissionCube"
    emission_cube.rotation_euler = (math.radians(15), math.radians(45), 0)
    
    return floor, normal_cube, emission_cube

def create_floor_material():
    """床用のマテリアルを作成"""
    mat = bpy.data.materials.get("FloorMaterial")
    if mat is None:
        mat = bpy.data.materials.new("FloorMaterial")
    
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    
    # プリンシプルBSDFノードを追加
    principled = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    principled.location = (0, 0)
    principled.inputs["Base Color"].default_value = (0.2, 0.2, 0.2, 1)  # 暗めの灰色
    principled.inputs["Roughness"].default_value = 0.7  # やや粗い表面
    
    output = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
    output.location = (300, 0)
    
    mat.node_tree.links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    
    return mat

def setup_scene_for_render():
    """
    レンダリング用のシーン設定を行う
    """
    # レンダリング設定
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 128
    bpy.context.scene.render.resolution_x = 1200
    bpy.context.scene.render.resolution_y = 800
    
    # ワールドの設定（暗めの環境）
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.02, 0.02, 0.02, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    
    # カメラの設定
    if 'Camera' not in bpy.data.objects:
        cam_data = bpy.data.cameras.new(name='Camera')
        cam_obj = bpy.data.objects.new('Camera', cam_data)
        bpy.context.scene.collection.objects.link(cam_obj)
    
    cam = bpy.data.objects['Camera']
    cam.location = (0, -8, 5)
    cam.rotation_euler = (math.radians(55), 0, 0)
    
    # メインライト（サン）
    main_light = bpy.data.lights.new(name="MainLight", type='SUN')
    main_light_obj = bpy.data.objects.new('MainLight', main_light)
    bpy.context.scene.collection.objects.link(main_light_obj)
    main_light_obj.rotation_euler = (math.radians(60), math.radians(30), 0)
    main_light_obj.data.energy = 3.0
    
    # フィルライト（弱い全体光）
    fill_light = bpy.data.lights.new(name="FillLight", type='SUN')
    fill_light_obj = bpy.data.objects.new('FillLight', fill_light)
    bpy.context.scene.collection.objects.link(fill_light_obj)
    fill_light_obj.rotation_euler = (math.radians(45), math.radians(-60), 0)
    fill_light_obj.data.energy = 0.3
    
    bpy.context.scene.camera = cam

def create_custom_node_group():
    """前のコードと同じ"""
    node_group = bpy.data.node_groups.get("CustomEmissionGroup")
    if node_group is None:
        node_group = bpy.data.node_groups.new("CustomEmissionGroup", 'ShaderNodeTree')
        print("新規ノードグループを作成: CustomEmissionGroup")
    else:
        node_group.nodes.clear()
        node_group.links.clear()
        print("既存のノードグループを更新: CustomEmissionGroup")
    
    node_group.interface.clear()
    
    color_input = node_group.interface.new_socket(
        name="Input Color",
        in_out='INPUT',
        socket_type='NodeSocketColor'
    )
    color_input.default_value = (1.0, 0.5, 0.0, 1.0)
    
    strength_input = node_group.interface.new_socket(
        name="Strength",
        in_out='INPUT',
        socket_type='NodeSocketFloat'
    )
    strength_input.default_value = 50.0
    strength_input.min_value = 0.0
    
    node_group.interface.new_socket(
        name="Shader",
        in_out='OUTPUT',
        socket_type='NodeSocketShader'
    )
    
    group_input = node_group.nodes.new("NodeGroupInput")
    group_input.location = (-300, 0)
    
    emission_node = node_group.nodes.new("ShaderNodeEmission")
    emission_node.location = (0, 0)
    
    group_output = node_group.nodes.new("NodeGroupOutput")
    group_output.location = (300, 0)
    
    node_group.links.new(group_input.outputs["Input Color"], emission_node.inputs["Color"])
    node_group.links.new(group_input.outputs["Strength"], emission_node.inputs["Strength"])
    node_group.links.new(emission_node.outputs["Emission"], group_output.inputs["Shader"])
    
    return node_group

def create_material_with_custom_group(node_group):
    """前のコードと同じ"""
    mat = bpy.data.materials.get("CustomEmissionMaterial")
    if mat is None:
        mat = bpy.data.materials.new("CustomEmissionMaterial")
        print("新規マテリアルを作成: CustomEmissionMaterial")
    else:
        print("既存のマテリアルを更新: CustomEmissionMaterial")
    
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    
    output_node = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
    output_node.location = (400, 0)
    
    group_node = mat.node_tree.nodes.new("ShaderNodeGroup")
    group_node.node_tree = node_group
    group_node.location = (0, 0)
    
    group_node.inputs["Input Color"].default_value = (1.0, 0.5, 0.0, 1.0)
    group_node.inputs["Strength"].default_value = 5.0  # 発光強度を下げる
    
    mat.node_tree.links.new(group_node.outputs["Shader"], output_node.inputs["Surface"])
    
    return mat

def ensure_output_directory():
    """出力ディレクトリの確認"""
    output_dir = os.path.abspath("output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir

def create_normal_material():
    """通常の比較用マテリアルを作成"""
    mat = bpy.data.materials.get("NormalMaterial")
    if mat is None:
        mat = bpy.data.materials.new("NormalMaterial")
    
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    
    principled = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    principled.location = (0, 0)
    principled.inputs["Base Color"].default_value = (1.0, 0.5, 0.0, 1.0)  # オレンジ
    principled.inputs["Metallic"].default_value = 0.0
    principled.inputs["Roughness"].default_value = 0.5
    
    output = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
    output.location = (300, 0)
    
    mat.node_tree.links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    
    return mat

def main():
    """メイン実行関数"""
    try:
        print("\n=== Blenderマテリアル比較スクリプト ===")
        
        # 比較用シーンのセットアップ
        print("\n1. シーンのセットアップ:")
        floor, normal_cube, emission_cube = create_comparison_scene()
        
        # レンダリング用シーン設定
        print("2. レンダリング設定の構成...")
        setup_scene_for_render()
        
        # マテリアル作成と割り当て
        print("\n3. マテリアルの作成と割り当て:")
        
        # 床のマテリアル
        floor_material = create_floor_material()
        floor.data.materials.append(floor_material)
        
        # 通常マテリアル
        normal_material = create_normal_material()
        normal_cube.data.materials.append(normal_material)
        
        # エミッションマテリアル
        custom_group = create_custom_node_group()
        emission_material = create_material_with_custom_group(custom_group)
        emission_cube.data.materials.append(emission_material)
        
        # レンダリングの実行と保存
        output_dir = ensure_output_directory()
        output_path = os.path.join(output_dir, "material_comparison.png")
        bpy.context.scene.render.filepath = output_path
        print(f"\nレンダリング中... 出力先: {output_path}")
        bpy.ops.render.render(write_still=True)
        
        print("\n処理が正常に完了しました。")
        print(f"比較レンダリング結果を保存: {output_path}")
        print("=======================================")
        
    except Exception as e:
        print(f"\nエラーが発生しました: {str(e)}")
        raise

if __name__ == "__main__":
    main()