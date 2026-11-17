# Create (or refresh) the "Study Desk" desktop shortcut on Windows.
#
#   powershell -ExecutionPolicy Bypass -File make_shortcut.ps1 [-Folder <study folder>] [-Port <n>]
#
# -Folder is the folder you study in (default: the folder this is run from).
# Every other path is worked out from where this script sits. If the plugin is
# updated and its folder moves, run this again.
param(
    [string]$Folder = (Get-Location).Path,
    [int]$Port = 0
)
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$app = Split-Path -Parent $here
$Folder = (Resolve-Path -LiteralPath $Folder).Path
$desktop = [Environment]::GetFolderPath('Desktop')
$link = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $desktop 'Study Desk.lnk'))
$link.TargetPath = Join-Path $env:WINDIR 'System32\wscript.exe'
$arguments = "`"$(Join-Path $here 'launch.vbs')`" `"$Folder`""
if ($Port -gt 0) { $arguments += " $Port" }
$link.Arguments = $arguments
$link.WorkingDirectory = $Folder
$link.IconLocation = Join-Path $app 'static\icon.ico'
$link.Description = 'Open Study Desk'
$link.Save()
Join-Path $desktop 'Study Desk.lnk'
