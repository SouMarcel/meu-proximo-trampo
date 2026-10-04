@echo off
rem Abre o dashboard (http://127.0.0.1:8765). Feche a janela "Dashboard de Candidaturas" para parar.
cd /d "%~dp0.."
set "PY=python"
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"
start "Dashboard de Candidaturas" /min "%PY%" "dash\servidor.py" %*
