# MinecraftFRP 项目结构

## 项目重构说明

根据 CLAUDE.md 的要求，已将单一文件 `main_original.py` 重构为模块化结构。

## 新的项目结构

```
MinecraftFRP/
├── app.py                  # 程序主入口
├── config/                 # 配置文件目录
│   ├── app_config.yaml    # 应用主配置文件（含设置选项）
│   ├── ping_data.yaml     # Ping数据存储文件
│   ├── frpc.ini          # FRP客户端配置文件（程序生成）
│   ├── ads.json          # 广告配置文件（自动下载）
│   └── frp-server-list.json # 服务器列表文件（自动下载）
├── src/                   # 源代码目录
│   ├── __init__.py
│   ├── core/              # 核心业务逻辑
│   │   ├── __init__.py
│   │   ├── config_manager.py    # FRP配置文件管理
│   │   ├── frpc_thread.py       # FRP客户端线程
│   │   ├── ping_thread.py       # Ping测试线程
│   │   ├── server_manager.py    # 服务器列表管理
│   │   └── yaml_config.py       # YAML配置管理器
│   ├── gui/               # 图形界面模块
│   │   ├── __init__.py
│   │   ├── dialogs.py           # 对话框组件
│   │   ├── main_window.py       # 主窗口
│   │   └── styles.py            # 界面样式
│   ├── network/           # 网络相关模块
│   │   ├── __init__.py
│   │   ├── minecraft_lan.py     # Minecraft局域网探测
│   │   └── ping_utils.py        # Ping工具函数
│   ├── tools/             # 工具模块
│   │   ├── __init__.py
│   │   └── ping_manager.py      # Ping管理器
│   └── utils/             # 通用工具模块
│       ├── __init__.py
│       ├── ad_manager.py        # 广告管理器
│       ├── crypto.py            # 加密解密工具
│       └── port_generator.py    # 端口生成器
├── main_original.py       # 原始单一文件（保留作参考）
└── requirements.txt       # 依赖包列表
```

## 主要改进

### 1. 模块化设计
- **职责单一**: 每个模块专注特定功能
- **代码量控制**: 每个模块代码量控制在200行以内
- **可维护性**: 提高了代码的可读性和可维护性

### 2. 配置管理优化
- **YAML格式**: 配置文件统一采用YAML格式，更易读
- **默认配置**: 程序启动时自动检查和创建默认配置文件
- **集中管理**: 所有配置文件存放在 `config/` 目录
- **自动图标**: 程序启动时自动加载 `logo.ico` 作为程序图标

### 3. 文件路径优化
- **frpc.ini**: 自动生成在 `config/frpc.ini`，执行时使用 `frpc.exe -c config/frpc.ini`
- **ads.json**: 自动下载并存储在 `config/ads.json`
- **服务器列表**: 自动下载并存储在 `config/frp-server-list.json`
- **Ping数据**: 存储在 `config/ping_data.yaml`

### 4. 新增设置功能 (2025-8-26 更新)
- **设置标签页**: 新增专用设置界面
- **自动映射**: 检测到Minecraft端口时自动开始映射并复制链接
- **主题控制**: 手动切换昼夜模式，暂停自动主题切换
- **配置持久化**: 设置自动保存到配置文件

### 5. 功能保持完整
- **兼容性**: 保持原有功能完全不变
- **命令行支持**: 继续支持命令行模式运行
- **图形界面**: GUI功能完整保留，新增设置管理

## 运行方式

### 图形界面模式
```bash
python app.py
```

### 命令行模式
```bash
python app.py --local_port 25565 --server 香港
python app.py --auto-find --server 宁波
```

## 模块说明

### 核心模块 (src/core/)
- `config_manager.py`: FRP配置文件的创建和删除
- `frpc_thread.py`: FRP客户端进程管理线程
- `ping_thread.py`: 服务器Ping测试线程
- `server_manager.py`: 服务器列表的加载和管理
- `yaml_config.py`: YAML配置文件的读写管理

### 界面模块 (src/gui/)
- `main_window.py`: 主窗口界面和事件处理
- `dialogs.py`: 各种对话框组件
- `styles.py`: 昼夜主题样式定义

### 网络模块 (src/network/)
- `minecraft_lan.py`: Minecraft局域网游戏端口自动探测
- `ping_utils.py`: Ping测试和数据存储工具

### 工具模块 (src/tools/)
- `ping_manager.py`: Ping命令执行管理器

### 通用工具 (src/utils/)
- `ad_manager.py`: 广告内容的下载和显示管理
- `crypto.py`: 服务器列表的加密解密处理
- `port_generator.py`: 随机端口生成，避开保留端口

## 技术特性

- **线程安全**: 保持多线程操作的安全性
- **资源管理**: 正确的线程和进程资源清理
- **错误处理**: 完善的异常处理机制
- **配置验证**: 启动时检查必要文件和配置
- **兼容性**: 保持与原版本的完全兼容

## 新功能详解 (2025-8-26)

### 设置标签页
程序界面新增"设置"标签页，提供以下功能：

#### 自动映射
- **功能**: 检测到Minecraft端口开放时，自动填入端口并根据选择的线路开始映射
- **特性**: 映射成功后自动复制地址到剪贴板
- **智能处理**: 端口变化时自动终止旧映射，重新开始新流程
- **用户控制**: 可随时开启/关闭此功能

#### 熄灭灯泡（主题模式）
- **功能**: 手动控制界面主题（夜间/昼间模式）
- **特性**: 开启后暂停程序的自动昼夜主题切换逻辑
- **即时生效**: 设置变更后立即应用新主题
- **配置保存**: 设置自动保存，重启后保持选择