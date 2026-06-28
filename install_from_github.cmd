@echo off
setlocal EnableExtensions EnableDelayedExpansion

echo Engineer Tools installer build: 2026-06-28 robust-verification-2

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
  "$utf8NoBom=[System.Text.UTF8Encoding]::new($false);" ^
  "$token=[System.IO.File]::ReadAllText($env:TOKEN_FILE,[System.Text.Encoding]::UTF8);" ^
  "$token=$token.Trim([char]0xFEFF).Trim().Trim([char]34).Trim([char]39);" ^
  "$token=[regex]::Replace($token,'(?i)^(bearer|token)\s+','').Trim();" ^
  "if([string]::IsNullOrWhiteSpace($token)){ Write-Host 'GitHub token file is empty after cleanup.'; exit 10 }" ^
  "$baseHeaders=@{Accept='application/vnd.github+json'; 'X-GitHub-Api-Version'='2022-11-28'; 'User-Agent'='EngineerToolsInstaller'};" ^
  "$branchUri='https://api.github.com/repos/%REPO%/branches/%BRANCH%';" ^
  "$branchData=$null;" ^
  "foreach($scheme in @('Bearer','token')){ try{ $headers=$baseHeaders.Clone(); $headers.Authorization=$scheme + ' ' + $token; $response=Invoke-WebRequest -Uri $branchUri -Headers $headers -UseBasicParsing; $branchData=$response.Content | ConvertFrom-Json; break } catch { if($_.Exception.Response -and [int]$_.Exception.Response.StatusCode -eq 401){ continue } throw } }" ^
  "if($null -eq $branchData){ Write-Host 'GitHub returned 401 Unauthorized.'; Write-Host 'The token is invalid, expired, or does not have read access to this private repository.'; exit 11 }" ^
  "$remoteSha=[string]$branchData.commit.sha;" ^
  "[System.IO.File]::WriteAllText($env:REMOTE_SHA_FILE,$remoteSha,$utf8NoBom);" ^
  "$localSha=''; if(Test-Path $env:COMMIT_STAMP){ $localSha=[System.IO.File]::ReadAllText($env:COMMIT_STAMP,[System.Text.Encoding]::UTF8).Trim([char]0xFEFF).Trim() }" ^
  "$runFile=Join-Path $env:INSTALL_DIR 'run_engineers_tools.cmd';" ^
  "$mainFile=Join-Path $env:INSTALL_DIR 'src\engineers_tools\main.py';" ^
  "$moduleWindow=Join-Path $env:INSTALL_DIR 'src\engineers_tools\app\module_window.py';" ^
  "$workspace=Join-Path $env:INSTALL_DIR 'modules\mechanics_dynamics_statics\workspace.py';" ^
  "$installOk=(Test-Path $runFile) -and (Test-Path $mainFile) -and (Test-Path $moduleWindow) -and (Test-Path $workspace);" ^
  "if($installOk -and $localSha -eq $remoteSha){ [System.IO.File]::WriteAllText($env:UPDATE_STATUS_FILE,'UP_TO_DATE',[System.Text.Encoding]::ASCII) } else { [System.IO.File]::WriteAllText($env:UPDATE_STATUS_FILE,'NEED_UPDATE',[System.Text.Encoding]::ASCII) }"

if errorlevel 1 (
    echo Version check failed.
    pause
    exit /b 1
)

set "UPDATE_STATUS=NEED_UPDATE"
if exist "%UPDATE_STATUS_FILE%" set /p UPDATE_STATUS=<"%UPDATE_STATUS_FILE%"

if /I "%UPDATE_STATUS%"=="UP_TO_DATE" (
    echo Engineer Tools is already up to date.
    echo Starting Engineer Tools...
    call "%INSTALL_DIR%\run_engineers_tools.cmd"
    goto :finish
)

