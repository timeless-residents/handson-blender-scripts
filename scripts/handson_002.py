import bpy
import random
import math


def setup_scene():
    # シーンをクリア
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    # カメラを追加
    bpy.ops.object.camera_add(location=(15, -15, 8))
    camera = bpy.context.active_object
    camera.rotation_euler = (math.radians(70), 0, math.radians(45))
    bpy.context.scene.camera = camera

    # 環境光の設定
    bpy.ops.object.light_add(type="SUN", location=(5, 5, 10))
    sun = bpy.context.active_object
    sun.data.energy = 3.0


def create_colored_material(name, base_color):
    material = bpy.data.materials.new(name=name)
    material.use_nodes = True
    nodes = material.node_tree.nodes

    # ノードをクリア
    nodes.clear()

    # プリンシプルBSDFを追加
    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.inputs["Base Color"].default_value = base_color
    principled.inputs["Metallic"].default_value = 0.7
    principled.inputs["Roughness"].default_value = 0.2

    # マテリアル出力を追加
    output = nodes.new("ShaderNodeOutputMaterial")

    # ノードを接続
    material.node_tree.links.new(principled.outputs["BSDF"], output.inputs["Surface"])

    return material


def create_abstract_shape():
    shapes = ["CONE", "SPHERE", "CYLINDER", "TORUS"]
    shape_type = random.choice(shapes)

    if shape_type == "CONE":
        bpy.ops.mesh.primitive_cone_add(vertices=random.randint(3, 8))
    elif shape_type == "SPHERE":
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=random.randint(8, 16), ring_count=random.randint(8, 16)
        )
    elif shape_type == "CYLINDER":
        bpy.ops.mesh.primitive_cylinder_add(vertices=random.randint(6, 12))
    else:  # TORUS
        bpy.ops.mesh.primitive_torus_add(
            major_segments=random.randint(12, 24), minor_segments=random.randint(6, 12)
        )

    obj = bpy.context.active_object

    # ランダムな変形を適用
    obj.scale = (
        random.uniform(0.5, 2.0),
        random.uniform(0.5, 2.0),
        random.uniform(0.5, 2.0),
    )

    obj.rotation_euler = (
        random.uniform(0, math.pi),
        random.uniform(0, math.pi),
        random.uniform(0, math.pi),
    )

    return obj


def main():
    setup_scene()

    # グラウンドプレーン（床）を作成
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
    floor = bpy.context.active_object
    floor_mat = create_colored_material("Floor", (0.2, 0.2, 0.2, 1))
    floor.data.materials.append(floor_mat)

    # 抽象的なオブジェクトを生成
    for i in range(8):
        x = random.uniform(-6, 6)
        y = random.uniform(-6, 6)
        z = random.uniform(0, 4)

        obj = create_abstract_shape()
        obj.location = (x, y, z)

        # ランダムな色のマテリアルを作成
        color = (
            random.uniform(0.2, 1),
            random.uniform(0.2, 1),
            random.uniform(0.2, 1),
            1,
        )
        mat = create_colored_material(f"Material_{i}", color)
        obj.data.materials.append(mat)

    # レンダリング設定
    bpy.context.scene.render.engine = "CYCLES"
    bpy.context.scene.cycles.samples = 128
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.context.scene.render.filepath = ".//output//handson_002.png"

    # レンダリングを実行
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    try:
        main()
        print("抽象的なシーンの生成とレンダリングが完了しました。")
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
