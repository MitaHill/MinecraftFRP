# MinecraftFRP 更新策略文档

## 🔒 重要：AppId 锁定

**永远不要修改这个 GUID！**

```
AppId: {8B5F6C3D-9E4A-4F2B-A1D3-7C8E9F0B1A2C}
```

### 为什么重要？
- Inno Setup 通过 AppId 识别是否为同一个软件
- 如果修改了 AppId，新版本会被识别为不同的软件
- 用户会同时看到两个"MinecraftFRP"程序
- 会导致注册表混乱和卸载问题

### 正确做法
无论版本如何变化（0.5.32 → 0.6.0 → 1.0.0），**AppId 始终保持不变**。

---

## ✅ 方案一：覆盖更新（已实现）

### 配置说明

已在 `setup.iss` 中配置以下选项：

```ini
[Setup]
AppId={8B5F6C3D-9E4A-4F2B-A1D3-7C8E9F0B1A2C}  ; 永远不变
DirExistsWarning=no                            ; 不询问，直接覆盖
CloseApplications=yes                          ; 自动关闭运行中的程序
RestartApplications=yes                        ; 安装后自动重启
CloseApplicationsFilter=*.exe                  ; 需要关闭的程序类型
```

### 工作流程

1. **用户下载新版安装包**（如 `MinecraftFRP_Setup_0.5.33.exe`）
2. **双击运行安装包**
3. **Inno Setup 自动检测**：
   - 通过 AppId 发现旧版本已安装
   - 自动切换为"升级模式"
   - 检测到程序正在运行，提示用户关闭
   - 如果用户确认，自动关闭程序
4. **覆盖安装**：
   - 保留配置文件（`onlyifdoesntexist` 标记）
   - 替换所有程序文件
   - 更新注册表版本号
5. **完成**：
   - 如果之前在运行，自动重启程序
   - 用户无感知升级

### 用户体验

类似微信/Chrome的升级体验：
- ✅ 不需要卸载旧版
- ✅ 安装路径保持不变
- ✅ 配置文件自动保留
- ✅ 自动处理进程占用
- ✅ 控制面板只显示一个条目

### 测试方法

1. 安装 v0.5.32
2. 修改版本号为 v0.5.33 并重新构建
3. 运行新的安装包
4. 观察是否提示"升级"而非"安装"

---

## 🚀 方案二：自动在线更新（未实现，可选）

### 架构设计

Inno Setup 不支持联网检查更新，需要在 Python 代码中实现。

#### 1. 服务器端

在你的文件服务器（如 `https://z.clash.ink/chfs/shared/MinecraftFRP/`）放置：

```
Data/
├── version.json          # 版本信息
└── downloads/
    ├── MinecraftFRP_Setup_0.5.32.exe
    ├── MinecraftFRP_Setup_0.5.33.exe
    └── ...
```

**version.json** 示例：
```json
{
  "version": "0.5.33",
  "download_url": "https://z.clash.ink/chfs/shared/MinecraftFRP/downloads/MinecraftFRP_Setup_0.5.33.exe",
  "changelog": "修复了一些bug",
  "force_update": false,
  "min_version": "0.5.0"
}
```

#### 2. 客户端实现

在 `src/updater.py` 或 `launcher.py` 中添加：

```python
import requests
import subprocess
import sys
import os
import tempfile
from packaging import version
from pathlib import Path

CURRENT_VERSION = "0.5.32"  # 从 src/version.py 读取
UPDATE_CHECK_URL = "https://z.clash.ink/chfs/shared/MinecraftFRP/Data/version.json"

def check_for_updates():
    """检查是否有新版本"""
    try:
        resp = requests.get(UPDATE_CHECK_URL, timeout=5)
        data = resp.json()
        
        remote_version = data['version']
        download_url = data['download_url']
        force_update = data.get('force_update', False)
        
        # 版本比较
        if version.parse(remote_version) > version.parse(CURRENT_VERSION):
            return {
                'has_update': True,
                'version': remote_version,
                'url': download_url,
                'force': force_update,
                'changelog': data.get('changelog', '')
            }
        
        return {'has_update': False}
        
    except Exception as e:
        print(f"检查更新失败: {e}")
        return {'has_update': False}

def download_and_install_update(update_info):
    """下载并安装更新"""
    try:
        url = update_info['url']
        filename = url.split('/')[-1]
        tmp_path = Path(tempfile.gettempdir()) / filename
        
        print(f"正在下载新版本 {update_info['version']}...")
        
        # 下载安装包
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            
            with open(tmp_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    # 显示进度
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        print(f"\r下载进度: {progress:.1f}%", end='')
        
        print("\n✅ 下载完成")
        
        # 启动安装程序
        # /VERYSILENT: 完全静默
        # /SUPPRESSMSGBOXES: 不弹消息框
        # /NORESTART: 不重启
        # /SP-: 跳过启动页
        subprocess.Popen([str(tmp_path), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/SP-"])
        
        print("正在启动安装程序...")
        print("⚠️  程序将自动关闭以完成更新")
        
        # 必须退出，否则安装程序无法覆盖当前运行的 exe
        sys.exit(0)
        
    except Exception as e:
        print(f"更新失败: {e}")

def auto_update_check():
    """启动时自动检查更新"""
    update_info = check_for_updates()
    
    if not update_info['has_update']:
        return  # 无更新，继续启动
    
    # 显示更新提示
    print(f"\n🎉 发现新版本: {update_info['version']}")
    print(f"📝 更新内容: {update_info['changelog']}")
    
    if update_info['force']:
        print("⚠️  这是强制更新，必须升级才能继续使用")
        download_and_install_update(update_info)
    else:
        # 询问用户是否更新
        user_input = input("\n是否立即更新？(y/n): ")
        if user_input.lower() == 'y':
            download_and_install_update(update_info)
        else:
            print("已跳过更新，继续启动程序")

# 在程序启动时调用
if __name__ == "__main__":
    auto_update_check()
    # ... 继续启动主程序 ...
```

