I created the PowerShell helper at 
scripts/start_server.ps1
.

How to use

From the repo root:
PowerShell:
.\scripts\start_server.ps1
To force a fresh venv: .\scripts\start_server.ps1 -RecreateVenv
To change port: .\scripts\start_server.ps1 -Port 5001
Notes

The script will:
Ensure .venv/ exists (or recreate it with -RecreateVenv).
Upgrade pip and install from 
requirements.txt
.
Start the backend via .venv\Scripts\python.exe and open http://localhost:5001/api/health.
Keep the terminal open; Ctrl+C stops the server.
If you get an execution policy warning

Unblock once:
Unblock-File .\scripts\start_server.ps1
Or run in the current process ignoring policy:
powershell -ExecutionPolicy Bypass -File .\scripts\start_server.ps1




I created the Windows batch wrapper at 
scripts/start_server.bat
.

How to use

Double-click: 
scripts\start_server.bat
Or from a terminal (repo root or anywhere):
scripts\start_server.bat
With options (passed through to the PowerShell script):
scripts\start_server.bat -RecreateVenv
scripts\start_server.bat -Port 5001
What it does

Changes directory to the repository root.
Invokes 
scripts\start_server.ps1
 with ExecutionPolicy Bypass, forwarding any arguments.
The PS1 script ensures .venv/ exists, upgrades pip, installs 
requirements.txt
, and starts 
api\server.py
 using .venv\Scripts\python.exe. It also opens http://localhost:5001/api/health.
Notes

Keep the window open; Ctrl+C stops the server.
If you prefer a desktop shortcut, create a shortcut to 
scripts\start_server.bat
 and set “Start in” to your repo root.