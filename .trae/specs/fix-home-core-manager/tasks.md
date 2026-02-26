# Tasks

- [x] Task 1: 修复 Home.qml 启动栏布局
  - [x] SubTask 1.1: 确保启动栏固定在底部不随内容滚动
  - [x] SubTask 1.2: 调整启动栏内部元素布局

- [x] Task 2: 修复版本选择对话框布局
  - [x] SubTask 2.1: 调整 LaunchSelectorDialog.qml 的布局和样式
  - [x] SubTask 2.2: 确保右键菜单正常显示

- [x] Task 3: 创建 QML 核心管理对话框
  - [x] SubTask 3.1: 创建 CoreManagerDialog.qml 组件
  - [x] SubTask 3.2: 实现基本信息编辑功能（名称、图标、快速访问）
  - [x] SubTask 3.3: 实现服务器设置功能
  - [x] SubTask 3.4: 实现资源包管理功能
  - [x] SubTask 3.5: 实现 Mod 管理功能
  - [x] SubTask 3.6: 实现高级设置功能（版本、Fabric 开关、删除核心）

- [x] Task 4: 在 Backend 中添加核心管理方法
  - [x] SubTask 4.1: 添加 coreManagerRequested 信号
  - [x] SubTask 4.2: 添加 getCoreData 方法
  - [x] SubTask 4.3: 添加 saveCoreData 方法
  - [x] SubTask 4.4: 添加 confirmDeleteCore 方法
  - [x] SubTask 4.5: 添加 openSubFolder 方法

- [x] Task 5: 连接核心管理信号
  - [x] SubTask 5.1: 在 Home.qml 中添加 CoreManagerDialog 实例
  - [x] SubTask 5.2: 连接 coreManagerRequested 信号

# Task Dependencies
- [Task 3] depends on [Task 4]
- [Task 5] depends on [Task 3, Task 4]
