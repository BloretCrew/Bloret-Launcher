#Requires -Version 5.1
<#
.SYNOPSIS
  Convert sign/root.pvk (+ spc/cer) to a PFX and print base64 for GitHub Secrets.

.EXAMPLE
  # On a Windows machine with Windows SDK (or 代码签名证书制作工具):
  .\scripts\export-codesign-pfx.ps1

  Then add repository secrets:
    WINDOWS_CODESIGN_PFX_BASE64  = <printed base64>
    WINDOWS_CODESIGN_PASSWORD    = <password you chose, optional if empty>
#>
[CmdletBinding()]
param(
    [string] $PvkPath = "",
    [string] $SpcPath = "",
    [string] $OutPfx = "sign\bloret-codesign.pfx",
    [string] $Password = "",
    [switch] $NoPrintBase64
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
if (-not $PvkPath) { $PvkPath = Join-Path $repoRoot "sign\root.pvk" }
if (-not $SpcPath) {
    $candidateSpc = Join-Path $repoRoot "sign\root.spc"
    if (Test-Path $candidateSpc) {
        $SpcPath = $candidateSpc
    }
}

if (-not (Test-Path $PvkPath)) {
    throw "PVK not found: $PvkPath"
}

function Find-Tool([string] $Name) {
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $roots = @(
        "${env:ProgramFiles(x86)}\Windows Kits\10\bin",
        "${env:ProgramFiles}\Windows Kits\10\bin",
        (Join-Path $repoRoot "代码签名证书制作工具")
    ) | Where-Object { $_ -and (Test-Path $_) }
    foreach ($root in $roots) {
        $hit = Get-ChildItem -Path $root -Recurse -Filter $Name -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($hit) { return $hit.FullName }
    }
    return $null
}

$pvk2pfx = Find-Tool "pvk2pfx.exe"
if (-not $pvk2pfx) {
    throw "pvk2pfx.exe not found. Install Windows SDK or keep 代码签名证书制作工具 next to the repo."
}

if (-not $SpcPath -or -not (Test-Path $SpcPath)) {
    $cer = Join-Path $repoRoot "sign\root.cer"
    $cert2spc = Find-Tool "cert2spc.exe"
    if (-not (Test-Path $cer) -or -not $cert2spc) {
        throw "Need sign/root.spc or (sign/root.cer + cert2spc.exe)"
    }
    $SpcPath = Join-Path $repoRoot "sign\root.generated.spc"
    & $cert2spc $cer $SpcPath
    if ($LASTEXITCODE -ne 0) { throw "cert2spc failed: $LASTEXITCODE" }
}

$OutPfxFull = if ([System.IO.Path]::IsPathRooted($OutPfx)) { $OutPfx } else { Join-Path $repoRoot $OutPfx }
New-Item -ItemType Directory -Force -Path (Split-Path $OutPfxFull -Parent) | Out-Null
if (Test-Path $OutPfxFull) { Remove-Item $OutPfxFull -Force }

$args = @("-pvk", $PvkPath, "-spc", $SpcPath, "-pfx", $OutPfxFull)
if ($Password -ne "") {
    $args += @("-pi", $Password, "-po", $Password)
}
else {
    $args += @("-pi", "", "-po", "")
}

Write-Host "Running: $pvk2pfx $($args -join ' ')"
& $pvk2pfx @args
if ($LASTEXITCODE -ne 0) {
    throw "pvk2pfx failed: $LASTEXITCODE"
}

Write-Host "PFX written: $OutPfxFull"
Write-Host "Do NOT commit this file. It is gitignored."

if (-not $NoPrintBase64) {
    $b64 = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($OutPfxFull))
    Write-Host ""
    Write-Host "=== Paste as GitHub secret WINDOWS_CODESIGN_PFX_BASE64 ==="
    Write-Host $b64
    Write-Host "=== end ==="
    if ($Password -ne "") {
        Write-Host "Also set secret WINDOWS_CODESIGN_PASSWORD to your PFX password."
    }
    else {
        Write-Host "PFX password is empty; WINDOWS_CODESIGN_PASSWORD may be left unset."
    }
}
