<img src="bloret.ico" width = "200" height = "200" alt="Bloret" align=left />
<div align="center">
  <h1>
    Bloret Launcher
  </h1>
  <p>
   Be creative, be simple. Your Personal Innovative Open Source AI Minecraft Launcher. Relax, it's Bloret Launcher.
  </p>
</div>

<div align="center">

[![Build](https://github.com/BloretCrew/Bloret-Launcher/actions/workflows/build.yml/badge.svg)](https://github.com/BloretCrew/Bloret-Launcher/actions/workflows/build.yml)
[![Build - Nuitka](https://github.com/BloretCrew/Bloret-Launcher/actions/workflows/Nuitka-Build.yml/badge.svg)](https://github.com/BloretCrew/Bloret-Launcher/actions/workflows/Nuitka-Build.yml)
[![Crowdin translation progress](https://badges.crowdin.net/Bloret-Launcher/localized.svg)](https://launcher.bloret.net/go/translate)
[![Discussions](https://img.shields.io/github/discussions/BloretCrew/Bloret-Launcher?style=social&label=Discussions)](https://github.com/BloretCrew/Bloret-Launcher/discussions)
![Repository size](https://img.shields.io/github/repo-size/BloretCrew/Bloret-Launcher?style=social&label=Repository%20size)
![Stars](https://img.shields.io/github/stars/BloretCrew/Bloret-Launcher?style=social&label=Stars)
[![wakatime](https://wakatime.com/badge/user/38dee536-8d34-42c1-925d-43b79e143e83/project/4f5bb74a-2298-419e-8ba8-dee40e51d08b.svg)](https://wakatime.com/badge/user/38dee536-8d34-42c1-925d-43b79e143e83/project/4f5bb74a-2298-419e-8ba8-dee40e51d08b)

[![Downloads](https://img.shields.io/github/downloads/BloretCrew/Bloret-Launcher/total?style=social&label=Downloads)](https://github.com/BloretCrew/Bloret-Launcher/releases)
![Latest stable release](https://img.shields.io/github/v/release/BloretCrew/Bloret-Launcher?label=Latest%20stable%20release)
![Latest release (including pre-releases)](https://img.shields.io/github/v/release/BloretCrew/Bloret-Launcher?include_prereleases&style=social&label=Latest%20release)
![WinGet package version](https://img.shields.io/winget/v/Bloret.Launcher?label=WinGet%20version)
![WinGet package name](https://img.shields.io/badge/WinGet_package-Bloret.Launcher-blue&style=social)

</div>


![Home](https://github.com/BloretCrew/Bloret-Launcher/blob/Windows/img/New-Images/cropped/Home-Long.PNG?raw=true)


## Multiplayer Guide
![](https://raw.githubusercontent.com/BloretCrew/Bloret-Launcher/refs/heads/Windows/ui/icon/OnlineClient.gif)<br>
Then enter the port you received into Bloret Launcher. You will get an address that lets your friends join your world as if they were joining a server.

> [!NOTE]
> You can open Bloret Launcher in three ways:
> 1. Download `Bloret-Launcher-Setup.exe` and run the installer.
> 2. Download `Bloret-Launcher-Windows.zip`, extract it, and open `Bloret-Launcher.exe`.
> 3. Download the source code archive `Source code (zip)`, extract it, and run `python Bloret-Launcher.py` in that directory.
>    (Install Python before step 3 with `winget install python`.)

> [!WARNING]
> Bloret Launcher is code-signed and should generally not be blocked.
> Windows Security may still flag this software. It is not a virus.
> Bloret Launcher is open source, so you can inspect the source code.
> Follow the steps below to open the app.
> <details>
> <summary>Click here to expand and view the instructions (2 images)</summary>
>
> ![](https://raw.githubusercontent.com/BloretCrew/Bloret-Launcher/refs/heads/Windows/img/Windows1.jpg)
> ![](https://raw.githubusercontent.com/BloretCrew/Bloret-Launcher/refs/heads/Windows/img/Windows2.jpg)
>
> </details>

## Added at the development team's request 👇
<details>

<summary>Click here to expand and view the promotional image (1 image)</summary>

![](https://raw.githubusercontent.com/BloretCrew/Bloret-Launcher/refs/heads/Windows/img/if-not-use-jiedi-will.jpg)

</details>

## Platform Support

| Platform | Notes |
|------|------|
| Windows | Full support (installer / zip / WinGet) |
| Linux | Source / AppImage / Arch `PKGBUILD` |
| macOS | CI artifacts (Intel / ARM) |
| **FreeBSD** | **Runs from source on amd64**; uses system `lwjgl3` to launch the game; CI artifact `Bloret-Launcher-FreeBSD-amd64` |

See **[docs/FreeBSD.md](docs/FreeBSD.md)** for FreeBSD installation and Minecraft instructions.

## Features and Roadmap

- [x] Tray icon and tray menu
- [x] Custom launch
- [x] Download Minecraft
- [x] Launch Minecraft
- [x] Minecraft data lookup
- [x] Logs
- [x] Light and dark themes
- [x] Microsoft account login
- [x] Offline login
- [x] Bloret PassPort login
- [x] Auto-update
- [x] Screenshots
- [x] EasyTier multiplayer
- [x] Bloriko
- [x] Bloriko with Modrinth
- [x] Fresh Minecraft installation
- [x] Fresh Minecraft with Fabric installation
- [x] New launch process
- [x] Version management
- [x] Version selection
- [x] Server management
- [x] Mod management
- [x] Resource pack management
- [x] Minecraft process manager
- [x] Terminate Minecraft processes
- [x] Bloret Server server information
- [x] Deep integration of Microsoft/offline login with Bloret PassPort
- [x] Bloret PassPort auxiliary verification
- [x] Multiple Minecraft accounts #38
- [x] Floating toolbar
- [x] Config migration to AppData
- [x] New installer
- [x] Bloriko DeepThink
- [x] NewIcon
- [x] FreeBSD support (system LWJGL / EasyTier / CI artifacts)
- [x] And more...

## Screenshots
<details>

<summary>Click here to expand and view the screenshots (11 images)</summary>

#### Main UI
![Home](https://github.com/BloretCrew/Bloret-Launcher/blob/Windows/img/New-Images/cropped/Home-Long.PNG?raw=true)
#### Download
![Download](https://github.com/BloretCrew/Bloret-Launcher/blob/Windows/img/New-Images/cropped/Download.jpg?raw=true)
#### Tools
![tools](https://github.com/BloretCrew/Bloret-Launcher/blob/Windows/img/New-Images/cropped/Tools.jpg?raw=true)
#### PassPort
![passport](https://github.com/BloretCrew/Bloret-Launcher/blob/Windows/img/New-Images/cropped/PassPort.jpg?raw=true)
#### Settings
![settings](https://github.com/BloretCrew/Bloret-Launcher/blob/Windows/img/New-Images/cropped/Settings.jpg?raw=true)
#### About
![info](https://github.com/BloretCrew/Bloret-Launcher/blob/Windows/img/New-Images/cropped/About.jpg?raw=true)
#### Modrinth
![Modrinth](https://github.com/BloretCrew/Bloret-Launcher/blob/Windows/img/New-Images/cropped/Mods-toast.jpg?raw=true)
![Modrinth](https://github.com/BloretCrew/Bloret-Launcher/blob/Windows/img/New-Images/cropped/Mods-Dialog.jpg?raw=true)
#### Multiplayer
![Client](https://github.com/BloretCrew/Bloret-Launcher/blob/Windows/img/New-Images/cropped/Client.jpg?raw=true)
![Client-Easytier-Server](https://github.com/BloretCrew/Bloret-Launcher/blob/Windows/img/New-Images/cropped/Client-Easytier-Server.jpg?raw=true)
![Client-Easytier-Client](https://github.com/BloretCrew/Bloret-Launcher/blob/Windows/img/New-Images/cropped/Client-Easytier-Client.jpg?raw=true)

</details>

## Contributors
![contributors](http://contrib.nn.ci/api?repo=BloretCrew/Bloret-Launcher)

![Alt](https://repobeats.axiom.co/api/embed/a5638ffaed2d2ba6776999fafc10b5e1513c53a9.svg "Repobeats analytics image")

## Acknowledgements

- [RinUI](https://github.com/Detritalw/Rin-UI)

**RinUI is the core component library of Bloret Launcher.**

- [SF Symbols](https://developer.apple.com/cn/sf-symbols/)
<details>

<summary><a href="https://github.com/MrShieh-X/console-minecraft-launcher">Console Minecraft Launcher</a></summary>

**Bloret Launcher has removed CMCL. CMCL was once used to implement some modules, and we thank CMCL for that.**

> This software has obtained permission from the CMCL author. Please do not ask about CMCL copyright issues in the same way as [Non-compliance with the Console Minecraft Launcher (CMCL) usage agreement #12](https://github.com/BloretCrew/Bloret-Launcher/issues/12).
> ![CMCLLICENSE](https://raw.githubusercontent.com/BloretCrew/Bloret-Launcher/refs/heads/Windows/img/CMCLLICENSE.png)

</details>

<details>

<summary><a href="https://github.com/Class-Widgets">Class Widgets</a></summary>

Why we thank [Class Widgets](https://github.com/Class-Widgets):
[Class Widgets](https://github.com/Class-Widgets) deserves our thanks for the following:
 - It provided ideas for Bloret Launcher's UI.
 - Bloret Launcher has been added to the Class Widgets plugin marketplace.
 - [@RinLit](https://github.com/RinLit-233-shiroko) provided coding guidance for this project.
 - [[not cw] Help: why does it crash? #392](https://github.com/orgs/Class-Widgets/discussions/392)
 - [How to make a dropdown selector? #338](https://github.com/orgs/Class-Widgets/discussions/338)
</details>

## Star History

<a href="https://www.star-history.com/?repos=BloretCrew%2FBloret-Launcher&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=BloretCrew/Bloret-Launcher&type=date&theme=dark&legend=top-left&sealed_token=I-RgMFUYDE01MKNYihURki9gORl3bk-X3FElwLPRukS2a238SDOdy-l-3IAFmmXMVHMb5GVTOKVE5Bu6rHXjXBCCXJUgck8t59CdjfaHchtvpWsvwy-vJfHoAAa7gWFHmhMqQN4uKxN4iBZ7Y5J0tkKLNyeAcmuAKYkkjXqXwLPVqY6BrborM9hKmnna" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=BloretCrew/Bloret-Launcher&type=date&legend=top-left&sealed_token=I-RgMFUYDE01MKNYihURki9gORl3bk-X3FElwLPRukS2a238SDOdy-l-3IAFmmXMVHMb5GVTOKVE5Bu6rHXjXBCCXJUgck8t59CdjfaHchtvpWsvwy-vJfHoAAa7gWFHmhMqQN4uKxN4iBZ7Y5J0tkKLNyeAcmuAKYkkjXqXwLPVqY6BrborM9hKmnna" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=BloretCrew/Bloret-Launcher&type=date&legend=top-left&sealed_token=I-RgMFUYDE01MKNYihURki9gORl3bk-X3FElwLPRukS2a238SDOdy-l-3IAFmmXMVHMb5GVTOKVE5Bu6rHXjXBCCXJUgck8t59CdjfaHchtvpWsvwy-vJfHoAAa7gWFHmhMqQN4uKxN4iBZ7Y5J0tkKLNyeAcmuAKYkkjXqXwLPVqY6BrborM9hKmnna" />
 </picture>
</a>

## Related Links
[Bloret QQ Group](https://qm.qq.com/q/clE5KHaVDG)
[Bloret Launcher Website](https://launcher.bloret.net/)
[Bloret PassPort](https://passport.bloret.net/)
[Bloret Software Community (599419775)](https://qm.qq.com/q/Z2QxjXejCy)
