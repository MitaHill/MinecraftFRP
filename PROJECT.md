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

### 重要规范：

*   **交互式脚本**: AI助手不应尝试执行需要用户输入的交互式脚本（如 `build.py`）。应当等待用户手动执行，并根据用户提供的结果或反馈来继续下一步工作。

*   **🚫 禁止使用 BAT/CMD/PowerShell 脚本**: 
    - **所有自动化脚本必须使用 Python 编写**
    - 禁止创建 `.bat` / `.cmd` / `.ps1` 文件
    - 原因：跨平台兼容性差、编码问题频发（PowerShell 中文乱码）、难以维护
    - 例外：仅允许使用 Python 的 `subprocess` 模块调用系统命令
    - 正确做法：将所有脚本逻辑封装为 Python 函数或模块

## 2. 技术栈
- **编程语言**: Python 3.8+
- **GUI 框架**: PySide6 (基于 Qt)
- **核心功能**: FRP (通过 subprocess 调用 frpc 可执行文件)
- **依赖管理**: pip (requirements.txt)
- **打包工具**: Nuitka
- **安装程序**: PySide6 (轻量化安装器)
- **版本控制**: Git

## 2.5 架构版本说明

### 安装器架构 (当前) - Inno Setup 专业安装器

项目采用 **Inno Setup** 专业安装程序，提供标准Windows安装体验；统一为“目录模式”发布（非单文件），所有组件以“exe + 子目录”形态交付。

---

#### 核心改进：
1. **Inno Setup 安装器**：使用业界标准的 Inno Setup 6，提供完整的 Windows 安装向导
2. **目录化部署**：采用标准软件目录结构（Program Files）
3. **启动器 (Launcher)**：用户入口改为 `launcher.exe`，负责更新检测和启动主程序
4. **配置文件分离**：用户数据存储在 `文档/MitaHillFRP/` 目录，支持跨版本保留配置
5. **覆盖更新机制**：类似微信/Chrome的升级体验，直接覆盖安装，无需卸载
6. **自动卸载程序**：完整的卸载功能，可选保留配置文件

---

#### 重要：AppId 锁定

**永远不要修改这个 GUID！**

```
AppId: {8B5F6C3D-9E4A-4F2B-A1D3-7C8E9F0B1A2C}
```

**为什么重要？**
- Inno Setup 通过 AppId 识别是否为同一个软件
- 如果修改了 AppId，新版本会被识别为不同的软件
- 用户会同时看到两个"MinecraftFRP"程序
- 会导致注册表混乱和卸载问题

**正确做法**：无论版本如何变化（0.5.32 → 0.6.0 → 1.0.0），**AppId 始终保持不变**。

---

#### 构建与发布目录结构：

**构建过程：**
```
项目根目录/
├── build/                         # 【构建缓存目录】所有中间产物和最终成品
│   ├── temp_launcher/             # Launcher 编译缓存
│   │   └── launcher.exe
│   ├── temp_main_app/             # 主程序编译缓存
│   │   └── app.dist/
│   │       ├── MinecraftFRP.exe
│   │       └── ... (478个文件)
│   ├── MinecraftFRP_build/        # 组织好的构建产物（给 Inno Setup 用）
│   │   ├── launcher.exe
│   │   └── app.dist/
│   └── installer_output/          # Inno Setup 输出目录
│       └── MinecraftFRP_Setup_0.5.32.exe  # 【最终成品】
│
├── dist/                          # 【发布目录】按版本号存档
│   └── 0.5.32/                    # 从 build/ 复制过来的成品
│       ├── MinecraftFRP_Setup_0.5.32.exe
│       ├── version.json           # 版本元数据
│       └── CHANGELOG.md           # 版本更新日志
│
└── setup.iss                      # Inno Setup 配置脚本
```

**关键规则：**
1. `build/` - 临时构建缓存，可随时删除重建
2. `dist/版本号/` - 发布归档，每个版本独立存储
3. 构建完成后，从 `build/installer_output/` 复制成品到 `dist/版本号/`
4. 防病毒软件干扰 build/ 不影响已发布的 dist/

---

#### v2.0 目录结构：

