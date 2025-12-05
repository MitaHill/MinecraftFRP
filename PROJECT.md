# MinecraftFRP 项目企划与架构文档

## 1. 项目概述
本项目 "MinecraftFRP" 是一个基于 Python 的 FRP (Fast Reverse Proxy) 客户端封装工具，专为 Minecraft 玩家设计。它提供了图形化界面 (GUI)，能够自动下载服务器列表、探测局域网内的 Minecraft 游戏端口，并一键开启内网穿透映射，方便玩家进行联机游戏。

## 1.5 对AI的说明
当你阅读此行文字时，请记住：
和平时的代码生成不同，这个项目的代码质量要求非常高，必须严格遵守文档中的各项规范和要求。
请务必完整、准确地理解并执行文档中的每一条规范，确保生成的代码符合项目的高标准。
如果你在生成代码时遇到任何不确定的地方，请务必参考并遵循本项目企划与架构文档中的相关内容，确保代码质量和一致性。
你的每一次代码生成都将直接影响项目的整体质量和可维护性，请务必认真对待每一个细节，严格按照文档要求进行编码。
感谢你的理解与配合！
以及请使用**简体中文**语言和用户进行对话沟通，以确保信息传达的准确性和一致性。
*   **交互式脚本**: AI助手不应尝试执行需要用户输入的交互式脚本（如 `build.py`）。应当等待用户手动执行，并根据用户提供的结果或反馈来继续下一步工作。

## 2. 技术栈
- **编程语言**: Python 3.8+
- **GUI 框架**: PySide6 (基于 Qt)
- **核心功能**: FRP (通过 subprocess 调用 frpc 可执行文件)
- **依赖管理**: pip (requirements.txt)
- **打包工具**: Nuitka
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
*   [x] 核心配置加密存储与动态加载 (Anti-Cracking)
*   [x] 完整的单文件打包 (内置 frpc, tracert, logo)
*   [x] 基于 Git 版本号的自动化构建流程

### 待开发/优化计划
*   [ ] 进一步完善异常处理机制
*   [ ] 优化多线程 Ping 测速性能
*   [ ] 支持更多类型的 FRP 配置选项
*   [ ] **客户端自动更新功能**
    *   [ ] **检查与下载**:
        *   [ ] 在主程序启动的后台线程中，从服务器异步获取 `version.json`。
        *   [ ] 比较本地版本与服务器版本，若有更新则弹出提示对话框，并显示更新日志。
        *   [ ] 用户确认后，在后台线程下载新版本程序，并可显示下载进度。
        *   [ ] 下载完成后，校验文件的 SHA256 哈希值，确保文件完整与安全。
    *   [ ] **执行与替换**:
        *   [ ] 创建一个独立的 `updater.py` 脚本，其唯一职责是执行文件替换和重启操作。
        *   [ ] `build.py` 脚本增加新逻辑：先将 `updater.py` 打包成 `updater.exe`。
        *   [ ] `build.py` 在打包主程序时，将 `updater.exe` 作为二进制资源嵌入。
        *   [ ] 主程序在校验下载成功后，从自身资源中释放 `updater.exe` 到临时目录。
        *   [ ] 主程序启动 `updater.exe`（通过命令行参数传递新/旧文件路径及主进程ID），然后完全退出。
        *   [ ] `updater.exe` 等待主进程结束后，执行文件覆盖，并重新启动新版主程序。

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

### 6.3 辅助脚本规范 (Scripting Convention)
*   **语言统一**: 为保证项目的技术栈统一与可维护性，所有辅助脚本（如构建、部署、自动化任务等）**必须**使用 **Python** 语言编写。
*   **入口文件**: 根目录下的 `build.py` 是项目主要的自动化入口。

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

## 9. 安全与稳定性规范 (Security & Stability)

### 9.1 配置加密 (Anti-Cracking)
*   **禁止明文**: 严禁在源代码中以明文形式存储关键配置数据（如默认服务器列表、Token、密钥）。
*   **加密存储**: 敏感数据应加密存储（如 AES），并在运行时动态解密。
*   **密钥混淆**: 解密密钥不得以单一字符串字面量形式出现，必须进行动态拼接或混淆。

