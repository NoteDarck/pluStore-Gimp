#!/bin/bash
# Instalador do pluStoreGimp para Linux

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
INSTALL_DIR="$HOME/.local/share/$APP_NAME"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICONS_DIR="$HOME/.local/share/icons/hicolor"
LOG_FILE="/tmp/plustoregimp_install.log"

# Função para log
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Verifica se está rodando como root
if [ "$EUID" -eq 0 ]; then 
    echo "❌ Erro: Não execute como root/sudo"
    echo "   O instalador configura para o usuário atual"
    exit 1
fi

# Verifica se o script está no diretório correto
if [ ! -f "pluStoreGimp" ]; then
    echo "❌ Erro: Arquivo 'pluStoreGimp' não encontrado!"
    echo "   Execute o instalador no mesmo diretório do executável"
    exit 1
fi

echo "📦 Iniciando instalação do $DISPLAY_NAME v$VERSION..."
echo "📝 Log: $LOG_FILE"
log "Iniciando instalação do $DISPLAY_NAME v$VERSION"

# Detectar distribuição
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "$ID"
    else
        echo "unknown"
    fi
}

DISTRO=$(detect_distro)

# Instala dependências do sistema
echo ""
echo "🔍 Verificando dependências do sistema..."

install_dependencies() {
    case "$DISTRO" in
        ubuntu|debian|linuxmint)
            echo "   📋 Distribuição: Ubuntu/Debian"
            sudo apt-get update >> "$LOG_FILE" 2>&1
            sudo apt-get install -y \
                python3-gi \
                python3-gi-cairo \
                gir1.2-gtk-3.0 \
                python3-requests \
                python3-pip >> "$LOG_FILE" 2>&1
            ;;
        fedora|rhel|centos)
            echo "   📋 Distribuição: Fedora/RHEL/CentOS"
            sudo dnf install -y \
                python3-gobject \
                gtk3 \
                python3-requests \
                python3-pip >> "$LOG_FILE" 2>&1
            ;;
        arch|manjaro)
            echo "   📋 Distribuição: Arch/Manjaro"
            sudo pacman -Sy --noconfirm \
                python-gobject \
                gtk3 \
                python-requests \
                python-pip >> "$LOG_FILE" 2>&1
            ;;
        *)
            echo "   ⚠️  Distribuição não identificada, tentando instalar genérico..."
            ;;
    esac
}

install_dependencies
echo "✅ Dependências do sistema OK"
log "Dependências instaladas"

# Cria diretórios
echo ""
echo "📁 Criando estrutura de diretórios..."
mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$DESKTOP_DIR" "$ICONS_DIR"
log "Diretórios criados: $INSTALL_DIR"

# Backup de instalação anterior se existir
if [ -f "$INSTALL_DIR/pluStoreGimp" ]; then
    echo "   🔄 Fazendo backup da instalação anterior..."
    cp "$INSTALL_DIR/pluStoreGimp" "$INSTALL_DIR/pluStoreGimp.backup" 2>/dev/null
    log "Backup da instalação anterior criado"
fi

# Copia executável
echo "📂 Copiando arquivos..."
if cp "pluStoreGimp" "$INSTALL_DIR/"; then
    chmod +x "$INSTALL_DIR/pluStoreGimp"
    echo "   ✅ Executável copiado: $INSTALL_DIR/pluStoreGimp"
    log "Executável copiado para $INSTALL_DIR/"
else
    echo "❌ Erro ao copiar executável!"
    log "ERRO: Falha ao copiar executável"
    exit 1
fi

# Copiar recursos adicionais se existirem
if [ -d "assets" ]; then
    echo "   📁 Copiando recursos..."
    cp -r "assets" "$INSTALL_DIR/" 2>/dev/null
    log "Recursos copiados"
fi

