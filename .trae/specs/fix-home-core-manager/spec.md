# 修复主页布局和核心管理功能 Spec

## Why
主页启动卡片和版本选择布局存在问题，核心管理功能无法正常打开。需要修复布局并使用 RinUI 迁移核心管理功能。

## What Changes
- 修复 Home.qml 启动栏布局问题
- 修复版本选择对话框布局问题
- 创建 QML 版本的核心管理对话框 (CoreManagerDialog.qml)
- 在 Backend 中添加核心管理相关方法
- 连接信号使核心管理功能正常工作

## Impact
- Affected code: 
  - `qml/pages/Home.qml`
  - `qml/components/CoreManagerDialog.qml`
  - `Bloret-Launcher.py`

## ADDED Requirements

### Requirement: 核心管理对话框
系统应提供 QML 版本的核心管理对话框，包含以下功能：
- 基本信息编辑（名称、图标）
- 服务器设置
- 高级设置（实际版本、Fabric 开关、JVM 参数）
- 删除核心功能

#### Scenario: 打开核心管理
- **WHEN** 用户右键点击 Minecraft 版本并选择"核心管理"
- **THEN** 系统显示核心管理对话框

#### Scenario: 保存核心设置
- **WHEN** 用户修改核心信息并点击保存
- **THEN** 系统保存核心数据到 .BL.json 文件

### Requirement: 启动栏布局
启动栏应固定在页面底部，不随内容滚动。

#### Scenario: 启动栏显示
- **WHEN** 用户滚动主页内容
- **THEN** 启动栏保持在底部不动
