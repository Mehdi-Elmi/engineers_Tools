@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "APP_ROOT=%~dp0"
set "EXPECTED_APP_ROOT=%LOCALAPPDATA%\EngineerTools\"
set "VENV_DIR=%APP_ROOT%.venv"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
set "PYTHONW_EXE=%VENV_DIR%\Scripts\pythonw.exe"
set "REQ_FILE=%APP_ROOT%requirements.txt"
set "REQ_STAMP=%VENV_DIR%\requirements.stamp"
set "NEED_INSTALL=0"

cd /d "%APP_ROOT%"

if not exist "%PYTHON_EXE%" (
    echo Creating Python virtual environment...
    py -3.11 -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo Python 3.11 was not found. Please install Python 3.11 and run this file again.
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
    "%PYTHON_EXE%" -m pip install --upgrade pip
    if errorlevel 1 (
        echo Failed to update pip.
        pause
        exit /b 1
    )
    if exist "%REQ_FILE%" (
        "%PYTHON_EXE%" -m pip install -r "%REQ_FILE%"
        if errorlevel 1 (
            echo Failed to install Python requirements.
            pause
            exit /b 1
        )
        copy /y "%REQ_FILE%" "%REQ_STAMP%" >nul
    )
) else (
    echo Python environment is ready.
)

if /I not "%APP_ROOT%"=="%EXPECTED_APP_ROOT%" (
    echo Warning: app is running from %APP_ROOT%
    echo Expected install path is %EXPECTED_APP_ROOT%
)

if not exist "%APP_ROOT%src\engineers_tools\main.py" (
    echo Missing application entry: %APP_ROOT%src\engineers_tools\main.py
    pause
    exit /b 1
)

echo Starting Engineer Tools GUI...
start "" "%PYTHONW_EXE%" -m src.engineers_tools.main

endlocal
