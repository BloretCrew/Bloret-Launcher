# FreeBSD Support

Bloret Launcher supports running from source on **native FreeBSD amd64** and launching modern Minecraft versions (the LWJGL3 era, preferably 1.20+) through the system package `games/lwjgl3`.

Linuxulator is not used. Mojang does not provide FreeBSD natives, so the launcher:

1. Maps the OS in Mojang library rules to `linux` (to select the correct jars).
2. Does **not** download `natives-linux`.
3. Injects the system LWJGL from `/usr/local/lib/lwjgl3` and `/usr/local/share/java/classes/lwjgl3`.

Reference implementation: `games/prismlauncher` + `games/lwjgl3` in the FreeBSD ports tree.

## System Requirements

| Component | Notes |
|------|------|
| FreeBSD | 13.2+ / 14.x / 15.x, **amd64** |
| Python 3.10+ | Match the PySide6 version in ports |
| PySide6 + Qt6 | **Use pkg/ports only**; do not install PySide6 with pip |
| OpenJDK | Install openjdk17 / openjdk21 or another version matching the game |
| lwjgl3 | `pkg install lwjgl3` |
| Optional | `libnotify`, `xdg-utils`, and a graphical stack (Xorg/Wayland) |

## Installing Dependencies

Package names follow the default Python version. Use `pkg search pyside6` to confirm them. Example for Python 3.11:

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

Pure Python dependencies can be installed with a user-level pip (**do not** install PySide6 again):

```sh
python3 -m pip install --user Send2Trash toml dulwich "qrcode[pil]"
```

## Getting the Launcher

### A. CI / Release Archive

GitHub Actions artifact: `Bloret-Launcher-FreeBSD-amd64`
(Contains the source layout, the FreeBSD EasyTier binary in `easytier/`, and the `bloret-launcher` wrapper script.)

```sh
tar -xzf Bloret-Launcher-FreeBSD-amd64.tar.gz
cd Bloret-Launcher-FreeBSD-amd64
./bloret-launcher
# or: python3 Bloret-Launcher.py
```

### B. Clone from Source

```sh
git clone --recursive https://github.com/BloretCrew/Bloret-Launcher.git
cd Bloret-Launcher
python3 Bloret-Launcher.py
```

## Data Directory

Default:

```text
~/.local/share/Bloret-Launcher
```

If `XDG_DATA_HOME` is set, the path is `$XDG_DATA_HOME/Bloret-Launcher`.

## Minecraft and LWJGL

Before launching, confirm:

```sh
ls /usr/local/lib/lwjgl3/liblwjgl.so
ls /usr/local/share/java/classes/lwjgl3/*.jar
```

You can override the paths with environment variables:

```sh
export BLORET_LWJGL_LIB=/path/to/lib
export BLORET_LWJGL_JARS=/path/to/jars
```

Notes:

- The LWJGL version in ports may not exactly match the version pinned by Mojang. Most 1.20+ versions are playable.
- Very old versions (LWJGL2) are not a target for the first release.
- **Do not** force Linux ELF natives on FreeBSD's native OpenJDK.

## Java

The launcher scans `JAVA_HOME`, `PATH`, `/usr/local/openjdk*`, and similar locations.

Automatic Java installation is **supported on Windows only**. On FreeBSD, use:

```sh
sudo pkg install openjdk17
# or
sudo pkg install openjdk21
```

Then select `/usr/local/openjdk17/bin/java` in Settings (use the actual path from the installed package).

## EasyTier Multiplayer

Official releases include FreeBSD assets such as:

```text
easytier-freebsd-13.2-x86_64-v2.6.4.zip
```

Source: <https://github.com/EasyTier/EasyTier/releases>

Place `easytier-core` / `easytier-cli` in the `easytier/` directory next to the launcher.
CI FreeBSD archives usually include them already.

TUN mode may require additional privileges. Live multiplayer can also use the launcher's privilege-free proxy path, as on Windows.

## Auto-Update

FreeBSD does **not** download the Windows `.exe` installer.

When the update API provides `downloads.stable.freebsd` (or an equivalent platform key) as a zip, the launcher downloads and extracts it into the application directory, then restarts.

If the API does not yet provide a FreeBSD asset, the UI will prompt you to update manually from GitHub Releases.

## Feature Limitations (Intentional)

| Feature | FreeBSD behavior |
|------|----------------|
| Global hotkey | Not implemented (Windows only) |
| In-game floating toolbar | Not implemented (Windows only) |
| Automatic Java download/install | Prompts you to use pkg |
| Input-method patches | Linux fcitx path is disabled; relies on system Qt/IME |
| System notifications | `notify-send` (requires libnotify) |

## Troubleshooting

**The game reports that system LWJGL was not found**

```sh
sudo pkg install lwjgl3
```

**The UI does not start / Qt cannot be found**

- Confirm that you are using the ports `py*-pyside6` package and uninstall the pip version of PySide6.
- Install QML-related packages such as `qt6-declarative`.

**Crash due to classpath / native version mismatch**

- Update the `lwjgl3` port.
- Or build LWJGL yourself and point `BLORET_LWJGL_*` at the build output.

## For Packagers

Optional dependency summary:

- Runtime: `python3`, PySide6/Qt6, requests, psutil, Send2Trash, toml, dulwich
- Game: `lwjgl3`, `openjdk17` / `openjdk21`
- Multiplayer: `easytier-core` (upstream FreeBSD release)

Suggested install layout (similar to an Arch `PKGBUILD`):

```text
/usr/local/share/bloret-launcher/   # source and resources
/usr/local/bin/bloret-launcher      # wrapper script: exec python3 ...
```