**安装目录** (默认: `C:\Program Files\MinecraftFRP\`)
```
MinecraftFRP/
├── launcher.exe               # 【用户入口】启动器（检查更新 + 启动主程序）
├── app.dist/                  # 主程序目录
│   ├── MinecraftFRP.exe       # 主程序
│   └── ... (478个依赖文件)
├── base/                      # 依赖资源目录
│   ├── frpc.exe               # FRP 客户端 (旧版)
│   ├── new-frpc.exe           # FRP 客户端 (新版 TOML)
│   ├── tracert.exe            # 网络诊断工具
│   └── logo.ico               # 程序图标
├── config/                    # 本地配置缓存 (非用户数据)
│   ├── frp-server-list.json   # 服务器列表缓存
│   └── ads/                   # 广告图片缓存
├── logs/                      # 运行日志
│   ├── app.log
│   └── launcher.log
└── unins000.exe              # Inno Setup 自动生成的卸载程序
```

**用户配置目录** (`C:\Users\<用户名>\Documents\MitaHillFRP\`)
```
MitaHillFRP/
└── app_config.yaml            # 用户个人配置（端口、主题等）
```

---

#### v2.0 安装流程：

**首次安装：**
1. 用户运行 `MinecraftFRP_Setup_0.5.32.exe`
2. 安装器显示欢迎页 → 许可协议 → 选择安装路径
3. 选择创建快捷方式（桌面/开始菜单）
4. 安装器解压所有文件到目标目录
5. 在注册表中注册应用程序信息（控制面板可见）
6. 安装完成，可选立即启动程序

**升级安装（覆盖安装）：**
1. 用户下载新版安装包 `MinecraftFRP_Setup_0.5.33.exe`
2. 双击运行安装包
3. Inno Setup 自动检测：
   - 通过 AppId 发现旧版本已安装
   - 自动切换为"升级模式"
   - 如程序正在运行，提示用户关闭（自动检测）
4. 覆盖安装：
   - 替换所有程序文件
   - 保留用户配置（`文档/MitaHillFRP/`）
   - 更新注册表版本号
5. 如程序之前在运行，安装完成后自动重启

**卸载流程：**
1. 方式1：设置 → 应用 → MinecraftFRP → 卸载
2. 方式2：开始菜单 → MinecraftFRP → 卸载 MinecraftFRP
3. 卸载程序删除整个安装目录
4. 询问用户是否保留配置文件（`文档/MitaHillFRP/`）
5. 删除桌面和开始菜单快捷方式
6. 清理注册表

---

#### v2.0 更新机制：

**完整流程：**
```
用户双击桌面快捷方式
    ↓
launcher.exe 启动
    ↓
读取本地版本 (从 app.exe 元数据或配置文件)
    ↓
异步请求 https://z.clash.ink/chfs/shared/MinecraftFRP/Data/version.json
    ↓
┌─────────────────────────────────────┐
│ 版本对比                            │
├─────────────────────────────────────┤
│ 【最新】→ 直接启动 app.exe          │
│ 【过旧】→ 提示用户下载新版安装包     │
└─────────────────────────────────────┘
```

**两种更新方式：**

**方案一：覆盖更新（已实现）**
- 用户手动下载新版安装包
- 双击运行，Inno Setup 自动检测旧版本
- 自动提示关闭程序、覆盖安装、保留配置
- 类似微信/Chrome的升级体验

**方案二：自动在线更新（未来增强，架构已设计）**
- Launcher 检测到新版本
- 后台下载安装包并校验 SHA256
- 唤起安装包进行静默安装
- 详细实现见 `docs/UPDATE_STRATEGY.md`

**关键特性：**
- **配置保留**：用户配置存储在独立的 `文档/MitaHillFRP/` 目录，永不被覆盖
- **自动卸载程序**：Inno Setup 自动生成，注册到控制面板
- **注册表集成**：应用信息、版本号、卸载路径自动写入注册表
- **静默更新选项**：未来可支持 `/VERYSILENT` 参数实现静默升级

---

#### 分发与部署：

**最终产物：**
```
dist/
└── MinecraftFRP_<版本号>/
    ├── MinecraftFRP_Setup_<版本号>.exe      # Stable 通道
    ├── MinecraftFRP_installer_dev.exe       # Dev 通道
    └── version.json
```

**服务器部署：**
- `MinecraftFRP_Setup_0.5.32.exe` → 上传到 `/root/chfs/share/MinecraftFRP/downloads/`
- `version.json` → 上传到 `/root/chfs/share/MinecraftFRP/Data/version.json`

**用户获取方式：**
- **首次安装**：从官网/分发渠道下载 `MinecraftFRP_Setup_x.x.x.exe`
- **后续更新**：手动下载新版安装包并运行（或等待方案二实现后自动更新）

---

#### 构建命令：

统一入口（仅此一种）：
```bash
python build.py [--channel dev|stable] [--upload] [-u "更新说明"] [--clean]
```

该命令将：
1. 清空 build/ 缓存（保留 dist/ 仅做最终归档）
2. 编译 Launcher（PyInstaller 目录模式，输出 launcher/）
3. 编译主程序（Nuitka 目录模式，输出 app.dist/）
4. 组织文件到 build/MinecraftFRP_build/
5. 使用 Inno Setup 打包到 build/installer_output/
6. 将安装器复制到 dist/MinecraftFRP_<版本号>/ 并生成 version.json（按通道命名：dev 为 MinecraftFRP_installer_dev.exe）

```
build/                              # 构建缓存（可删除）
├── launcher_build/                 # Launcher 编译缓存
├── temp_main_app/
│   └── app.dist/
├── MinecraftFRP_build/             # 组织好给 Inno Setup 用
│   ├── Launcher.exe
│   ├── launcher_internal/          # Launcher 依赖
│   └── MitaHill-FRP-APP/
└── installer_output/
    └── MinecraftFRP_Setup_0.5.32.exe   # 安装程序

dist/                               # 发布目录（永久保存）
└── 0.5.32/
    └── MinecraftFRP_Setup_0.5.32.exe   # 最终成品
```

**依赖要求：**
- Inno Setup 6.6.1 (安装路径: `C:\Program Files (x86)\Inno Setup 6\`)
- Python 3.8+
- Nuitka 2.8.9
- PySide6
- PyInstaller

**常见问题：**
1. **Inno Setup 报错"文件被占用"**：关闭所有资源管理器窗口，确保没有程序占用 build/ 目录
2. **缺少语言文件**：已使用英语，中文需手动下载 `ChineseSimplified.isl`
3. **防病毒软件干扰**：将项目目录添加到信任区

---

#### v2.0 技术栈：

- **安装器**: Inno Setup 6.6.1
- **编译器**: Nuitka 2.8.9 (主程序), PyInstaller (Launcher)
- **GUI框架**: PySide6
- **构建脚本**: Python (src_builder/)
- **部署**: SSH/SFTP (paramiko)

## 3. Git 工作流与规范 (严格执行)

本项目采用严格的 Git 提交与分支管理规范，以确保代码库的整洁与可维护性。

### 3.0 版本标记与构建前置命令（信息采集，仅参考）
为确保 `version.json` 与安装器版本信息一致，构建前可以选择执行以下命令采集 Git 信息（不强制）：

```powershell
# 可选：查看当前分支与最近标签
git rev-parse --abbrev-ref HEAD
git tag --list
```

注意：
- 构建脚本已取消所有 Git 写操作（不自动创建/推送标签），仅获取分支信息用于默认更新说明。
- 构建缓存目录为 `build/`，发布目录为 `dist/MinecraftFRP_<版本号>/`，二者严格分离。
- 构建成功后，安装器与 `version.json` 会复制到 `dist/MinecraftFRP_<版本号>/`，其中 Dev 通道安装器命名为 `MinecraftFRP_installer_dev.exe`。

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
*   [x] **客户端自动更新功能**
    *   [x] **检查与下载**:
        *   [x] 在主程序启动的后台线程中，从服务器异步获取 `version.json`。
        *   [x] 比较本地版本与服务器版本，若有更新则弹出提示对话框，并显示更新日志。
        *   [x] 用户确认后，在后台线程下载新版本程序，并可显示下载进度。
        *   [x] 下载完成后，校验文件的 SHA256 哈希值，确保文件完整与安全。
    *   [x] **执行与替换**:
        *   [x] 创建一个独立的 `updater.py` 脚本，其唯一职责是执行文件替换和重启操作。
        *   [x] `build.py` 脚本增加新逻辑：先将 `updater.py` 打包成 `updater.exe`。
        *   [x] `build.py` 在打包主程序时，将 `updater.exe` 作为二进制资源嵌入。
        *   [x] 主程序在校验下载成功后，从自身资源中释放 `updater.exe` 到临时目录。
        *   [x] 主程序启动 `updater.exe`（通过命令行参数传递新/旧文件路径及主进程ID），然后完全退出。
        *   [x] `updater.exe` 等待主进程结束后，执行文件覆盖，并重新启动新版主程序。

### 待开发/优化计划
*   [x] **实现启动广告弹窗并重构为统一广告系统**
    *   [x] 程序启动后，在后台从 `.../ads/ads_index.yaml` 获取统一配置文件。
    *   [x] 弹窗能展示图片、备注文字，并支持点击图片跳转链接。
    *   [x] 图片URL由基础路径 (`.../source/`) 和文件名拼接而成。
    *   [x] 弹窗包含“上一张”/“下一张”按钮，支持用户手动翻页。
    *   [x] 弹窗能根据配置文件中 `duration` 字段，自动轮播广告。
    *   [x] 状态栏滚动广告与弹窗广告均由 `ads_index.yaml` 统一控制。
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
*   **编译目标**: Nuitka 编译为“目录模式”（standalone，非 onefile），以便 `exe + 子目录` 的架构。
*   **隐藏控制台**: GUI 程序必须使用 `--windows-disable-console` (或 `--disable-console`) 隐藏 CMD 窗口。
*   **资源内置/目录随附**: 外部依赖通过 `--include-data-file` / `--include-data-dir` 或随 `app.dist/`、`nuitka_launcher/` 目录分发。

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
        *   `https://z.clash.ink/chfs/shared/MinecraftFRP/Data/version.json`
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
| 2025-12-14 | `refactor` | 将 Launcher 打包方式改为 PyInstaller 目录模式 (onedir) | `current` |
| 2025-12-10 | `feat` | 迁移到 Inno Setup 专业安装器，彻底重构 v2 架构 | `v2-installer-architecture` |
| 2025-12-10 | `feat` | 添加覆盖更新支持（类似微信/Chrome升级体验） | `a02b905` |
| 2025-12-10 | `feat` | 简化构建命令，--v2 默认启用 fast 模式 | `e1bc046` |
| 2025-12-10 | `fix` | 修复 Inno Setup 的 DirExistsWarning 参数错误 | 进行中 |
| 2025-12-08 | `fix` | 修复 `Styles` 模块的 `ModuleNotFoundError` | `09174aa` |
| 2025-12-08 | `fix` | 修复服务器管理窗口和文件下载功能 | `ed245b2` |
| 2025-12-07 | `feat` | 实现启动广告弹窗，并重构统一广告系统 | `feat/startup-ad-dialog` |
| 2025-11-28 | `refactor` | 初始化模块化项目结构，分离核心逻辑与界面 | `87d948f` |
| 2025-11-28 | `docs` | 制定并写入项目企划与架构文档，添加 Logs 规则 | `9351384` |
| 2025-11-28 | `fix` | 修复 GUI 关闭时的线程安全隐患 (添加 wait()) | `348cafd` |
| 2025-11-28 | `refactor` | 加密内置默认服务器列表，混淆密钥 (Anti-Cracking) | `348cafd` |
| 2025-11-28 | `fix` | 修复因移除 DEFAULT_SERVERS 导致的 ImportError | `97777ac` |
| 2025-11-28 | `refactor` | PyInstaller打包优化 (内置 frpc.exe 和 logo.ico) | `d2b66b6` |
| 2025-11-28 | `refactor` | 封装 tracert_gui.exe 并实现基于 Git Hash 的多版本打包 | `2d5bc5f` |
| 2025-11-28 | `docs` | 更新项目企划，增加安全、稳定性及打包发布规范 | `c7afce0` |
| 2025-11-28 | `feat` | 默认开启自动映射功能 | `2f7043e` |
| 2025-11-28 | `refactor` | GUI模块重构：拆分 Tab 组件，重命名文件符合 PascalCase 规范 | `d76f885` |
| 2025-11-28 | `fix` | 修复 MainWindow.py 语法错误 | `a287bf6` |
| 2025-11-28 | `fix` | 修复 GUI 重构后的 ImportError 和 SyntaxError | `2dd855d` |
| 2025-11-28 | `refactor` | 深度模块化 GUI 代码并修复初始化错误 | `3bd1949` |
| 2025-12-06 | `feat`     | 实现完整的客户端自动更新与自动化部署流水线 | `4d4950b` |
| 2025-11-28 | `chore`    | 执行正式打包构建 (PyInstaller)              | `3bd1949` |

## 12. 自动化构建与部署 (CI/CD)

本项目拥有一套基于 Python 的自动化构建与部署流水线，其核心是根目录下的 `build.py` 脚本。

### 12.1 核心组件
*   **`build.py`**: 自动化主脚本，负责驱动整个流程（仅 Python，禁止 BAT/CMD/PS1）。
*   **`cicd.yaml`**: 流水线配置文件，用于定义版本号、部署目标服务器信息、打包参数等。

### 12.2 自动化流程
运行 `python build.py` 后，脚本将自动执行以下端到端(End-to-End)任务：
1.  **读取配置**: 解析 `cicd.yaml` 获取当前版本号和部署配置；每次构建版本号自增一次并写回。
2.  **Nuitka 编译**: 以目录模式编译 `launcher.py` 与 `app.py`（非单文件），输出 `launcher.dist/` 与 `app.dist/`。
3.  **组织产物**: 汇总到 `build/MinecraftFRP_build/`（launcher.exe + nuitka_launcher/ + app.dist/）。
4.  **生成安装器**: 使用 Inno Setup 将上述目录打包输出到 `build/installer_output/`。
5.  **生成清单**:
    *   自动计算安装器的 **SHA256**。
    *   获取当前 **Git 分支**（仅用于信息显示，不做写操作）。
    *   将版本号、SHA256、分支信息与更新说明写入 `version.json` 文件。
6.  **部署 (可选)**:
    *   通过 SFTP 将安装器与 `version.json` 上传到服务器指定目录（按通道隔离：Stable/ 与 Dev/）。
7.  **缓存清理**: 结束后清空 `build/` 目录，保留 `dist/` 归档。

### 12.3 如何使用
确保已安装所有 `requirements.txt` 中的依赖后，在项目根目录的虚拟环境中执行：
```shell
python build.py --channel dev            # 默认：开发通道
python build.py --channel stable --upload -u "修复BUG"   # 正式发布并上传
```

#### 构建说明（安装器模式）
已取消 `--v2` 参数，统一使用 `build.py`，通过 `--channel` 指定通道。

**构建阶段：**
1. **Launcher 编译** (4-5分钟) - 使用 PyInstaller 目录模式 (onedir)
2. **主应用编译** (4-5分钟) - 使用 Nuitka standalone 模式，生成 app.dist/
3. **文件组织** (几秒) - 复制到 build/MinecraftFRP_build/
4. **Inno Setup 打包** (30秒) - 生成最终的 Setup.exe（输出到 build/installer_output/，随后复制到 dist/版本号/）

**总耗时**: 约 10-12 分钟

**构建产物**:
```
dist/
├── MinecraftFRP_0.5.32_installer/
│   └── MinecraftFRP_Setup_0.5.32.exe    # 最终安装器（~180-200MB）
├── MinecraftFRP_build/                  # 中间产物（Inno Setup 源）
│   ├── launcher.exe
│   └── app.dist/ (478个文件)
└── minecraft_version_index/
    └── version.json
```

**远程构建**:
```shell
# 在远程服务器构建
.\build_remote.ps1 -Remote -Fast

# SSH 直接构建
ssh vgpu-server-user@192.168.9.158 "cd /d D:\MinecraftFRP && .venv\Scripts\python.exe build.py --v2"
```

**参考文档**:
- `docs/v2_build_guide.md` - 完整构建指南
- `docs/UPDATE_STRATEGY.md` - 更新策略详解
- `docs/INNO_SETUP_DEPENDENCIES.md` - Inno Setup 依赖安装

### 12.4 远程构建指令
如需在远程服务器上执行构建，可使用以下 SSH 命令：
```shell
ssh vgpu-server-user@192.168.9.158 "cd /d D:\MinecraftFRP && venv\Scripts\python.exe build.py --v2"
```
此命令将在远程 Windows 服务器上执行 v2.0 架构的完整构建流程。

## 13. 附录：技术细节与修复记录

### 统一HTTP请求实现
- **问题**: 项目中存在多种HTTP请求实现 (`urllib`, `requests`, `PowerShell`)，维护成本高且行为不一。
- **解决方案**: 在 `HttpManager.py` 中实现统一的 `fetch_url_content()` 函数，基于 `requests` 并提供重试和SSL降级能力。所有模块均已迁移至此新接口。

### Bug修复：服务器管理窗口无法打开
- **问题**: `AttributeError` 导致对话框创建失败。
- **原因**: UI组件在创建时为局部变量，但后续代码尝试作为实例属性访问。
- **修复**: 在 `src/gui/dialogs/UiComponents.py` 中，将按钮正确赋值给对话框实例的属性。

### Bug修复：Ping数据显示加载失败
- **问题**: `AttributeError: 'NoneType' object has no attribute 'get'`
- **原因**: `load_ping_data()` 在文件为空时可能返回 `None`。
- **修复**: 确保 `load_ping_data()` 始终返回字典。

---

## 14. 维护与改进建议

### 待办事项
- **高优先级**:
  - [ ] **安全**: 立即修改所有在（现已删除的）`CLAUDE.md` 中暴露的密码。
- **中优先级**:
  - [ ] **文档**: 修复所有 `.md` 文件的编码问题，确保中文在所有环境下正常显示。
  - [ ] **测试**: 在干净的虚拟环境中验证 `requirements.txt` 的完整性。
  - [ ] **优化**: 考虑将 `DownloadThread.py` 的实现也迁移到 `requests`，以进一步统一网络请求。
- **低优先级**:
  - [ ] **清理**: 考虑移除旧的 `HttpUtils.py` 或明确标记为已弃用。
  - [ ] **CI/CD**: 在 `build.py` 中添加依赖自动检查功能，确保所有 `import` 的库都已在 `requirements.txt` 中声明。

### 关键建议
1.  **处理敏感信息**: 尽管包含敏感信息的文件已被删除，但Git历史记录中可能仍存在相关信息。建议采取措施清理历史记录，并立即更改所有相关密码。
2.  **统一网络请求**: `HttpManager` 作为统一接口的方案已部分实施，建议完成剩余部分的迁移（如 `DownloadThread.py`）。
3.  **改进构建流程**: 在 `build.py` 中添加自动化依赖检查，防止因缺少依赖导致的问题。

## 15. 特殊节点 (Special Nodes)

项目中用于心跳与 FRP 连接测试的特殊节点示例（仅作记录与测试使用）：

特殊节点命名规则：使用单个大写字母（A、B、C...）作为节点名称，便于识别和扩展。

- 节点 A:
  - serverAddr = "111.170.153.228"
  - serverPort = 15443

- 节点 B:
  - serverAddr = "47.98.206.171"
  - serverPort = 15443

心跳数据示例:

提交房间数据: {"remote_port": 21987, "node_id": 5, "room_name": "玩家的房间", "game_version": "1.20.1", "player_count": 1, "max_players": 20, "description": "欢迎来玩！", "is_public": true, "host_player": "玩家", "server_addr": "47.98.206.171"}

注意：以上节点信息用于项目内部测试与调试，请遵守安全规范，不要将敏感信息直接提交到公共仓库或日志中。

## 16. Updater 更新机制详解

### 16.1 概述
MinecraftFRP 的自动更新系统采用独立的 updater 程序来替换主程序文件，确保更新过程的可靠性和安全性。

### 16.2 新机制特点

#### Updater 提取与部署
- **编译时**：updater.exe 被打包到主程序内部（作为数据文件）
- **运行时**：主程序启动时自动将 updater.exe 提取到主程序所在目录
- **位置**：updater.exe 与 MinecraftFRP.exe 在同一目录

#### 更新流程
1. 用户点击更新按钮
2. 主程序下载新版本到临时目录并校验 SHA256
3. 启动 updater.exe（传入主程序PID和相关路径）
4. 主程序正常退出
5. Updater 等待15秒，超时则强制kill进程
6. 替换主程序文件
7. 重启主程序，updater自动关闭

#### 安全机制
- **超时强制终止**: 等待15秒后强制kill主进程，确保进程一定被终止
- **文件锁检测**: 替换前确保文件锁已释放
- **备份回滚**: 替换失败时自动恢复旧版本
- **SHA256校验**: 下载后验证文件完整性

### 16.3 代码模块

#### UpdaterManager (src/utils/UpdaterManager.py)
- `is_compiled()`: 检测是否是Nuitka编译版本
- `extract_updater()`: 提取 updater 到运行目录
- `get_runtime_updater_path()`: 获取运行时 updater 路径
- `cleanup_old_updater()`: 清理旧的临时文件

#### Updater (src_updater/)
- 基于 PySide6 的图形界面更新器
- 15秒超时+强制kill机制
- 文件替换+备份回滚
- 模块化设计，逻辑清晰

### 16.4 优势
1. **更可靠**: updater 在主程序目录，不受临时文件清理影响
2. **更快速**: 只需提取一次，后续更新直接使用
3. **更安全**: 15秒超时+强制kill确保进程一定会被终止
4. **易维护**: 模块化设计，职责清晰

## 17. 构建系统 (Build System)

### 17.1 概述
模块化构建系统位于 `src_builder/` 目录，用于自动化编译和部署 MinecraftFRP。

### 17.2 模块结构

```
src_builder/
├── __init__.py           # 包初始化
├── config.py             # 配置管理 (BuildConfig)
├── utils.py              # 通用工具函数
├── version_manager.py    # 版本和发布说明管理
├── builder.py            # Nuitka 编译器封装
└── deployer.py           # SSH/SFTP 部署
```

### 17.3 模块说明

#### config.py - BuildConfig
负责加载和管理 cicd.yaml 配置文件：
- `get_version_string()` - 获取当前版本号
- `increment_version()` - 递增补丁版本号
- `get_ssh_config()` - 获取 SSH 配置（包括密码）
- `get_nuitka_config()` - 获取 Nuitka 配置

#### utils.py
通用工具函数：
- `run_command()` - 执行命令并实时输出
- `verify_dependencies()` - 验证必需文件存在
- `clean_cache()` - 清理 Nuitka 缓存

#### version_manager.py - VersionManager
版本信息和发布说明管理：
- `generate_release_notes()` - 从 Git 生成发布说明
- `create_version_json()` - 生成 version.json 元数据文件
- `update_version_file()` - 更新 src/_version.py

#### builder.py - NuitkaBuilder
Nuitka 编译器封装：
- `build_updater()` - 编译更新器
- `build_main_app()` - 编译主应用程序
- 自动处理编译选项和依赖包含

#### deployer.py - Deployer
SSH/SFTP 部署功能：
- `deploy()` - 上传可执行文件和 version.json 到远程服务器
- 优化的传输参数和进度显示

### 17.4 命令行使用

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

### 17.5 优势
1. **模块化** - 每个功能独立模块，易于维护和测试
2. **可复用** - 模块可在其他脚本中复用
3. **清晰的职责分离** - 配置、构建、部署各司其职
4. **易于扩展** - 添加新功能只需新增模块
5. **参数化** - 支持命令行参数快速调整构建选项

### 17.6 依赖
- PyYAML - YAML 配置文件解析
- paramiko - SSH/SFTP 部署
- Nuitka - Python 编译器

## 18. 网络安全防护机制

### 18.1 Web 服务检测与拦截
为防止用户滥用工具搭建 Web 服务，程序实现了以下防护机制：

#### 检测策略
- **映射前检测**: 在启动 FRP 映射前，检测本地端口是否已运行 HTTP/HTTPS 服务
- **运行时监控**: 映射过程中定期检测，如发现 Web 服务则立即终止映射
- **判断依据**: 通过 HTTP 状态码和响应头来识别 Web 服务

#### 配置文件安全
- **临时文件**: FRP 配置文件使用临时文件（`tempfile`），启动后延迟删除
- **文件权限**: 配置文件设置严格的读写权限，仅当前用户可访问
- **内存运行**: 配置数据仅在内存中构建，最小化磁盘暴露时间
- **快速清理**: FRP 进程启动后1-2秒内删除配置文件

#### 实现模块
- **WebGuard** (src/core/security/WebGuard.py): 负责检测和拦截 Web 服务
- **ConfigManager**: 增强配置文件的安全写入和删除机制

### 18.2 配置文件防盗取
- **写入 -> 启动 -> 锁定/删除** 策略
- **文件句柄锁定**: 在 Windows 上使用文件锁，防止外部进程读取
- **自动清理**: 即使程序异常退出，临时文件也会被系统自动清理

## 19. 广告与推广系统

### 19.1 统一广告配置
所有广告内容由服务器上的 `ads_index.yaml` 统一管理：
- **弹窗广告**: 程序启动时以标签页形式展示
- **状态栏广告**: 主界面底部滚动展示
- **配置同步**: 后台异步更新，支持图片缓存

### 19.2 启动推广标签页
#### 特性
- **新建标签页**: 启动时自动创建"推广"标签页并切换
- **锁定机制**: 广告播放期间锁定其他标签页（除"线上公告"外）
- **自动轮播**: 根据配置文件中的 `duration` 字段自动切换图片
- **进度显示**: 底部进度条显示当前图片停留进度
- **加速按钮**: 用户可点击加速按钮随机快进（3秒冷却，最大60%跳跃，98%处停止）
- **点击跳转**: 点击图片跳转到"线上公告"并加载对应链接
- **一日一次**: 通过 `app_config.yaml` 记录日期，每天仅展示一次

#### 图片缓存
- **本地缓存**: 图片下载后缓存到 `config/ads/` 目录
- **异步下载**: 后台下载新广告图片，下次启动时使用
- **差异更新**: 对比索引文件，仅下载新增广告，删除过期广告
- **并行下载**: 多线程并行下载，提升效率

### 19.3 备注与样式
- **备注文字**: 显示在图片下方，根据主题自动调整颜色（浅色/深色）
- **自适应缩放**: 图片等比例缩小以适应窗口大小
- **高DPI支持**: 自动适配高分辨率显示器

## 20. 图形界面增强

### 20.1 小型浏览器
- **QWebEngineView**: 完整支持 JS、超链接、GPU渲染加速
- **配置化**: 默认URL可在 `app_config.yaml` 中配置（`browser_default_url`）
- **简化UI**: 取消地址栏、前进/后退按钮，仅在右键菜单中保留
- **标签名称**: "线上公告"

### 20.2 主题切换
- **昼夜模式**: 支持浅色和深色主题切换
- **平滑过渡**: 主题切换时使用动画效果
- **自适应**: 所有组件自动适配主题颜色

### 20.3 日志管理
- **自动裁剪**: 日志文件最大 1MB，超过后自动删除最旧内容
- **速率限制**: 重复日志消息在50秒内仅记录一次（如Ping服务）
- **日志级别**: INFO、WARNING、ERROR 分级记录

## 21. 代码质量要求

### 21.1 模块化
- **严格分层**: 所有功能必须按照 `src/core/`, `src/gui/`, `src/network/`, `src/utils/` 等目录分类
- **单一职责**: 每个模块文件仅负责一个功能点
- **深度嵌套**: 允许最多5层目录嵌套以实现精细化管理

### 21.2 健壮性
- **异常处理**: 所有可能抛出异常的代码必须使用 try-except 捕获
- **默认值**: 配置读取失败时必须提供合理的默认值
- **版本兼容**: 新增配置项必须考虑旧版本配置文件的兼容性
- **线程安全**: 多线程访问共享资源必须使用锁机制

### 21.3 日志记录
- **全面覆盖**: 关键操作（网络请求、文件IO、状态变更）必须记录日志
- **详细信息**: 错误日志必须包含异常类型、堆栈信息和上下文
- **速率限制**: 高频日志使用速率限制机制，避免日志爆炸

### 21.4 性能优化
- **异步加载**: 耗时操作（网络请求、文件下载）必须在后台线程执行
- **并行处理**: 独立任务使用多线程并行执行
- **资源复用**: 避免重复创建对象，合理使用缓存

## 22. 安全规范补充

### 22.1 配置文件保护
- **Git 排除**: 敏感配置文件（如 `cicd.yaml`）必须在 `.gitignore` 中排除
- **密码存储**: SSH密码等敏感信息可明文存储在已排除的配置文件中
- **权限控制**: 生成的临时文件设置严格的文件权限

### 22.2 防滥用机制
- **Web 服务检测**: 实时监控映射端口，发现 HTTP 服务立即终止
- **配置文件安全**: 使用临时文件+延迟删除，防止配置泄露
- **文件锁定**: 配置文件在使用期间锁定，防止外部读取

## 23. 联机厅（Online Lobby）系统设计与实施计划

### 23.1 目标与范围
- 为玩家提供一个“可发现、可加入、可筛选”的公共房间大厅，支持公开/私有两种模式。
- 保障大厅数据的实时性（心跳<=30s）、稳定性（断线自愈）、安全性（防滥用、防伪造）。
- 与现有客户端能力无缝衔接：沿用 HeartbeatManager、FRPC 管理、广告与更新体系，不破坏当前流程。

### 23.2 客户端现状与可复用模块
- HeartbeatManager（heartbeat_manager.py）：已具备房间发布、DELETE 删除、30s 心跳与退出清理能力。
- MainWindow（src/gui/MainWindow.py）：已在映射启动/终止时对心跳做集成调用；具备统一日志、线程管理与版本信息输出。
- 特殊节点：以 A、B、C... 命名，界面样式与普通节点一致，始终排在列表底部。

### 23.3 数据模型（客户端 -> 服务器）
- Room 对象（POST/DELETE/Heartbeat）：
  {
    "remote_port": int,           # 服务器分配的远端端口
    "node_id": int,               # 节点ID（A=1，B=2...以服务端映射为准）
    "room_name": str,             # 房间显示名
    "game_version": str,          # 游戏版本（可未知）
    "player_count": int,          # 当前人数
    "max_players": int,           # 最大人数
    "description": str,           # 备注
    "is_public": bool,            # 是否公开
    "host_player": str,           # 主机玩家ID（已做合规校验）
    "server_addr": str,           # 节点出口地址（非玩家真实IP）
    "full_room_code": str         # 由客户端内部生成的幂等键："{remote_port}_{node_id}"
  }
- 约束：full_room_code 作为幂等键；重复 POST 视作 upsert；DELETE 需提供同样键。

### 23.4 客户端工作流（状态机）
1) StartMapping -> Submit(POST) -> Heartbeat(30s) -> StopMapping(DELETE) -> Idle
2) 进程守护：若 FRPC 退出/异常，自动停止心跳并触发 DELETE；重连时自动重新发布+续心跳。
3) UI：发布成功/失败、心跳成功/失败均通过统一 Logger 记录；速率限制避免刷屏。

