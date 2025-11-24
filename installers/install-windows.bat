@echo off
REM Instalador do pluStoreGimp para Windows
setlocal enabledelayedexpansion

set "VERSION=1.0"
set "APP_NAME=pluStoreGimp"
set "DISPLAY_NAME=pluStore GIMP"

cls
echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║                                                        ║
echo ║          Instalador pluStoreGimp v%VERSION%                 ║
echo ║          Gerenciador de Plugins para GIMP             ║
echo ║                                                        ║
echo ╚════════════════════════════════════════════════════════╝
echo.

REM Verificar se está executando como administrador
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ⚠️  AVISO: Executando como Administrador
    echo    Recomendado executar como usuário normal
    echo.
    choice /C SN /M "Deseja continuar mesmo assim? (S/N)"
    if errorlevel 2 goto :cancel
)

REM Verificar se o arquivo existe
if not exist "pluStoreGimp.exe" (
    echo ❌ ERRO: Arquivo pluStoreGimp.exe não encontrado!
    echo.
    echo Certifique-se de executar o instalador no mesmo diretório
    echo do arquivo pluStoreGimp.exe
    echo.
    pause
    exit /b 1
)

echo 📦 Iniciando instalação do %DISPLAY_NAME%...
echo.

REM Define diretórios
set "INSTALL_DIR=%LOCALAPPDATA%\%APP_NAME%"
set "START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
set "DESKTOP_DIR=%USERPROFILE%\Desktop"
set "LOG_FILE=%TEMP%\%APP_NAME%_install.log"

echo 📝 Log: %LOG_FILE%
echo %date% %time% - Iniciando instalação >> "%LOG_FILE%"

REM Criar diretório de instalação
echo 📁 Criando diretório de instalação...
if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
    if !errorlevel! neq 0 (
        echo ❌ Erro ao criar diretório: %INSTALL_DIR%
        goto :error
    )
    echo ✅ Diretório criado: %INSTALL_DIR%
) else (
    echo 🔄 Diretório já existe, fazendo backup...
    if exist "%INSTALL_DIR%\pluStoreGimp.exe" (
        copy "%INSTALL_DIR%\pluStoreGimp.exe" "%INSTALL_DIR%\pluStoreGimp.exe.backup" >nul
    )
)

REM Copiar executável
echo 📂 Copiando arquivos...
copy /Y "pluStoreGimp.exe" "%INSTALL_DIR%\" >nul
if !errorlevel! neq 0 (
    echo ❌ Erro ao copiar arquivo executável
    goto :error
)
echo ✅ Executável copiado

REM Copiar recursos se existirem
if exist "assets" (
    echo 📁 Copiando recursos...
    xcopy "assets" "%INSTALL_DIR%\assets\" /E /I /Y >nul 2>&1
    echo ✅ Recursos copiados
)

REM Verificar e copiar ícone
set "ICON_PATH=%INSTALL_DIR%\app.ico"
set "HAS_CUSTOM_ICON=0"

if exist "assets\icons\windows\app.ico" (
    echo 🎨 Copiando ícone personalizado...
    copy "assets\icons\windows\app.ico" "%ICON_PATH%" >nul
    if !errorlevel! == 0 (
        set "HAS_CUSTOM_ICON=1"
        echo ✅ Ícone personalizado copiado
    ) else (
        echo ⚠️  Não foi possível copiar o ícone personalizado
    )
) else (
    echo ℹ️  Ícone personalizado não encontrado, usando ícone padrão
)

REM Criar atalho no Menu Iniciar
echo 🔗 Criando atalho no Menu Iniciar...
set "SHORTCUT_PATH=%START_MENU%\%DISPLAY_NAME%.lnk"

if !HAS_CUSTOM_ICON! == 1 (
    REM Criar atalho com ícone personalizado
    powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%'); $Shortcut.TargetPath = '%INSTALL_DIR%\pluStoreGimp.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = 'Gerenciador de Plugins para GIMP'; $Shortcut.IconLocation = '%ICON_PATH%'; $Shortcut.Save()" >nul
) else (
    REM Criar atalho sem ícone personalizado
    powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%'); $Shortcut.TargetPath = '%INSTALL_DIR%\pluStoreGimp.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = 'Gerenciador de Plugins para GIMP'; $Shortcut.Save()" >nul
)

