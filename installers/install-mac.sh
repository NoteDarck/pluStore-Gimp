#!/bin/bash
# Instalador do pluStoreGimp para macOS

clear
echo "╔════════════════════════════════════════════════════════╗"
echo "║                                                        ║"
echo "║          Instalador pluStoreGimp v2.0                 ║"
echo "║          Gerenciador de Plugins para GIMP             ║"
echo "║                                                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

echo "📦 Instalando pluStoreGimp..."
echo ""

# Verifica Homebrew
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew não encontrado"
    echo "   Instale em: https://brew.sh"
    exit 1
fi

# Instala dependências
echo "🔍 Verificando dependências..."
if ! brew list pygobject3 &>/dev/null; then
    echo "   Instalando pygobject3..."
    brew install pygobject3 gtk+3
fi
echo "✅ Dependências OK"

# Cria diretórios
INSTALL_DIR="$HOME/Applications/pluStoreGimp"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"

# Copia executável
echo "📂 Copiando arquivos..."
cp pluStoreGimp "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/pluStoreGimp"

# Cria link simbólico
ln -sf "$INSTALL_DIR/pluStoreGimp" "$BIN_DIR/plustoregimp"

# Adiciona ao PATH se necessário
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
    echo "⚠️  Reinicie o terminal para aplicar mudanças no PATH"
fi

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║                                                        ║"
echo "║          ✅ Instalação Concluída! ✅                  ║"
echo "║                                                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "Para executar: plustoregimp"
echo ""
