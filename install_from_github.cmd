@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "REPO=Mehdi-Elmi/engineers_Tools"
set "BRANCH=main"
set "TOKEN_FILE=%USERPROFILE%\Desktop\token.txt"
set "FALLBACK_TOKEN_FILE=%USERPROFILE%\Desktop\testdoctoken.txt"
set "INSTALL_DIR=%LOCALAPPDATA%\EngineerTools"
set "LEGACY_INSTALL_DIR=%LOCALAPPDATA%\EngineersTools"
set "COMMIT_STAMP=%INSTALL_DIR%\.install_commit"
set "ZIP_FILE=%TEMP%\engineer_tools.zip"
set "EXTRACT_DIR=%TEMP%\engineer_tools_extract"
set "REMOTE_SHA_FILE=%TEMP%\engineer_tools_remote_sha.txt"
set "UPDATE_STATUS_FILE=%TEMP%\engineer_tools_update_status.txt"
set "FORCE_UPDATE=0"

if not exist "%TOKEN_FILE%" (
    if exist "%FALLBACK_TOKEN_FILE%" (
        set "TOKEN_FILE=%FALLBACK_TOKEN_FILE%"
    ) else (
        echo token.txt was not found on Desktop.
        echo Expected path: %USERPROFILE%\Desktop\token.txt
        echo Fallback path: %USERPROFILE%\Desktop\testdoctoken.txt
        pause
        exit /b 1
    )
)

if exist "%REMOTE_SHA_FILE%" del /f /q "%REMOTE_SHA_FILE%" >nul 2>nul
if exist "%UPDATE_STATUS_FILE%" del /f /q "%UPDATE_STATUS_FILE%" >nul 2>nul

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "$utf8NoBom=New-Object System.Text.UTF8Encoding($false);" ^
  "$tokenPath=$env:TOKEN_FILE;" ^
  "$token=[System.IO.File]::ReadAllText($tokenPath,[System.Text.Encoding]::UTF8).Trim();" ^
  "$token=$token.Trim([char]0xFEFF).Trim().Trim([char]34).Trim([char]39);" ^
  "$token=[regex]::Replace($token,'(?i)^(bearer|token)\s+','').Trim();" ^
  "if([string]::IsNullOrWhiteSpace($token)){ Write-Host 'GitHub token file is empty after cleanup.'; exit 10 }" ^
  "$branchUri='https://api.github.com/repos/%REPO%/branches/%BRANCH%';" ^
  "$baseHeaders=@{Accept='application/vnd.github+json'; 'X-GitHub-Api-Version'='2022-11-28'; 'User-Agent'='EngineerToolsInstaller'};" ^
  "$branchData=$null;" ^
  "foreach($scheme in @('Bearer','token')){ try{ $headers=$baseHeaders.Clone(); $headers.Authorization=$scheme + ' ' + $token; $response=Invoke-WebRequest -Uri $branchUri -Headers $headers -UseBasicParsing; $branchData=$response.Content | ConvertFrom-Json; break } catch { if($_.Exception.Response -and [int]$_.Exception.Response.StatusCode -eq 401){ continue } throw } }" ^
  "if($null -eq $branchData){ Write-Host 'GitHub returned 401 Unauthorized.'; Write-Host 'The token is invalid, expired, or does not have read access to this private repository.'; exit 11 }" ^
  "$remoteSha=[string]$branchData.commit.sha;" ^
  "[System.IO.File]::WriteAllText($env:REMOTE_SHA_FILE,$remoteSha,$utf8NoBom);" ^
  "$localSha=''; if(Test-Path $env:COMMIT_STAMP){ $localSha=[System.IO.File]::ReadAllText($env:COMMIT_STAMP,[System.Text.Encoding]::UTF8).Trim([char]0xFEFF).Trim() }" ^
  "$runFile=Join-Path $env:INSTALL_DIR 'run_engineers_tools.cmd';" ^
  "$readmeFile=Join-Path $env:INSTALL_DIR 'README.md';" ^
  "$uiFile=Join-Path $env:INSTALL_DIR 'src\engineers_tools\app\module_window.py';" ^
  "$repoOk=(Test-Path $readmeFile) -and ((Get-Content $readmeFile -Raw) -match 'Mehdi-Elmi/engineers_Tools');" ^
  "$runnerOk=(Test-Path $runFile) -and ((Get-Content $runFile -Raw) -match 'EXPECTED_APP_ROOT');" ^
  "$uiOk=(Test-Path $uiFile) -and ((Get-Content $uiFile -Raw) -match 'ENGINEER_TOOLS_ACTIVE_UI_2026_06_27_A');" ^
  "$force=$env:FORCE_UPDATE -eq '1';" ^
  "if((Test-Path $runFile) -and $repoOk -and $runnerOk -and $uiOk -and -not $force -and $localSha -eq $remoteSha){ [System.IO.File]::WriteAllText($env:UPDATE_STATUS_FILE,'UP_TO_DATE',[System.Text.Encoding]::ASCII) } else { [System.IO.File]::WriteAllText($env:UPDATE_STATUS_FILE,'NEED_UPDATE',[System.Text.Encoding]::ASCII) }"

