@echo off
REM Instalador do pluStoreGimp para Windows

cls
echo ============================================================
echo.
echo          Instalador pluStoreGimp v2.0
echo          Gerenciador de Plugins para GIMP
echo.
echo ============================================================
echo.

echo Instalando pluStoreGimp...
echo.

REM Define diretórios
set "INSTALL_DIR=%LOCALAPPDATA%\pluStoreGimp"
set "START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"

REM Cria diretório de instalação
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Copia executável
echo Copiando arquivos...
copy /Y pluStoreGimp.exe "%INSTALL_DIR%\" >nul

REM Cria atalho no menu iniciar
echo Criando atalho...
powershell -Command "$WS = New-Object -ComObject WScript.Shell; $Shortcut = $WS.CreateShortcut('%START_MENU%\pluStore GIMP.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\pluStoreGimp.exe'; $Shortcut.Save()"

REM Adiciona ao PATH (opcional)
echo.
echo ============================================================
echo.
echo          Instalacao Concluida!
echo.
echo ============================================================
echo.
echo Para executar:
echo   - Procure "pluStore GIMP" no menu Iniciar
echo   - Ou execute: %INSTALL_DIR%\pluStoreGimp.exe
echo.
pause
