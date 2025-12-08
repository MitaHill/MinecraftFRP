# Bug修复记录

## Bug 1: Ping数据显示加载失败

### 问题描述
启动程序时出现以下错误：
```
AttributeError: 'NoneType' object has no attribute 'get'
```

### 问题原因
`load_ping_data()` 函数在某些情况下返回 `None`（当YAML文件为空或格式不正确时），但调用代码期望得到字典类型的返回值。

### 修复内容
- 在 `src/network/ping_utils.py` 的 `load_ping_data()` 函数中添加 `None` 检查，确保函数始终返回字典类型，即使YAML文件为空。
- 在 `src/gui/main_window.py` 的 `setupUI()` 和 `update_server_combo()` 方法中添加额外的安全检查和类型验证。

### 状态
**已解决**

---

## Bug 2: 服务器管理配置窗口无法打开

### 问题描述
在“设置”标签页中，点击“服务器管理配置”按钮时，程序没有响应，无法打开对应的配置窗口。

### 问题原因
`ServerManagementDialog` 在初始化 (`__init__`) 时，会调用 `setup_server_management_ui` 来构建界面。这个函数接着调用 `setup_table_buttons` 来创建“添加服务器”和“删除选中”按钮。问题在于，`setup_table_buttons` 将这两个按钮创建为局部变量，而 `ServerManagementDialog` 的 `__init__` 方法在UI设置完成后，尝试以实例属性（`self.add_button`, `self.delete_button`）的形式访问它们并禁用，因此引发 `AttributeError`，导致对话框创建失败。

### 修复内容
修改了 `src/gui/dialogs/UiComponents.py` 文件中的 `setup_table_buttons` 函数。

### 修复前后对比

#### 修复前:
```python
# In src/gui/dialogs/UiComponents.py
def setup_table_buttons(dialog, layout):
    table_button_layout = QHBoxLayout()
    add_button = QPushButton("添加服务器") # <-- Local variable
    add_button.clicked.connect(dialog.add_server_row)
    table_button_layout.addWidget(add_button)
    
    delete_button = QPushButton("删除选中") # <-- Local variable
    delete_button.clicked.connect(dialog.delete_selected_row)
    table_button_layout.addWidget(delete_button)
    
    table_button_layout.addStretch()
    layout.addLayout(table_button_layout)
```

#### 修复后:
```python
# In src/gui/dialogs/UiComponents.py
def setup_table_buttons(dialog, layout):
    table_button_layout = QHBoxLayout()
    dialog.add_button = QPushButton("添加服务器") # <-- Assigned to instance
    dialog.add_button.clicked.connect(dialog.add_server_row)
    table_button_layout.addWidget(dialog.add_button)
    
    dialog.delete_button = QPushButton("删除选中") # <-- Assigned to instance
    dialog.delete_button.clicked.connect(dialog.delete_selected_row)
    table_button_layout.addWidget(dialog.delete_button)
    
    table_button_layout.addStretch()
    layout.addLayout(table_button_layout)
```

### 测试结果
- ✅ 点击“服务器管理配置”按钮后，对话框可以正常弹出。
- ✅ 相关的“添加”和“删除”按钮在对话框上被正确禁用，符合只读逻辑。

### 状态
**已解决** - 对话框现在可以按预期打开。