if errorlevel 1 (
    echo Version check failed.
    pause
    exit /b 1
)

set "UPDATE_STATUS=NEED_UPDATE"
if exist "%UPDATE_STATUS_FILE%" set /p UPDATE_STATUS=<"%UPDATE_STATUS_FILE%"

if /I "%UPDATE_STATUS%"=="UP_TO_DATE" (
    echo Engineer Tools is already up to date.
    call "%INSTALL_DIR%\run_engineers_tools.cmd"
    goto :finish
)

if exist "%ZIP_FILE%" del /f /q "%ZIP_FILE%" >nul 2>nul
if exist "%EXTRACT_DIR%" rmdir /s /q "%EXTRACT_DIR%" >nul 2>nul
mkdir "%EXTRACT_DIR%" >nul 2>nul

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "$tokenPath=$env:TOKEN_FILE;" ^
  "$token=[System.IO.File]::ReadAllText($tokenPath,[System.Text.Encoding]::UTF8).Trim();" ^
  "$token=$token.Trim([char]0xFEFF).Trim().Trim([char]34).Trim([char]39);" ^
  "$token=[regex]::Replace($token,'(?i)^(bearer|token)\s+','').Trim();" ^
  "if([string]::IsNullOrWhiteSpace($token)){ Write-Host 'GitHub token file is empty after cleanup.'; exit 10 }" ^
  "$uri='https://api.github.com/repos/%REPO%/zipball/%BRANCH%';" ^
  "$baseHeaders=@{Accept='application/vnd.github+json'; 'X-GitHub-Api-Version'='2022-11-28'; 'User-Agent'='EngineerToolsInstaller'};" ^
  "$downloaded=$false;" ^
  "foreach($scheme in @('Bearer','token')){ try{ $headers=$baseHeaders.Clone(); $headers.Authorization=$scheme + ' ' + $token; Invoke-WebRequest -Uri $uri -Headers $headers -OutFile '%ZIP_FILE%' -UseBasicParsing; $downloaded=$true; break } catch { if($_.Exception.Response -and [int]$_.Exception.Response.StatusCode -eq 401){ continue } throw } }" ^
  "if(-not $downloaded){ Write-Host 'GitHub returned 401 Unauthorized.'; Write-Host 'The token is invalid, expired, or does not have read access to this private repository.'; Write-Host 'Required access: read access to repository contents for Mehdi-Elmi/engineers_Tools.'; exit 11 }" ^
  "Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '%EXTRACT_DIR%' -Force;"

if errorlevel 1 (
    echo Download or extraction failed.
    pause
    exit /b 1
)

if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%" >nul 2>nul

echo Install directory: %INSTALL_DIR%
echo Mirroring GitHub source tree into install directory...

set "SOURCE_DIR="
for /d %%D in ("%EXTRACT_DIR%\*") do set "SOURCE_DIR=%%D"

if not defined SOURCE_DIR (
    echo Installation failed: extracted repository folder was not found.
    pause
    exit /b 1
)

robocopy "%SOURCE_DIR%" "%INSTALL_DIR%" /MIR /XD .venv __pycache__ /XF .install_commit >nul
set "ROBOCOPY_CODE=%ERRORLEVEL%"
if %ROBOCOPY_CODE% GEQ 8 (
    echo Robocopy failed with code %ROBOCOPY_CODE%.
    pause
    exit /b 1
)

for /d /r "%INSTALL_DIR%" %%D in (__pycache__) do if exist "%%D" rmdir /s /q "%%D" >nul 2>nul

