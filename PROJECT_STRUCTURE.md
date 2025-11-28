# MinecraftFRP 项目企划与架构文档

## 1. 项目概述
本项目 "MinecraftFRP" 是一个基于 Python 的 FRP (Fast Reverse Proxy) 客户端封装工具，专为 Minecraft 玩家设计。它提供了图形化界面 (GUI)，能够自动下载服务器列表、探测局域网内的 Minecraft 游戏端口，并一键开启内网穿透映射，方便玩家进行联机游戏。

## 2. 技术栈
- **编程语言**: Python 3.8+
- **GUI 框架**: PySide6 (基于 Qt)
- **核心功能**: FRP (通过 subprocess 调用 frpc 可执行文件)
- **依赖管理**: pip (requirements.txt)
- **打包工具**: PyInstaller
- **版本控制**: Git

## 3. Git 工作流与规范 (严格执行)

本项目采用严格的 Git 提交与分支管理规范，以确保代码库的整洁与可维护性。

### 3.1 分支管理策略
*   **主分支 (`main`)**: 仅存放经过测试、稳定可运行的代码。
*   **开发/功能分支 (`feat/xxx`, `fix/xxx`)**: 所有的开发工作**必须**在独立分支上进行。
    *   **规则**: 每进行一次较大的功能开发或架构调整时，**必须**新建一个分支。
    *   **命名范例**:
        *   新增功能: `feat/auto-mapping`
        *   修复 Bug: `fix/ui-freeze`
        *   重构代码: `refactor/config-manager`
    *   **合并要求**: 分支代码在确认无异常、可正常运行后，方可合并（Merge）到 `main` 分支。

### 3.2 Commit 提交规范
每次改动（即使是微小的改动）都应进行 Commit，避免一次性提交大量无关更改。

**格式**: `<Type>: <Subject>`

*   **Type (类型)**:
    *   `feat`: 新功能 (Feature)
    *   `fix`: 修复 Bug
    *   `docs`: 文档修改
    *   `style`: 代码格式修改 (不影响逻辑)
    *   `refactor`: 代码重构 (既无新功能也无 Bug 修复)
    *   `test`: 增加或修改测试
    *   `chore`: 构建过程或辅助工具的变动

*   **Subject (主题)**: 简短描述本次修改的内容 (50字以内)。

**Commit 范例**:
> `feat: 实现自动探测 Minecraft 局域网端口`  
> `fix: 修复配置文件加载失败的问题`  
> `docs: 更新项目架构文档`  
> `refactor: 重构服务器列表获取逻辑`

## 4. 开发路线图 (Roadmap)

### 当前已实现功能
*   [x] 模块化代码结构重构
*   [x] 基于 YAML 的配置文件管理
*   [x] 自动下载 FRP 服务器列表与广告配置
*   [x] 局域网 Minecraft 端口自动探测
*   [x] 图形化界面 (GUI) 与 昼夜主题切换
*   [x] 自动映射与地址复制功能

### 待开发/优化计划
*   [ ] 进一步完善异常处理机制
*   [ ] 优化多线程 Ping 测速性能
*   [ ] 支持更多类型的 FRP 配置选项

## 5. 目录结构

```
MinecraftFRP/
├── app.py                  # 程序主入口 (Minimal)
├── config/                 # 配置文件目录 (YAML/JSON)
│   ├── app_config.yaml     # 应用主配置
│   ├── ping_data.yaml      # Ping 数据
│   ├── frp-server-list.json # 服务器列表
│   └── ads.json            # 广告数据
├── src/                    # 源代码目录
│   ├── core/               # 核心业务逻辑
│   │   ├── config_manager.py
│   │   ├── frpc_thread.py
│   │   ├── server_manager.py
│   │   └── ...
│   ├── gui/                # 图形界面模块
│   │   ├── main_window.py
│   │   └── ...
│   ├── network/            # 网络相关模块
│   ├── tools/              # 工具模块
│   └── utils/              # 通用工具模块
├── main_original.py        # 原始备份
├── requirements.txt        # 依赖列表
└── README.md
```

