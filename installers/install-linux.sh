#!/bin/bash
# Instalador do pluStoreGimp para Linux

clear
echo "╔════════════════════════════════════════════════════════╗"
echo "║                                                        ║"
echo "║          Instalador pluStoreGimp v2.0                 ║"
echo "║          Gerenciador de Plugins para GIMP             ║"
echo "║                                                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Verifica se está rodando como root
if [ "$EUID" -eq 0 ]; then 
    echo "⚠️  Não execute como root/sudo"
    exit 1
fi

echo "📦 Instalando pluStoreGimp..."
echo ""

# Instala dependências do sistema
echo "🔍 Verificando dependências do sistema..."
if ! dpkg -l | grep -q python3-gi; then
    echo "   Instalando python3-gi..."
    sudo apt-get update
    sudo apt-get install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0
fi
echo "✅ Dependências do sistema OK"

# Cria diretórios
INSTALL_DIR="$HOME/.local/share/pluStoreGimp"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"

mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$DESKTOP_DIR"

# Copia executável
echo "📂 Copiando arquivos..."
cp pluStoreGimp "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/pluStoreGimp"

# Cria link simbólico
ln -sf "$INSTALL_DIR/pluStoreGimp" "$BIN_DIR/plustoregimp"

# Cria arquivo .desktop
cat > "$DESKTOP_DIR/plustoregimp.desktop" << 'DESKTOP_EOF'
[Desktop Entry]
Version=2.0
Type=Application
Name=pluStore GIMP
Comment=Gerenciador de Plugins para GIMP
Exec=$HOME/.local/share/pluStoreGimp/pluStoreGimp
Icon=gimp
Terminal=false
Categories=Graphics;Photography;
DESKTOP_EOF

# Atualiza banco de dados de aplicativos
update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║                                                        ║"
echo "║          ✅ Instalação Concluída! ✅                  ║"
echo "║                                                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "Para executar:"
echo "  - Digite: plustoregimp"
echo "  - Ou procure 'pluStore GIMP' no menu de aplicativos"
echo ""