### 9.2 线程安全 (Thread Safety)
*   **优雅退出**: 程序退出时，必须确保所有子线程（如 FRP 进程线程、网络轮询线程）已安全终止。
    *   必须调用 `wait()` 方法等待线程清理完毕，禁止仅使用 `stop()` 或 `terminate()` 后直接退出主进程。

## 10. 打包与发布规范 (Packaging)

### 10.1 Nuitka 打包标准
*   **编译目标**: Nuitka 将 Python 源码编译为C语言级别，以追求更高的性能和反逆向能力。
*   **单文件发布**: 默认使用 `--onefile` 模式。
*   **隐藏控制台**: GUI 程序必须使用 `--windows-disable-console` (或 `--disable-console`) 隐藏 CMD 窗口。
*   **资源内置**: 所有外部依赖（如 `frpc.exe`, 图标文件等）必须通过 `--include-data-file` 或 `--include-data-dir` 等参数内置到 EXE 中。

### 10.2 路径解析
*   **动态路径**: 代码中禁止使用硬编码的相对路径加载资源。
*   **统一接口**: 必须使用 `src.utils.path_utils.get_resource_path` (或类似函数) 来自动处理开发环境与打包环境 (`sys._MEIPASS`) 的路径差异。

### 10.3 版本归档
*   **Git Hash**: 打包输出目录必须包含当前的 Git Commit Hash (Short)，以便区分不同版本构建。
    *   格式: `dist/AppName_<git_hash>`

### 10.4 自动更新与分发 (Auto-Update & Distribution)

为了实现一个健壮、安全且不易被杀毒软件误报的自动更新功能，本项目采用**“独立Python更新器”**方案。

*   **架构设计**:
    1.  **独立更新器**: 开发一个独立的 `updater.py` 脚本，其唯一职责是执行更新操作。该脚本将被 Nuitka 打包成 `updater.exe`。
    2.  **资源嵌入**: 在最终打包 `MinecraftFRP.exe` 时，会将 `updater.exe` 作为二进制资源嵌入到主程序内部。用户下载的始终是单文件程序。

*   **更新流程**:
    1.  **检查更新**: 主程序 `MinecraftFRP.exe` 通过访问版本清单文件，判断是否存在新版本。
    2.  **释放更新器**: 用户同意更新后，主程序会将内置的 `updater.exe` 释放到系统临时目录。
    3.  **执行并退出**: 主程序启动 `updater.exe`，并通过命令行参数传递必要信息（如主进程ID、新旧文件路径），然后主程序完全退出。
    4.  **更新器接管**: `updater.exe` 确认主程序退出后，执行文件替换操作，并能以更智能的方式处理潜在的异常（如文件占用、权限问题）。
    5.  **重启**: 更新完成后，`updater.exe` 负责重新启动新版本的 `MinecraftFRP.exe`。

*   **版本清单与下载地址**:
    *   **版本清单**: 自动更新机制依赖于服务器上的 `version.json` 文件来获取最新版本信息。其固定访问地址为：
        *   `https://z.clash.ink/chfs/shared/MinecraftFRP/version.json`
    *   **固定下载地址**: 最新版本的 `MinecraftFRP.exe` 程序包将始终可通过以下地址获取：
        *   `https://z.clash.ink/chfs/shared/MinecraftFRP/lastet/MinecraftFRP.exe`

### 10.5 Nuitka 构建命令
*   **一键构建**: 根目录下的 `build.py` 脚本提供了自动化构建功能，可一键完成编译、打包和重命名。
*   **核心命令参考**:
    ```shell
    .\.venv\Scripts\python.exe -m nuitka --onefile --windows-disable-console --plugin-enable=pyside6 --windows-icon-from-ico=logo.ico --include-data-file=frpc.exe=frpc.exe --include-data-file=tracert_gui.exe=tracert_gui.exe --include-data-file=logo.ico=logo.ico --output-dir=<OUTPUT_DIR> --assume-yes-for-downloads app.py
    ```

## 11. 项目变更日志 (Logs)

**重要规则**: 任何对项目架构、功能逻辑或规范的重大修改，都**必须**在此文档中进行记录。记录应参考 Git Commit 记录，确保可追溯性。

