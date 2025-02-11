import bpy
import math
import random

def clear_scene():
    """シーンをクリアする"""
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat, do_unlink=True)

def create_3d_text_layer(text, location, color, size=1.0, extrude=0.2, bevel=0.02, rotation=(0, 0, 0)):
    """3Dテキストレイヤーを作成する（改良版）"""
    bpy.ops.object.text_add(location=location)
    text_obj = bpy.context.active_object
    text_obj.data.body = text
    
    # テキストの基本設定
    text_obj.data.size = size
    text_obj.data.extrude = extrude
    text_obj.data.bevel_depth = bevel
    text_obj.data.bevel_resolution = 3
    
    # テキストの配置設定
    text_obj.data.align_x = 'CENTER'
    text_obj.data.align_y = 'CENTER'
    
    # 回転を適用
    text_obj.rotation_euler = (
        math.radians(rotation[0]),
        math.radians(rotation[1]),
        math.radians(rotation[2])
    )
    
    # マテリアルを作成して割り当て
    mat = create_text_material(color)
    text_obj.data.materials.append(mat)
    
    return text_obj

def create_text_material(color):
    """改良版テキストマテリアル作成"""
    mat = bpy.data.materials.new(name=f"TextMaterial_{random.randint(0,1000)}")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # プリンシプルBSDFノード
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.inputs["Base Color"].default_value = (*color, 1)
    principled.inputs["Metallic"].default_value = 0.3
    principled.inputs["Roughness"].default_value = 0.2
    principled.inputs["Specular IOR Level"].default_value = 0.5
    # Clearcoat関連のパラメータは削除
    
    # 出力ノード
    output = nodes.new("ShaderNodeOutputMaterial")
    
    # ノードを接続
    mat.node_tree.links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    
    return mat

def setup_camera():
    """カメラセットアップ（正面からの視点）"""
    bpy.ops.object.camera_add(location=(0, -4, 0))
    camera = bpy.context.active_object
    camera.rotation_euler = (math.radians(0), 0, 0)
    
    # カメラの視野角を調整（より広い視野に）
    camera.data.lens = 35
    
    # カメラをテキストに向けて追跡制約を設定
    target_empty = bpy.data.objects.new("CameraTarget", None)
    bpy.context.scene.collection.objects.link(target_empty)
    target_empty.location = (0, 0, 0)
    
    track = camera.constraints.new(type='TRACK_TO')
    track.target = target_empty
    track.track_axis = 'TRACK_NEGATIVE_Z'
    track.up_axis = 'UP_Y'
    
    bpy.context.scene.camera = camera

def setup_lighting():
    """改良版ライティングセットアップ"""
    # フロントライト
    bpy.ops.object.light_add(type='AREA', location=(0, -3, 1))
    front_light = bpy.context.active_object
    front_light.data.energy = 800
    front_light.data.size = 5
    
    # 上部ライト
    bpy.ops.object.light_add(type='AREA', location=(0, -1, 3))
    top_light = bpy.context.active_object
    top_light.data.energy = 500
    top_light.data.size = 3
    
    # サイドライト（左）
    bpy.ops.object.light_add(type='AREA', location=(-2, -2, 1))
    left_light = bpy.context.active_object
    left_light.data.energy = 300
    left_light.data.size = 2
    
    # サイドライト（右）
    bpy.ops.object.light_add(type='AREA', location=(2, -2, 1))
    right_light = bpy.context.active_object
    right_light.data.energy = 300
    right_light.data.size = 2

def setup_render():
    """レンダリング設定（高品質）"""
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 256
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.film_transparent = True
    
    # ワールド設定
    world = scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.9, 0.9, 0.9, 1)

def create_layered_pop_text(text="POP!", base_location=(0, 0, 0)):
    """改良版レイヤードポップアートテキスト作成"""
    # 洗練されたカラーパレット
    colors = [
        (0.2, 0.8, 0.4),  # ミントグリーン
        (0.4, 0.6, 0.9),  # ペールブルー
        (0.9, 0.4, 0.4),  # コーラルピンク
        (0.9, 0.8, 0.3),  # パステルイエロー
    ]
    
    text_objects = []
    for i, color in enumerate(colors):
        # 各レイヤーの位置とローテーションを計算
        z_offset = i * 0.1
        x_offset = i * 0.05
        y_offset = i * -0.05
        
        location = (
            base_location[0] + x_offset,
            base_location[1] + y_offset,
            base_location[2] + z_offset
        )
        
        # 各レイヤーに微妙な回転を加える
        rotation = (90, 0, 0)  # 回転を0に設定して正面を向くように
        
        # テキストの厚みと面取りを調整
        extrude = 0.2 - (i * 0.02)  # レイヤーごとに少しずつ薄く
        bevel = 0.02 - (i * 0.002)  # レイヤーごとに面取りも調整
        
        text_obj = create_3d_text_layer(
            text,
            location,
            color,
            size=1.2,
            extrude=extrude,
            bevel=bevel,
            rotation=rotation
        )
        text_objects.append(text_obj)
    
    return text_objects

def main():
    """メイン実行関数"""
    try:
        print("\n=== 3Dポップアートテキスト生成開始 ===")
        
        # シーンをクリア
        clear_scene()
        
        # ポップアートテキストを作成
        text_objects = create_layered_pop_text("POP!", (0, 0, 0))
        
        # カメラ、ライティング、レンダリング設定
        setup_camera()
        setup_lighting()
        setup_render()
        
        # 出力先ディレクトリの作成
        import os
        output_dir = os.path.abspath("output")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # レンダリング実行と保存
        output_path = os.path.join(output_dir, "handson_012.png")
        bpy.context.scene.render.filepath = output_path
        bpy.ops.render.render(write_still=True)
        
        print("\n処理が完了しました。")
        print("ファイルは 'pop_art_text_3d.png' として保存されました。")
        
    except Exception as e:
        print(f"\nエラーが発生しました: {str(e)}")
        raise

if __name__ == "__main__":
    main()