if /I not "%LEGACY_INSTALL_DIR%"=="%INSTALL_DIR%" (
    if not exist "%LEGACY_INSTALL_DIR%" mkdir "%LEGACY_INSTALL_DIR%" >nul 2>nul
    > "%LEGACY_INSTALL_DIR%\run_engineers_tools.cmd" echo @echo off
    >> "%LEGACY_INSTALL_DIR%\run_engineers_tools.cmd" echo echo Legacy path detected. Redirecting to %%LOCALAPPDATA%%\EngineerTools...
    >> "%LEGACY_INSTALL_DIR%\run_engineers_tools.cmd" echo call "%%LOCALAPPDATA%%\EngineerTools\run_engineers_tools.cmd"
    >> "%LEGACY_INSTALL_DIR%\run_engineers_tools.cmd" echo exit /b %%ERRORLEVEL%%
    > "%LEGACY_INSTALL_DIR%\install_from_github.cmd" echo @echo off
    >> "%LEGACY_INSTALL_DIR%\install_from_github.cmd" echo echo Legacy path detected. Redirecting to %%LOCALAPPDATA%%\EngineerTools installer source...
    >> "%LEGACY_INSTALL_DIR%\install_from_github.cmd" echo call "%%LOCALAPPDATA%%\EngineerTools\install_from_github.cmd"
    >> "%LEGACY_INSTALL_DIR%\install_from_github.cmd" echo exit /b %%ERRORLEVEL%%
)

set "APP_MODULE_DIR=%INSTALL_DIR%\src\engineers_tools\app"
set "MECH_DIR=%INSTALL_DIR%\modules\mechanics_dynamics_statics"

if not exist "%MECH_DIR%\module_entry.py" (
    echo Installation verification failed.
    echo Missing: %MECH_DIR%\module_entry.py
    pause
    exit /b 1
)

if not exist "%MECH_DIR%\workspace.py" (
    echo Installation verification failed.
    echo Missing: %MECH_DIR%\workspace.py
    pause
    exit /b 1
)

if not exist "%APP_MODULE_DIR%\module_window.py" (
    echo Installation verification failed.
    echo Missing: %APP_MODULE_DIR%\module_window.py
    pause
    exit /b 1
)

if not exist "%APP_MODULE_DIR%\project_file_dialog.py" (
    echo Installation verification failed.
    echo Missing: %APP_MODULE_DIR%\project_file_dialog.py
    pause
    exit /b 1
)

findstr /C:"Mehdi-Elmi/engineers_Tools" "%INSTALL_DIR%\README.md" >nul
if errorlevel 1 (
    echo Installation verification failed.
    echo README.md does not identify the active repository path.
    pause
    exit /b 1
)

findstr /C:"from .workspace import EngineeringDesignWorkspace" "%MECH_DIR%\module_entry.py" >nul
if errorlevel 1 (
    echo Installation verification failed.
    echo module_entry.py does not point to the active EngineeringDesignWorkspace.
    pause
    exit /b 1
)

findstr /C:"class EngineeringDesignWorkspace(ModuleWindow)" "%MECH_DIR%\workspace.py" >nul
if errorlevel 1 (
    echo Installation verification failed.
    echo workspace.py does not define the active EngineeringDesignWorkspace class.
    pause
    exit /b 1
)

findstr /C:"class ModuleWindow(QMainWindow)" "%APP_MODULE_DIR%\module_window.py" >nul
if errorlevel 1 (
    echo Installation verification failed.
    echo module_window.py does not contain the shared active workspace window.
    pause
    exit /b 1
)

findstr /C:"ENGINEER_TOOLS_ACTIVE_UI_2026_06_27_A" "%APP_MODULE_DIR%\module_window.py" >nul
if errorlevel 1 (
    echo Installation verification failed.
    echo module_window.py does not contain the active UI marker.
    pause
    exit /b 1
)

findstr /C:"class ProjectFileDialog(QDialog)" "%APP_MODULE_DIR%\project_file_dialog.py" >nul
if errorlevel 1 (
    echo Installation verification failed.
    echo project_file_dialog.py does not contain the custom project file dialog.
    pause
    exit /b 1
)

findstr /C:"EXPECTED_APP_ROOT" "%INSTALL_DIR%\run_engineers_tools.cmd" >nul
if errorlevel 1 (
    echo Installation verification failed.
    echo run_engineers_tools.cmd does not lock the active install path.
    pause
    exit /b 1
)

if exist "%REMOTE_SHA_FILE%" copy /y "%REMOTE_SHA_FILE%" "%COMMIT_STAMP%" >nul

echo Installation completed.
if exist "%COMMIT_STAMP%" (
    set /p INSTALLED_COMMIT=<"%COMMIT_STAMP%"
    echo Installed commit: !INSTALLED_COMMIT!
)
echo Verified repository: %REPO%
echo Verified install path: %INSTALL_DIR%
echo Verified entry: %MECH_DIR%\module_entry.py
echo Verified workspace: %MECH_DIR%\workspace.py
echo Verified shared window: %APP_MODULE_DIR%\module_window.py
echo Verified file dialog: %APP_MODULE_DIR%\project_file_dialog.py
echo Starting Engineer Tools...
call "%INSTALL_DIR%\run_engineers_tools.cmd"

:finish
endlocal
