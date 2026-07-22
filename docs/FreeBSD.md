# FreeBSD 支持说明

Bloret Launcher 支持在 **原生 FreeBSD amd64** 上从源码运行，并通过系统包
`games/lwjgl3` 启动现代版本的 Minecraft（LWJGL3 时代，优先 1.20+）。

不使用 Linuxulator。官方 Mojang 不提供 FreeBSD natives；启动器会：

1. 将 Mojang 库规则中的 OS 映射为 `linux`（以选中正确的 jar）
2. **不**下载 `natives-linux`
3. 使用 `/usr/local/lib/lwjgl3` 与 `/usr/local/share/java/classes/lwjgl3` 注入系统 LWJGL

参考实现：FreeBSD ports 中的 `games/prismlauncher` + `games/lwjgl3`。

## 系统要求

| 组件 | 说明 |
|------|------|
| FreeBSD | 13.2+ / 14.x / 15.x，**amd64** |
| Python 3.10+ | 与 ports 中 PySide6 版本匹配 |
| PySide6 + Qt6 | **必须使用 pkg/ports**，不要 pip 安装 PySide6 |
| OpenJDK | 按游戏版本安装 openjdk17 / openjdk21 等 |
| lwjgl3 | `pkg install lwjgl3` |
| 可选 | `libnotify`、`xdg-utils`、图形栈（Xorg/Wayland） |

## 安装依赖

包名随 Python 默认版本变化，请用 `pkg search pyside6` 确认。示例（Python 3.11）：

```sh
sudo pkg install -y \
  python3 \
  py311-pyside6 \
  py311-requests \
  py311-psutil \
  py311-sqlite3 \
  qt6-base \
  qt6-declarative \
  qt6-shadertools \
  openjdk17 \
  lwjgl3 \
  libnotify \
  xdg-utils \
  git
```

纯 Python 依赖可用用户级 pip（**不要**再装 PySide6）：

```sh
python3 -m pip install --user Send2Trash toml dulwich "qrcode[pil]"
```

## 获取启动器

### A. CI / Release 压缩包

GitHub Actions 产物：`Bloret-Launcher-FreeBSD-amd64`  
（内含源码布局、`easytier/` FreeBSD 二进制、`bloret-launcher` 包装脚本）

```sh
tar -xzf Bloret-Launcher-FreeBSD-amd64.tar.gz
cd Bloret-Launcher-FreeBSD-amd64
./bloret-launcher
# 或: python3 Bloret-Launcher.py
```

### B. 源码克隆

```sh
git clone --recursive https://github.com/BloretCrew/Bloret-Launcher.git
cd Bloret-Launcher
python3 Bloret-Launcher.py
```

## 数据目录

默认：

```text
~/.local/share/Bloret-Launcher
```

若设置了 `XDG_DATA_HOME`，则为 `$XDG_DATA_HOME/Bloret-Launcher`。

## Minecraft 与 LWJGL

启动前请确认：

```sh
ls /usr/local/lib/lwjgl3/liblwjgl.so
ls /usr/local/share/java/classes/lwjgl3/*.jar
```

自定义路径可用环境变量：

```sh
export BLORET_LWJGL_LIB=/path/to/lib
export BLORET_LWJGL_JARS=/path/to/jars
```

说明：

- ports 中的 LWJGL 版本可能与 Mojang 锁定版本不完全一致；多数 1.20+ 可玩。
- 极老版本（LWJGL2）未作为首版目标。
- **不要**在 FreeBSD 本机 OpenJDK 上强行使用 Linux ELF natives。

## Java

启动器会扫描 `JAVA_HOME`、`PATH`、`/usr/local/openjdk*` 等。

自动安装 Java **仅支持 Windows**。FreeBSD 请使用：

```sh
sudo pkg install openjdk17
# 或
sudo pkg install openjdk21
```

然后在设置中选择 `/usr/local/openjdk17/bin/java`（路径以实际包为准）。

## EasyTier 联机

官方发布包含 FreeBSD 资产，例如：

```text
easytier-freebsd-13.2-x86_64-v2.6.4.zip
```

来源：<https://github.com/EasyTier/EasyTier/releases>

将 `easytier-core` / `easytier-cli` 放到启动器目录下的 `easytier/` 中。  
CI 的 FreeBSD 压缩包通常已打好。

若需要 TUN 模式，可能涉及权限；Live 联机也可走启动器的免提权代理路径（与 Windows 一致）。

## 自动更新

FreeBSD **不会**下载 Windows `.exe` 安装包。

当更新 API 提供 `downloads.stable.freebsd`（或等价平台键）且为 zip 时，
启动器会下载并解压到应用目录后重启。

若 API 尚未提供 FreeBSD 资产，界面会提示从 GitHub Releases 手动更新。

## 功能降级（有意）

| 功能 | FreeBSD 行为 |
|------|----------------|
| 全局热键 | 未实现（Windows） |
| 游戏内浮动工具栏 | 未实现（Windows） |
| Java 自动下载安装 | 提示使用 pkg |
| 输入法特殊补丁 | 不启用 Linux fcitx 路径；依赖系统 Qt/IME |
| 系统通知 | `notify-send`（需 libnotify） |

## 故障排查

**启动游戏提示未找到系统 LWJGL**

```sh
sudo pkg install lwjgl3
```

**界面无法启动 / 找不到 Qt**

- 确认使用 ports 的 `py*-pyside6`，卸载 pip 版 PySide6
- 安装 `qt6-declarative` 等 QML 相关包

**classpath / native 版本不匹配崩溃**

- 更新 `lwjgl3` port
- 或自建 LWJGL 并用 `BLORET_LWJGL_*` 指向构建产物

## 给打包者

可选依赖摘要：

- 运行：`python3`, PySide6/Qt6, requests, psutil, Send2Trash, toml, dulwich
- 游戏：`lwjgl3`, `openjdk17`/`openjdk21`
- 联机：`easytier-core`（上游 FreeBSD release）

安装布局建议（类 Arch `PKGBUILD`）：

```text
/usr/local/share/bloret-launcher/   # 源码与资源
/usr/local/bin/bloret-launcher      # 包装脚本 exec python3 ...
```
