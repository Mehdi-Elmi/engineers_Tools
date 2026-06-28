@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "APP_ROOT=%~dp0"
set "EXPECTED_APP_ROOT=%LOCALAPPDATA%\EngineerTools\"
set "VENV_DIR=%APP_ROOT%.venv"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
set "PYTHONW_EXE=%VENV_DIR%\Scripts\pythonw.exe"
set "REQ_FILE=%APP_ROOT%requirements.txt"
set "REQ_STAMP=%VENV_DIR%\requirements.stamp"
set "LOG_DIR=%APP_ROOT%logs"
set "STARTUP_LOG=%LOG_DIR%\launcher_startup.log"
set "NEED_INSTALL=0"
set "PYTHONNOUSERSITE=1"
set "PYTHONDONTWRITEBYTECODE=1"

cd /d "%APP_ROOT%"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>nul
> "%STARTUP_LOG%" echo Engineer Tools startup command started.
>> "%STARTUP_LOG%" echo App root: %APP_ROOT%
>> "%STARTUP_LOG%" echo Expected app root: %EXPECTED_APP_ROOT%

if not exist "%PYTHON_EXE%" (
    echo Creating Python virtual environment...
    >> "%STARTUP_LOG%" echo Creating Python virtual environment...
    py -3.11 -m venv "%VENV_DIR%" >> "%STARTUP_LOG%" 2>&1
    if errorlevel 1 (
        echo Python 3.11 was not found. Please install Python 3.11 and run this file again.
        type "%STARTUP_LOG%"
        pause
        exit /b 1
    )
    set "NEED_INSTALL=1"
)

if not exist "%PYTHONW_EXE%" (
    set "PYTHONW_EXE=%PYTHON_EXE%"
)

if exist "%REQ_FILE%" (
    if not exist "%REQ_STAMP%" (
        set "NEED_INSTALL=1"
    ) else (
        fc /b "%REQ_FILE%" "%REQ_STAMP%" >nul
        if errorlevel 1 set "NEED_INSTALL=1"
    )
)

if "%NEED_INSTALL%"=="1" (
    echo Preparing Python dependencies...
    >> "%STARTUP_LOG%" echo Preparing Python dependencies...
    "%PYTHON_EXE%" -m pip --version >> "%STARTUP_LOG%" 2>&1
    if errorlevel 1 (
        "%PYTHON_EXE%" -m ensurepip --upgrade >> "%STARTUP_LOG%" 2>&1
        if errorlevel 1 (
            echo Failed to prepare pip.
            type "%STARTUP_LOG%"
            pause
            exit /b 1
        )
    )
    if exist "%REQ_FILE%" (
        "%PYTHON_EXE%" -m pip install --disable-pip-version-check -r "%REQ_FILE%" >> "%STARTUP_LOG%" 2>&1
        if errorlevel 1 (
            echo Failed to install Python requirements.
            type "%STARTUP_LOG%"
            pause
            exit /b 1
        )
        copy /y "%REQ_FILE%" "%REQ_STAMP%" >nul
    )
) else (
    echo Python environment is ready.
    >> "%STARTUP_LOG%" echo Python environment is ready.
)

if /I not "%APP_ROOT%"=="%EXPECTED_APP_ROOT%" (
    echo Warning: app is running from %APP_ROOT%
    echo Expected install path is %EXPECTED_APP_ROOT%
    >> "%STARTUP_LOG%" echo Warning: app is running from %APP_ROOT%
)

if not exist "%APP_ROOT%src\engineers_tools\main.py" (
    echo Missing application entry: %APP_ROOT%src\engineers_tools\main.py
    >> "%STARTUP_LOG%" echo Missing application entry: %APP_ROOT%src\engineers_tools\main.py
    type "%STARTUP_LOG%"
    pause
    exit /b 1
)

>> "%STARTUP_LOG%" echo Running Python startup import preflight...
"%PYTHON_EXE%" -c "import importlib; importlib.import_module('src.engineers_tools.main'); print('startup import ok')" >> "%STARTUP_LOG%" 2>&1
if errorlevel 1 (
    echo Engineer Tools startup preflight failed.
    echo Startup log: %STARTUP_LOG%
    type "%STARTUP_LOG%"
    pause
    exit /b 1
)

>> "%STARTUP_LOG%" echo Starting Engineer Tools GUI with %PYTHONW_EXE%.
echo Starting Engineer Tools GUI...
start "" "%PYTHONW_EXE%" -m src.engineers_tools.main

endlocal
