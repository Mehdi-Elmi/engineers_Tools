@echo off
setlocal EnableExtensions DisableDelayedExpansion

set "APP_NAME=EngineeringTools"
set "REPO_OWNER=Mehdi-Elmi"
set "REPO_NAME=engineers_Tools"
set "BRANCH=main"
set "INSTALL_DIR=%LOCALAPPDATA%\%APP_NAME%"
set "TEMP_ZIP=%TEMP%\%APP_NAME%.zip"
set "TEMP_DIR=%TEMP%\%APP_NAME%_extract"
set "LEGACY_DESKTOP_RUNNER=%USERPROFILE%\Desktop\Engineering Tools.cmd"
set "LEGACY_DESKTOP_ENGINEER=%USERPROFILE%\Desktop\engineer.cmd"
set "LEGACY_DESKTOP_LAUNCHER=%USERPROFILE%\Desktop\launch_engineering_tools.cmd"
set "LOG_FILE=%USERPROFILE%\Desktop\EngineeringTools_install.log"
set "TOKEN_FILE="

call :log "=== Engineering Tools installer started ==="
call :log "Install directory: %INSTALL_DIR%"

if /I "%~1"=="update" set "FORCE_UPDATE=1"
if /I "%~1"=="/update" set "FORCE_UPDATE=1"

if exist "%INSTALL_DIR%\main.py" if not "%FORCE_UPDATE%"=="1" (
    call :log "Existing local installation found. Skipping download and launching installed copy."
    call :launch_gui "%INSTALL_DIR%"
    if errorlevel 1 (
        call :fail "Installed Engineering Tools GUI could not be launched."
    )
    call :log "Engineering Tools GUI launch command completed."
    endlocal
    exit /b 0
)

for %%F in (
    "%USERPROFILE%\Desktop\token.txt"
    "%USERPROFILE%\Desktop\github_token.txt"
    "%USERPROFILE%\Desktop\Github_token.txt"
) do (
    if not defined TOKEN_FILE if exist "%%~F" set "TOKEN_FILE=%%~F"
)

if not defined TOKEN_FILE (
    call :fail "GitHub token file was not found on Desktop. Expected token.txt or github_token.txt."
)

for /f "usebackq delims=" %%A in ("%TOKEN_FILE%") do (
    set "GITHUB_TOKEN=%%A"
    goto :token_read
)
:token_read

if "%GITHUB_TOKEN%"=="" (
    call :fail "GitHub token file is empty: %TOKEN_FILE%"
)

where curl >nul 2>nul
if errorlevel 1 (
    call :fail "curl was not found. Windows curl is required for downloading the GitHub repository."
)

call :log "Cleaning temporary files and legacy launchers..."
if exist "%TEMP_ZIP%" del /f /q "%TEMP_ZIP%" >> "%LOG_FILE%" 2>&1
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%" >> "%LOG_FILE%" 2>&1
if "%FORCE_UPDATE%"=="1" if exist "%INSTALL_DIR%" rmdir /s /q "%INSTALL_DIR%" >> "%LOG_FILE%" 2>&1
if exist "%LEGACY_DESKTOP_RUNNER%" del /f /q "%LEGACY_DESKTOP_RUNNER%" >> "%LOG_FILE%" 2>&1
if exist "%LEGACY_DESKTOP_ENGINEER%" del /f /q "%LEGACY_DESKTOP_ENGINEER%" >> "%LOG_FILE%" 2>&1
if exist "%LEGACY_DESKTOP_LAUNCHER%" del /f /q "%LEGACY_DESKTOP_LAUNCHER%" >> "%LOG_FILE%" 2>&1

mkdir "%TEMP_DIR%" >nul 2>nul
mkdir "%INSTALL_DIR%" >nul 2>nul

call :log "Downloading latest GitHub content..."
curl -fL --retry 2 --connect-timeout 20 ^
  -H "Authorization: Bearer %GITHUB_TOKEN%" ^
  -H "Accept: application/vnd.github+json" ^
  -o "%TEMP_ZIP%" ^
  "https://api.github.com/repos/%REPO_OWNER%/%REPO_NAME%/zipball/%BRANCH%" >> "%LOG_FILE%" 2>&1

