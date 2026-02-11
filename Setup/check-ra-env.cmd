@echo off
setlocal enabledelayedexpansion

goto :main

:log
setlocal enabledelayedexpansion
set "line=%*"
echo !line!
>>"%LOGFILE%" echo !line!
endlocal & goto :eof

:main
rem -----------------------------------------------------------------------------
rem Verifies the ra-env conda environment exists and is ready to launch GUI/main_ui.py.
rem Checks:
rem  1) ArcGIS Pro and conda presence.
rem  2) Environment folder exists.
rem  3) All packages in requirements.txt are installed.
rem  4) GUI/main_ui.py file exists.
rem Usage: check-ra-env.cmd [EnvName]
rem Exit code 0 = ready; non-zero = not ready.
rem -----------------------------------------------------------------------------

set "EnvName=ra-env"
set "ReqFile=%~dp0requirements.txt"
set "LOGFILE=%~dp0check.log"
> "%LOGFILE%" echo ===== %date% %time% =====
rem Resolve repo root based on script location to avoid hard-coding USERPROFILE
for %%i in ("%~dp0..") do set "ProjectRoot=%%~fi"
rem Main GUI entrypoint (matches Setup/Run.bat)
set "MainGui=%ProjectRoot%\GUI\main_ui.py"

if not "%~1"=="" (
    set "EnvName=%~1"
)

rem --- Locate ArcGIS Pro and conda -------------------------------------------
set "InstallDir="
for %%R in ("HKLM\SOFTWARE\Esri\ArcGISPro" "HKLM\SOFTWARE\WOW6432Node\Esri\ArcGISPro") do (
    for /f "tokens=2,*" %%A in ('reg query "%%~R" /v InstallDir 2^>nul ^| find "InstallDir"') do (
        set "InstallDir=%%B"
    )
)
if not defined InstallDir if exist "C:\Program Files\ArcGIS\Pro\bin\ArcGISPro.exe" set "InstallDir=C:\Program Files\ArcGIS\Pro"
if not defined InstallDir (
    call :log [ERROR] ArcGIS Pro not found.
    exit /b 1
)
if "%InstallDir:~-1%"=="\" set "InstallDir=%InstallDir:~0,-1%"
set "CondaExe=%InstallDir%\bin\Python\Scripts\conda.exe"
if not exist "%CondaExe%" (
    call :log [ERROR] conda.exe not found under %InstallDir%\bin\Python\Scripts
    exit /b 1
)

rem --- Check env existence ----------------------------------------------------
set "EnvPrefix=%InstallDir%\bin\Python\envs\%EnvName%"

call :log [INFO] Checking environment: %EnvName%
call :log [INFO] Resolved prefix   : %EnvPrefix%

if not exist "%EnvPrefix%\conda-meta" (
    call :log [ERROR] Environment not found at %EnvPrefix%. Run setup-ra-env first.
    exit /b 1
)

rem --- Verify dependencies from requirements file ----------------------------
set "MissingDeps="
set "PkgList=%TEMP%\\ra_env_list_%RANDOM%.txt"
"%CondaExe%" list --prefix "%EnvPrefix%" > "%PkgList%" 2>nul
if errorlevel 1 (
    call :log [WARN] Unable to list packages for "%EnvName%"; skipping dependency check.
) else if exist "%ReqFile%" (
    for /f "usebackq eol=# tokens=1" %%P in ("%ReqFile%") do (
        set "found="
        if not "%%P"=="" (
            findstr /i "^%%P" "%PkgList%" >nul && set "found=1"
            if not defined found set "MissingDeps=!MissingDeps! %%P"
        )
    )
) else (
    call :log [WARN] Requirements file not found: %ReqFile%
)
if exist "%PkgList%" del "%PkgList%" >nul 2>&1

rem --- Check Main GUI entrypoint ---------------------------------------------
if not exist "%MainGui%" (
    call :log [ERROR] GUI/main_ui.py not found at %MainGui%
    exit /b 1
)

rem --- Summarize -------------------------------------------------------------
if defined MissingDeps (
call :log [ERROR] Missing packages:%MissingDeps%
    exit /b 1
)

call :log [OK] Environment exists, dependencies present, and GUI/main_ui.py found.

exit /b 0
endlocal
