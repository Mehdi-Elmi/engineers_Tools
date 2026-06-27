@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "REPO=Mehdi-Elmi/engineers_Tools"
set "BRANCH=main"
set "TOKEN_FILE=%USERPROFILE%\Desktop\token.txt"
set "FALLBACK_TOKEN_FILE=%USERPROFILE%\Desktop\testdoctoken.txt"
set "INSTALL_DIR=%LOCALAPPDATA%\EngineerTools"
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
  "[System.IO.File]::WriteAllText($env:REMOTE_SHA_FILE,$remoteSha,[System.Text.Encoding]::UTF8);" ^
  "$localSha=''; if(Test-Path $env:COMMIT_STAMP){ $localSha=[System.IO.File]::ReadAllText($env:COMMIT_STAMP,[System.Text.Encoding]::UTF8).Trim() }" ^
  "$runFile=Join-Path $env:INSTALL_DIR 'run_engineers_tools.cmd';" ^
  "$force=$env:FORCE_UPDATE -eq '1';" ^
  "if((Test-Path $runFile) -and -not $force -and $localSha -eq $remoteSha){ [System.IO.File]::WriteAllText($env:UPDATE_STATUS_FILE,'UP_TO_DATE',[System.Text.Encoding]::ASCII) } else { [System.IO.File]::WriteAllText($env:UPDATE_STATUS_FILE,'NEED_UPDATE',[System.Text.Encoding]::ASCII) }"

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

for /d %%D in ("%EXTRACT_DIR%\*") do (
    xcopy "%%D\*" "%INSTALL_DIR%\" /E /I /Y >nul
)

if exist "%REMOTE_SHA_FILE%" copy /y "%REMOTE_SHA_FILE%" "%COMMIT_STAMP%" >nul

echo Installation completed.
call "%INSTALL_DIR%\run_engineers_tools.cmd"

:finish
endlocal
