#Requires -Version 5.1
<#
.SYNOPSIS
  Sign Windows PE files (exe/dll/msi) with Authenticode for CI or local use.

.DESCRIPTION
  Certificate resolution order:
    1. WINDOWS_CODESIGN_PFX_BASE64 (+ optional WINDOWS_CODESIGN_PASSWORD)
    2. Explicit -PfxPath
    3. Convert sign/root.pvk + sign/root.spc (or root.cer) via pvk2pfx

  Secrets are preferred. The repo currently ships a self-signed PVK under sign/
  for continuity; commercial certs should only live in GitHub Secrets / local PFX.

.PARAMETER Path
  File or directory to sign. Directories recurse for *.exe by default.

.PARAMETER PfxPath
  Optional path to an existing .pfx/.p12.

.PARAMETER Password
  PFX / PVK password. Falls back to env WINDOWS_CODESIGN_PASSWORD.

.PARAMETER Description
  Optional signtool /d description.

.PARAMETER TimestampUrl
  Authenticode timestamp server. Default: DigiCert.

.PARAMETER IncludeDll
  Also sign *.dll under directories.

.PARAMETER SkipIfMissingCert
  Exit 0 with a warning when no cert material is available (useful for forks).
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string[]] $Path,

    [string] $PfxPath = "",

    [string] $Password = "",

    [string] $Description = "Bloret Launcher",

    [string] $TimestampUrl = "http://timestamp.digicert.com",

    [switch] $IncludeDll,

    [switch] $SkipIfMissingCert
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Info([string] $Message) {
    Write-Host "[codesign] $Message"
}

function Write-WarnLine([string] $Message) {
    Write-Host "[codesign] WARNING: $Message" -ForegroundColor Yellow
}

function Find-SdkTool([string] $Name) {
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    $roots = @(
        "${env:ProgramFiles(x86)}\Windows Kits\10\bin",
        "${env:ProgramFiles}\Windows Kits\10\bin",
        "${env:ProgramFiles(x86)}\Microsoft SDKs\Windows"
    ) | Where-Object { $_ -and (Test-Path $_) }

    foreach ($root in $roots) {
        $hits = Get-ChildItem -Path $root -Recurse -Filter $Name -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -match '\\x64\\' -or $_.FullName -match '\\x86\\' } |
            Sort-Object FullName -Descending
        if ($hits) {
            $x64 = $hits | Where-Object { $_.FullName -match '\\x64\\' } | Select-Object -First 1
            if ($x64) { return $x64.FullName }
            return $hits[0].FullName
        }
    }

    # Bundled legacy tool folder (local / optional checkout)
    $bundled = @(
        Join-Path $PSScriptRoot "..\..\代码签名证书制作工具\$Name"
        Join-Path (Get-Location) "代码签名证书制作工具\$Name"
    )
    foreach ($candidate in $bundled) {
        if (Test-Path $candidate) {
            return (Resolve-Path $candidate).Path
        }
    }

    return $null
}

