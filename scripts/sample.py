try:
    import bpy
except ImportError:
    print("このスクリプトはBlenderから実行する必要があります。")
    print("以下のコマンドを使用してください：")
    print("/Applications/Blender.app/Contents/MacOS/Blender --background --python script.py")
    exit(1)
print(bpy.app.version_string)