### 23.5 服务端接口（建议）
- REST
  - POST   /api/lobby/rooms                 # upsert 创建/续签（携带 full_room_code）
  - DELETE /api/lobby/rooms                 # 删除（按 full_room_code）
  - GET    /api/lobby/rooms                 # 查询（分页/筛选：version、loader、node、keyword、is_public、tags[]）
  - GET    /api/lobby/nodes                 # 节点元数据（展示名称、地区、负载、是否特殊节点）
  - POST   /api/auth/login                  # 账号登录（保留接口），入参：username/password；出参：access_token/refresh_token
  - POST   /api/auth/refresh                # 刷新令牌（保留接口）
  - GET    /api/users/me                    # 获取当前账号信息（保留接口）
  - GET    /api/moderation/wordlist        # 敏感词词表增量/版本（客户端本地缓存，保留接口）
  - POST   /api/moderation/report          # 举报接口（房间/用户/文本），用于反馈与二次审核
- WebSocket（可选增强）
  - /api/lobby/stream                       # 房间增删改推送，客户端用于实时刷新列表
- 鉴权与防伪造（最小闭环方案）
  - Header：x-app=MCFRP，x-ts=unix_ms，x-sign=HMAC_SHA256(body+ts, shared_key)
  - Authorization: Bearer <access_token>（当账号体系启用时）
  - shared_key 按版本轮换；客户端内做混淆拼接；服务端允许±60s 时间偏差。
  - 频控：同一IP 1min 内创建≤N、心跳≤120/小时；可灰度动态调整。
