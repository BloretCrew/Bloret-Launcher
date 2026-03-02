# 修复 Bloret PassPort 头像显示 Spec

## Why
用户报告 Bloret PassPort 头像无法正常显示在主页启动卡片和通行证页面上。

## What Changes
- 检查并修复 `getPassPortAvatar` 方法的实现
- 确保登录时正确保存头像 URL 到 config.json
- 确保 QML 中正确加载和显示头像图片

## Impact
- Affected code: 
  - `Bloret-Launcher.py` (getPassPortAvatar 方法)
  - `modules/web.py` (登录时保存头像)
  - `qml/pages/Home.qml` (头像显示)
  - `qml/pages/PassPort.qml` (头像显示)

## ADDED Requirements

### Requirement: 头像显示功能
系统应正确显示 Bloret PassPort 用户头像。

#### Scenario: 登录后显示头像
- **WHEN** 用户登录 Bloret PassPort
- **THEN** 系统保存头像 URL 到 config.json
- **AND** 主页启动卡片显示用户头像
- **AND** 通行证页面显示用户头像

#### Scenario: 未登录时显示默认头像
- **WHEN** 用户未登录 Bloret PassPort
- **THEN** 系统显示默认头像图标
