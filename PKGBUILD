# Maintainer: Detritalw <detritalw@users.noreply.github.com>
pkgname=bloret-launcher
pkgver=318
pkgrel=2
pkgdesc="A Minecraft Launcher designed by BloretValley administrator"
arch=('x86_64' 'aarch64')
url="https://github.com/BloretCrew/Bloret-Launcher"
license=('GPL-3.0-or-later')

# ===== 运行时依赖 =====
# Nuitka standalone 会把多数 Python/Qt 库打进包内；系统依赖用于源码运行
# 或与 fcitx5-qt 共用系统 Qt 的场景。打包产物本身仍建议安装下列库以兼容插件。
depends=(
    'python'
    'python-pyside6'
    'python-requests'
    'python-psutil'
    'python-dulwich'
    'python-send2trash'
    'python-toml'
    'python-qrcode'
    'python-pillow'
    'python-darkdetect'
    'qt6-5compat'               # Qt5Compat.GraphicalEffects QML
    'qt6-declarative'           # QtQuick / QML
)

# ===== 编译时依赖 =====
makedepends=(
    'git'
    'python-nuitka'
    'python-ordered-set'
    'python-zstandard'
    'python-setuptools'
    'python-pip'
    'ccache'
    'patchelf'
    'curl'
    'unzip'
)

# ===== 可选依赖 =====
optdepends=(
    'java-runtime: 运行 Minecraft 所需的 Java 环境'
    'easytier: 局域网联机（也可使用打包进应用的 easytier 二进制）'
    'fcitx5-qt: Qt fcitx5 输入法前端（源码 + 系统 PySide6 时中文输入必需）'
    'fcitx5: fcitx5 输入法框架'
    'python-websocket-client: Bloriko QQ/Discord/Slack 等 connector'
    'python-cryptography: 微信媒体加解密'
)

# ===== 源码 =====
# release tarball 通常不含子模块；prepare 中再拉 RinUI 等
source=("${pkgname}-${pkgver}.tar.gz::${url}/archive/v${pkgver}.tar.gz")
sha256sums=('SKIP')

_easytier_version=v2.6.4

prepare() {
    cd "${srcdir}/Bloret-Launcher-${pkgver}"

    # 子模块（RinUI / BLAPI 等）；tarball 场景可能无 .git，失败则依赖源码树已含内容
    if [ -f .gitmodules ]; then
        git submodule update --init --recursive 2>/dev/null || true
    fi

    # 下载平台 EasyTier（仓库内 easytier/ 多为 Windows 二进制，不可直接用于 Linux）
    local arch_name zip_name
    case "$CARCH" in
        x86_64)  arch_name=x86_64; zip_name="easytier-linux-x86_64-${_easytier_version}.zip" ;;
        aarch64) arch_name=aarch64; zip_name="easytier-linux-aarch64-${_easytier_version}.zip" ;;
        *)       echo "Unsupported CARCH=$CARCH for EasyTier"; return 0 ;;
    esac

    rm -rf easytier
    mkdir -p easytier
    if curl -fsSL --retry 3 --retry-delay 5 \
        -o "${zip_name}" \
        "https://github.com/EasyTier/EasyTier/releases/download/${_easytier_version}/${zip_name}"; then
        if unzip -t "${zip_name}" &>/dev/null; then
            mkdir -p easytier-tmp
            unzip -o "${zip_name}" -d easytier-tmp
            find easytier-tmp -name 'easytier-core*' -exec cp {} easytier/ \;
            find easytier-tmp -name 'easytier-cli*' -exec cp {} easytier/ \;
            chmod +x easytier/easytier-core* easytier/easytier-cli* 2>/dev/null || true
            rm -rf easytier-tmp "${zip_name}"
            echo "EasyTier ${arch_name} ready"
        else
            echo "warning: EasyTier zip invalid, skipping"
            rm -f "${zip_name}"
        fi
    else
        echo "warning: EasyTier download failed,联机功能可能不可用"
    fi
}