- 校验与拦截
  - 文本字段统一按长度、字符集与敏感词规则进行校验；违规请求直接 400/422。
  - 支持可配置的正则黑白名单（前缀/后缀/关键词/Emoji 过滤），并在响应中回传 normalized 文本。

### 23.6 心跳与清理策略
- 心跳周期：30s；服务端容忍窗口：90s 未收到则标记下线、120s 清理。
- 幂等：相同 full_room_code 在有效期内 POST 直接覆盖并续期。
- 回收：DELETE 请求即刻下架；客户端异常退出由服务端超时清理兜底。

### 23.7 安全与反滥用
- 本地 WebGuard：映射前/映射中检测映射端口是否提供 HTTP/HTTPS，命中则阻断映射并提示。
- 信息最小化：大厅仅展示 relay 地址与房间信息，不暴露玩家真实 IP/端口。
- 反爬与滥用：分页+签名校验+IP 频控+可选验证码（仅创建接口），服务端侧记录异常指纹并黑名单。
- 配置防盗：FRPC TOML 采用“写入->启动->延迟删除”的短生命周期策略；尽量短时落盘并加文件锁。

### 23.8 匹配与发现（体验层）
- 筛选/排序：按延迟（近似）、版本、节点、人数、关键字；默认推荐低负载、低延迟房间。
- 标签化：房间可选标签（生存/建筑/PVP/模组名），便于发现；服务端侧做简单词频统计。
- 多端一致：PC UI 与（未来）Web 列表协议一致，便于复用。

