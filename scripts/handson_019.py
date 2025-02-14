"""
Blender 4.0.2 用スクリプト

カーブに沿ったカメラ移動とズームイン演出によって、奥行きのある動画を生成します。
今回の修正では、カメラがシーン内のオブジェクトに近すぎないよう、
カメラをパスを追従する Empty の子として作成し、ローカルオフセットで後方・上方に配置します。
また、カメラ移動用のカーブのZ軸座標を0～6から0～4に調整し、
床およびオブジェクトに識別しやすいノードベースのマテリアルを設定しています。
さらに、動画の再生時間を10秒（30fpsで300フレーム）に調整し、
初期状態でカメラがシーン中央（対象オブジェクト群）を向くよう「Track To」制約を追加しています。

出力は "output/animation.mp4" に保存し、同一ファイルが存在する場合は退避します。
"""

import bpy
import os
import shutil
from datetime import datetime


def backup_existing_file(filepath):
    """
    出力先に同一ファイルが存在する場合、タイムスタンプ付きのファイル名にリネームして退避します.
    
    Args:
        filepath (str): 出力ファイルのパス
    """
    if os.path.exists(filepath):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base, ext = os.path.splitext(filepath)
        backup_path = f"{base}_backup_{timestamp}{ext}"
        shutil.move(filepath, backup_path)


def clear_scene():
    """
    現在のシーン内の全オブジェクトを削除し、使用済みデータブロックもクリーンアップします.
    """
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in bpy.data.meshes:
        bpy.data.meshes.remove(block)
    for block in bpy.data.curves:
        bpy.data.curves.remove(block)
    for block in bpy.data.cameras:
        bpy.data.cameras.remove(block)
    for block in bpy.data.lights:
        bpy.data.lights.remove(block)


def create_curve():
    """
    カメラ移動用のBezierカーブを作成します.
    ※各制御点のZ座標を元の2/3にすることで、最終点がZ=4になるように調整しています。
    
    Returns:
        Object: 作成したカーブオブジェクト
    """
    curve_data = bpy.data.curves.new(name='CameraPath', type='CURVE')
    curve_data.dimensions = '3D'
    spline = curve_data.splines.new(type='BEZIER')
    spline.bezier_points.add(count=3)
    points = spline.bezier_points

    # 制御点の設定（Z座標は元の値の2/3に調整）
    points[0].co = (0.0, 0.0, 0.0)
    points[0].handle_left = (-1.0, -1.0, 0.0)
    points[0].handle_right = (1.0, 1.0, 0.0)

    points[1].co = (2.0, 2.0, 2.0 * 2/3)  # 約1.33
    points[1].handle_left = (1.0, 1.0, 2.0 * 2/3)
    points[1].handle_right = (3.0, 3.0, 2.0 * 2/3)

    points[2].co = (4.0, 0.0, 4.0 * 2/3)  # 約2.67
    points[2].handle_left = (3.0, -1.0, 4.0 * 2/3)
    points[2].handle_right = (5.0, 1.0, 4.0 * 2/3)

    points[3].co = (6.0, -2.0, 6.0 * 2/3)  # 6*2/3 = 4.0
    points[3].handle_left = (5.0, -3.0, 6.0 * 2/3)
    points[3].handle_right = (7.0, -1.0, 6.0 * 2/3)

    # パスアニメーション有効化（30fps で10秒 = 300フレーム）
    curve_data.use_path = True
    curve_data.path_duration = 300

    curve_obj = bpy.data.objects.new(name='CameraPath', object_data=curve_data)
    bpy.context.collection.objects.link(curve_obj)
    return curve_obj


def create_path_follower(curve):
    """
    空のオブジェクトを作成し、Follow Path制約を追加してカーブに沿って移動するアニメーションを設定します.
    
    Args:
        curve (Object): カメラパス用のカーブオブジェクト
    Returns:
        Object: 制約付き空オブジェクト ("PathFollower")
    """
    follower = bpy.data.objects.new("PathFollower", None)
    bpy.context.collection.objects.link(follower)
    constraint = follower.constraints.new(type='FOLLOW_PATH')
    constraint.target = curve
    constraint.use_fixed_location = True
    constraint.use_curve_follow = True
    constraint.forward_axis = 'FORWARD_Y'
    constraint.up_axis = 'UP_Z'
    constraint.offset_factor = 0.0
    constraint.keyframe_insert(data_path="offset_factor", frame=1)
    constraint.offset_factor = 1.0
    constraint.keyframe_insert(data_path="offset_factor", frame=300)
    return follower


def create_camera(parent_obj):
    """
    カメラを作成し、指定されたオブジェクトの子として追加します.
    ローカル位置を調整してシーンから適切な距離に配置します.
    
    Args:
        parent_obj (Object): カメラを親にするオブジェクト
    Returns:
        Object: 作成したカメラオブジェクト
    """
    cam_data = bpy.data.cameras.new(name='Camera')
    camera = bpy.data.objects.new('Camera', cam_data)
    bpy.context.collection.objects.link(camera)
    camera.parent = parent_obj
    # ローカル座標で後方かつ上方にオフセット（例: Y軸-7, Z軸+6）
    camera.location = (0.0, -7.0, 6.0)
    return camera


