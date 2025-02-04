import bpy
import math
import mathutils # type: ignore
import random
import os

def clear_scene():
    """シーン内の全オブジェクトを削除"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def setup_camera():
    """カメラを配置し、シーンのアクティブカメラに設定"""
    bpy.ops.object.camera_add(location=(10, -10, 10))
    cam = bpy.context.active_object
    # カメラが原点を向くように回転を設定
    cam.rotation_euler = (math.radians(60), 0, math.radians(45))
    bpy.context.scene.camera = cam

def setup_light():
    """サンライトを追加してシーンを照らす"""
    bpy.ops.object.light_add(type='SUN', location=(10, 10, 10))
    light = bpy.context.active_object
    light.data.energy = 3.0

def create_branch(origin, direction, length, thickness, depth):
    """
    再帰的に枝（シリンダー）を作成する関数
      - origin: 枝の開始位置 (mathutils.Vector)
      - direction: 枝の進行方向（正規化済み mathutils.Vector）
      - length: 枝の長さ
      - thickness: 枝の太さ（半径）
      - depth: 再帰の深さ（depth==0 で再帰終了）
    """
    if depth == 0:
        return

    # 枝（シリンダー）の中心位置は、枝の底から length/2 進んだ位置とする
    loc = origin + direction * (length / 2)
    bpy.ops.mesh.primitive_cylinder_add(radius=thickness, depth=length, location=loc)
    branch = bpy.context.active_object

    # デフォルトのシリンダーは Z 軸方向に伸びているため、
    # Z 軸 (0,0,1) から目的の方向への回転差を求めて回転を適用
    rot = mathutils.Vector((0, 0, 1)).rotation_difference(direction)
    branch.rotation_euler = rot.to_euler()

    # 次の枝の開始位置は、この枝の上端
    new_origin = origin + direction * length

    if depth > 1:
        # 分岐する枝の本数（例として2～3本）
        num_branches = random.randint(2, 3)
        for i in range(num_branches):
            # 分岐角度（20～40度）をランダムに設定
            angle = random.uniform(math.radians(20), math.radians(40))
            # direction に垂直なランダムな回転軸を生成
            rand_vec = mathutils.Vector((random.uniform(-1, 1),
                                         random.uniform(-1, 1),
                                         random.uniform(-1, 1)))
            perp = rand_vec - rand_vec.project(direction)
            if perp.length == 0:
                perp = mathutils.Vector((1, 0, 0))
            perp.normalize()
            # 現在の direction を perp 軸回りに angle 回転
            new_direction = direction.copy()
            rot_matrix = mathutils.Matrix.Rotation(angle, 4, perp)
            new_direction = rot_matrix @ new_direction
            new_direction.normalize()
            # 再帰呼び出し：枝の長さと太さを縮小して分岐を生成
            create_branch(new_origin, new_direction, length * 0.7, thickness * 0.7, depth - 1)

def render_image():
    """レンダリング実行して画像を出力する関数"""
    scene = bpy.context.scene

    # プロジェクトファイルのあるディレクトリを基準に output フォルダを作成（なければ作成）
    current_dir = os.path.dirname(bpy.data.filepath)
    output_dir = os.path.join(current_dir, "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 出力ファイルパスの設定
    scene.render.filepath = os.path.join(output_dir, "fractal_tree.png")
    scene.render.image_settings.file_format = 'PNG'

    # レンダリング実行（静止画）
    bpy.ops.render.render(write_still=True)

def main():
    clear_scene()
    setup_camera()
    setup_light()

    # 初期条件の設定
    origin = mathutils.Vector((0, 0, 0))
    direction = mathutils.Vector((0, 0, 1))  # 上方向
    initial_length = 2.0      # 初期の枝の長さ
    initial_thickness = 0.1   # 初期の枝の太さ
    recursion_depth = 5       # 再帰の深さ

    create_branch(origin, direction, initial_length, initial_thickness, recursion_depth)
    
    # フラクタルツリー生成後にレンダリングを実行
    render_image()
    print("フラクタルツリーの生成とレンダリングが完了しました。")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("エラーが発生しました:", e)