### 23.9 断线自愈与容错
- 客户端对网络错误做指数退避（1s/2s/4s..上限15s），但不阻塞 UI。
- 进程级事件：FRPC 退出->立即停止心跳+发起 DELETE；重连成功后自动恢复心跳。
- 日志：失败原因与上下文完整记录，且 50s 内重复报文仅记录一次。

### 23.10 与现有规范的兼容
- 特殊节点维持 A/B/C... 命名，展示与普通节点一致，排序固定在列表末尾（不硬编码地址）。
- 完全遵循模块化：新增客户端逻辑放入 src/network/LobbyClient.py、src/core/LobbyService.py（或等价拆分）。
- GUI 改动最小化：映射 Tab 新增“发布到联机厅”开关与房间信息表单（默认读取缓存）。

### 23.11 实施里程碑（客户端）
- M1（D+2）: 抽象 LobbyClient，改造 HeartbeatManager 以支持签名与幂等键；最小闭环联调。
- M2（D+5）: GUI 表单、房间列表页（仅本地渲染）、错误与速率限制完善；日志与埋点。
- M3（D+8）: WebSocket 增强（可选）、搜索筛选、排序策略；异常自愈与A/B测试开关。
- M4（D+10）: 文档与自动化测试补充、性能与稳定性压测、灰度发布。