# Instalar ícones
echo "🎨 Instalando ícones..."
install_icons() {
    # Verifica se existem ícones personalizados
    if [ -d "assets/icons/linux" ]; then
        echo "   📁 Copiando ícones personalizados..."
        
        # Copiar ícones para cada tamanho
        for size in 16x16 32x32 48x48 64x64 128x128 256x256; do
            if [ -f "assets/icons/linux/$size/plustoregimp.png" ]; then
                mkdir -p "$ICONS_DIR/$size/apps"
                cp "assets/icons/linux/$size/plustoregimp.png" "$ICONS_DIR/$size/apps/"
                echo "     ✅ Ícone $size instalado"
            fi
        done
        
        # Ícone scalable (SVG)
        if [ -f "assets/icons/linux/scalable/plustoregimp.svg" ]; then
            mkdir -p "$ICONS_DIR/scalable/apps"
            cp "assets/icons/linux/scalable/plustoregimp.svg" "$ICONS_DIR/scalable/apps/"
            echo "     ✅ Ícone SVG instalado"
        fi
        
        # Atualizar cache de ícones
        if command -v gtk-update-icon-cache &> /dev/null; then
            gtk-update-icon-cache -f -t "$ICONS_DIR" >> "$LOG_FILE" 2>&1
            echo "     ✅ Cache de ícones atualizado"
        fi
        
        ICON_NAME="plustoregimp"
        
    else
        # Usar ícone do GIMP se ícones personalizados não existirem
        echo "   ⚠️  Ícones personalizados não encontrados, usando ícone do GIMP"
        ICON_NAME="gimp"
    fi
}

install_icons
log "Ícones instalados"

# Cria link simbólico
echo "🔗 Criando link simbólico..."
ln -sf "$INSTALL_DIR/pluStoreGimp" "$BIN_DIR/plustoregimp"
log "Link simbólico criado: $BIN_DIR/plustoregimp"

# Cria arquivo .desktop
echo "🎯 Criando atalho do aplicativo..."
cat > "$DESKTOP_DIR/plustoregimp.desktop" << DESKTOP_EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=$DISPLAY_NAME
Comment=Gerenciador de Plugins para GIMP
Exec=env HOME=\$HOME $INSTALL_DIR/pluStoreGimp
Icon=$ICON_NAME
Terminal=false
StartupWMClass=pluStoreGimp
Categories=Graphics;
Keywords=gimp;plugin;store;graphics;
X-GNOME-UsesNotifications=true
DESKTOP_EOF

# Torna o .desktop executável
chmod +x "$DESKTOP_DIR/plustoregimp.desktop"

# Atualiza banco de dados de aplicativos
echo "🔄 Atualizando banco de dados de aplicativos..."
update-desktop-database "$DESKTOP_DIR" >> "$LOG_FILE" 2>&1 || true

# Verifica se o GIMP está instalado
echo ""
echo "🔍 Verificando se o GIMP está instalado..."
if command -v gimp >/dev/null 2>&1; then
    GIMP_VERSION=$(gimp --version | head -n1)
    echo "   ✅ $GIMP_VERSION"
    log "GIMP encontrado: $GIMP_VERSION"
else
    echo "   ⚠️  GIMP não encontrado. O $DISPLAY_NAME requer o GIMP instalado."
    log "AVISO: GIMP não encontrado"
fi

# Verificação final da instalação
echo ""
echo "🔍 Verificando instalação..."
if [ -x "$INSTALL_DIR/pluStoreGimp" ] && [ -L "$BIN_DIR/plustoregimp" ]; then
    echo "   ✅ Instalação verificada com sucesso"
    log "Instalação verificada com sucesso"
else
    echo "   ⚠️  Possíveis problemas na instalação"
    log "AVISO: Possíveis problemas na instalação"
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
echo "   • Atalho: Menu de aplicativos → '$DISPLAY_NAME'"
echo "   • Ícone: $ICON_NAME"
echo ""
echo "🚀 Para executar:"
echo "   - Terminal: plustoregimp"
echo "   - Menu: Procure '$DISPLAY_NAME' em Gráficos"
echo ""
echo "🐛 Problemas? Verifique o log: $LOG_FILE"
echo ""