| 日期 (Date) | 类型 (Type) | 描述 (Description) | Git Hash (Short) / Branch |
| :--- | :--- | :--- | :--- |
| 2025-11-28 | `refactor` | 初始化模块化项目结构，分离核心逻辑与界面 | `87d948f` (refactor/init-structure) |
| 2025-11-28 | `docs` | 制定并写入项目企划与架构文档，添加 Logs 规则 | `9351384` (refactor/init-structure) |
| 2025-11-28 | `fix` | 修复 GUI 关闭时的线程安全隐患 (添加 wait()) | `348cafd` (refactor/init-structure) |
| 2025-11-28 | `refactor` | 加密内置默认服务器列表，混淆密钥 (Anti-Cracking) | `348cafd` (refactor/init-structure) |
| 2025-11-28 | `fix` | 修复因移除 DEFAULT_SERVERS 导致的 ImportError | `97777ac` (refactor/init-structure) |
| 2025-11-28 | `refactor` | PyInstaller打包优化 (内置 frpc.exe 和 logo.ico) | `d2b66b6` (refactor/init-structure) |
| 2025-11-28 | `refactor` | 封装 tracert_gui.exe 并实现基于 Git Hash 的多版本打包 | `2d5bc5f` (refactor/init-structure) |
| 2025-11-28 | `docs` | 更新项目企划，增加安全、稳定性及打包发布规范 | `c7afce0` (refactor/init-structure) |
| 2025-11-28 | `feat` | 默认开启自动映射功能 | `2f7043e` (refactor/init-structure) |
| 2025-11-28 | `refactor` | GUI模块重构：拆分 Tab 组件，重命名文件符合 PascalCase 规范 | `d76f885` (refactor/init-structure) |
| 2025-11-28 | `fix` | 修复 MainWindow.py 语法错误 | `a287bf6` (refactor/init-structure) |
| 2025-11-28 | `fix` | 修复 GUI 重构后的 ImportError 和 SyntaxError | `2dd855d` (refactor/init-structure) |
| 2025-11-28 | `refactor` | 深度模块化 GUI 代码并修复初始化错误 | `3bd1949` (refactor/init-structure) |
| 2025-11-28 | `chore` | 执行正式打包构建 (PyInstaller) | `3bd1949` (refactor/init-structure) |

## 12. 自动化构建与部署 (CI/CD)

本项目拥有一套基于 Python 的自动化构建与部署流水线，其核心是根目录下的 `build.py` 脚本。

### 12.1 核心组件
*   **`build.py`**: 自动化主脚本，负责驱动整个流程。
*   **`cicd.yaml`**: 流水线配置文件，用于定义版本号、部署目标服务器信息、打包参数等。

### 12.2 自动化流程
运行 `python build.py` 后，脚本将自动执行以下端到端(End-to-End)任务：
1.  **读取配置**: 解析 `cicd.yaml` 获取当前版本号和部署配置。
2.  **Nuitka 编译**: 调用 Nuitka 将 `app.py` 打包为高性能的单文件可执行程序。
3.  **版本化命名**: 根据当前版本号，将编译产物重命名（例如 `MinecraftFRP_0.5.0.exe`）。
4.  **生成清单**:
    *   自动计算可执行文件的 **SHA256** 哈希值，用于客户端安全校验。
    *   自动获取当前的 **Git Commit Hash**。
    *   将版本号、Git Hash、SHA256等信息组装成 `version.json` 文件。
5.  **安全部署 (可选)**:
    *   脚本会交互式地询问是否部署。
    *   如果确认，会**安全地提示输入SSH密码**（密码仅在内存中，不保存）。
    *   通过 SFTP 将编译好的 `.exe` 文件和 `version.json` 文件上传到`cicd.yaml`中指定的服务器路径。
6.  **版本递增**: 部署成功或选择不部署后，脚本会自动将 `cicd.yaml` 中的补丁版本号加一，为下一次构建做准备。

### 12.3 如何使用
确保已安装所有 `requirements.txt` 中的依赖后，在项目根目录的虚拟环境中执行：
```shell
python build.py
```
