@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "APP_ROOT=%~dp0"
set "VENV_DIR=%APP_ROOT%.venv"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
set "REQ_FILE=%APP_ROOT%requirements.txt"
set "REQ_STAMP=%VENV_DIR%\requirements.stamp"
set "NEED_INSTALL=0"

cd /d "%APP_ROOT%"
set "PYTHONPATH=%APP_ROOT%;%PYTHONPATH%"

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

echo App root: %APP_ROOT%
echo Python: %PYTHON_EXE%
"%PYTHON_EXE%" -c "import importlib.util as u; mods=('src.engineers_tools.app.module_window','src.engineers_tools.app.project_file_dialog','modules.mechanics_dynamics_statics.module_entry','modules.mechanics_dynamics_statics.workspace'); [print(m + ': ' + str((u.find_spec(m).origin if u.find_spec(m) else 'NOT FOUND'))) for m in mods]"
if errorlevel 1 (
    echo Runtime path check failed.
    pause
    exit /b 1
)

"%PYTHON_EXE%" -c "from modules.mechanics_dynamics_statics.workspace import EngineeringDesignWorkspace; from src.engineers_tools.app.module_window import ModuleWindow; from src.engineers_tools.app.project_file_dialog import ProjectFileDialog; print('active workspace class: ' + EngineeringDesignWorkspace.__module__ + '.' + EngineeringDesignWorkspace.__name__); print('shared window class: ' + ModuleWindow.__module__ + '.' + ModuleWindow.__name__); print('file dialog class: ' + ProjectFileDialog.__module__ + '.' + ProjectFileDialog.__name__)"
if errorlevel 1 (
    echo Active runtime verification failed.
    pause
    exit /b 1
)

"%PYTHON_EXE%" -m src.engineers_tools.main

endlocal
