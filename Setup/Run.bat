@echo off
setlocal

set "LOGFILE=%~dp0run.log"
>> "%LOGFILE%" echo ===== %date% %time% =====

rem Fixed paths requested
set "PROENV=C:\Progra~1\ArcGIS\Pro\bin\Python\Scripts\proenv.bat"
set "ACTIVATE=C:\Progra~1\ArcGIS\Pro\bin\Python\Scripts\activate.bat"
set "ENV_NAME=ra-env"
set "ENV_PREFIX=C:\Progra~1\ArcGIS\Pro\bin\Python\envs\%ENV_NAME%"
set "SCRIPT_TO_RUN=%~dp0..\GUI\main_ui.py"
set "PYTHON_EXE=%ENV_PREFIX%\python.exe"

call :log [INFO] Starting launcher for %ENV_NAME%

rem Step 1: enter ArcGIS Pro conda shell
call :log [STEP] proenv.bat
call "%PROENV%" >>"%LOGFILE%" 2>&1

rem Step 2: activate the ra-env clone
call :log [STEP] conda activate "%ENV_PREFIX%"
call conda activate "%ENV_PREFIX%" >>"%LOGFILE%" 2>&1

rem Fallback manual activation if conda did not switch
if not "%CONDA_PREFIX%"=="%ENV_PREFIX%" (
    call :log [WARN] conda activate failed; trying activate.bat directly.
    call "%ACTIVATE%" "%ENV_PREFIX%" >>"%LOGFILE%" 2>&1
    set "PATH=%ENV_PREFIX%;%ENV_PREFIX%\Scripts;%ENV_PREFIX%\Library\bin;%PATH%"
    set "CONDA_PREFIX=%ENV_PREFIX%"
    set "CONDA_DEFAULT_ENV=%ENV_NAME%"
)

rem Step 2.5: ensure river_architect database and tables exist
call :log [STEP] init river_architect database
"%PYTHON_EXE%" "%~dp0..\Database\input_condition_database.py" >>"%LOGFILE%" 2>&1

rem Step 3: launch the app
if not exist "%SCRIPT_TO_RUN%" (
    call :log [ERROR] Script not found at: "%SCRIPT_TO_RUN%"
    pause
    exit /b 1
)

if not exist "%PYTHON_EXE%" (
    call :log [ERROR] Python executable missing at %PYTHON_EXE%
    pause
    exit /b 1
)

call :log [STEP] python "%SCRIPT_TO_RUN%"
"%PYTHON_EXE%" "%SCRIPT_TO_RUN%" >>"%LOGFILE%" 2>&1

endlocal
exit /b 0

:log
setlocal enabledelayedexpansion
set "line=%*"
echo !line!
>>"%LOGFILE%" echo !line!
endlocal & goto :eof