if exist "%SHORTCUT_PATH%" (
    echo ✅ Atalho do Menu Iniciar criado
) else (
    echo ⚠️  Aviso: Não foi possível criar atalho no Menu Iniciar
)

REM Oferecer criar atalho na Área de Trabalho
echo.
choice /C SN /M "Deseja criar atalho na Área de Trabalho? (S/N)"
if errorlevel 2 goto :no_desktop

echo 🔗 Criando atalho na Área de Trabalho...
set "DESKTOP_SHORTCUT=%DESKTOP_DIR%\%DISPLAY_NAME%.lnk"

if !HAS_CUSTOM_ICON! == 1 (
    REM Criar atalho com ícone personalizado
    powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP_SHORTCUT%'); $Shortcut.TargetPath = '%INSTALL_DIR%\pluStoreGimp.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = 'Gerenciador de Plugins para GIMP'; $Shortcut.IconLocation = '%ICON_PATH%'; $Shortcut.Save()" >nul
) else (
    REM Criar atalho sem ícone personalizado
    powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP_SHORTCUT%'); $Shortcut.TargetPath = '%INSTALL_DIR%\pluStoreGimp.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = 'Gerenciador de Plugins para GIMP'; $Shortcut.Save()" >nul
)

if exist "%DESKTOP_SHORTCUT%" (
    echo ✅ Atalho da Área de Trabalho criado
) else (
    echo ⚠️  Aviso: Não foi possível criar atalho na Área de Trabalho
)

:no_desktop

REM Verificar se o GIMP está instalado
echo.
echo 🔍 Verificando se o GIMP está instalado...
reg query "HKLM\SOFTWARE\GIMP" >nul 2>&1
if !errorlevel! == 0 (
    echo ✅ GIMP encontrado (registro do sistema)
) else (
    reg query "HKCU\SOFTWARE\GIMP" >nul 2>&1
    if !errorlevel! == 0 (
        echo ✅ GIMP encontrado (registro do usuário)
    ) else (
        where gimp-2.99 >nul 2>&1
        if !errorlevel! == 0 (
            echo ✅ GIMP encontrado (PATH)
        ) else (
            where gimp-2.10 >nul 2>&1
            if !errorlevel! == 0 (
                echo ✅ GIMP encontrado (PATH)
            ) else (
                echo ⚠️  GIMP não encontrado. O %DISPLAY_NAME% requer o GIMP instalado.
            )
        )
    )
)

REM Atualizar log
echo %date% %time% - Instalação concluída com sucesso >> "%LOG_FILE%"

REM Mensagem final
echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║                                                        ║
echo ║          ✅ Instalação Concluída! ✅                  ║
echo ║                                                        ║
echo ╚════════════════════════════════════════════════════════╝
echo.
echo 📋 Resumo da instalação:
echo    • Local: %INSTALL_DIR%
echo    • Menu Iniciar: "%DISPLAY_NAME%"
if !HAS_CUSTOM_ICON! == 1 (
    echo    • Ícone: Personalizado ✅
) else (
    echo    • Ícone: Padrão do sistema
)
echo.
echo 🚀 Para executar:
echo    - Menu Iniciar: Procure "%DISPLAY_NAME%"
echo    - Área de Trabalho: Atalho "%DISPLAY_NAME%" (se criado)
echo    - Executar: %INSTALL_DIR%\pluStoreGimp.exe
echo.
echo 🔧 Para desinstalar, execute uninstall_plustoregimp.bat
echo.
pause
exit /b 0

:error
echo.
echo ❌ Ocorreu um erro durante a instalação
echo 📝 Verifique o log: %LOG_FILE%
echo %date% %time% - ERRO na instalação >> "%LOG_FILE%"
pause
exit /b 1

:cancel
echo.
echo Instalação cancelada pelo usuário
pause
exit /b 0