### 23.12 服务端参考实现（建议）
- 技术栈任选（Go/FastAPI/Node），持久层 MySQL/SQLite + Redis（心跳TTL）；Nginx 限流与缓存。
- 数据表：rooms(full_room_code PK, meta..., updated_at idx)、nodes(id PK, meta...)；rooms 按 updated_at 建索引。
- 清理任务：每60s 扫描 rooms，过期清理；指标上报。

### 23.13 监控与可观测性
- 指标：活跃房间数、创建/删除QPS、心跳成功率、超时清理数、平均心跳延迟、敏感词命中率、拦截率。
- 日志：按 request-id 关联；异常类型聚合；可选接入 Sentry/Prometheus/Grafana。
- 应急：灰度开关、签名轮换、黑名单实时下发与回滚预案；敏感词/正则规则热更新。

### 23.14 内容审核与敏感词（客户端+服务端）
- 客户端：本地缓存词表与正则规则（版本化），在提交前本地预检并高亮违规字段；不修改原输入，仅提示。
- 服务端：最终裁决；返回 422 并附带字段级错误原因与命中条目；支持按地区/语言下发差异化词表。
- 词表更新：GET /api/moderation/wordlist 返回 {version, rules[]}；客户端按版本号增量更新并落盘。

### 23.15 账号体系与权限（保留接口）
- 形态：阶段一匿名（签名+频控），阶段二账号（用户名/密码），阶段三三方登录（可选）。
- Token：JWT 或等价，短期 access + 长期 refresh；客户端仅在 Header 发送，不落入房间业务体。
- 权限：普通玩家/认证房主/官方节点管理员；不同角色的发布额度、可见性、审核流程不同。

