# pluStoreGimp v2.0 - Distribuição

## 📦 Executáveis Incluídos

Este pacote contém executáveis pré-compilados do pluStoreGimp para diferentes plataformas.

## 🚀 Instalação

### Linux

```bash
chmod +x install-linux.sh
./install-linux.sh
```

Dependências (instaladas automaticamente):
- python3-gi
- python3-gi-cairo
- gir1.2-gtk-3.0

### macOS

```bash
chmod +x install-mac.sh
./install-mac.sh
```

Dependências (instaladas automaticamente via Homebrew):
- pygobject3
- gtk+3

### Windows

1. Execute `install-windows.bat`
2. Procure "pluStore GIMP" no menu Iniciar

**Nota para Windows**: Pode ser necessário instalar o GTK3 separadamente:
- Download: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer

## 📋 Requisitos Mínimos

- **Linux**: Ubuntu 20.04+, Fedora 34+, ou similar
- **macOS**: macOS 10.14+ (Mojave ou superior)
- **Windows**: Windows 10/11 (64-bit)

## 🎯 Uso

Após a instalação:

### Linux/macOS
```bash
plustoregimp
```

### Windows
Procure "pluStore GIMP" no menu Iniciar

## 📚 Documentação

Consulte os arquivos markdown incluídos:
- `GUIA_RAPIDO.md` - Início rápido
- `README.md` - Documentação completa
- `MELHORIAS.md` - Detalhes técnicos

## 🐛 Problemas Conhecidos

### Linux
- Se GTK não estiver instalado, execute:
  ```bash
  sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
  ```

### macOS
- Requer Homebrew instalado
- Pode ser necessário permitir execução em Preferências de Segurança

### Windows
- Antivírus pode alertar sobre executável não assinado (é seguro)
- Pode ser necessário instalar Visual C++ Redistributable

## 📞 Suporte

Para problemas ou dúvidas:
1. Consulte a documentação incluída
2. Verifique se as dependências estão instaladas
3. Execute a versão Python diretamente se houver problemas

## 🔒 Verificação

Checksums dos executáveis serão fornecidos em `checksums.txt`

## 📄 Licença

Veja LICENSE.txt para detalhes

---

**Versão**: 2.0  
**Data**: 2025  
**Status**: Estável
