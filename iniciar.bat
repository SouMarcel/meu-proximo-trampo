@echo off
rem Inicia o meu-proximo-trampo com dois cliques: o mesmo que "python iniciar.py", com as mesmas opções.
rem A ferramenta roda nesta janela; feche a janela (ou Ctrl+C) para parar.
chcp 65001 >nul
cd /d "%~dp0"
set "PY="
rem py -3 é o lançador oficial; "python" pode ser só o atalho da Microsoft Store, por isso testa a execução
py -3 --version >nul 2>&1 && set "PY=py -3"
if not defined PY python --version >nul 2>&1 && set "PY=python"
if not defined PY (
  echo Não encontrei o Python 3.10 ou mais novo neste computador.
  echo Baixe em https://www.python.org/downloads/ e, na instalação, marque "Add python.exe to PATH".
  pause
  exit /b 2
)
%PY% iniciar.py %*
set "CODIGO=%ERRORLEVEL%"
if not "%CODIGO%"=="0" pause
exit /b %CODIGO%
