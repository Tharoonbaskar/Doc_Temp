# PowerShell Script to Install MSYS2 and GTK for WeasyPrint
# Run this script as Administrator

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "WeasyPrint GTK Dependencies Installer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script requires administrator privileges." -ForegroundColor Red
    Write-Host "Please right-click and select 'Run as Administrator'" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

$msys2Path = "C:\msys64"
$msys2BinPath = "$msys2Path\mingw64\bin"

# Check if MSYS2 is already installed
if (Test-Path $msys2Path) {
    Write-Host "[OK] MSYS2 found at $msys2Path" -ForegroundColor Green
} else {
    Write-Host "[INFO] MSYS2 not found. Installing..." -ForegroundColor Yellow
    
    $installerUrl = "https://github.com/msys2/msys2-installer/releases/download/2024-01-13/msys2-x86_64-20240113.exe"
    $installerPath = "$env:TEMP\msys2-installer.exe"
    
    Write-Host "Downloading MSYS2 installer..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath
    
    Write-Host "Running MSYS2 installer (automated)..." -ForegroundColor Cyan
    Start-Process -FilePath $installerPath -ArgumentList "install", "--root", $msys2Path, "--confirm-command" -Wait
    
    Remove-Item $installerPath -ErrorAction SilentlyContinue
    
    if (Test-Path $msys2Path) {
        Write-Host "[OK] MSYS2 installed successfully" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] MSYS2 installation failed" -ForegroundColor Red
        exit 1
    }
}

# Install GTK packages using MSYS2
Write-Host ""
Write-Host "Installing GTK3 and dependencies..." -ForegroundColor Cyan

$msys2Bash = "$msys2Path\usr\bin\bash.exe"

if (-not (Test-Path $msys2Bash)) {
    Write-Host "[ERROR] MSYS2 bash not found at $msys2Bash" -ForegroundColor Red
    exit 1
}

# Update MSYS2 package database
Write-Host "Updating MSYS2 package database..." -ForegroundColor Cyan
& $msys2Bash -lc "pacman -Sy --noconfirm"

# Install GTK and dependencies
Write-Host "Installing GTK packages (this may take a few minutes)..." -ForegroundColor Cyan
$packages = @(
    "mingw-w64-x86_64-gtk3",
    "mingw-w64-x86_64-pango",
    "mingw-w64-x86_64-cairo",
    "mingw-w64-x86_64-gdk-pixbuf2",
    "mingw-w64-x86_64-gobject-introspection"
)

foreach ($package in $packages) {
    Write-Host "  - Installing $package..." -ForegroundColor Gray
    & $msys2Bash -lc "pacman -S --noconfirm $package"
}

Write-Host "[OK] GTK packages installed" -ForegroundColor Green

# Verify critical DLL
$pangoDll = "$msys2BinPath\libpango-1.0-0.dll"
if (Test-Path $pangoDll) {
    Write-Host "[OK] libpango-1.0-0.dll found" -ForegroundColor Green
} else {
    Write-Host "[WARNING] libpango-1.0-0.dll not found at expected location" -ForegroundColor Yellow
}

# Add to system PATH
Write-Host ""
Write-Host "Adding $msys2BinPath to system PATH..." -ForegroundColor Cyan

$currentPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::Machine)

if ($currentPath -notlike "*$msys2BinPath*") {
    $newPath = "$msys2BinPath;$currentPath"
    [Environment]::SetEnvironmentVariable("Path", $newPath, [EnvironmentVariableTarget]::Machine)
    Write-Host "[OK] Added to system PATH" -ForegroundColor Green
    Write-Host "[INFO] You need to restart your terminal/IDE for PATH changes to take effect" -ForegroundColor Yellow
} else {
    Write-Host "[OK] Already in system PATH" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Close and reopen VS Code / Terminal" -ForegroundColor White
Write-Host "2. Restart your Django backend server" -ForegroundColor White
Write-Host "3. Run 'python debug_pdf.py' to test PDF generation" -ForegroundColor White
Write-Host ""

Read-Host "Press Enter to exit"