def animate_camera_zoom(camera):
    """
    カメラのレンズ値（焦点距離）をフレーム1で35.0からフレーム300で70.0にアニメーションさせます.
    
    Args:
        camera (Object): 対象のカメラオブジェクト
    """
    camera.data.lens = 35.0
    camera.data.keyframe_insert(data_path="lens", frame=1)
    camera.data.lens = 70.0
    camera.data.keyframe_insert(data_path="lens", frame=300)


def setup_render_settings(output_filepath):
    """
    アニメーションレンダリングの設定を行います.
    
    Args:
        output_filepath (str): 出力ファイルのフルパス
    """
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.filepath = output_filepath
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.fps = 30
    scene.frame_start = 1
    scene.frame_end = 300


def create_material(name, base_color):
    """
    ノードベースのマテリアルを作成し、Principled BSDF の Base Color を設定します.
    
    Args:
        name (str): マテリアル名
        base_color (tuple): (R, G, B, A) の色値
    
    Returns:
        Material: 作成したマテリアル
    """
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = base_color
    return mat


def add_materials_to_objects():
    """
    Plane、Cube、Sphere に個別のマテリアルを設定し、レンダリングで識別しやすいようにします.
    """
    # 床 (Plane): 明るいグレー
    plane = bpy.data.objects.get("Plane")
    if plane is not None:
        mat_plane = create_material("FloorMaterial", (0.8, 0.8, 0.8, 1.0))
        if plane.data.materials:
            plane.data.materials[0] = mat_plane
        else:
            plane.data.materials.append(mat_plane)

    # Cube: 鮮やかな赤
    cube = bpy.data.objects.get("Cube")
    if cube is not None:
        mat_cube = create_material("CubeMaterial", (0.8, 0.1, 0.1, 1.0))
        if cube.data.materials:
            cube.data.materials[0] = mat_cube
        else:
            cube.data.materials.append(mat_cube)

    # Sphere: 鮮やかな青
    sphere = bpy.data.objects.get("Sphere")
    if sphere is not None:
        mat_sphere = create_material("SphereMaterial", (0.1, 0.1, 0.8, 1.0))
        if sphere.data.materials:
            sphere.data.materials[0] = mat_sphere
        else:
            sphere.data.materials.append(mat_sphere)


def create_sun_light():
    """
    シーンを照らすサンライトを作成して追加します.
    """
    light_data = bpy.data.lights.new(name="Sun", type='SUN')
    light_data.energy = 5.0
    light_object = bpy.data.objects.new(name="Sun", object_data=light_data)
    light_object.location = (5.0, 5.0, 10.0)
    bpy.context.collection.objects.link(light_object)


def setup_world_background():
    """
    ワールド背景を調整し、落ち着いた深みのある色合いに設定します.
    """
    world = bpy.context.scene.world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    bg = nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.05, 0.1, 0.15, 1.0)
        bg.inputs[1].default_value = 1.0


def create_camera_target():
    """
    カメラが向くターゲットとしての Empty を作成します.
    シーン中央（(0,0,0)）に配置します.
    
    Returns:
        Object: 作成したターゲット用 Empty
    """
    target = bpy.data.objects.new("CameraTarget", None)
    target.empty_display_type = 'PLAIN_AXES'
    target.location = (0.0, 0.0, 0.0)
    bpy.context.collection.objects.link(target)
    return target


def setup_camera_track(camera, target):
    """
    カメラに「Track To」制約を追加し、常にターゲットを向くようにします.
    
    Args:
        camera (Object): 対象のカメラオブジェクト
        target (Object): トラッキング対象のオブジェクト
    """
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.target = target
    # カメラの場合、通常は TRACK_NEGATIVE_Z, UP_Y とするのが一般的です.
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis = 'UP_Y'


def main():
    """
    メイン処理:
    - 出力先の設定・バックアップ
    - シーン初期化、ライティング・背景・オブジェクトの作成とマテリアル設定
    - カーブ、Empty(パスフォロワー)およびカメラの作成とアニメーション設定
    - カメラが初期状態からターゲット（シーン中央）を向くように設定
    - アニメーションレンダリング実行
    """
    # 出力フォルダの設定
    output_dir = os.path.join(os.getcwd(), "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_filepath = os.path.join(output_dir, "animation.mp4")
    backup_existing_file(output_filepath)

    # シーン初期化と各種設定
    clear_scene()
    setup_world_background()
    create_sun_light()

    # オブジェクト追加
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0.0, 0.0, -1.0))
    bpy.ops.mesh.primitive_cube_add(size=1, location=(2.0, 0.0, 0.0))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(-2.0, 0.0, 1.0))
    add_materials_to_objects()

    # カメラ移動用カーブの作成と、カーブに沿って移動する Empty（PathFollower）の生成
    curve = create_curve()
    follower = create_path_follower(curve)
    camera = create_camera(follower)
    animate_camera_zoom(camera)
    bpy.context.scene.camera = camera

    # カメラが初期状態から対象を向くよう、ターゲット Empty を作成してトラック制約を設定
    target = create_camera_target()
    setup_camera_track(camera, target)

    setup_render_settings(output_filepath)

    # アニメーションレンダリング実行
    bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
