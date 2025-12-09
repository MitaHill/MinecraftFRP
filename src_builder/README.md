# Build System (src_builder)

模块化构建系统，用于编译和部署 MinecraftFRP。

## 模块结构

```
src_builder/
├── __init__.py           # 包初始化
├── config.py            # 配置管理 (BuildConfig)
├── utils.py             # 通用工具函数
├── version_manager.py   # 版本和发布说明管理
├── builder.py           # Nuitka 编译器封装
└── deployer.py          # SSH/SFTP 部署
```

## 模块说明

### config.py - BuildConfig
负责加载和管理 cicd.yaml 配置文件：
- `get_version_string()` - 获取当前版本号
- `increment_version()` - 递增补丁版本号
- `get_ssh_config()` - 获取 SSH 配置
- `get_nuitka_config()` - 获取 Nuitka 配置

### utils.py
通用工具函数：
- `run_command()` - 执行命令并实时输出
- `verify_dependencies()` - 验证必需文件存在
- `clean_cache()` - 清理 Nuitka 缓存

### version_manager.py - VersionManager
版本信息和发布说明管理：
- `generate_release_notes()` - 从 Git 生成发布说明
- `create_version_json()` - 生成 version.json 元数据文件
- `update_version_file()` - 更新 src/_version.py

### builder.py - NuitkaBuilder
Nuitka 编译器封装：
- `build_updater()` - 编译更新器
- `build_main_app()` - 编译主应用程序
- 自动处理编译选项和依赖包含

### deployer.py - Deployer
SSH/SFTP 部署功能：
- `deploy()` - 上传可执行文件和 version.json 到远程服务器
- 优化的传输参数和进度显示

## 使用示例

```python
from src_builder.config import BuildConfig
from src_builder.builder import NuitkaBuilder
from src_builder.deployer import Deployer
from src_builder.version_manager import VersionManager

# 加载配置
config = BuildConfig()
version = config.get_version_string()

# 构建
builder = NuitkaBuilder(sys.executable, cache_dir, fast_build=False)
exe_path, build_time = builder.build_main_app(version, output_dir, updater_path)

# 部署
deployer = Deployer(ssh_config, username, password)
deployer.deploy(exe_path, version_json_path)
```

## 命令行使用

```bash
# 快速构建（无 LTO 优化）
python build.py --fast

# 构建并部署
python build.py --upload

# 快速构建并部署
python build.py --fast --upload

# 清理缓存后构建
python build.py --clean

# 仅验证依赖
python build.py --verify-only

# 跳过更新器重新构建
python build.py --skip-updater
```

## 优势

1. **模块化** - 每个功能独立模块，易于维护和测试
2. **可复用** - 模块可在其他脚本中复用
3. **清晰的职责分离** - 配置、构建、部署各司其职
4. **易于扩展** - 添加新功能只需新增模块
5. **参数化** - 支持命令行参数快速调整构建选项

## 依赖

- PyYAML - YAML 配置文件解析
- paramiko - SSH/SFTP 部署
- Nuitka - Python 编译器
