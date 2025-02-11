import bpy
import math
import os

def clear_scene():
    """シーンをクリアする"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    for material in bpy.data.materials:
        bpy.data.materials.remove(material)
    
    for obj in bpy.data.objects:
        if obj.type in ['CAMERA', 'LIGHT']:
            bpy.data.objects.remove(obj, do_unlink=True)

def create_material(alpha=0.1, name="CubeMaterial"):
    """透明なマテリアルを作成"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # プリンシプルBSDFを追加
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 0.1)
    principled.inputs["Metallic"].default_value = 0.1
    principled.inputs["Roughness"].default_value = 0.3
    principled.inputs["Alpha"].default_value = alpha
    
    # マテリアル出力を追加
    output = nodes.new("ShaderNodeOutputMaterial")
    mat.node_tree.links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    
    # 透明度の設定
    mat.use_backface_culling = False
    mat.blend_method = 'BLEND'
    mat.shadow_method = 'NONE'
    
    return mat

def create_hollow_cube(size=2.0, thickness=0.3, location=(0, 0, 0), alpha=0.1, apply=True):
    """中空の立方体を作成"""
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.active_object

    if apply:
        # Solidifyモディファイアを追加
        solidify = cube.modifiers.new(name="Hollow", type='SOLIDIFY')
        solidify.thickness = thickness
        solidify.offset = 0
        solidify.use_rim = True
        solidify.use_even_offset = True
    
    # マテリアルを適用
    mat = create_material(alpha=alpha, name=f"CubeMaterial_{location[0]}")
    cube.data.materials.append(mat)
    
    # ワイヤーフレーム表示を有効化
    cube.show_wire = True
    cube.show_all_edges = True
    
    return cube

def setup_lighting():
    """ライティングをセットアップ"""
    # メインライト
    bpy.ops.object.light_add(type='AREA', location=(5, -5, 5))
    main_light = bpy.context.active_object
    main_light.data.energy = 1000
    main_light.data.size = 5
    
    # フィルライト
    bpy.ops.object.light_add(type='AREA', location=(-3, -2, 3))
    fill_light = bpy.context.active_object
    fill_light.data.energy = 400
    fill_light.data.size = 3
    
    # リムライト
    bpy.ops.object.light_add(type='AREA', location=(0, 5, 2))
    rim_light = bpy.context.active_object
    rim_light.data.energy = 300
    rim_light.data.size = 3

def setup_camera():
    """カメラをセットアップ - X軸60度回転"""
    bpy.ops.object.camera_add(location=(0, -12, 7))
    camera = bpy.context.active_object
    
    # X軸60度、Y軸とZ軸は0度に設定
    camera.rotation_euler = (math.radians(60), 0, 0)
    
    bpy.context.scene.camera = camera

def setup_render():
    """軽量化したレンダリング設定"""
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    # サンプル数を大幅に削減
    scene.cycles.samples = 64  # 256から64に削減
    # 解像度を下げる
    scene.render.resolution_x = 1280  # 1920から1280に
    scene.render.resolution_y = 720   # 1080から720に
    
    # 最適化設定
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.05  # 閾値を緩める
    scene.cycles.use_denoising = True

def create_comparison_scene():
    """比較シーンを作成"""
    # オリジナルの立方体（モディファイア適用前）
    cube1 = create_hollow_cube(size=2.0, thickness=0.3, location=(-2.5, 0, 0), alpha=0.1, apply=False)
    
    # モディファイア適用後の立方体
    cube2 = create_hollow_cube(size=2.0, thickness=0.3, location=(2.5, 0, 0), alpha=0.1, apply=True)

def render_comparison():
    """比較画像をレンダリング"""
    scene = bpy.context.scene
    
    # 出力ディレクトリの作成
    output_dir = "//output"
    if not os.path.exists(bpy.path.abspath(output_dir)):
        os.makedirs(bpy.path.abspath(output_dir))
    
    # レンダリング実行
    scene.render.filepath = f"{output_dir}//handson_013.png"
    bpy.ops.render.render(write_still=True)

def main():
    """メイン実行関数"""
    try:
        print("\n=== モディファイア比較の開始 ===")
        
        clear_scene()
        setup_render()
        setup_lighting()
        setup_camera()
        create_comparison_scene()
        render_comparison()
        
        print("\n処理が完了しました。")
        print("出力ディレクトリ: comparison_renders/")
        
    except Exception as e:
        print(f"\nエラーが発生しました: {str(e)}")
        raise

if __name__ == "__main__":
    main()