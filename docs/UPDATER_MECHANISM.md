# Updater 更新机制说明

## 概述

MinecraftFRP 的自动更新系统采用独立的 updater 程序来替换主程序文件。

## 新机制特点

### 1. Updater 提取
- **编译时**：updater.exe 被打包到主程序内部（作为数据文件）
- **运行时**：主程序启动时自动将 updater.exe 提取到主程序所在目录
- **位置**：updater.exe 与 MinecraftFRP.exe 在同一目录

### 2. 更新流程
1. 用户点击更新
2. 下载新版本到临时目录并校验 SHA256
3. 启动 updater.exe（传入主程序PID）
4. 主程序正常退出
5. Updater 等待15秒，超时则强制kill进程
6. 替换主程序文件
7. 重启主程序，updater自动关闭

### 3. 安全机制
- **超时强制终止**: 等待15秒后强制kill主进程
- **文件锁检测**: 替换前确保文件锁已释放
- **备份回滚**: 替换失败时自动恢复旧版本
- **SHA256校验**: 下载后验证文件完整性

## 代码模块

### UpdaterManager (src/utils/UpdaterManager.py)
- is_compiled(): 检测是否是编译版本
- extract_updater(): 提取 updater 到运行目录
- get_runtime_updater_path(): 获取运行时 updater 路径
- cleanup_old_updater(): 清理旧的临时文件

### Updater (src_updater/main.py)
- 基于 PySide6 的图形界面更新器
- 15秒超时+强制kill
- 文件替换+备份回滚

## 优势
1. **更可靠**: updater 在主程序目录，不受临时文件清理影响
2. **更快速**: 只需提取一次，后续更新直接使用
3. **更安全**: 15秒超时+强制kill确保进程一定会被终止
4. **易维护**: 模块化设计，逻辑清晰
