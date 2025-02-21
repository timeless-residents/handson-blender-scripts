import bpy
import os
import shutil
from math import pi
from random import uniform
import time

# 実行時間計測用
start_time = time.time()

# outputディレクトリを準備
output_dir = "output"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 既存のレンダリング結果を退避
render_output = os.path.join(output_dir, "render.png")
if os.path.exists(render_output):
    timestamp = int(time.time())
    backup_file = os.path.join(output_dir, f"render_backup_{timestamp}.png")
    shutil.move(render_output, backup_file)

# シーンをクリア
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()


# ローポリ円柱（ミニタワー）の作成
def create_mini_tower(location):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=8, radius=0.5, depth=3.0, location=location  # 8面のローポリ
    )
    tower = bpy.context.active_object
    # 少しランダムに回転
    tower.rotation_euler[2] = uniform(0, 2 * pi)
    return tower


# ミニタワーを10x10のグリッドに配置（合計100個）
towers = []
for x in range(-5, 5):
    for y in range(-5, 5):
        loc = (x * 2, y * 2, 0)  # 2単位間隔で配置
        tower = create_mini_tower(loc)
        towers.append(tower)

# カメラの設定
bpy.ops.object.camera_add(location=(15, -15, 10))
camera = bpy.context.active_object
camera.rotation_euler = (1.0, 0, 0.8)  # 斜め上から見下ろす角度
bpy.context.scene.camera = camera

# 簡易照明の追加
bpy.ops.object.light_add(type="SUN", location=(10, 10, 10))
light = bpy.context.active_object
light.data.energy = 2.0

# レンダリング設定
scene = bpy.context.scene
scene.render.engine = "CYCLES"  # より高质量なレンダリング
scene.render.resolution_x = 800
scene.render.resolution_y = 600
scene.render.filepath = render_output
scene.cycles.samples = 32  # 高速レンダリング用にサンプル数を低めに

# レンダリング実行
bpy.ops.render.render(write_still=True)

# 実行時間計測
end_time = time.time()
execution_time = end_time - start_time
print(f"Execution time: {execution_time:.2f} seconds")

# 必要に応じてシーンをクリーンアップ
bpy.ops.object.select_all(action="SELECT")
# bpy.ops.object.delete()  # 必要に応じてコメント解除