### 23.16 API 版本化与兼容
- Header: X-Api-Version: 1；Body 中携带 api_version: "v1"；当 v2 演进时保持向后兼容并保留旧字段。
- 字段演进：新增字段默认可空；删除字段先标记 deprecated≥2个小版本周期后再移除。

### 23.17 前瞻功能路线（保留接口）
- 房间口令与邀请：支持一次性邀请链接/二维码；私密房间不在公共列表展示，仅持有链接可见。
- 匹配推荐：结合节点负载、近似延迟、玩家偏好与历史加入记录，提供个性化排序（端上可关闭）。
- 兼容性匹配：基于 loader/modpack_hash 的兼容建议与冲突提示。
- 社交：收藏/最近加入/屏蔽；房主公告与轮播；跨房间消息通道（仅服务端可见的系统广播）。
- 反滥用扩展：设备指纹与风险评分（隐私合规前提下），灰度拦截与人工复核通道。

### 23.18 小型自建形态（当前阶段最简实现）
- 更新于：2025-12-09T19:05:03.964Z（自建版规划，保持大胆设想但实现最小闭环）
- 服务端形态：单进程 FastAPI + SQLite（rooms.db，单表 rooms，按 updated_at 建索引），无账号体系；仅暴露三条接口：
  - POST /api/lobby/rooms（upsert，携带 full_room_code）
  - DELETE /api/lobby/rooms（按 full_room_code 下架）
  - GET /api/lobby/rooms（分页+简单筛选：keyword、node、loader、is_public、version）
