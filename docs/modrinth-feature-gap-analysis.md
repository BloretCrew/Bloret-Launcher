# Bloret Launcher vs Modrinth App 功能差距分析

> 分支：`analysis/modrinth-feature-gap`  
> 对照源码：`/data/modrinth-code`（sparse checkout：`apps/app` + `apps/app-frontend` + `packages/app-lib` + `packages/daedalus`）  
> 对照仓库：https://github.com/modrinth/code  
> 分析日期：2026-08-05

## 0. 一句话结论

| 维度 | Bloret | Modrinth App |
|------|--------|--------------|
| 定位 | AI + 联机 + 通行证 + 插件的「个人创新启动器」 | 内容生态 + 实例管理 + 社交同步的「Modrinth 官方客户端」 |
| 技术栈 | Python + PySide6/RinUI (QML) | Rust (Theseus) + Vue + Tauri |
| 架构模型 | 版本目录（`.minecraft/versions/<name>`） | 真·实例（独立目录 + SQLite 元数据） |
| 独有优势 | AI、EasyTier/Live、PassPort、资源包编辑器、插件宿主、FreeBSD | 整合包生态深度、跨启动器导入、Shared Instance、好友、皮肤库、Hosting |
| 最大短板（相对对方） | 内容/实例/社交基础设施偏薄 | 无 AI、无国内联机、无自有通行证生态 |

**不要照搬 Modrinth 全套。** 优先补「用户迁移成本 + 内容生命周期」相关缺口；AI/联机/PassPort 继续当差异化护城河。

---

## 1. 源码地图

### Modrinth App（Theseus）

```
packages/app-lib/src/
  api/          # 对外能力面
    instance/   # 实例生命周期 / 内容 / 导出 / Shared
    pack/       # mrpack 安装 + 跨启动器导入
    minecraft_skins / worlds / friends / process / jre / logs ...
  launcher/     # 参数、下载、hooks、Quick Play
  install/      # 安装流水线（可恢复、分阶段进度）
  state/        # SQLite + Discord RPC + 好友 socket
apps/app-frontend/src/pages/
  library/ instance/ project/ Browse / Skins / Servers / hosting/
```

### Bloret Launcher

```
Bloret-Launcher.py          # Backend 大一统（~6k 行）
modules/
  install / launch / versions / modrinth / mrpack_export
  easytier / bbbs_live / Bloriko / plugin_host / resourcepack_editor
  services/{versions,content,launch,config}_service
qml/pages/
  Home Download Cores Mods Live Multiplayer Bloriko PassPort Tools Settings ...
```

---

## 2. 功能对照总表

图例：✅ 有　🟡 部分/简陋　❌ 无　⭐ 我方独有

