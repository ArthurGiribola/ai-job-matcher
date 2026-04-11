@echo off
title AI Job Matcher
echo.
echo  ========================================
echo   AI Job Matcher - Iniciando...
echo  ========================================
echo.

cd /d "%~dp0"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo ERRO: ambiente virtual nao encontrado!
    pause
    exit
)

echo Abrindo no navegador...
streamlit run frontend/app.py

pause
