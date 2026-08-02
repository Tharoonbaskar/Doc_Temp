@echo off
REM Quick installation and test script for WeasyPrint on Windows

echo ========================================
echo WeasyPrint Setup and Test
echo ========================================
echo.

echo Step 1: Installing GTK dependencies...
echo This requires administrator privileges.
echo.

powershell -Command "Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -File install_gtk_for_weasyprint.ps1' -Verb RunAs -Wait"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Installation failed or was cancelled.
    echo Please run install_gtk_for_weasyprint.ps1 manually with administrator rights.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Step 2: Testing PDF Generation
echo ========================================
echo.
echo Please close and reopen your terminal if this is the first install.
echo Press any key to continue with the test...
pause >nul

cd /d %~dp0

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo No virtual environment found. Using global Python.
)

echo.
echo Running end-to-end PDF generation test...
echo.

python test_pdf_e2e.py

echo.
echo ========================================
echo Test Complete
echo ========================================
echo.
pause
