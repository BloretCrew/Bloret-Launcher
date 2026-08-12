# Windows 代码签名（GitHub Actions）

发布构建会在 CI 中自动对 Windows 产物做 Authenticode 签名，替代本地「代码签名证书制作工具」手工签名。

## 会签名哪些文件

| 流水线 | 文件 |
|--------|------|
| `Nuitka-Build.yml` | `Bloret-Launcher.exe`、`Bloret-Launcher-Setup.exe` |
| `build.yml`（PyInstaller） | 同上 |

主程序在打 zip / 做 Inno Setup **之前**签名；安装包在 Inno Setup 生成后单独签名。

## 证书从哪里来（优先级）

1. **推荐**：GitHub Secrets 中的 PFX  
   - `WINDOWS_CODESIGN_PFX_BASE64`：`.pfx` 的 base64  
   - `WINDOWS_CODESIGN_PASSWORD`：PFX 密码（无密码可省略）
2. 工作流参数 / 本地传入的 `-PfxPath`
3. 回退：仓库内 `sign/root.pvk` + `sign/root.spc`（经 `pvk2pfx` 转成临时 PFX）

脚本：`.github/scripts/windows-codesign.ps1`  
本地导出 PFX：`scripts/export-codesign-pfx.ps1`

## 配置 Secrets（推荐）

在 Windows 本机（有 Windows SDK 或「代码签名证书制作工具」）执行：

```powershell
cd <repo>
.\scripts\export-codesign-pfx.ps1
```

脚本会生成 `sign/bloret-codesign.pfx`（已 gitignore），并打印 base64。

然后到仓库 **Settings → Secrets and variables → Actions** 添加：

| Secret | 值 |
|--------|----|
| `WINDOWS_CODESIGN_PFX_BASE64` | 打印出的整段 base64 |
| `WINDOWS_CODESIGN_PASSWORD` | 导出时使用的密码（若为空可跳过） |

有商业代码签名证书时，直接把购买的 `.pfx` 转 base64 写入上述 Secret 即可，不必再用自签 PVK。

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("your.pfx")) | Set-Clipboard
```

## 本地手动签名

```powershell
$env:WINDOWS_CODESIGN_PFX_BASE64 = "..."   # 或使用 -PfxPath
$env:WINDOWS_CODESIGN_PASSWORD = "..."

.\.github\scripts\windows-codesign.ps1 -Path .\Bloret-Launcher.exe
.\.github\scripts\windows-codesign.ps1 -Path .\output\Bloret-Launcher-Setup.exe -Description "Bloret Launcher Setup"
```

## 效果说明（请读）

当前仓库自带的是 **自签名证书**（`CN=Bloret`，MD5/RSA-1024 历史证书）。CI 自动签名后：

- 文件属性里可以看到「数字签名」
- **不能** 像 EV/OV 商业证书那样消除 SmartScreen「未知发布者」
- 要明显改善拦截，需要向 CA 购买 **OV/EV Code Signing**，把新 PFX 放进 Secrets，无需改工作流逻辑

## 安全建议

- **不要** 把 `.pfx` / 私钥密码提交进 Git（已忽略 `*.pfx`）
- 仓库里已有 `sign/root.pvk` 属于历史做法；长期应只保留 Secrets 中的证书，并考虑轮换密钥
- Fork 无 Secret 且删掉 `sign/` 时，步骤带 `-SkipIfMissingCert`，会跳过签名而不是失败
