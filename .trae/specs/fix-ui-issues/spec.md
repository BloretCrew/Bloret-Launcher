# 修复界面布局和功能问题 Spec

## Why
用户报告多个界面布局和功能问题未修复，包括启动卡片布局混乱、版本选择对话框文字重叠、核心管理对话框标题重叠、右键菜单第一次只显示 Launch、服务器页面无法正常添加服务器等。

## What Changes
- 修复主页启动卡片布局混乱问题
- 修复版本选择对话框文字重叠问题
- 修复核心管理对话框标题重叠问题
- 修复右键菜单第一次只显示 Launch 的问题
- 修复服务器页面添加服务器和显示问题
- 优化 Mod、资源包、服务器页面使用 RinUI 组件

## Impact
- Affected code: 
  - `qml/pages/Home.qml`
  - `qml/components/LaunchSelectorDialog.qml`
  - `qml/components/CoreManagerDialog.qml`
  - `Bloret-Launcher.py`

## ADDED Requirements

### Requirement: 主页启动卡片布局
主页启动卡片应清晰显示用户信息和版本选择，布局应整洁不混乱。

#### Scenario: 启动卡片显示
- **WHEN** 用户查看主页
- **THEN** 启动卡片显示 "您好, {用户名} ! 将使用 {玩家名} 来登录 Minecraft"
- **AND** 版本图标、版本名称、切换核心按钮、启动按钮正确对齐

### Requirement: 版本选择对话框
版本选择对话框的提示文字不应与标题重叠。

#### Scenario: 版本选择对话框显示
- **WHEN** 用户打开版本选择对话框
- **THEN** "右键单击启动项可进行管理" 提示文字与标题 "选择启动项目" 不重叠

### Requirement: 核心管理对话框标题
核心管理对话框标题应只显示一次，不重叠。

#### Scenario: 核心管理对话框显示
- **WHEN** 用户打开核心管理对话框
- **THEN** 标题显示 "核心管理: {版本名}"，无重复

### Requirement: 右键菜单
右键菜单应在第一次打开时就显示所有菜单项。

#### Scenario: 右键菜单显示
- **WHEN** 用户右键点击 Minecraft 启动项
- **THEN** 菜单显示 "启动"、"核心管理"、"打开文件位置" 等选项

### Requirement: 服务器管理
服务器页面应能正常添加服务器并显示服务器列表。

#### Scenario: 添加服务器
- **WHEN** 用户点击 "添加服务器" 并输入服务器名称和地址
- **THEN** 服务器被添加到列表中并显示
