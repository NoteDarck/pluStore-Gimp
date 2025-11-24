#!/bin/bash
# Desinstalador do pluStoreGimp para macOS

clear
echo "╔════════════════════════════════════════════════════════╗"
echo "║                                                        ║"
echo "║          Desinstalador pluStoreGimp                   ║"
echo "║                                                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

APP_NAME="pluStoreGimp"
DISPLAY_NAME="pluStore GIMP"
INSTALL_DIR="$HOME/Applications/$APP_NAME"
BIN_DIR="$HOME/.local/bin"
APP_DIR="$HOME/Applications"

echo "🗑️  Desinstalando $DISPLAY_NAME..."
echo ""

# Verificar se existe instalação
if [ ! -d "$INSTALL_DIR" ] && [ ! -d "$APP_DIR/$DISPLAY_NAME.app" ]; then
    echo "❌ $DISPLAY_NAME não está instalado"
    exit 1
fi

echo "📋 Itens que serão removidos:"
echo "   • Diretório: $INSTALL_DIR"
echo "   • Link simbólico: $BIN_DIR/plustoregimp"
echo "   • Aplicativo: $APP_DIR/$DISPLAY_NAME.app"
echo ""

read -p "Tem certeza que deseja desinstalar? (s/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "❕ Desinstalação cancelada"
    exit 0
fi

# Remover aplicativo
echo ""
echo "🚀 Removendo aplicativo..."
if [ -d "$APP_DIR/$DISPLAY_NAME.app" ]; then
    rm -rf "$APP_DIR/$DISPLAY_NAME.app"
    echo "✅ Aplicativo removido do Launchpad"
fi

# Remover link simbólico
if [ -L "$BIN_DIR/plustoregimp" ]; then
    rm -f "$BIN_DIR/plustoregimp"
    echo "✅ Link simbólico removido"
fi

# Remover diretório de instalação
echo "📁 Removendo arquivos..."
if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
    echo "✅ Diretório removido: $INSTALL_DIR"
fi

# Limpar PATH (opcional)
echo ""
echo "🛠️  Limpando configurações..."
SHELL_RC="$HOME/.zshrc"
if [ -n "$BASH_VERSION" ]; then
    SHELL_RC="$HOME/.bash_profile"
fi

if [ -f "$SHELL_RC" ]; then
    # Remove a linha do PATH se existir
    sed -i '' '/export PATH="\$HOME\/.local\/bin:\$PATH"/d' "$SHELL_RC" 2>/dev/null
    echo "✅ Configurações removidas de $SHELL_RC"
fi

echo ""
echo "✅ $DISPLAY_NAME foi desinstalado com sucesso!"
echo ""