## 6. 模块设计与命名规范 (Module Design & Naming)

### 6.1 职责单一化与细分 (Single Responsibility & Granularity)
*   **单一职责原则 (SRP)**: 每个模块文件应仅负责一个单一的功能点或逻辑单元。避免创建“上帝类”。
*   **文件粒度**: 严格控制单个文件的代码量。
*   **多模块与子目录**: 鼓励建立多个模块文件及子目录来组织代码。
    *   **递归深度**: 允许并鼓励使用深层目录结构，最大递归深度层级为 **5层**。

### 6.2 命名规范 (Naming Convention)
*   **模块文件名**: 必须采用 **驼峰命名法 (CamelCase/UpperCamelCase)**。
    *   例如: `PacketHandler.py`, `ConfigLoader.py`, `ServerManager.py`。
    *   *(注意: 当前项目部分旧文件可能使用蛇形命名，后续重构或新文件应遵循此规范)*
*   **类名**: 推荐与文件名保持一致，使用大驼峰命名法。
*   **目录名**: 推荐使用大驼峰命名法或全小写（根据具体层级保持统一）。

## 7. 配置、数据与入口规范 (Config, Data & Entry Point)

### 7.1 程序入口 (Entry Point)
*   **文件**: `app.py`
*   **原则**: **最小化 (Minimalism)**。
    *   仅负责参数解析、加载配置、初始化核心容器及启动主循环。
    *   **严禁**在入口文件中编写业务逻辑。

### 7.2 配置文件 (Configuration)
*   **目录**: `config/`
*   **格式**: **YAML** (`.yaml`) 或 **JSON** (`.json`)
*   **用途**: 存储用户配置、服务器列表、应用状态等。

## 8. 日志与异常处理规范 (Logging & Error Handling)

### 8.1 全局日志集成 (Global Integration)
*   **强制要求**: 项目中每一个功能模块和逻辑类都应集成 `Logger` 模块（或统一的 logging 机制）。
*   **高强度记录**: 关键行为（网络请求、状态变更、IO操作）必须有日志记录。
*   **调试追踪**: 错误排查以日志为第一依据。

### 8.2 日志等级与格式
*   **[INFO]**: 正常流程、状态更新。
*   **[WARN]**: 非致命异常、默认值使用。
*   **[ERROR]**: 功能失败、未捕获异常。

### 8.3 异常捕获
*   所有的 `try-except` 块中，`except` 分支必须记录详细的错误信息。

## 9. 项目变更日志 (Logs)

**重要规则**: 任何对项目架构、功能逻辑或规范的重大修改，都**必须**在此文档中进行记录。记录应参考 Git Commit 记录，确保可追溯性。

| 日期 (Date) | 类型 (Type) | 描述 (Description) | Git Hash (Short) / Branch |
| :--- | :--- | :--- | :--- |
| 2025-11-28 | `refactor` | 初始化模块化项目结构，分离核心逻辑与界面 | `87d948f` (refactor/init-structure) |
| 2025-11-28 | `docs` | 制定并写入项目企划与架构文档，添加 Logs 规则 | `9351384` (refactor/init-structure) |
| 2025-11-28 | `fix` | 修复 GUI 关闭时的线程安全隐患 (添加 wait()) | `348cafd` (refactor/init-structure) |
| 2025-11-28 | `refactor` | 加密内置默认服务器列表，混淆密钥 (Anti-Cracking) | `348cafd` (refactor/init-structure) |
| 2025-11-28 | `fix` | 修复因移除 DEFAULT_SERVERS 导致的 ImportError | `97777ac` (refactor/init-structure) |
| 2025-11-28 | `refactor` | PyInstaller打包优化 (内置 frpc.exe 和 logo.ico) | `68b8006` (refactor/init-structure) |