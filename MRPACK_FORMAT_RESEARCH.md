# Modrinth Modpack Format (.mrpack) 研究文档

## 概述

`.mrpack` 是 Modrinth 平台的整合包文件格式，用于分发 Minecraft 模组整合包。

## 文件结构

`.mrpack` 文件本质上是一个 **ZIP 压缩包**，包含以下结构：

```
example.mrpack (ZIP 文件)
├── modrinth.index.json    # 必需的索引文件（位于根目录）
└── files/                 # 可选的文件目录
    ├── config/            # 配置文件
    ├── mods/              # 模组文件
    ├── resourcepacks/     # 资源包
    ├── shaderpacks/       # 光影包
    └── ...                # 其他需要覆盖的文件
```

## modrinth.index.json 格式

这是整合包的核心配置文件，必须位于 ZIP 文件的根目录。

### 完整结构示例

```json
{
  "formatVersion": 1,
  "game": "minecraft",
  "versionId": "1.0.0",
  "name": "我的整合包",
  "summary": "一个很棒的整合包",
  "files": [
    {
      "path": "mods/example-mod.jar",
      "hashes": {
        "sha512": "abcdef1234567890...",
        "sha1": "1234567890abcdef..."
      },
      "env": {
        "client": "required",
        "server": "required"
      },
      "downloads": [
        "https://cdn.modrinth.com/mod/xxx/version/yyy/file.jar"
      ],
      "fileSize": 123456
    },
    {
      "path": "config/mod-config.toml",
      "hashes": {
        "sha512": "fedcba0987654321..."
      }
    }
  ],
  "dependencies": {
    "minecraft": "1.20.1",
    "fabric-loader": ">=0.14.0",
    "quilt-loader": "*",
    "minecraft-resourcepacks": "*"
  }
}
```

### 字段详解

#### 顶层字段

| 字段名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| `formatVersion` | integer | ✓ | 格式版本号，当前为 `1` |
| `game` | string | ✓ | 游戏标识，通常是 `"minecraft"` |
| `versionId` | string | ✓ | 整合包版本号 |
| `name` | string | ✓ | 整合包名称 |
| `summary` | string | ✗ | 整合包简介 |
| `files` | array | ✓ | 文件列表 |
| `dependencies` | object | ✓ | 依赖项（游戏版本、加载器等） |

#### files 数组中的对象字段

| 字段名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| `path` | string | ✓ | 文件在实例目录中的相对路径 |
| `hashes` | object | ✓ | 文件哈希值（至少包含 sha512 或 sha1） |
| `hashes.sha512` | string | △ | SHA-512 哈希（推荐） |
| `hashes.sha1` | string | △ | SHA-1 哈希 |
| `env` | object | ✗ | 环境要求 |
| `env.client` | string | ✗ | 客户端要求：`"required"`, `"optional"`, `"unsupported"`, `"enforced"` |
| `env.server` | string | ✗ | 服务器要求：同上 |
| `downloads` | array | ✗ | 下载 URL 列表 |
| `fileSize` | integer | ✗ | 文件大小（字节） |

**env 字段说明：**
- `"required"`: 必须安装此文件
- `"optional"`: 可选文件
- `"unsupported"`: 不支持此环境（不会安装）
- `"enforced"`: 强制要求（类似 required，但更严格）

#### dependencies 对象字段

键值对形式，键为依赖项 ID，值为版本范围字符串。

常见依赖项：
- `"minecraft"`: Minecraft 游戏版本（如 `"1.20.1"`, `"~1.20.1"`）
- `"fabric-loader"`: Fabric 加载器版本
- `"quilt-loader"`: Quilt 加载器版本
- `"forge"`: Forge 加载器版本
- `"neoforge"`: NeoForge 加载器版本
- `"minecraft-resourcepacks"`: 资源包支持
- `"minecraft-shaders"`: 光影包支持

**版本范围语法：**
- `"1.20.1"`: 精确匹配
- `">=1.20"`: 大于等于
- `"~1.20.1"`: 兼容版本（小版本可变动）
- `"*"`: 任意版本

## 创建 .mrpack 的步骤

### Python 实现示例

