import bpy
import math
import os

def clear_scene():
    """シーンをクリアする"""
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            bpy.data.objects.remove(obj, do_unlink=True)

def create_room():
    """部屋の壁を作成する"""
    # 床
    bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, 0))
    floor = bpy.context.active_object
    floor.name = "Floor"
    
    # 壁1 (正面)
    bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 2, 2))
    wall1 = bpy.context.active_object
    wall1.name = "Wall1"
    wall1.rotation_euler = (math.radians(90), 0, 0)
    
    # 壁2 (右側)
    bpy.ops.mesh.primitive_plane_add(size=4, location=(2, 0, 2))
    wall2 = bpy.context.active_object
    wall2.name = "Wall2"
    wall2.rotation_euler = (math.radians(90), 0, math.radians(90))
    
    return floor, wall1, wall2

def create_window():
    """窓を作成する"""
    # 窓枠を作成
    bpy.ops.mesh.primitive_plane_add(size=1.5, location=(1.99, -0.5, 2))
    window = bpy.context.active_object
    window.name = "Window"
    window.rotation_euler = (math.radians(90), 0, math.radians(90))
    
    return window

def create_wall_material():
    """壁用のマテリアルを作成"""
    mat = bpy.data.materials.new("WallMaterial")
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    
    # プリンシプルBSDFノードを追加
    principled = mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    principled.location = (0, 0)
    principled.inputs["Base Color"].default_value = (1, 1, 1, 1)  # 純白
    principled.inputs["Roughness"].default_value = 0.2  # より光沢のある仕上げ
    principled.inputs["Specular IOR Level"].default_value = 0.5  # 適度な反射
    
    output = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
    output.location = (300, 0)
    
    mat.node_tree.links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    
    output = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
    output.location = (300, 0)
    
    mat.node_tree.links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    
    return mat

def create_window_material():
    """窓用の発光マテリアルを作成"""
    mat = bpy.data.materials.new("WindowMaterial")
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    
    # エミッションノードを追加
    emission = mat.node_tree.nodes.new("ShaderNodeEmission")
    emission.location = (0, 0)
    emission.inputs["Color"].default_value = (1, 0.95, 0.8, 1)  # 暖かみのある光
    emission.inputs["Strength"].default_value = 500.0  # 発光強度を大幅に上昇
    
    output = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
    output.location = (400, 0)
    
    # ノードを接続
    mat.node_tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])
    
    return mat

def setup_camera():
    """カメラをセットアップ"""
    cam_data = bpy.data.cameras.new(name='Camera')
    cam_obj = bpy.data.objects.new('Camera', cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    
    # カメラの位置をさらに上げ、窓方向を見る
    cam_obj.location = (-1.2, -1.2, 1.6)
    cam_obj.rotation_euler = (math.radians(90), 0, math.radians(-45))
    
    # カメラの視野角を調整
    cam_data.lens = 20  # 広角維持
    
    bpy.context.scene.camera = cam_obj

def setup_scene_for_render():
    """レンダリング設定"""
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 128  # サンプル数を増やしてノイズ低減
    bpy.context.scene.render.resolution_x = 800
    bpy.context.scene.render.resolution_y = 600
    
    # デノイズを有効化
    bpy.context.scene.cycles.use_denoising = True
    
    # ワールドの設定
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    
    # ノードを設定
    world.use_nodes = True
    nodes = world.node_tree.nodes
    nodes.clear()
    
    # バックグラウンドノード
    bg = nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = (0.01, 0.01, 0.01, 1)  # 環境光を少し明るく
    bg.inputs["Strength"].default_value = 1.0
    bg.location = (0, 200)
    
    # ボリュームノード
    volume = nodes.new("ShaderNodeVolumePrincipled")
    volume.location = (0, 0)
    volume.inputs["Density"].default_value = 0.02
    volume.inputs["Anisotropy"].default_value = 0.3
    
    # 出力ノード
    output = nodes.new("ShaderNodeOutputWorld")
    output.location = (300, 0)
    
    # ノードを接続
    links = world.node_tree.links
    links.new(bg.outputs["Background"], output.inputs["Surface"])
    links.new(volume.outputs["Volume"], output.inputs["Volume"])

def main():
    """メイン実行関数"""
    try:
        print("\n=== 部屋のライティングシミュレーション ===")
        
        # シーンのクリア
        clear_scene()
        
        # 部屋の作成
        floor, wall1, wall2 = create_room()
        window = create_window()
        
        # マテリアルの作成と割り当て
        wall_material = create_wall_material()
        window_material = create_window_material()
        
        # マテリアルの割り当て
        for obj in [floor, wall1, wall2]:
            obj.data.materials.append(wall_material)
        window.data.materials.append(window_material)
        
        # カメラとレンダリング設定
        setup_camera()
        setup_scene_for_render()
        
        # レンダリングの実行と保存
        output_dir = os.path.abspath("output")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        output_path = os.path.join(output_dir, "room_lighting.png")
        bpy.context.scene.render.filepath = output_path
        print(f"\nレンダリング中... 出力先: {output_path}")
        bpy.ops.render.render(write_still=True)
        
        print("\n処理が完了しました。")
        print(f"レンダリング結果を保存: {output_path}")
        
    except Exception as e:
        print(f"\nエラーが発生しました: {str(e)}")
        raise

if __name__ == "__main__":
    main()