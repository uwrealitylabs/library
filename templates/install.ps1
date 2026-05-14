<#
.SYNOPSIS
    Installs KiCad project templates from this repo into the current user's KiCad template directory.

.DESCRIPTION
    Detects the highest installed KiCad version under %APPDATA%\kicad, copies each template
    folder in this directory (siblings of install.ps1) into %USERPROFILE%\Documents\KiCad\<ver>\template\,
    and reports what was installed.

.PARAMETER Force
    Overwrite existing templates with the same name in the destination.

.PARAMETER Symlink
    Create directory junctions instead of copying. Edits to this repo will show up live in KiCad.
    Recommended for the template author; use plain copy for distribution.

.PARAMETER KicadVersion
    Pin a specific KiCad major version (e.g. "10.0"). Auto-detected if omitted.

.EXAMPLE
    .\install.ps1
    .\install.ps1 -Force
    .\install.ps1 -Symlink
    .\install.ps1 -KicadVersion 10.0 -Force
#>
[CmdletBinding()]
param(
    [switch]$Force,
    [switch]$Symlink,
    [string]$KicadVersion
)

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

# --- Detect KiCad version ---------------------------------------------------
if (-not $KicadVersion) {
    $cfgRoot = Join-Path $env:APPDATA 'kicad'
    if (-not (Test-Path $cfgRoot)) {
        throw "KiCad config dir not found at $cfgRoot. Is KiCad installed and has it been launched at least once?"
    }
    $versions = Get-ChildItem -Directory $cfgRoot |
        Where-Object { $_.Name -match '^\d+\.\d+$' } |
        Sort-Object { [version]$_.Name } -Descending
    if (-not $versions) { throw "No KiCad version directories found in $cfgRoot." }
    $KicadVersion = $versions[0].Name
    Write-Host "Detected KiCad version: $KicadVersion"
}

# --- Resolve template destination ------------------------------------------
$destRoot = Join-Path $env:USERPROFILE "Documents\KiCad\$KicadVersion\template"
if (-not (Test-Path $destRoot)) {
    Write-Host "Creating $destRoot"
    New-Item -ItemType Directory -Force -Path $destRoot | Out-Null
}

# --- Find templates to install ---------------------------------------------
# A template = any subdirectory of $here that contains a .kicad_pro file.
$templates = Get-ChildItem -Directory $here | Where-Object {
    Get-ChildItem -Path $_.FullName -Filter '*.kicad_pro' -File -ErrorAction SilentlyContinue
}

if (-not $templates) {
    throw "No templates found in $here. (Expected subdirectories containing a *.kicad_pro file.)"
}

Write-Host "Found $($templates.Count) template(s) to install."

# --- Install each template -------------------------------------------------
foreach ($tpl in $templates) {
    $dest = Join-Path $destRoot $tpl.Name
    if (Test-Path $dest) {
        if (-not $Force) {
            Write-Warning "Skipping '$($tpl.Name)' — already exists at $dest. Use -Force to overwrite."
            continue
        }
        Write-Host "Removing existing $dest"
        # If existing dest is a junction, Remove-Item -Recurse can be dangerous —
        # use cmd /c rmdir which removes the junction without following it.
        $item = Get-Item $dest -Force
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            & cmd /c rmdir """$dest""" | Out-Null
        } else {
            Remove-Item -Recurse -Force $dest
        }
    }

    if ($Symlink) {
        Write-Host "Linking '$($tpl.Name)' -> $($tpl.FullName)"
        New-Item -ItemType Junction -Path $dest -Target $tpl.FullName | Out-Null
    } else {
        Write-Host "Copying '$($tpl.Name)' -> $dest"
        Copy-Item -Recurse -Path $tpl.FullName -Destination $dest
    }
}

Write-Host "`nDone. Installed templates:"
Get-ChildItem -Directory $destRoot | ForEach-Object { Write-Host "  - $($_.Name)" }
Write-Host "`nIn KiCad: File -> New Project from Template -> User Templates"