#### 3. 集成到 Launcher

在 `src_launcher/launcher.py` 的开头添加：

```python
from updater import auto_update_check

def main():
    # 启动时检查更新
    auto_update_check()
    
    # 继续正常的launcher逻辑
    # ...
```

---

## 📊 两种方案对比

| 特性 | 方案一（覆盖更新） | 方案二（自动更新） |
|------|-------------------|-------------------|
| **实现难度** | ✅ 简单（配置即可） | ⚠️ 中等（需要写代码） |
| **用户操作** | 手动下载新版安装包 | 程序内一键更新 |
| **网络依赖** | ❌ 不需要 | ✅ 需要 |
| **适用场景** | 小规模/内部使用 | 大规模/公开发布 |
| **当前状态** | ✅ 已实现 | ❌ 待实现 |

---

## 🎯 推荐实施顺序

### Phase 1: 立即实施（已完成）
- ✅ 配置 Inno Setup 覆盖更新
- ✅ 锁定 AppId
- ✅ 测试覆盖安装流程

### Phase 2: 后续增强（可选）
- ⏳ 实现 `updater.py` 模块
- ⏳ 集成到 launcher
- ⏳ 搭建版本服务器
- ⏳ 测试自动更新流程

---

## 🧪 测试清单

### 覆盖更新测试

- [ ] 安装 v0.5.32
- [ ] 运行程序
- [ ] 不关闭程序，双击 v0.5.33 安装包
- [ ] 验证是否提示关闭程序
- [ ] 确认后安装
- [ ] 验证程序是否自动重启
- [ ] 检查版本号是否更新
- [ ] 检查配置文件是否保留

### 自动更新测试（未来）

- [ ] 修改 version.json 模拟新版本
- [ ] 启动程序
- [ ] 验证是否检测到更新
- [ ] 点击"立即更新"
- [ ] 验证下载进度显示
- [ ] 验证安装包是否正确下载
- [ ] 验证程序是否自动关闭并安装

---

## 📝 版本发布流程

每次发布新版本时：

1. **更新版本号**
   ```python
   # src/version.py
   __version__ = "0.5.33"
   ```
   
2. **更新 setup.iss**
   ```ini
   #define MyAppVersion "0.5.33"
   ```

3. **构建安装包**
   ```powershell
   python build.py --v2
   ```

4. **上传到服务器**
   ```powershell
   python build.py --v2 --upload
   ```

5. **更新 version.json** (如果实现了自动更新)
   ```json
   {
     "version": "0.5.33",
     "download_url": "https://.../MinecraftFRP_Setup_0.5.33.exe"
   }
   ```

6. **测试覆盖安装**
   - 在已安装旧版本的机器上运行新安装包
   - 验证覆盖安装流程

---

## 🔒 安全注意事项

1. **AppId 保护**
   - 添加到 `.gitignore` 的文档注释中
   - 在团队内明确告知不可修改

2. **下载验证**（如果实现自动更新）
   - 使用 HTTPS 防止中间人攻击
   - 验证下载文件的 SHA256 哈希
   - 检查数字签名（可选）

3. **强制更新谨慎使用**
   - 仅在发现严重安全漏洞时使用
   - 给用户足够的提示和说明

---

## 📞 故障排查

### 覆盖安装失败

**问题**: 提示"无法覆盖正在使用的文件"
- **原因**: 程序未正确关闭
- **解决**: 检查 `CloseApplicationsFilter` 配置

**问题**: 安装后配置丢失
- **原因**: 未使用 `onlyifdoesntexist` 标记
- **解决**: 修改 `[Files]` 段落的配置文件条目

### 自动更新失败（未来）

**问题**: 无法连接更新服务器
- **原因**: 网络问题或服务器故障
- **解决**: 增加超时设置和重试机制

**问题**: 下载后无法启动安装
- **原因**: 权限不足或文件损坏
- **解决**: 验证文件完整性，提示用户手动安装
