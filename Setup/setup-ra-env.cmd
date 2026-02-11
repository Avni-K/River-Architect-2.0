@echo off
setlocal enabledelayedexpansion

:: Log file location
set "LOGFILE=%~dp0setup.log"
echo ===== %date% %time% ===== > "%LOGFILE%"

:: Run main logic with stdout/stderr captured to log
call :main %* >> "%LOGFILE%" 2>&1
set "EXITCODE=%errorlevel%"

echo Full log saved to %LOGFILE%
type "%LOGFILE%"

if %EXITCODE% neq 0 (
    echo Script failed with exit code %EXITCODE%. Check the log for details.
) else (
    echo Setup completed successfully.
)

pause
exit /b %EXITCODE%

:main
:: Configuration
set CLONE_NAME=ra-env
set REQ_PATH=%~dp0requirements.txt

echo [1/4] Locating ArcGIS Pro Conda...
for /f "tokens=2*" %%a in ('reg query "HKEY_LOCAL_MACHINE\SOFTWARE\ESRI\ArcGISPro" /v "InstallDir" 2^>nul') do set "PRO_DIR=%%b"

if "%PRO_DIR%"=="" (
    echo [ERROR] ArcGIS Pro not found in registry.
    exit /b 1
)

set CONDA_EXE=%PRO_DIR%bin\Python\Scripts\conda.exe

echo [2/4] Checking for environment: %CLONE_NAME%
call "%CONDA_EXE%" env list | findstr /C:"%CLONE_NAME%" >nul
if %errorlevel% neq 0 (
    echo Environment %CLONE_NAME% not found. Creating clone...
    call "%CONDA_EXE%" create --name %CLONE_NAME% --clone arcgispro-py3 -y
)

echo [3/4] Activating and checking Arcpy...
call "%PRO_DIR%bin\Python\Scripts\activate.bat" %CLONE_NAME%

:: Verification Step
python -c "import arcpy; print('ArcPy successfully linked.')" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Arcpy is NOT accessible in %CLONE_NAME%.
    echo Improvement: Try deleting the env and running this script as Administrator.
    exit /b 1
)

echo [4/4] Installing dependencies...
if exist "%REQ_PATH%" (
    pip install -r "%REQ_PATH%"
) else (
    echo [WARNING] requirements.txt NOT found at %REQ_PATH%.
)

exit /b 0
