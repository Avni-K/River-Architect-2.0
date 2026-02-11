@echo off
setlocal enabledelayedexpansion

set CLONE_NAME=ra-env

echo [WARNING] This will permanently delete the environment: %CLONE_NAME%
set /p "CONFIRM=Are you sure you want to proceed? (Y/N): "

if /i "%CONFIRM%" neq "Y" (
    echo Deletion cancelled.
    pause
    exit /b
)

:: Locate ArcGIS Pro Conda
for /f "tokens=2*" %%a in ('reg query "HKEY_LOCAL_MACHINE\SOFTWARE\ESRI\ArcGISPro" /v "InstallDir" 2^>nul') do set "PRO_DIR=%%b"
set CONDA_EXE=%PRO_DIR%bin\Python\Scripts\conda.exe

echo [1/2] Deleting environment %CLONE_NAME%...
call "%CONDA_EXE%" env remove --name %CLONE_NAME% -y

if %errorlevel% equ 0 (
    echo [2/2] Cleanup successful.
    echo Suggestion: Run setup-ra-env.cmd now to create a fresh environment.
) else (
    echo [ERROR] Could not delete environment. 
    echo Improvement: Ensure no Python processes or ArcGIS Pro instances are running.
)

pauses