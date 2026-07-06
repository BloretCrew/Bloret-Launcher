# Maintainer: Detritalw <detritalw@users.noreply.github.com>
pkgname=bloret-launcher
pkgver=318
pkgrel=1
pkgdesc="A Minecraft Launcher designed by BloretValley administrator"
arch=('x86_64' 'aarch64')
url="https://github.com/BloretCrew/Bloret-Launcher"
license=('GPL-3.0-or-later')

# ===== 运行时依赖 =====
# 以下为 Arch 官方仓库中可用的 Python 依赖
depends=(
    'python'                    # Python 运行时
    'python-pyside6'            # PySide6 (Qt for Python) - UI 框架
    'python-requests'           # HTTP 客户端
    'python-psutil'             # 进程管理 (监控 Minecraft 进程)
    'python-dulwich'            # Git 操作库
    'python-send2trash'         # 安全删除文件 (移到回收站)
    'python-toml'               # TOML 文件解析
    'qt6-5compat'               # Qt5Compat.GraphicalEffects QML 模块
    'qt6-declarative'           # QtQuick / QML 引擎
)

# ===== 编译时依赖 =====
# Nuitka 编译 + git 子模块
makedepends=(
    'git'                       # 克隆子模块 (BLAPI, BL4CW2)
    'python-nuitka'             # Python 编译器
    'python-ordered-set'        # Nuitka 依赖
    'python-zstandard'          # Nuitka 压缩依赖
    'python-setuptools'         # Nuitka 兼容性
    'ccache'                    # 可选: 加速重复编译
)

# ===== 可选依赖 =====
# Minecraft 运行所需的 Java
optdepends=(
    'java-runtime: 运行 Minecraft 所需的 Java 环境'
    'easytier: 局域网联机功能所需的 EasyTier 网络工具'
)

# ===== 源码 =====
# 使用 GitHub release 源码包，需要 --recurse-submodules 获取子模块
source=("${pkgname}-${pkgver}.tar.gz::${url}/archive/v${pkgver}.tar.gz")
sha256sums=('SKIP')  # 后续可用 updpkgsums 生成

# ===== 如果 GitHub 不支持自动打包子模块，改用 git 克隆 =====
# source=("git+${url}#tag=v${pkgver}?signed")
# sha256sums=('SKIP')

prepare() {
    cd "${srcdir}/Bloret-Launcher-${pkgver}"

    # 初始化并更新 git 子模块 (BLAPI, BL4CW2)
    git submodule update --init --recursive 2>/dev/null || true
}

build() {
    cd "${srcdir}/Bloret-Launcher-${pkgver}"

    # 使用 Nuitka 编译为独立可执行文件
    # --standalone: 包含所有依赖
    # --onefile: 单文件可执行
    # --enable-plugin=pyside6: 启用 PySide6 插件
    # --include-qt-plugins=sensible: 包含必要的 Qt 插件
    # --include-data-dir: 打包数据文件 (QML, 图标, 语言文件等)
    python -m nuitka \
        --standalone \
        --onefile \
        --enable-plugin=pyside6 \
        --include-qt-plugins=sensible \
        --include-data-dir=qml=qml \
        --include-data-dir=RinUI=RinUI \
        --include-data-dir=icon=icon \
        --include-data-dir=lang=lang \
        --include-data-dir=modules=modules \
        --include-data-files=Bloret.png=Bloret.png \
        --include-data-files=Bloret-Fluent.png=Bloret-Fluent.png \
        --output-file=bloret-launcher \
        --assume-yes-for-downloads \
        --remove-output \
        Bloret-Launcher.py
}

package() {
    cd "${srcdir}/Bloret-Launcher-${pkgver}"

    # 安装编译后的可执行文件
    install -Dm755 bloret-launcher "${pkgdir}/usr/bin/bloret-launcher"

    # 安装数据文件 (config.json, JavaWrapper.jar 等)
    install -Dm644 config.json "${pkgdir}/usr/share/bloret-launcher/config.json"
    install -Dm644 JavaWrapper.jar "${pkgdir}/usr/share/bloret-launcher/JavaWrapper.jar"
    install -Dm644 servers.dat "${pkgdir}/usr/share/bloret-launcher/servers.dat" 2>/dev/null || true

    # 安装图标
    install -Dm644 Bloret-Fluent.png "${pkgdir}/usr/share/pixmaps/bloret-launcher.png"

    # 安装桌面文件
    install -Dm644 /dev/stdin "${pkgdir}/usr/share/applications/bloret-launcher.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Bloret Launcher
GenericName=Minecraft Launcher
Comment=A Minecraft Launcher designed by BloretValley administrator.
Exec=bloret-launcher
Icon=bloret-launcher
Terminal=false
Categories=Game;
Keywords=minecraft;game;launcher;
EOF

    # 安装许可证
    install -Dm644 LICENSE "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
}
