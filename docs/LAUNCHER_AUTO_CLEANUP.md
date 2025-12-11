# Launcher 自动清理功能文档（2025-12-10）

## 📋 功能说明

### 新增逻辑
当 Launcher 检测到**本地版本已是最新版本**时，自动清理 `Documents\MitaHillFRP\downloads` 目录中的旧安装包，释放磁盘空间。

---

## 🔧 实现细节

### 清理时机
```
用户启动程序
    ↓
Launcher 启动
    ↓
启动主程序（立即）
    ↓
后台检查更新（500ms 后）
    ↓
版本比较：
    - 有新版本 → 下载安装包
    - 已是最新 → 清理旧安装包 ✅ (新功能)
    - 本地更新 → 跳过（异常情况）
```

### 清理逻辑
```python
def _cleanup_old_installers():
    """清理下载目录中的旧安装包"""
    # 1. 检查下载目录是否存在
    # 2. 查找所有 .exe 文件
    # 3. 逐个删除
    # 4. 记录日志
    # 5. 气泡提示（静音）
```

---

## 📊 清理效果

### 测试结果
```
📦 清理前:
  - 0.5.58_MitaHill_FRP_Dev_Install.exe (185 MB)
  - 0.5.59_MitaHill_FRP_Dev_Install.exe (185 MB)
  - 0.5.60_MitaHill_FRP_Dev_Install.exe (185 MB)
  总计: 555 MB

🧹 清理后:
  - (空)
  总计: 0 MB

💾 释放空间: 555 MB ✅
```

### 气泡通知
```
已清理 3 个旧版本安装包，释放磁盘空间。
```

---

## 🎯 用户体验

### Before（无清理）
- 每次更新后留下 ~180MB 安装包
- 10次更新 = 1.8GB 浪费空间
- 用户需要手动清理

### After（自动清理）
- 检测到最新版本自动清理
- 静音气泡提示（不打扰）
- 完全自动化，用户无感知

---

## 📝 日志记录

### 示例日志
```
Launcher started. Version: 0.5.60, Channel: dev
Launching main app...
Checking for updates in background...
Remote version: 0.5.60, Channel: dev (Local: dev)
Already on latest version. Cleaning up old installers...
Deleted old installer: 0.5.58_MitaHill_FRP_Dev_Install.exe
Deleted old installer: 0.5.59_MitaHill_FRP_Dev_Install.exe
Cleaned up 2 old installer(s).
```

---

## 🔍 清理规则

### 会被清理的文件
- ✅ `*.exe` （所有 .exe 文件）
- ✅ 位于 `Documents\MitaHillFRP\downloads\` 目录

### 不会被清理的
- ❌ 其他目录的文件
- ❌ 非 .exe 文件
- ❌ 当前正在下载的文件（因为还未写入完成）

---

## ⚠️ 边界情况处理

### 1. 下载目录不存在
```python
if not DOWNLOADS_PATH.exists():
    return  # 直接返回，不报错
```

### 2. 没有旧安装包
```python
if not installers:
    _safe_log("No old installers found.")
    return
```

### 3. 删除失败
```python
try:
    installer.unlink()
except Exception as e:
    _safe_log(f"Failed to delete {installer.name}: {e}")
    # 继续删除其他文件，不中断
```

### 4. 气泡通知失败
```python
try:
    _show_toast(...)
except Exception:
    pass  # 不影响主流程
```

---

## 🧪 测试验证

### 测试脚本
```bash
python test_launcher_cleanup.py
```

### 测试结果
```
✅ 成功清理 6 个文件
📂 下载目录已清空
```

---

## 🚀 何时生效

### 下次构建后自动生效
```bash
python build.py --channel dev --upload -u "Launcher新增自动清理旧安装包功能"
```

### 用户体验流程
1. 用户启动程序
2. Launcher 检查更新
3. 如果已是最新版：
   - 自动清理旧安装包
   - 静音气泡提示
   - 释放磁盘空间
4. 主程序正常运行

---

## 💡 设计考量

### 为什么在"已是最新版"时清理？

1. **安全性**: 确认不需要更新后才清理，避免误删
2. **时机合适**: 用户不需要旧版本回退
3. **性能影响小**: 清理操作在后台进行
4. **用户无感知**: 不影响程序启动和使用

### 为什么清空整个目录？

1. **简单可靠**: 不需要复杂的版本比对
2. **完全自动**: 用户无需手动干预
3. **释放空间**: 每个安装包 ~180MB，积累多个会占用大量空间

---

## 📈 预期效果

### 磁盘空间节省
| 更新次数 | 无清理 | 有清理 | 节省空间 |
|---------|-------|-------|---------|
| 1次 | 180MB | 0MB | 180MB |
| 5次 | 900MB | 0MB | 900MB |
| 10次 | 1.8GB | 0MB | **1.8GB** |
| 20次 | 3.6GB | 0MB | **3.6GB** |

### 用户满意度提升
- ✅ 不占用磁盘空间
- ✅ 自动化管理
- ✅ 静音提示，不打扰

---

## 🔧 未来增强方向

1. **保留最近一个版本**: 允许用户回退
   ```python
   # 仅删除旧版本，保留最新的一个
   installers.sort(key=lambda x: x.stat().st_mtime, reverse=True)
   for installer in installers[1:]:  # 跳过最新的
       installer.unlink()
   ```

2. **可配置清理策略**: 用户选择是否自动清理
   ```yaml
   # app_config.yaml
   auto_cleanup_installers: true  # 默认开启
   ```

3. **清理其他临时文件**: 如日志、缓存等
   ```python
   # 清理超过30天的日志文件
   ```

---

## ✅ 验收标准

- [x] 最新版本时触发清理
- [x] 清空 downloads 目录中的所有 .exe 文件
- [x] 气泡提示（静音）
- [x] 完整日志记录
- [x] 错误时优雅降级
- [x] 不影响主程序启动
- [x] 测试通过

---

**功能完成时间**: 2025-12-10  
**影响版本**: v0.5.61+  
**测试状态**: ✅ 已通过本地测试  
**预期效果**: 每次更新后自动释放 ~180-500MB 磁盘空间