function Get-RepoRoot {
    if ($env:GITHUB_WORKSPACE -and (Test-Path $env:GITHUB_WORKSPACE)) {
        return (Resolve-Path $env:GITHUB_WORKSPACE).Path
    }
    # .github/scripts -> repo root
    return (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

function New-TempDir {
    $dir = Join-Path ([System.IO.Path]::GetTempPath()) ("bloret-codesign-" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    return $dir
}

function ConvertFrom-Base64File([string] $Base64, [string] $Destination) {
    $bytes = [Convert]::FromBase64String(($Base64 -replace '\s', ''))
    [System.IO.File]::WriteAllBytes($Destination, $bytes)
}

function Resolve-SigningPfx {
    param(
        [string] $ExplicitPfx,
        [string] $PlainPassword,
        [string] $WorkDir
    )

    $resolvedPassword = $PlainPassword
    if (-not $resolvedPassword -and $env:WINDOWS_CODESIGN_PASSWORD) {
        $resolvedPassword = $env:WINDOWS_CODESIGN_PASSWORD
    }

    if ($ExplicitPfx -and (Test-Path $ExplicitPfx)) {
        return @{
            Path     = (Resolve-Path $ExplicitPfx).Path
            Password = $resolvedPassword
            Source   = "PfxPath"
        }
    }

    if ($env:WINDOWS_CODESIGN_PFX_BASE64) {
        $pfxOut = Join-Path $WorkDir "codesign.pfx"
        ConvertFrom-Base64File -Base64 $env:WINDOWS_CODESIGN_PFX_BASE64 -Destination $pfxOut
        Write-Info "Loaded PFX from WINDOWS_CODESIGN_PFX_BASE64"
        return @{
            Path     = $pfxOut
            Password = $resolvedPassword
            Source   = "Secret"
        }
    }

    $repoRoot = Get-RepoRoot
    $pvk = Join-Path $repoRoot "sign\root.pvk"
    $spc = Join-Path $repoRoot "sign\root.spc"
    $cer = Join-Path $repoRoot "sign\root.cer"

    if (-not (Test-Path $pvk)) {
        return $null
    }

    $pvk2pfx = Find-SdkTool "pvk2pfx.exe"
    if (-not $pvk2pfx) {
        throw "pvk2pfx.exe not found. Install Windows SDK or place 代码签名证书制作工具 in the repo."
    }

    $pfxOut = Join-Path $WorkDir "root-from-pvk.pfx"
    $spcArg = $null
    if (Test-Path $spc) {
        $spcArg = $spc
    }
    elseif (Test-Path $cer) {
        # cert2spc can build SPC from CER when SPC is missing
        $cert2spc = Find-SdkTool "cert2spc.exe"
        if (-not $cert2spc) {
            throw "root.spc missing and cert2spc.exe not found"
        }
        $spcArg = Join-Path $WorkDir "root.spc"
        & $cert2spc $cer $spcArg
        if ($LASTEXITCODE -ne 0) {
            throw "cert2spc failed with exit code $LASTEXITCODE"
        }
    }
    else {
        throw "Neither sign/root.spc nor sign/root.cer found next to root.pvk"
    }

    Write-Info "Converting PVK/SPC -> PFX via $pvk2pfx"
    $pvkArgs = @("-pvk", $pvk, "-spc", $spcArg, "-pfx", $pfxOut)
    if ($resolvedPassword) {
        $pvkArgs += @("-pi", $resolvedPassword, "-po", $resolvedPassword)
    }

    & $pvk2pfx @pvkArgs
    if ($LASTEXITCODE -ne 0) {
        # Retry with empty password (common for self-signed toolkits)
        Write-WarnLine "pvk2pfx failed (exit $LASTEXITCODE); retrying with empty password"
        $pvkArgs = @("-pvk", $pvk, "-spc", $spcArg, "-pfx", $pfxOut, "-pi", "", "-po", "")
        & $pvk2pfx @pvkArgs
        if ($LASTEXITCODE -ne 0) {
            throw "pvk2pfx failed with exit code $LASTEXITCODE"
        }
        $resolvedPassword = ""
    }

    return @{
        Path     = $pfxOut
        Password = $resolvedPassword
        Source   = "RepoPvk"
    }
}

function Get-Targets([string[]] $Inputs, [switch] $Dlls) {
    $files = New-Object System.Collections.Generic.List[string]
    foreach ($item in $Inputs) {
        if (-not $item) { continue }
        if (-not (Test-Path $item)) {
            Write-WarnLine "Path not found, skip: $item"
            continue
        }
        $resolved = (Resolve-Path $item).Path
        if (Test-Path $resolved -PathType Container) {
            $patterns = @("*.exe")
            if ($Dlls) { $patterns += "*.dll" }
            foreach ($pat in $patterns) {
                Get-ChildItem -Path $resolved -Recurse -File -Filter $pat |
                    ForEach-Object { $files.Add($_.FullName) }
            }
        }
        else {
            $files.Add($resolved)
        }
    }
    return $files | Select-Object -Unique
}

function Invoke-SignFile {
    param(
        [string] $SignTool,
        [string] $File,
        [string] $Pfx,
        [string] $PfxPassword,
        [string] $Desc,
        [string] $TsUrl
    )

    $common = @(
        "sign",
        "/f", $Pfx,
        "/fd", "sha256",
        "/td", "sha256",
        "/tr", $TsUrl,
        "/d", $Desc
    )
    if ($null -ne $PfxPassword -and $PfxPassword -ne "") {
        $common += @("/p", $PfxPassword)
    }
    # Empty password still needs /p "" for some PFX exports
    elseif ($null -ne $PfxPassword) {
        $common += @("/p", "")
    }

    Write-Info "Signing $File"
    & $SignTool @common $File
    if ($LASTEXITCODE -ne 0) {
        throw "signtool sign failed for $File (exit $LASTEXITCODE)"
    }

    & $SignTool "verify" "/pa" "/v" $File
    if ($LASTEXITCODE -ne 0) {
        # Self-signed certs often fail strict /pa trust checks on clean runners.
        Write-WarnLine "signtool verify /pa reported issues (common for self-signed). Checking signature presence..."
        & $SignTool "verify" "/v" $File
        if ($LASTEXITCODE -ne 0) {
            throw "signtool verify failed for $File (exit $LASTEXITCODE)"
        }
    }
}

$workDir = $null
try {
    $signTool = Find-SdkTool "signtool.exe"
    if (-not $signTool) {
        throw "signtool.exe not found. Use windows-latest or install Windows SDK 10+."
    }
    Write-Info "Using signtool: $signTool"

    $workDir = New-TempDir
    $cert = Resolve-SigningPfx -ExplicitPfx $PfxPath -PlainPassword $Password -WorkDir $workDir
    if (-not $cert) {
        $msg = "No signing certificate found (set WINDOWS_CODESIGN_PFX_BASE64 or provide sign/root.pvk)."
        if ($SkipIfMissingCert) {
            Write-WarnLine $msg
            Write-WarnLine "SkipIfMissingCert set — leaving binaries unsigned."
            exit 0
        }
        throw $msg
    }
    Write-Info "Certificate source: $($cert.Source)"

    $targets = @(Get-Targets -Inputs $Path -Dlls:$IncludeDll)
    if ($targets.Count -eq 0) {
        Write-WarnLine "No files to sign."
        exit 0
    }

    Write-Info ("Files to sign: {0}" -f $targets.Count)
    foreach ($file in $targets) {
        Invoke-SignFile `
            -SignTool $signTool `
            -File $file `
            -Pfx $cert.Path `
            -PfxPassword $cert.Password `
            -Desc $Description `
            -TsUrl $TimestampUrl
    }

    Write-Info "Done."
}
finally {
    if ($workDir -and (Test-Path $workDir)) {
        Remove-Item -Recurse -Force $workDir -ErrorAction SilentlyContinue
    }
}
