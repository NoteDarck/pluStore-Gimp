#!/bin/bash
# Desinstalador do pluStoreGimp para Linux

clear
echo "╔════════════════════════════════════════════════════════╗"
echo "║                                                        ║"
echo "║          Desinstalador pluStoreGimp                   ║"
echo "║                                                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

APP_NAME="pluStoreGimp"
DISPLAY_NAME="pluStore GIMP"
INSTALL_DIR="$HOME/.local/share/$APP_NAME"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICONS_DIR="$HOME/.local/share/icons/hicolor"

echo "🗑️  Desinstalando $DISPLAY_NAME..."
echo ""

# Verificar se existe instalação
if [ ! -d "$INSTALL_DIR" ]; then
    echo "❌ $DISPLAY_NAME não está instalado"
    exit 1
fi

echo "📋 Itens que serão removidos:"
echo "   • Diretório: $INSTALL_DIR"
echo "   • Link simbólico: $BIN_DIR/plustoregimp"
echo "   • Atalho: $DESKTOP_DIR/plustoregimp.desktop"
echo "   • Ícones: $ICONS_DIR/*/apps/plustoregimp.*"
echo ""

read -p "Tem certeza que deseja desinstalar? (s/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "❕ Desinstalação cancelada"
    exit 0
fi

# Remover atalho do desktop
echo ""
echo "🔗 Removendo atalho..."
if [ -f "$DESKTOP_DIR/plustoregimp.desktop" ]; then
    rm -f "$DESKTOP_DIR/plustoregimp.desktop"
    echo "✅ Atalho removido"
    
    # Atualizar banco de dados
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi

# Remover link simbólico
if [ -L "$BIN_DIR/plustoregimp" ]; then
    rm -f "$BIN_DIR/plustoregimp"
    echo "✅ Link simbólico removido"
fi

# Remover ícones
echo "🎨 Removendo ícones..."
for size in 16x16 32x32 48x48 64x64 128x128 256x256 scalable; do
    if [ -f "$ICONS_DIR/$size/apps/plustoregimp.png" ]; then
        rm -f "$ICONS_DIR/$size/apps/plustoregimp.png"
    fi
    if [ -f "$ICONS_DIR/$size/apps/plustoregimp.svg" ]; then
        rm -f "$ICONS_DIR/$size/apps/plustoregimp.svg"
    fi
done

# Atualizar cache de ícones
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f -t "$ICONS_DIR" 2>/dev/null || true
    echo "✅ Cache de ícones atualizado"
fi

# Remover diretório de instalação
echo "📁 Removendo arquivos..."
if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
    echo "✅ Diretório removido: $INSTALL_DIR"
fi

echo ""
echo "✅ $DISPLAY_NAME foi desinstalado com sucesso!"
echo ""