| 能力域 | Bloret | Modrinth | 差距等级 |
|--------|--------|----------|----------|
| 原版安装 | ✅ | ✅ | — |
| Fabric | ✅ | ✅ | — |
| Forge / NeoForge | ✅ | ✅ | — |
| Quilt | ❌ | ✅ | 中 |
| 实例/版本管理 | 🟡 版本目录 | ✅ 真实例 + SQLite | **高** |
| 每实例设置（内存/分辨率/Java/env/hooks） | 🟡 偏全局 | ✅ 实例级完整 | **高** |
| mrpack 导入 | ✅ | ✅ 深度（依赖、hash、并发） | 中 |
| mrpack 导出 | ✅ 基础 | ✅ 候选文件树 + 智能默认勾选 | 中 |
| 跨启动器导入（Prism/MMC/ATL/GDL/CF） | ❌ | ✅ | **高** |
| CurseForge 内容源 | ❌ | 🟡 导入侧有 | 中 |
| Mod 安装（Modrinth） | ✅ | ✅ + 依赖解析 | **高** |
| Mod 一键更新 / 全量更新 | ❌/弱 | ✅ `update_all_projects` | **高** |
| 内容修复 repair | ❌ | ✅ `repair_managed_modrinth` | 中 |
| 依赖自动安装 | ❌ | ✅ `install_project_with_dependencies` | **高** |
| 资源包 / 光影 / 数据包 | 🟡 资源包为主；浏览含 shader/datapack | ✅ 一等公民 content type | 中 |
| 服务器列表 | ✅ | ✅ worlds 统一模型 | 低 |
| 单人世界浏览 / 编辑 / 导出 | ❌ | ✅ worlds API（NBT、icon、last played） | **高** |
| Quick Play（直进世界/服务器） | ❌ | ✅ Builtin/Legacy/Injected | **高** |
| 皮肤管理（上传/装备/披风/预览） | 🟡 仅 URL 查询 | ✅ 完整皮肤库 | **高** |
| 微软账号 | ✅ | ✅ | — |
| 离线账号 | ✅ | ❌/弱 | ⭐ |
| Bloret PassPort | ✅ | ❌ | ⭐ |
| Shared Instance（云同步分享） | ❌ | ✅ 邀请/角色/内容 diff/config bundle | **高** |
| 好友在线状态 | ❌ | ✅ friends socket | 中 |
| Discord Rich Presence | ❌ | ✅ | 低 |
| 启动 Hooks（pre/wrapper/post） | 🟡 插件 hook，非用户实例 hook | ✅ 用户可配 hooks | 中 |
| 进程管理 | ✅ | ✅ UUID 级 | 低 |
| 日志 / 崩溃报告 | 🟡 日志 | ✅ InfoLog + CrashReport + 脱敏 | 中 |
| 游玩时长 | ✅ 细（焦点/日统计） | 🟡 有 playtime | ⭐ 我方更细 |
| Hosting（租用服务器面板） | ❌ | ✅ hosting/* | 低（商业能力） |
| 安装进度 / 可恢复安装 | 🟡 | ✅ InstallPhase + recovery | 中 |
| 自动 Java | ✅ | ✅ | — |
| 自动更新启动器 | ✅ | ✅ | — |
| 插件系统 | ✅ | ❌ | ⭐ |
| AI 助手 Bloriko | ✅ | ❌ | ⭐ |
| 资源包编辑器 | ✅ | ❌ | ⭐ |
| EasyTier / Live 联机 | ✅ | ❌ | ⭐ |
| FreeBSD | ✅ | ❌ | ⭐ |
| 托盘 / 浮动工具栏 | ✅ | ❌/弱 | ⭐ |
| 深浅色 / i18n | ✅ | ✅（语种更多） | 低 |
| 架构：状态持久化 | JSON 配置 | SQLite + 迁移 + 备份 | **高** |

---

## 3. 结构性差距（比「缺功能」更重要）

### 3.1 实例模型

**Modrinth**：每个实例独立目录 + `instances` 表元数据；内容用 content set / content item 建模；支持 linked modpack、managed content、sync state。

**Bloret**：更接近「一个 Minecraft 根目录下的多个 version 文件夹」；`bl.json` 做轻量标注。

影响：
- 很难做干净的实例级设置、实例复制、共享同步
- 内容更新/依赖图难做（没有 content 实体层）
- 跨启动器导入/导出语义对不齐

**建议**：不必立刻 SQLite 化全盘，但应引入 **Instance 抽象层**（路径、loader、MC 版本、内容清单、设置 overrides），现有 version 目录做 adapter。

### 3.2 内容生命周期

Modrinth `projects.rs` 已有：
- `install_project_with_dependencies`
- `switch_project_version_with_dependencies`
- `update_all_projects` / `update_project`
- `repair_managed_modrinth`
- hash → Modrinth 文件反查（`is_file_on_modrinth`）

Bloret 目前：
- 能下 Mod、能列本地 jar、能开关/删
- **缺依赖图、缺批量更新、缺修复、缺「这个 jar 对应哪个 project/version」的稳定映射**

这是用户感知最强的差距之一（「为什么 Modrinth 一键更新，我们要一个个找」）。

### 3.3 安装流水线

Modrinth `install/`：分 phase、进度事件、recovery、shared instance 安装数据。

Bloret `install.py` 很重（~2.5k 行）但阶段语义、失败恢复、取消一致性仍偏脚本化。

---

## 4. 按优先级的缺失清单

### P0 — 直接影响「能不能当主力启动器」

| # | 缺口 | 说明 | 参考 |
|---|------|------|------|
| 1 | **Mod 依赖自动解析与安装** | 装一个模组应拉齐 required 依赖 | `install_project_with_dependencies` |
| 2 | **已装内容检测更新 / 一键更新** | 按 hash 或 project_id 对照 Modrinth | `update_all_projects` / `check_content_updates` |
| 3 | **内容元数据持久化** | 记录 project_id / version_id / hash / 文件路径 | content set 模型 |
| 4 | **实例级设置** | 内存、Java、JVM 参数、环境变量、窗口、自定义目录 | instance settings modal |

### P1 — 迁移与生态

| # | 缺口 | 说明 | 参考 |
|---|------|------|------|
| 5 | **从 Prism / MultiMC / ATL / GDL / CurseForge 导入** | 用户换启动器零成本 | `api/pack/import/*` |
| 6 | **Quilt 安装** | 加载器矩阵补全 | ModLoader |
| 7 | **更强的 mrpack 导出** | 文件树勾选、默认路径、排除缓存/native | `export_mrpack` candidates |
| 8 | **光影包 / 数据包一等管理** | 与 mods/resourcepacks 同级 UI + 服务 | content types |

### P2 — 体验与「现代启动器」体感

| # | 缺口 | 说明 | 参考 |
|---|------|------|------|
| 9 | **世界管理 + Quick Play** | 主页最近世界、直进单人/服务器 | `api/worlds.rs` + `quick_play_version.rs` |
| 10 | **皮肤库** | 保存/上传/装备/披风/模型变体，不只查 URL | `api/minecraft_skins` |
| 11 | **用户级 Launch Hooks** | pre-launch / wrapper / post-exit | `launcher/hooks.rs` |
| 12 | **崩溃报告浏览 + 日志脱敏** | 启动失败可自助 | `api/logs.rs` |
| 13 | **Discord RPC** | 可选，成本低 | `state/discord.rs` |

### P3 — 可后置 / 或用差异化替代

| # | 缺口 | 说明 |
|---|------|------|
| 14 | Shared Instance 云同步 | 强依赖 Modrinth 账号与后端；可用 EasyTier + 整合包分享部分替代 |
| 15 | Friends 社交 | 同上；Live 房间已是另一种社交 |
| 16 | Hosting 面板 | 商业能力，非启动器核心 |
| 17 | Feature flags / 遥测 | 工程设施，非用户功能 |

---

## 5. Bloret 已领先 / 不该丢掉的差异化

这些是 **Modrinth 没有、我们有** 的，分析时不要被「缺功能」带偏：

1. **Bloriko AI**（对话装模组、DeepThink、多 IM connector）
2. **EasyTier + BBBS Live 联机**（免端口映射的房间制联机）
3. **Bloret PassPort**（自有账号体系 + 与微软/离线融合）
4. **资源包编辑器**（整套 Agent + 纹理/模型/音效/语言…）
5. **插件宿主**（hooks / 权限 / 进程与声明式加载）
6. **细粒度游玩统计**（焦点时间、日统计）
7. **FreeBSD / 托盘 / 浮动工具栏 / Bark 通知** 等桌面体验

策略建议：**用 AI + 联机降低「内容管理不足」的痛感，同时把 P0 内容生命周期补齐**，而不是去堆 Shared Instance / Hosting。

---

## 6. 建议落地路线（可执行）

### Phase A — 内容实体层（2–4 周量级）

1. 为每个 version/instance 增加 `content-index.json`（或 SQLite 表）：
   - path, sha1/sha512, project_id, version_id, source(modrinth/local), enabled
2. 安装 Mod 时写入索引；本地扫描 jar 时尝试 hash 反查 Modrinth
3. UI：Mods 页显示「可更新」角标

### Phase B — 依赖与更新（接 A）

1. 调 Labrinth dependencies API，装 required
2. `更新全部` / `更新选中`
3. 可选：`修复`（按 version_id 重下）

### Phase C — 实例设置与导入

1. 实例 overrides：memory / java / jvm args / env / resolution
2. Prism/MultiMC 导入（二者格式接近，ROI 最高）
3. Quilt

### Phase D — 体验件

1. Quick Play（至少服务器直进；单人世界 NBT 解析可复用现有 `SimpleNBT`）
2. 皮肤库 MVP（本地保存 + 装备到微软账号）
3. 用户 hooks + Discord RPC

---

## 7. 风险与注意

- **许可证**：Modrinth monorepo 各包许可证不同，**禁止直接拷代码**；只学模型与流程。
- **实例模型迁移**：现有用户 version 目录不能破坏；用 adapter + 渐进迁移。
- **主文件过大**：`Bloret-Launcher.py` ~6k 行，新能力应进 `modules/services/` + QML，避免继续堆 Backend。
- **不要为对齐而对齐**：Shared Instance / Hosting 没有自有后端就不要硬做壳。

---

## 8. 本地对照路径

| 用途 | 路径 |
|------|------|
| 本分析文档 | `/data/Bloret-Launcher/docs/modrinth-feature-gap-analysis.md` |
| Bloret 分支 | `analysis/modrinth-feature-gap`（基于 `Windows`） |
| Modrinth 源码（sparse） | `/data/modrinth-code` |
| Modrinth 能力面入口 | `packages/app-lib/src/api/mod.rs` |
| 导入实现 | `packages/app-lib/src/api/pack/import/` |
| 内容/依赖 | `packages/app-lib/src/api/instance/projects.rs` |
| 世界 / Quick Play | `api/worlds.rs` + `launcher/quick_play_version.rs` |
| 皮肤 | `api/minecraft_skins.rs` |
| Shared Instance | `api/instance/shared/` |

---

## 9. 总结

Bloret 在 **AI、联机、通行证、插件、资源包创作** 上已经走出差异化；  
相对官方 Modrinth App，短板集中在：

1. **真实例 + 持久化内容模型**  
2. **依赖 / 更新 / 修复的内容生命周期**  
3. **跨启动器迁移**  
4. **世界 / 皮肤 / Quick Play 等「现代启动器」体感**

先做 P0（内容索引 + 依赖 + 更新），再做导入与实例设置，性价比最高。

---

## 10. 实现状态（analysis/modrinth-feature-gap，2026-08-05）

| 项 | 状态 | 落点 |
|----|------|------|
| P0 content-index + hash | ✅ | `modules/services/content_index.py` |
| P0 依赖安装 / 一键更新 | ✅ | `content_lifecycle.py` + `modrinth_content.py`；`Backend._download_one_mod` 已走依赖安装 |
| P0 实例级设置 | ✅ | `instance_settings.py`；`launch.py` 合并 overrides；CoreManager 高级页 UI |
| P1 Prism/MMC 导入 | ✅ 服务层 | `instance_import.py` + Backend slots |
| P1 Quilt | ✅ | `install.py` Quilt 分支；Download.qml 卡片；`downloadQuilt` |
| P1 光影/数据包 | ✅ | content_service list + 安装目录创建 |
| P1 mrpack 候选导出 | ✅ | `mrpack_export.get_export_candidates` / selected_paths |
| P2 世界 + Quick Play | ✅ | `worlds_service.py`；CoreManager 世界页；launch 注入参数 |
| P2 皮肤库 | ✅ 服务层 | `skins_service.py` + Backend slots（独立皮肤页 UI 可再补） |
| P2 hooks / Discord / 崩溃日志 | ✅ | `runtime_extras.py`；launch + feature_bridge |
| 单测 | ✅ | `test_p0_p2_features.py`（7 passed） |

验证：`python3 test_p0_p2_features.py -v`