```python
import zipfile
import json
import hashlib
from pathlib import Path

def calculate_hash(file_path, algorithm='sha512'):
    """计算文件的哈希值"""
    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def create_mrpack(output_path, name, version, game_version, files_list, summary=""):
    """
    创建 .mrpack 文件
    
    Args:
        output_path: 输出的 .mrpack 文件路径
        name: 整合包名称
        version: 整合包版本号
        game_version: Minecraft 版本
        files_list: 文件列表，每个元素包含：
            - path: 文件在实例中的路径
            - source: 源文件路径
            - env: 环境要求（可选）
            - downloads: 下载链接列表（可选）
    """
    
    # 构建 index 文件
    index = {
        "formatVersion": 1,
        "game": "minecraft",
        "versionId": version,
        "name": name,
        "summary": summary,
        "files": [],
        "dependencies": {
            "minecraft": game_version
        }
    }
    
    # 创建 ZIP 文件
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 处理每个文件
        for file_info in files_list:
            source_path = Path(file_info['source'])
            target_path = file_info['path']
            
            # 计算哈希
            sha512_hash = calculate_hash(source_path, 'sha512')
            sha1_hash = calculate_hash(source_path, 'sha1')
            
            # 构建文件条目
            file_entry = {
                "path": target_path,
                "hashes": {
                    "sha512": sha512_hash,
                    "sha1": sha1_hash
                },
                "fileSize": source_path.stat().st_size
            }
            
            # 添加环境要求
            if 'env' in file_info:
                file_entry['env'] = file_info['env']
            
            # 添加下载链接
            if 'downloads' in file_info:
                file_entry['downloads'] = file_info['downloads']
            
            index['files'].append(file_entry)
            
            # 将文件添加到 ZIP
            zipf.write(source_path, f"files/{target_path}")
        
        # 写入 index 文件
        zipf.writestr('modrinth.index.json', json.dumps(index, indent=2))
    
    print(f"已创建整合包：{output_path}")

# 使用示例
if __name__ == "__main__":
    files = [
        {
            "path": "mods/fabric-api.jar",
            "source": "/path/to/fabric-api.jar",
            "env": {"client": "required", "server": "required"},
            "downloads": ["https://cdn.modrinth.com/..."]
        },
        {
            "path": "config/my-mod.toml",
            "source": "/path/to/config.toml"
        }
    ]
    
    create_mrpack(
        output_path="my-pack.mrpack",
        name="我的整合包",
        version="1.0.0",
        game_version="1.20.1",
        files_list=files,
        summary="这是一个测试整合包"
    )
```

## 从现有实例导出 .mrpack

如果你要从现有的 Minecraft 实例导出整合包：

```python
import os
import json
import zipfile
import hashlib
from pathlib import Path

def export_instance_to_mrpack(instance_path, output_path, name, version):
    """
    从现有实例导出 .mrpack
    
    Args:
        instance_path: 实例目录路径
        output_path: 输出的 .mrpack 路径
        name: 整合包名称
        version: 整合包版本
    """
    
    instance = Path(instance_path)
    files_list = []
    
    # 检测游戏版本和加载器
    game_version = detect_game_version(instance)
    loader = detect_loader(instance)
    
    dependencies = {"minecraft": game_version}
    if loader:
        dependencies[loader['name']] = loader['version']
    
    # 收集 mods 目录
    mods_dir = instance / "mods"
    if mods_dir.exists():
        for mod_file in mods_dir.glob("*.jar"):
            rel_path = f"mods/{mod_file.name}"
            files_list.append({
                "path": rel_path,
                "source": str(mod_file),
                "env": {"client": "required", "server": "required"}
            })
    
    # 收集 config 目录
    config_dir = instance / "config"
    if config_dir.exists():
        for config_file in config_dir.rglob("*"):
            if config_file.is_file():
                rel_path = f"config/{config_file.relative_to(config_dir)}"
                files_list.append({
                    "path": rel_path,
                    "source": str(config_file)
                })
    
    # 收集 resourcepacks
    rp_dir = instance / "resourcepacks"
    if rp_dir.exists():
        for rp_file in rp_dir.rglob("*"):
            if rp_file.is_file():
                rel_path = f"resourcepacks/{rp_file.relative_to(rp_dir)}"
                files_list.append({
                    "path": rel_path,
                    "source": str(rp_file)
                })
    
    # 创建 mrpack
    create_mrpack_with_deps(
        output_path=output_path,
        name=name,
        version=version,
        game_version=game_version,
        dependencies=dependencies,
        files_list=files_list
    )

def detect_game_version(instance_path):
    """检测游戏版本（从 version.json 或其他文件）"""
    # 实现版本检测逻辑
    version_file = instance_path / "version.json"
    if version_file.exists():
        with open(version_file) as f:
            data = json.load(f)
            return data.get('id', '1.20.1')
    return "1.20.1"  # 默认值

def detect_loader(instance_path):
    """检测加载器类型和版本"""
    # Fabric: 检查 fabric-loader-*.jar
    # Forge: 检查 forge-*.jar 或 .minecraft/forgeVersion.txt
    # 实现检测逻辑
    return None
```

## 注意事项

1. **哈希算法**: 推荐使用 SHA-512，但也应该提供 SHA-1 以兼容旧客户端
2. **路径规范**: 使用正斜杠 `/`，即使是在 Windows 上
3. **文件大小**: `fileSize` 字段是可选的，但建议提供以便客户端验证
4. **环境变量**: 合理使用 `env` 字段来区分客户端专用和服务端专用的文件
5. **下载链接**: 对于来自 Modrinth 的模组，提供官方下载链接可以让客户端直接下载而不是从包内提取

## 参考资源

- Modrinth API 文档: https://docs.modrinth.com/
- Modrinth 整合包规范: https://support.modrinth.com/en/articles/8792413-modrinth-modpack-format-mrpack
- Knossos (Modrinth 官方启动器) 源码: https://github.com/modrinth/knossos

## 在 Bloret Launcher 中实现导出功能

基于你现有的代码结构，建议在以下位置添加功能：

1. **新增模块**: `modules/mrpack_export.py` - 导出逻辑
2. **UI 集成**: 在实例管理界面添加"导出为 .mrpack"按钮
3. **API 扩展**: 在 `modules/modrinth.py` 中添加相关函数

这样可以保持代码的组织性和可维护性。
