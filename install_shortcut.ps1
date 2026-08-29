# 把 Predoc Watcher 装进「开始」菜单，这样能在应用列表里找到、也能搜到。
# Add Predoc Watcher to the Start menu so it shows up in the app list and search.
#
#   .\install_shortcut.ps1              开始菜单
#   .\install_shortcut.ps1 -Desktop     顺带放一个桌面快捷方式
#   .\install_shortcut.ps1 -Startup     顺带设为开机自启（缩到托盘启动）
#   .\install_shortcut.ps1 -Uninstall   全部移除
#
# 快捷方式直接指向解释器而不是 启动.bat —— 走 .bat 会闪一下黑框。

[CmdletBinding()]
param(
    [switch]$Desktop,
    [switch]$Startup,
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"

$AppName    = "Predoc Watcher"
$ProjectDir = $PSScriptRoot
$Script     = Join-Path $ProjectDir "desktop.py"
$IconPath   = Join-Path $ProjectDir "app.ico"

$StartMenu  = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\$AppName.lnk"
$DesktopLnk = Join-Path ([Environment]::GetFolderPath("Desktop")) "$AppName.lnk"
$StartupLnk = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup\$AppName.lnk"

if ($Uninstall) {
    foreach ($p in @($StartMenu, $DesktopLnk, $StartupLnk)) {
        if (Test-Path $p) { Remove-Item $p -Force; Write-Host "已移除 / Removed: $p" }
    }
    return
}

if (-not (Test-Path $Script)) { throw "desktop.py not found in $ProjectDir" }

# 解释器的找法与 启动.bat 保持一致：环境变量 -> python_path.txt -> PATH
function Resolve-Python {
    if ($env:PREDOC_PYTHON) { return $env:PREDOC_PYTHON }
    $txt = Join-Path $ProjectDir "python_path.txt"
    if (Test-Path $txt) {
        $line = (Get-Content $txt -TotalCount 1).Trim().Trim('"')
        if ($line) { return $line }
    }
    foreach ($n in @("pythonw", "python")) {
        $c = Get-Command $n -ErrorAction SilentlyContinue
        if ($c) {
            $w = Join-Path (Split-Path $c.Source) "pythonw.exe"
            if (Test-Path $w) { return $w }
            return $c.Source
        }
    }
    return $null
}

$Python = Resolve-Python
if (-not $Python) {
    throw "找不到 Python。装好 Python 3.9+，或把解释器完整路径写进 python_path.txt。`nPython not found. Install Python 3.9+, or put the interpreter path in python_path.txt."
}
if (-not (Test-Path $Python)) { throw "解释器路径不存在 / interpreter not found: $Python" }
if ($Python -notmatch 'pythonw\.exe$') {
    Write-Host "提示：$Python 不是 pythonw.exe，启动时会闪一下黑框。" -ForegroundColor Yellow
    Write-Host "Note: not pythonw.exe — a console window will flash on launch." -ForegroundColor Yellow
}

function New-Shortcut($Path, $Arguments) {
    $shell = New-Object -ComObject WScript.Shell
    $sc = $shell.CreateShortcut($Path)
    $sc.TargetPath       = $Python
    $sc.Arguments        = $Arguments
    $sc.WorkingDirectory = $ProjectDir
    $sc.IconLocation     = "$IconPath,0"
    $sc.Description      = "Watch predoc.org and NBER for new pre-doc / RA postings"
    $sc.Save()
    Write-Host "已创建 / Created: $Path" -ForegroundColor Green
}

Write-Host "解释器 / Interpreter: $Python"
New-Shortcut $StartMenu "`"$Script`""
if ($Desktop) { New-Shortcut $DesktopLnk "`"$Script`"" }
# 开机自启时直接缩到托盘，不弹窗打扰
if ($Startup) { New-Shortcut $StartupLnk "`"$Script`" --minimized" }

Write-Host ""
Write-Host "在「开始」菜单搜 `"Predoc`" 就能找到。" -ForegroundColor Cyan
Write-Host "Search the Start menu for `"Predoc`"." -ForegroundColor Cyan
