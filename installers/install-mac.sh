#!/bin/bash
# Instalador do pluStoreGimp para macOS

set -e  # Sai automaticamente em caso de erro

clear
echo "╔════════════════════════════════════════════════════════╗"
echo "║                                                        ║"
echo "║          Instalador pluStoreGimp v1.0                 ║"
echo "║          Gerenciador de Plugins para GIMP             ║"
echo "║                                                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Configurações
VERSION="1.0"
APP_NAME="pluStoreGimp"
DISPLAY_NAME="pluStore GIMP"
INSTALL_DIR="$HOME/Applications/$APP_NAME"
BIN_DIR="$HOME/.local/bin"
APP_DIR="$HOME/Applications"
LOG_FILE="/tmp/plustoregimp_install.log"

# Função para log
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

echo "📦 Iniciando instalação do $DISPLAY_NAME v$VERSION..."
echo "📝 Log: $LOG_FILE"
log "Iniciando instalação do $DISPLAY_NAME v$VERSION"

# Verificar arquivo executável
if [ ! -f "pluStoreGimp" ]; then
    echo "❌ Erro: Arquivo 'pluStoreGimp' não encontrado!"
    echo "   Execute o instalador no mesmo diretório do executável"
    log "ERRO: Arquivo pluStoreGimp não encontrado"
    exit 1
fi

# Verificar arquitetura
ARCH=$(uname -m)
echo "🔍 Arquitetura: $ARCH"
log "Arquitetura detectada: $ARCH"

# Verificar versão do macOS
MACOS_VERSION=$(sw_vers -productVersion)
echo "🔍 macOS: $MACOS_VERSION"
log "macOS version: $MACOS_VERSION"

# Verifica Homebrew
echo ""
echo "🔍 Verificando dependências do sistema..."

if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew não encontrado"
    echo "   Instale com:"
    echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    log "ERRO: Homebrew não encontrado"
    exit 1
fi

echo "✅ Homebrew encontrado"

# Instala/atualiza dependências
install_dependencies() {
    echo "📦 Verificando e instalando dependências..."
    
    # Atualizar Homebrew primeiro
    brew update >> "$LOG_FILE" 2>&1
    
    # Verificar e instalar Python se necessário
    if ! command -v python3 &> /dev/null; then
        echo "   📦 Instalando Python 3..."
        brew install python >> "$LOG_FILE" 2>&1
    fi
    
    # Dependências principais
    local deps=("pygobject3" "gtk+3" "adwaita-icon-theme")
    
    for dep in "${deps[@]}"; do
        if ! brew list "$dep" &>/dev/null; then
            echo "   📦 Instalando $dep..."
            brew install "$dep" >> "$LOG_FILE" 2>&1
        else
            echo "   ✅ $dep já instalado"
        fi
    done
    
    # Instalar pycairo via pip se necessário
    if ! python3 -c "import cairo" &> /dev/null; then
        echo "   📦 Instalando pycairo..."
        pip3 install pycairo >> "$LOG_FILE" 2>&1
    fi
}

install_dependencies
echo "✅ Dependências do sistema OK"
log "Dependências instaladas/verificadas"

# Criar estrutura de diretórios
echo ""
echo "📁 Criando estrutura de diretórios..."
mkdir -p "$INSTALL_DIR" "$BIN_DIR"
log "Diretórios criados: $INSTALL_DIR, $BIN_DIR"

# Backup de instalação anterior
if [ -f "$INSTALL_DIR/pluStoreGimp" ]; then
    echo "🔄 Fazendo backup da instalação anterior..."
    cp "$INSTALL_DIR/pluStoreGimp" "$INSTALL_DIR/pluStoreGimp.backup" 2>/dev/null
    log "Backup da instalação anterior criado"
fi

# Copiar executável
echo "📂 Copiando arquivos..."
if cp "pluStoreGimp" "$INSTALL_DIR/"; then
    chmod +x "$INSTALL_DIR/pluStoreGimp"
    echo "✅ Executável copiado: $INSTALL_DIR/pluStoreGimp"
    log "Executável copiado para $INSTALL_DIR/"
else
    echo "❌ Erro ao copiar executável!"
    log "ERRO: Falha ao copiar executável"
    exit 1
fi

# Copiar recursos se existirem
if [ -d "assets" ]; then
    echo "📁 Copiando recursos..."
    cp -r "assets" "$INSTALL_DIR/" 2>/dev/null
    log "Recursos copiados"
fi

# Criar link simbólico
echo "🔗 Criando link simbólico..."
ln -sf "$INSTALL_DIR/pluStoreGimp" "$BIN_DIR/plustoregimp"
log "Link simbólico criado: $BIN_DIR/plustoregimp"

