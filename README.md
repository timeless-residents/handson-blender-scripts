# Blender Python スクリプト開発環境セットアップガイド

このリポジトリではBlenderのPythonスクリプト開発環境のセットアップ方法を説明します。

## 前提条件

- macOS
- Blenderがインストールされていること
- VS Code（オプション：より良い開発体験のため）

## Blenderのコマンドライン実行

### 基本的な起動方法

```bash
/Applications/Blender.app/Contents/MacOS/Blender
```

### Pythonスクリプトを実行する場合

```bash
/Applications/Blender.app/Contents/MacOS/Blender --python your_script.py
```

### バックグラウンドモード（GUIなし）で実行

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background
```

### バックグラウンドでPythonスクリプトを実行（推奨）

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python your_script.py
```

### エイリアスの設定（オプション）

毎回長いパスを入力する手間を省くために、以下のコマンドでエイリアスを設定できます：

```bash
echo 'alias blender="/Applications/Blender.app/Contents/MacOS/Blender"' >> ~/.zshrc
# または
echo 'alias blender="/Applications/Blender.app/Contents/MacOS/Blender"' >> ~/.bashrc
```

## VS Code統合

より効率的な開発のために、VS Codeに開発環境を統合することができます。

### 必要な拡張機能

1. "Blender Development"
2. "Python"

### VS Code設定

1. `settings.json` に以下を追加：

```json
{
    "blender.executeable": "/Applications/Blender.app/Contents/MacOS/Blender",
    "python.analysis.extraPaths": [
        "/Applications/Blender.app/Contents/Resources/4.0/scripts/modules"
    ]
}
```

2. `.vscode/launch.json` を作成：

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Blender",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "python": "/Applications/Blender.app/Contents/Resources/4.0/python/bin/python3.10",
            "env": {
                "PYTHONPATH": "/Applications/Blender.app/Contents/Resources/4.0/scripts/modules"
            }
        }
    ]
}
```

3. `.vscode/tasks.json` を作成：

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Run in Blender",
            "type": "shell",
            "command": "/Applications/Blender.app/Contents/MacOS/Blender --background --python ${file}",
            "group": {
                "kind": "build",
                "isDefault": true
            }
        }
    ]
}
```

## スクリプト開発のベストプラクティス

スクリプトの最初に以下のようなインポートチェックを入れることを推奨します：

```python
try:
    import bpy
except ImportError:
    print("このスクリプトはBlenderから実行する必要があります。")
    print("以下のコマンドを使用してください：")
    print("/Applications/Blender.app/Contents/MacOS/Blender --background --python script.py")
    exit(1)
```

## 注意事項

- bpyモジュールは直接pipでインストールすることはできません
- スクリプトは必ずBlenderの実行環境から実行する必要があります
- パスやバージョン番号は、インストールされているBlenderのバージョンによって異なる場合があります

## キーボードショートカット

- VS Codeでインタープリタを選択: `Command + Shift + P` → "Python: Select Interpreter"
- スクリプトの実行: `Command + Shift + B`（tasks.jsonの設定後）