- 预留接口但暂不启用：/api/auth/login、/api/auth/refresh、/api/users/me、/api/moderation/wordlist（返回固定占位数据或 404）。
- 客户端上报字段扩展（立即生效，均可选）：
  - loader: "Vanilla" | "Forge" | "NeoForge" | "Fabric" | "Quilt"
  - modpack_name: str, modpack_version: str
  - tags: list[str]（如 ["生存","建筑","PVP"]）
  - region: str（展示区域/线路，如 CN-North）
  - allow_listed: bool（房主声明是否启用白名单，仅用作展示）
  - ext: dict（保留扩展字段，客户端与服务端均应原样透传）
- 防滥用（轻量化）：
  - 签名可选：Header x-ts + x-sign = HMAC_SHA256(body+ts, shared_key)，shared_key 存服务端配置，客户端做混淆；时间偏移±60s。
  - 频控：同一 IP 1分钟内 POST ≤ 3；心跳频次 ≤ 120/小时；超出返回 429。
  - 敏感词：客户端本地正则预检（可空），服务端使用最简 regex 列表（支持通配词根），命中则 422 返回具体字段与命中词。
- 心跳策略：仍为 30s；服务端 90s 标记下线、120s 清理；客户端异常退出由服务端超时兜底。
- 部署与运维（极简）：
  - 启动：python server.py 或 uvicorn server:app --host 0.0.0.0 --port 9000
  - 数据：SQLite 单文件，提供每日自动备份（可选 cron）；无需外部缓存。
  - CORS：仅允许客户端 User-Agent/Origin 白名单（简化为 * 也可，但不推荐）。
- 渐进式演进轨道：
  - P1（当前）三接口+SQLite+HMAC（可关）；
  - P2（可选）加入 WebSocket 推送与更细筛选；
  - P3（保留）启用账号、令牌与更完整审核链路。

### 23.19 反向代理与源IP识别（Nginx/SSL 终止/控制协议）
- 目标：在启用 SSL 反向代理（如 Nginx、Caddy）时，服务端能够准确识别客户端真实源 IP，并支持反代控制协议。
- 支持能力：
  - Header 信任链：X-Forwarded-For（首个未信任代理IP）、X-Real-IP、X-Forwarded-Proto、X-Forwarded-Host。
  - PROXY protocol v1/v2（可选）：在内网直连或四层反代下启用，以获取源地址信息。
  - 受信代理白名单：仅当请求来源于 127.0.0.1/内网网段/配置的反代IP 时才信任上述头部，避免伪造。
- 记录策略：
  - request_ip_raw：TCP 层对端地址（反代地址）。
  - request_ip_effective：解析自可信头部/PROXY 协议的真实客户端IP。
  - tls_offload: true/false 标记请求是否经由 TLS 终止（X-Forwarded-Proto==https 视为 true）。
- 接口兼容：所有 REST/WebSocket 接口均应填充 request_ip_effective，用于频控、审计与展示（UI 可脱敏显示）。
- 参考 Nginx 配置（示例）：
  ```nginx
  server {
      listen 443 ssl http2;
      server_name example.com;
      ssl_certificate     /etc/ssl/fullchain.pem;
      ssl_certificate_key /etc/ssl/privkey.pem;

      location /api/ {
          proxy_pass http://127.0.0.1:9000;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
          proxy_http_version 1.1;
          proxy_set_header Connection "";
      }
  }
  ```
- FastAPI 获取源 IP（示例伪码）：
  ```python
  def get_effective_ip(request):
      peer = request.client.host
      if peer in TRUSTED_PROXIES:
          xff = request.headers.get("X-Forwarded-For", "")
          xri = request.headers.get("X-Real-IP")
          ip = (xff.split(",")[0].strip() if xff else xri) or peer
      else:
          ip = peer
      return ip
  ```
- 审计与风控：日志中同时记录 raw/effective IP；频控以 effective IP 为主、raw IP 为辅；
- 时间戳：更新于 2025-12-09T19:06:16.291Z（预留反代控制协议与 SSL 终止场景支持）。

版本文件 https://z.clash.ink/chfs/shared/MinecraftFRP/Data/version.json
上传 /root/chfs/share/MinecraftFRP/Data/version.json

下载通道

DEV版本
https://z.clash.ink/chfs/shared/MinecraftFRP/Dev/MitaHill_Dev_FRP.exe

上传 /root/chfs/share/MinecraftFRP/Dev/MitaHill_Dev_FRP.exe

STABLE版本
https://z.clash.ink/chfs/shared/MinecraftFRP/Stable/MitaHill_Stable_FRP.exe

上传 /root/chfs/share/Minecraft/Stable/MitaHill_Stable_FRP.exe

版本文件只有一个，因为我不想两个版本分支相同维护。

更新程序从服务器拉取更新索引文件 version.json ，和自身的版本通道进行比对，如果匹配，那么看版本号，如果服务器的版本号大于自身，则触发更新，从指定位置下载安装包，并安装