build() {
    cd "${srcdir}/Bloret-Launcher-${pkgver}"

    # 安装 RinUI，使 Nuitka 能解析 import RinUI（含 darkdetect 等）
    pip install ./RinUI --no-build-isolation 2>/dev/null \
        || pip install ./RinUI --no-build-isolation --no-deps || true

    # PySide6 QML 目录中的 *.o/*.a 会误导 Nuitka+patchelf
    if python -c "from PySide6.QtCore import QLibraryInfo" &>/dev/null; then
        local qml_dir
        qml_dir="$(python -c "from PySide6.QtCore import QLibraryInfo; print(QLibraryInfo.path(QLibraryInfo.LibraryPath.QmlImportsPath))")"
        if [ -n "$qml_dir" ] && [ -d "$qml_dir" ]; then
            find "$qml_dir" -type f \( -name '*.o' -o -name '*.a' -o -name '*.prl' \) -delete || true
        fi
    fi

    local easytier_arg=()
    if [ -d easytier ] && [ -n "$(ls -A easytier 2>/dev/null)" ]; then
        easytier_arg=(--include-data-dir=easytier=easytier)
    fi

    local extra_files=()
    [ -f bloret.ico ] && extra_files+=(--include-data-files=bloret.ico=bloret.ico)
    [ -f servers.dat ] && extra_files+=(--include-data-files=servers.dat=servers.dat)
    [ -f JavaWrapper.jar ] && extra_files+=(--include-data-files=JavaWrapper.jar=JavaWrapper.jar)
    [ -f LICENSE ] && extra_files+=(--include-data-files=LICENSE=LICENSE)
    [ -f config.json ] && extra_files+=(--include-data-files=config.json=config.json)

    # 与 CI Nuitka-Build 对齐：standalone 目录分发（非 onefile）
    python -m nuitka \
        --standalone \
        --enable-plugin=pyside6 \
        --include-qt-plugins=sensible,styles,qml \
        --include-data-dir=qml=qml \
        --include-data-dir=RinUI/RinUI=RinUI \
        --include-data-dir=icon=icon \
        --include-data-dir=lang=lang \
        --include-data-dir=modules=modules \
        --include-data-files=Bloret.png=Bloret.png \
        --include-data-files=Bloret-Fluent.png=Bloret-Fluent.png \
        "${extra_files[@]}" \
        "${easytier_arg[@]}" \
        --output-filename=Bloret-Launcher \
        --assume-yes-for-downloads \
        Bloret-Launcher.py
}

package() {
    cd "${srcdir}/Bloret-Launcher-${pkgver}"

    local dist=""
    if [ -d Bloret-Launcher.dist ]; then
        dist=Bloret-Launcher.dist
    else
        dist="$(find . -maxdepth 2 -type d -name 'Bloret-Launcher*.dist' | head -1)"
    fi
    if [ -z "$dist" ] || [ ! -d "$dist" ]; then
        echo "error: Nuitka dist directory not found" >&2
        return 1
    fi

    # 应用文件树 → /usr/lib/bloret-launcher
    install -d "${pkgdir}/usr/lib/bloret-launcher"
    cp -a "$dist"/. "${pkgdir}/usr/lib/bloret-launcher/"

    # 入口脚本
    install -Dm755 /dev/stdin "${pkgdir}/usr/bin/bloret-launcher" <<'EOF'
#!/bin/sh
exec /usr/lib/bloret-launcher/Bloret-Launcher "$@"
EOF
    chmod +x "${pkgdir}/usr/lib/bloret-launcher/Bloret-Launcher" 2>/dev/null || true

    # 图标与桌面项
    if [ -f Bloret-Fluent.png ]; then
        install -Dm644 Bloret-Fluent.png "${pkgdir}/usr/share/pixmaps/bloret-launcher.png"
    elif [ -f Bloret.png ]; then
        install -Dm644 Bloret.png "${pkgdir}/usr/share/pixmaps/bloret-launcher.png"
    fi

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

    install -Dm644 LICENSE "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
}