# Instalar ícones e criar aplicativo
echo "🎨 Configurando ícones e aplicativo..."
create_macos_app() {
    local app_path="$APP_DIR/$DISPLAY_NAME.app"
    local contents_dir="$app_path/Contents"
    local macos_dir="$contents_dir/MacOS"
    local resources_dir="$contents_dir/Resources"
    
    # Criar estrutura do aplicativo
    mkdir -p "$macos_dir" "$resources_dir"
    
    # Script principal do aplicativo
    cat > "$macos_dir/$APP_NAME" << 'SCRIPT_EOF'
#!/bin/bash
exec "$HOME/Applications/pluStoreGimp/pluStoreGimp"
SCRIPT_EOF
    
    chmod +x "$macos_dir/$APP_NAME"
    
    # Verificar se existe ícone personalizado
    local icon_source=""
    if [ -f "assets/icons/macos/app.icns" ]; then
        icon_source="assets/icons/macos/app.icns"
        echo "   ✅ Usando ícone personalizado"
    elif [ -f "$INSTALL_DIR/assets/icons/macos/app.icns" ]; then
        icon_source="$INSTALL_DIR/assets/icons/macos/app.icns"
        echo "   ✅ Usando ícone personalizado (do diretório de instalação)"
    else
        echo "   ℹ️  Ícone personalizado não encontrado, usando ícone padrão"
    fi
    
    # Copiar ícone se existir
    if [ -n "$icon_source" ] && [ -f "$icon_source" ]; then
        cp "$icon_source" "$resources_dir/app.icns"
        echo "   ✅ Ícone copiado para o aplicativo"
    fi
    
    # Criar Info.plist
    cat > "$contents_dir/Info.plist" << PLIST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>$DISPLAY_NAME</string>
    <key>CFBundleDisplayName</key>
    <string>$DISPLAY_NAME</string>
    <key>CFBundleIdentifier</key>
    <string>com.plustore.gimp</string>
    <key>CFBundleVersion</key>
    <string>$VERSION</string>
    <key>CFBundleShortVersionString</key>
    <string>$VERSION</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>CFBundleExecutable</key>
    <string>$APP_NAME</string>
    <key>CFBundleDevelopmentRegion</key>
    <string>en</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
PLIST_EOF

    # Adicionar ícone se existir
    if [ -f "$resources_dir/app.icns" ]; then
        cat >> "$contents_dir/Info.plist" << PLIST_EOF
    <key>CFBundleIconFile</key>
    <string>app.icns</string>
PLIST_EOF
    fi

    # Finalizar Info.plist
    cat >> "$contents_dir/Info.plist" << PLIST_EOF
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSHumanReadableCopyright</key>
    <string>Copyright © 2024 pluStore GIMP. Todos os direitos reservados.</string>
</dict>
</plist>
PLIST_EOF

    echo "   ✅ Aplicativo criado: $app_path"
}

create_macos_app
log "Aplicativo macOS criado com ícones"

# Adicionar ao PATH se necessário
echo "🛠️  Configurando ambiente..."
SHELL_RC="$HOME/.zshrc"
if [ -n "$BASH_VERSION" ]; then
    SHELL_RC="$HOME/.bash_profile"
fi

if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "📝 Adicionando ~/.local/bin ao PATH em $SHELL_RC"
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
    export PATH="$HOME/.local/bin:$PATH"
    echo "⚠️  Reinicie o terminal ou execute: source $SHELL_RC"
    log "PATH atualizado em $SHELL_RC"
fi

# Verificar se o GIMP está instalado
echo ""
echo "🔍 Verificando se o GIMP está instalado..."
if mdfind "kMDItemKind == 'Application'" | grep -i gimp > /dev/null; then
    echo "✅ GIMP encontrado no sistema"
    log "GIMP encontrado no sistema"
elif [ -d "/Applications/GIMP.app" ]; then
    echo "✅ GIMP encontrado em /Applications"
    log "GIMP encontrado em /Applications"
else
    echo "⚠️  GIMP não encontrado. O $DISPLAY_NAME requer o GIMP instalado."
    echo "   Baixe em: https://www.gimp.org/downloads/"
    log "AVISO: GIMP não encontrado"
fi

# Verificação final
echo ""
echo "🔍 Verificando instalação..."
if [ -x "$INSTALL_DIR/pluStoreGimp" ] && [ -L "$BIN_DIR/plustoregimp" ]; then
    echo "✅ Instalação verificada com sucesso"
    log "Instalação verificada com sucesso"
else
    echo "⚠️  Possíveis problemas na instalação"
    log "AVISO: Possíveis problemas na instalação"
fi

# Verificar se o aplicativo foi criado
if [ -d "$APP_DIR/$DISPLAY_NAME.app" ]; then
    echo "✅ Aplicativo criado no Launchpad"
    log "Aplicativo criado no Launchpad"
fi

# Mensagem final
echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║                                                        ║"
echo "║          🎉 Instalação Concluída! 🎉                  ║"
echo "║                                                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "📋 Resumo da instalação:"
echo "   • Executável: $INSTALL_DIR/pluStoreGimp"
echo "   • Comando: plustoregimp"
echo "   • Aplicativo: $APP_DIR/$DISPLAY_NAME.app"
if [ -f "assets/icons/macos/app.icns" ] || [ -f "$INSTALL_DIR/assets/icons/macos/app.icns" ]; then
    echo "   • Ícone: Personalizado ✅"
else
    echo "   • Ícone: Padrão do sistema"
fi
echo ""
echo "🚀 Para executar:"
echo "   - Terminal: plustoregimp"
echo "   - Launchpad: Procure '$DISPLAY_NAME'"
echo "   - Finder: Navegue até $APP_DIR/$DISPLAY_NAME.app"
echo ""
echo "🔧 Para desinstalar, execute:"
echo "   curl -fsSL https://raw.githubusercontent.com/seu-usuario/pluStoreGimp/main/uninstall_macos.sh | bash"
echo ""
echo "🐛 Problemas? Verifique o log: $LOG_FILE"
echo ""
