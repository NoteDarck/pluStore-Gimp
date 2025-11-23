pluStore GIMP - Gerenciador de Plugins
Um gerenciador de plugins moderno e intuitivo para GIMP, desenvolvido em Python + GTK3, que permite pesquisar, instalar, atualizar e desinstalar plugins diretamente do GitHub.

Funcionalidades
🔍 Pesquisa Avançada: Busca plugins no GitHub por categoria ou palavras-chave

📦 Gerenciamento Completo: Instalar, atualizar e desinstalar plugins com um clique

🎯 Interface Intuitiva: Design moderno com tema escuro e navegação simplificada

📂 Categorias Organizadas: Filtros, Fotografia, Efeitos, Texturas, IA e Exportação

🔄 Atualizações: Mantenha seus plugins sempre atualizados

💾 Backup Automático: Cria backup antes de atualizar plugins

⚡ Multi-threading: Operações não bloqueiam a interface

🚀 Instalação
Pré-requisitos
Ubuntu/Debian:

bash
sudo apt update
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 python3-pip
Fedora:

bash
sudo dnf install python3-gobject gtk3 python3-pip
Arch Linux:

bash
sudo pacman -S python-gobject gtk3 python-pip
Instalação das Dependências Python
bash
pip3 install requests

Opcional: Token do GitHub (Recomendado)
Para evitar limites de requisição da API do GitHub:

Crie um token em GitHub Settings > Developer settings > Personal access tokens

Adicione no seu .bashrc ou .zshrc:

bash
export GITHUB_TOKEN='seu_token_aqui'
📥 Como Usar
Baixe o script:

bash
wget https://raw.githubusercontent.com/seu-usuario/gimp-plugin-store/main/plustore_gimp.py
chmod +x plustore_gimp.py
Execute:

bash
./plustore_gimp.py
Configure a pasta de plugins:

Clique em "📁 Configurar Pasta de Plugins"

Selecione a pasta correta (geralmente ~/.config/GIMP/2.10/plug-ins/)

Explore e instale:

Navegue pelas categorias ou pesquise plugins específicos

Clique em "⬇️ Instalar" para adicionar novos plugins

Use "🔄 Gerenciar" para atualizar ou desinstalar

🎯 Categorias Disponíveis

Categoria	Descrição	Exemplos

🎨 Filtros	Efeitos de processamento de imagem	GMIC, Resynthesizer

📷 Fotografia	Ferramentas para fotógrafos	G'MIC, Wavelet Denoise

✨ Efeitos	Efeitos visuais criativos	BIMP, Layer Effects

🎭 Texturas	Geração e aplicação de texturas	Seamless Texture

🤖 IA	Plugins com inteligência artificial	Stable Diffusion, GFPGAN

💾 Exportação	Exportação e conversão	Export Layers, WebP


🛠️ Estrutura do Projeto

text
plustore_gimp.py          # Script principal
~/.config/gimp_plugin_store.json  

# Configurações do usuário

🔧 Funcionalidades Técnicas
Instalação de Plugins
Download automático do branch principal

Extração para pasta de plugins do GIMP

Configuração automática de permissões de execução

Backup antes de atualizações

Gerenciamento
Detecção automática de plugins instalados

Interface dinâmica que atualiza em tempo real

Operações em background (não bloqueia a UI)

Tratamento de erros robusto

Interface
Tema escuro moderno com CSS customizado

Cards informativos com metadata dos plugins

Barra de status com feedback em tempo real

Navegação intuitiva por categorias

🐛 Solução de Problemas
Erro: "GTK não encontrado"
bash
# Ubuntu/Debian
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0

# Fedora
sudo dnf install python3-gobject gtk3

# Arch
sudo pacman -S python-gobject gtk3
Erro: "Limite de requisições do GitHub"
Crie um token do GitHub e configure a variável GITHUB_TOKEN

Plugin não aparece no GIMP
Verifique se a pasta de plugins está correta

Reinicie o GIMP após instalar novos plugins

Verifique permissões de execução nos arquivos .py

🤝 Contribuindo
Contribuições são bem-vindas! Areas onde você pode ajudar:

🔍 Melhorar a busca de plugins

🎨 Adicionar novas categorias

🌐 Traduções para outros idiomas

🐛 Reportar e corrigir bugs

📚 Documentação e tutoriais

📄 Licença
Este projeto é distribuído sob a licença GPL-3.0. Veja o arquivo LICENSE para mais detalhes.

⚠️ Aviso Legal
Este software não é afiliado oficialmente ao GIMP ou ao GitHub. Plugins são instalados por conta e risco do usuário. Sempre verifique a segurança dos repositórios antes da instalação.

🆘 Suporte
Se encontrar problemas:

Verifique se todas as dependências estão instaladas

Confirme que o GIMP 2.10+ está instalado

Teste com um plugin simples primeiro

Abra uma issue no repositório do projeto

Desenvolvido com ❤️ para a comunidade GIMP
