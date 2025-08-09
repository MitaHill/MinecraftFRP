# Minecraft FRP 端口映射工具

## 项目简介

这是一个基于Python和PySide6开发的Minecraft局域网多人游戏端口映射工具，通过FRP（Fast Reverse Proxy）隧道技术，使玩家能够从外网连接到本地Minecraft服务器。

## 主要功能

- **自动检测Minecraft服务器端口**：自动监听局域网广播，发现Minecraft服务器端口
- **多服务器支持**：支持多个FRP服务器线路，可实时测试延迟
- **图形化界面**：基于PySide6的用户友好界面，支持明暗主题
- **命令行支持**：支持CLI模式，适合服务器环境使用
- **网络工具集**：内置ping测试、路由追踪、网络适配器查看等工具
- **服务器列表编辑**：内置图形化服务器列表编辑器，支持加密存储

## 技术架构

### 目录结构

```
MinecraftFRP/
├── main.py                 # 程序主入口
├── main_original.py        # 原始单文件版本备份
├── requirements.txt        # 依赖列表
├── config/                 # 配置和数据文件目录
│   ├── app_config.yaml     # 应用配置
│   ├── user_data.yaml      # 用户数据
│   ├── ads.json           # 广告数据（下载后存储）
│   ├── frp-server-list.json # 服务器列表（下载后存储）
│   └── ping_data.json     # Ping测试结果缓存
├── src/                    # 源代码模块
│   ├── frp-client/        # FRP客户端文件
│   │   ├── frpc.exe       # FRP客户端程序
│   │   └── frpc.ini       # FRP配置文件（运行时生成）
│   ├── gui/               # 图形界面模块
│   │   ├── window.py      # 主窗口
│   │   ├── dialogs.py     # 对话框
│   │   └── styles.py      # 样式定义
│   ├── network/           # 网络功能模块
│   │   ├── frpc_thread.py    # FRP客户端线程
│   │   ├── lan_poller.py     # LAN轮询器
│   │   ├── ping_thread.py    # Ping测试线程
│   │   ├── ads_manager.py    # 广告管理
│   │   └── server_loader.py  # 服务器列表加载
│   ├── config/            # 配置管理模块
│   │   ├── manager.py     # 配置文件管理
│   │   └── yaml_manager.py   # YAML配置管理
│   ├── tools/             # 工具模块
│   │   └── edit_frp_server_list.py # 服务器列表编辑器
│   └── utils/             # 工具函数模块
│       ├── constants.py   # 常量定义
│       ├── port_generator.py # 端口生成
│       ├── ping.py        # Ping工具
│       ├── file_io.py     # 文件IO操作
│       ├── crypto.py      # 加密解密
│       └── lan_utils.py   # LAN工具
├── Project.md             # 项目说明文档
└── CLAUDE.md              # 开发说明文档
```

### 模块职责

- **main.py**: 程序入口，负责参数解析和应用初始化
- **src/gui/**: 图形界面相关功能，包括主窗口、对话框和样式
- **src/network/**: 网络通讯和多线程管理
- **src/config/**: 配置文件管理，支持YAML格式
- **src/tools/**: 工具模块，包括服务器列表编辑器等实用工具
- **src/utils/**: 通用工具函数和常量定义

## 依赖项

### 外部依赖
- `PySide6`: Qt6图形界面框架
- `pycryptodome`: AES加密库
- `requests`: HTTP请求库
- `PyYAML`: YAML配置文件支持

### 系统要求
- Python 3.8+
- Windows操作系统
- frpc.exe（FRP客户端，需要单独下载）

## 使用方法

### GUI模式（推荐）
```bash
python main.py
```

### CLI模式
```bash
# 指定本地端口和服务器
python main.py --local_port 25565 --server "北京1"

# 自动检测端口
python main.py --auto-find --server "香港"

# 自动检测+备用端口
python main.py --auto-find --local_port 25565
```

## 配置文件

### 应用配置 (config/app_config.yaml)
包含应用的基本设置，如主题、窗口大小、网络参数等。

### 用户数据 (config/user_data.yaml)
存储用户的使用记录和偏好设置，如上次使用的服务器、ping缓存等。

## 开发特性

- **模块化设计**：每个模块专注特定功能，便于维护和扩展
- **配置驱动**：使用YAML配置文件，便于定制和部署
- **多线程架构**：FRP进程、LAN检测、ping测试等功能独立运行
- **错误处理**：完善的异常处理和用户提示
- **代码组织**：遵循Python最佳实践，代码结构清晰

## 未来改进

- [ ] 支持更多操作系统（Linux/macOS）
- [ ] 添加配置文件加密
- [ ] 实现插件系统
- [ ] 添加使用统计和分析功能
- [ ] 支持自定义服务器配置