if errorlevel 1 (
    call :log "API zipball download failed. Trying codeload fallback..."
    curl -fL --retry 2 --connect-timeout 20 ^
      -H "Authorization: Bearer %GITHUB_TOKEN%" ^
      -o "%TEMP_ZIP%" ^
      "https://codeload.github.com/%REPO_OWNER%/%REPO_NAME%/zip/refs/heads/%BRANCH%" >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        call :fail "Download failed. Check token access, internet connection, and repository permission."
    )
)

if not exist "%TEMP_ZIP%" (
    call :fail "Download file was not created."
)

for %%Z in ("%TEMP_ZIP%") do if %%~zZ LSS 1000 (
    call :fail "Downloaded file is too small to be a valid project archive."
)

call :log "Extracting GitHub content..."
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Force '%TEMP_ZIP%' '%TEMP_DIR%'" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    call :fail "Extract failed. The downloaded file was not a valid zip archive."
)

for /d %%D in ("%TEMP_DIR%\*") do set "EXTRACTED=%%D"

if not defined EXTRACTED (
    call :fail "Extracted project folder was not found."
)

if not exist "%EXTRACTED%\main.py" (
    call :fail "main.py was not found after extraction."
)

call :log "Copying GitHub content into install directory..."
xcopy "%EXTRACTED%\*" "%INSTALL_DIR%\" /E /I /Y >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    call :fail "Copying project files failed."
)

call :log "Launching Engineering Tools GUI directly from installer..."
call :launch_gui "%INSTALL_DIR%"
if errorlevel 1 (
    call :fail "Engineering Tools GUI could not be launched."
)

call :log "Engineering Tools GUI launch command completed."
endlocal
exit /b 0

:launch_gui
set "APP_DIR=%~1"
set "REQUIRED_PYTHON=3.11"
set "PYTHON_EXE="
set "PYTHONW_EXE="

where py >nul 2>nul
if not errorlevel 1 (
    for /f "usebackq delims=" %%P in (`py -%REQUIRED_PYTHON% -c "import sys; print(sys.executable)" 2^>nul`) do set "PYTHON_EXE=%%P"
)

if not defined PYTHON_EXE (
    where python >nul 2>nul
    if not errorlevel 1 for /f "usebackq delims=" %%P in (`python -c "import sys; print(sys.executable) if sys.version_info[:2] == (3, 11) else sys.exit(1)" 2^>nul`) do set "PYTHON_EXE=%%P"
)

if defined PYTHON_EXE (
    set "PYTHONW_EXE=%PYTHON_EXE%"
    set "PYTHONW_EXE=%PYTHONW_EXE:python.exe=pythonw.exe%"
    set "PYTHONW_EXE=%PYTHONW_EXE:python.EXE=pythonw.exe%"
    if not exist "%PYTHONW_EXE%" set "PYTHONW_EXE="
)

if not defined PYTHON_EXE (
    call :log "Python %REQUIRED_PYTHON% was not found."
    exit /b 1
)

if defined PYTHONW_EXE (
    call :log "Using Python GUI runner: %PYTHONW_EXE%"
    "%PYTHONW_EXE%" "%APP_DIR%\main.py"
) else (
    where pyw >nul 2>nul
    if errorlevel 1 (
        call :log "pythonw.exe or pyw.exe was not found for Python %REQUIRED_PYTHON%."
        exit /b 1
    )
    call :log "Using Python GUI launcher: pyw -%REQUIRED_PYTHON%"
    pyw -%REQUIRED_PYTHON% "%APP_DIR%\main.py"
)

exit /b %ERRORLEVEL%

:log
echo %~1
>> "%LOG_FILE%" echo [%DATE% %TIME%] %~1
exit /b 0

:fail
echo.
echo ERROR: %~1
echo.
echo Log file:
echo %LOG_FILE%
>> "%LOG_FILE%" echo [%DATE% %TIME%] ERROR: %~1
goto :abort

:abort
pause
endlocal
exit /b 1
