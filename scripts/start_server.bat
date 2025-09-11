@echo off
REM Simple wrapper to start the Flask backend using the PowerShell helper
REM It ensures the working directory is the repository root, then runs the PS1 with any passed args

SETLOCAL ENABLEDELAYEDEXPANSION

REM %~dp0 is the directory of this .bat (scripts\)
set SCRIPT_DIR=%~dp0
REM Go to repo root (parent of scripts\)
for %%I in ("%SCRIPT_DIR%..") do set REPO_ROOT=%%~fI

pushd "%REPO_ROOT%"

REM Run PowerShell script with ExecutionPolicy bypass and forward all arguments
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%REPO_ROOT%\scripts\start_server.ps1" %*

popd

ENDLOCAL