if exist "%ZIP_FILE%" del /f /q "%ZIP_FILE%" >nul 2>nul
if exist "%EXTRACT_DIR%" rmdir /s /q "%EXTRACT_DIR%" >nul 2>nul
mkdir "%EXTRACT_DIR%" >nul 2>nul

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "$token=[System.IO.File]::ReadAllText($env:TOKEN_FILE,[System.Text.Encoding]::UTF8);" ^
  "$token=$token.Trim([char]0xFEFF).Trim().Trim([char]34).Trim([char]39);" ^
  "$token=[regex]::Replace($token,'(?i)^(bearer|token)\s+','').Trim();" ^
  "if([string]::IsNullOrWhiteSpace($token)){ Write-Host 'GitHub token file is empty after cleanup.'; exit 10 }" ^
  "$uri='https://api.github.com/repos/%REPO%/zipball/%BRANCH%';" ^
  "$baseHeaders=@{Accept='application/vnd.github+json'; 'X-GitHub-Api-Version'='2022-11-28'; 'User-Agent'='EngineerToolsInstaller'};" ^
  "$downloaded=$false;" ^
  "foreach($scheme in @('Bearer','token')){ try{ $headers=$baseHeaders.Clone(); $headers.Authorization=$scheme + ' ' + $token; Invoke-WebRequest -Uri $uri -Headers $headers -OutFile '%ZIP_FILE%' -UseBasicParsing; $downloaded=$true; break } catch { if($_.Exception.Response -and [int]$_.Exception.Response.StatusCode -eq 401){ continue } throw } }" ^
  "if(-not $downloaded){ Write-Host 'GitHub returned 401 Unauthorized.'; Write-Host 'Required access: read access to repository contents for %REPO%.'; exit 11 }" ^
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
)

set "VERIFY_FAILED=0"
if not exist "%INSTALL_DIR%\README.md" echo VERIFY FAILED: missing README.md & set "VERIFY_FAILED=1"
if not exist "%INSTALL_DIR%\run_engineers_tools.cmd" echo VERIFY FAILED: missing run_engineers_tools.cmd & set "VERIFY_FAILED=1"
if not exist "%INSTALL_DIR%\requirements.txt" echo VERIFY FAILED: missing requirements.txt & set "VERIFY_FAILED=1"
if not exist "%INSTALL_DIR%\src\engineers_tools\main.py" echo VERIFY FAILED: missing src\engineers_tools\main.py & set "VERIFY_FAILED=1"
if not exist "%INSTALL_DIR%\src\engineers_tools\app\launcher.py" echo VERIFY FAILED: missing src\engineers_tools\app\launcher.py & set "VERIFY_FAILED=1"
if not exist "%INSTALL_DIR%\src\engineers_tools\app\module_window.py" echo VERIFY FAILED: missing src\engineers_tools\app\module_window.py & set "VERIFY_FAILED=1"
if not exist "%INSTALL_DIR%\src\engineers_tools\app\project_file_dialog.py" echo VERIFY FAILED: missing src\engineers_tools\app\project_file_dialog.py & set "VERIFY_FAILED=1"
if not exist "%INSTALL_DIR%\modules\mechanics_dynamics_statics\module_entry.py" echo VERIFY FAILED: missing modules\mechanics_dynamics_statics\module_entry.py & set "VERIFY_FAILED=1"
if not exist "%INSTALL_DIR%\modules\mechanics_dynamics_statics\workspace.py" echo VERIFY FAILED: missing modules\mechanics_dynamics_statics\workspace.py & set "VERIFY_FAILED=1"

if "%VERIFY_FAILED%"=="1" goto :verify_failed

if exist "%REMOTE_SHA_FILE%" copy /y "%REMOTE_SHA_FILE%" "%COMMIT_STAMP%" >nul

echo Installation completed.
if exist "%COMMIT_STAMP%" (
    set /p INSTALLED_COMMIT=<"%COMMIT_STAMP%"
    echo Installed commit: !INSTALLED_COMMIT!
)
echo Verified repository: %REPO%
echo Verified install path: %INSTALL_DIR%
echo Starting Engineer Tools...
call "%INSTALL_DIR%\run_engineers_tools.cmd"
goto :finish

:verify_failed
echo Installation verification failed.
echo The required files listed above must exist after mirroring GitHub source tree.
pause
exit /b 1

:finish
endlocal
