@echo off
setlocal enabledelayedexpansion

set "APP_NAME=pluStoreGimp"
set "DISPLAY_NAME=pluStore GIMP"

cls
echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║                                                        ║
echo ║          Desinstalador %DISPLAY_NAME%                 ║
echo ║                                                        ║
echo ╚════════════════════════════════════════════════════════╝
echo.

set "INSTALL_DIR=%LOCALAPPDATA%\%APP_NAME%"
set "START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
set "DESKTOP_DIR=%USERPROFILE%\Desktop"

echo 🗑️  Desinstalando %DISPLAY_NAME%...
echo.

REM Verificar se existe instalação
if not exist "%INSTALL_DIR%" (
    echo ❌ %DISPLAY_NAME% não está instalado
    pause
    exit /b 1
)

REM Mostrar confirmação
echo 📋 Itens que serão removidos:
echo    • Diretório: %INSTALL_DIR%
echo    • Atalho do Menu Iniciar
echo    • Atalho da Área de Trabalho (se existir)
echo    • Ícones personalizados
echo.
choice /C SN /M "Tem certeza que deseja desinstalar? (S/N)"
if errorlevel 2 goto :cancel

REM Remover atalhos
echo.
echo 🔗 Removendo atalhos...
if exist "%START_MENU%\%DISPLAY_NAME%.lnk" (
    del "%START_MENU%\%DISPLAY_NAME%.lnk"
    echo ✅ Atalho do Menu Iniciar removido
)

if exist "%DESKTOP_DIR%\%DISPLAY_NAME%.lnk" (
    del "%DESKTOP_DIR%\%DISPLAY_NAME%.lnk"
    echo ✅ Atalho da Área de Trabalho removido
)

REM Remover diretório de instalação
echo 📁 Removendo arquivos...
if exist "%INSTALL_DIR%" (
    rmdir /S /Q "%INSTALL_DIR%"
    if !errorlevel! == 0 (
        echo ✅ Diretório removido: %INSTALL_DIR%
    ) else (
        echo ⚠️  Aviso: Não foi possível remover completamente o diretório
        echo    Você pode remover manualmente: %INSTALL_DIR%
    )
)

echo.
echo ✅ %DISPLAY_NAME% foi desinstalado com sucesso!
echo.
pause
exit /b 0

:cancel
echo.
echo Desinstalação cancelada
pause
exit /b 0
