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

    # Optional local toolkit folder (name may be Chinese on disk)
    $repoRoot = Get-RepoRoot
    $bundledDirs = Get-ChildItem -Path $repoRoot -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like '*signtool*' -or $_.Name -match 'code.?sign' -or (Test-Path (Join-Path $_.FullName 'signtool.exe')) }
    foreach ($dir in $bundledDirs) {
        $candidate = Join-Path $dir.FullName $Name
        if (Test-Path $candidate) {
            return (Resolve-Path $candidate).Path
        }
    }

    $legacyName = Join-Path $repoRoot ([string]([char]0x4EE3) + [string]([char]0x7801) + [string]([char]0x7B7E) + [string]([char]0x540D) + [string]([char]0x8BC1) + [string]([char]0x4E66) + [string]([char]0x5236) + [string]([char]0x4F5C) + [string]([char]0x5DE5) + [string]([char]0x5177))
    $legacy = Join-Path $legacyName $Name
    if (Test-Path $legacy) {
        return (Resolve-Path $legacy).Path
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
    $clean = ($Base64 -replace '\s', '')
    $bytes = [Convert]::FromBase64String($clean)
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
        try {
            ConvertFrom-Base64File -Base64 $env:WINDOWS_CODESIGN_PFX_BASE64 -Destination $pfxOut
        }
        catch {
            Write-WarnLine "Failed to decode WINDOWS_CODESIGN_PFX_BASE64: $($_.Exception.Message)"
            Write-WarnLine "Will try repository sign/root.pvk fallback if available."
            $pfxOut = $null
        }
        if ($pfxOut -and (Test-Path $pfxOut) -and ((Get-Item $pfxOut).Length -ge 64)) {
            # Probe whether .NET can open the PFX with the given password
            $probeOk = $false
            try {
                $flags = [System.Security.Cryptography.X509Certificates.X509KeyStorageFlags]::Exportable -bor `
                         [System.Security.Cryptography.X509Certificates.X509KeyStorageFlags]::EphemeralKeySet
                if ($resolvedPassword) {
                    $null = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($pfxOut, $resolvedPassword, $flags)
                }
                else {
                    $null = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($pfxOut, "", $flags)
                }
                $probeOk = $true
            }
            catch {
                try {
                    # Older runtimes may not support EphemeralKeySet
                    $flags2 = [System.Security.Cryptography.X509Certificates.X509KeyStorageFlags]::Exportable -bor `
                              [System.Security.Cryptography.X509Certificates.X509KeyStorageFlags]::MachineKeySet
                    if ($resolvedPassword) {
                        $null = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($pfxOut, $resolvedPassword, $flags2)
                    }
                    else {
                        $null = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($pfxOut, "", $flags2)
                    }
                    $probeOk = $true
                }
                catch {
                    Write-WarnLine "PFX from secret could not be opened: $($_.Exception.Message)"
                    Write-WarnLine "Check WINDOWS_CODESIGN_PASSWORD or re-export the PFX. Falling back to sign/root.pvk if present."
                }
            }
            if ($probeOk) {
                Write-Info "Loaded PFX from WINDOWS_CODESIGN_PFX_BASE64 ($((Get-Item $pfxOut).Length) bytes)"
                return @{
                    Path     = $pfxOut
                    Password = $resolvedPassword
                    Source   = "Secret"
                }
            }
        }
        else {
            Write-WarnLine "WINDOWS_CODESIGN_PFX_BASE64 missing or too small after decode; trying PVK fallback."
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
        throw "pvk2pfx.exe not found. Install Windows SDK Signing Tools."
    }

    $pfxOut = Join-Path $WorkDir "root-from-pvk.pfx"
    $spcArg = $null
    if (Test-Path $spc) {
        $spcArg = $spc
    }
    elseif (Test-Path $cer) {
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
    elseif ($null -ne $PfxPassword) {
        # Empty password: some PFX exports still need /p ""
        $common += @("/p", "")
    }

    Write-Info "Signing $File"
    & $SignTool @common $File
    if ($LASTEXITCODE -ne 0) {
        throw "signtool sign failed for $File (exit $LASTEXITCODE)"
    }

    # Do not use "signtool verify /pa" as a hard failure for self-signed certs:
    # CI runners do not trust CN=Bloret, so /pa exits 1 even when the PE is signed.
    # Confirm Authenticode blob presence via Get-AuthenticodeSignature instead.
    $sig = Get-AuthenticodeSignature -FilePath $File
    $status = [string]$sig.Status
    $subject = $null
    if ($sig.SignerCertificate) {
        $subject = $sig.SignerCertificate.Subject
    }
    Write-Info ("Authenticode status={0}; subject={1}" -f $status, $subject)

    if ($status -eq "NotSigned" -or -not $sig.SignerCertificate) {
        throw "File appears unsigned after signtool reported success: $File (status=$status)"
    }

    # Valid = trusted chain. UnknownError / NotTrusted / HashMismatch etc. for self-signed
    # still means a signature block exists; only NotSigned is fatal above.
    if ($status -ne "Valid") {
        Write-WarnLine ("Signature present but not fully trusted on this machine (status={0}). This is expected for self-signed certs." -f $status)
    }

    # Optional verbose dump for logs (non-fatal)
    & $SignTool "verify" "/pa" "/v" $File | Out-Host
    if ($LASTEXITCODE -ne 0) {
        Write-WarnLine ("signtool verify /pa exit {0} (ignored for self-signed / untrusted roots)" -f $LASTEXITCODE)
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
            Write-WarnLine "SkipIfMissingCert set - leaving binaries unsigned."
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
