# Tasks

- [x] Task 1: 检查 getPassPortAvatar 方法
  - [x] SubTask 1.1: 检查方法是否正确读取 config.json 中的头像 URL
  - [x] SubTask 1.2: 检查头像缓存逻辑是否正确
  - [x] SubTask 1.3: 添加 fallback 使用 visage.surgeplay.com 获取头像

- [x] Task 2: 检查登录时头像保存逻辑
  - [x] SubTask 2.1: 检查 web.py 中是否正确保存头像 URL
  - [x] SubTask 2.2: 确保 avatar 字段正确写入 config.json

- [x] Task 3: 检查 QML 头像显示
  - [x] SubTask 3.1: 检查 Home.qml 中头像 Image 组件的 source 绑定
  - [x] SubTask 3.2: 检查 PassPort.qml 中头像 Image 组件的 source 绑定
  - [x] SubTask 3.3: 确保正确处理加载错误和显示默认头像

# Task Dependencies
- [Task 3] depends on [Task 1, Task 2]
