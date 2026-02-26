# Tasks

- [ ] Task 1: 修复 Home.qml 启动栏布局
  - [ ] SubTask 1.1: 确保启动栏固定在底部不随内容滚动
  - [ ] SubTask 1.2: 调整启动栏内部元素布局

- [ ] Task 2: 修复版本选择对话框布局
  - [ ] SubTask 2.1: 调整 LaunchSelectorDialog.qml 的布局和样式
  - [ ] SubTask 2.2: 确保右键菜单正常显示

- [ ] Task 3: 创建 QML 核心管理对话框
  - [ ] SubTask 3.1: 创建 CoreManagerDialog.qml 组件
  - [ ] SubTask 3.2: 实现基本信息编辑功能
  - [ ] SubTask 3.3: 实现高级设置功能
  - [ ] SubTask 3.4: 实现删除核心功能

- [ ] Task 4: 在 Backend 中添加核心管理方法
  - [ ] SubTask 4.1: 添加 coreManagerRequested 信号
  - [ ] SubTask 4.2: 添加 getCoreData 方法
  - [ ] SubTask 4.3: 添加 saveCoreData 方法
  - [ ] SubTask 4.4: 添加 confirmDeleteCore 方法

- [ ] Task 5: 连接核心管理信号
  - [ ] SubTask 5.1: 在 Home.qml 中添加 CoreManagerDialog 实例
  - [ ] SubTask 5.2: 连接 coreManagerRequested 信号

# Task Dependencies
- [Task 3] depends on [Task 4]
- [Task 5] depends on [Task 3, Task 4]
