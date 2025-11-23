#!/usr/bin/env python3
"""
GIMP Plugin Store - versão aprimorada (Python + GTK3)

Funcionalidades principais:
- pesquisa no GitHub por "gimp plugin + categoria"
- instala repositórios baixando o zip do branch padrão e copiando para a pasta de plugins
- permite escolher e salvar a pasta de plugins do usuário
- aba INSTALADOS que mostra plugins já presentes na pasta escolhida
- desinstalar plugins instalados
- atualizar plugins existentes
- botão dinâmico: Instalar / Instalado / Atualizar / Desinstalar
- mostra avatar do criador do plugin

Dependências:
- Python 3.6+
- GTK3 (python3-gi)
- requests
- pillow
"""

import os
import sys
import subprocess
import platform
import importlib
import tempfile
import zipfile
import stat
import shutil
import threading
import requests
import json
from urllib.parse import quote_plus
from io import BytesIO

# =============================================================================
# VERIFICAÇÃO E INSTALAÇÃO DE REQUISITOS
# =============================================================================

def check_and_install_requirements():
    """Verifica e instala requisitos automaticamente"""
    missing_packages = []
    system = platform.system().lower()
    
    print("🔍 Verificando requisitos do pluStore GIMP...")
    print(f"📋 Sistema detectado: {platform.system()} {platform.release()}")
    print(f"🐍 Versão do Python: {platform.python_version()}")
    
    # Verificar Python version
    python_version = tuple(map(int, platform.python_version().split('.')))
    if python_version < (3, 6):
        print("❌ Python 3.6 ou superior é necessário!")
        return False
    
    # Verificar GTK
    try:
        import gi
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk, GLib, GdkPixbuf
        print("✅ GTK3 encontrado")
    except ImportError as e:
        missing_packages.append(('gi', 'python3-gi (Linux) / pygobject (Windows/Mac)'))
        print("❌ GTK3 não encontrado")
    
    # Verificar requests
    try:
        import requests
        print("✅ requests encontrado")
    except ImportError:
        missing_packages.append(('requests', 'requests'))
        print("❌ requests não encontrado")
    
    # Verificar pillow
    try:
        from PIL import Image
        print("✅ pillow encontrado")
    except ImportError:
        missing_packages.append(('pillow', 'pillow'))
        print("❌ pillow não encontrado")
    
    if not missing_packages:
        print("🎉 Todos os requisitos estão instalados!")
        return True
    
    print(f"\n❌ Faltam {len(missing_packages)} pacotes:")
    for pkg, install_name in missing_packages:
        print(f"   - {pkg} -> {install_name}")
    
    # Oferecer instalação automática
    if system == "windows":
        return install_windows_requirements(missing_packages)
    elif system == "darwin":  # Mac
        return install_mac_requirements(missing_packages)
    else:  # Linux
        return install_linux_requirements(missing_packages)

def install_windows_requirements(missing_packages):
    """Instala requisitos no Windows"""
    print("\n🔄 Tentando instalar requisitos no Windows...")
    
    # Mapeamento de pacotes para pip
    pip_packages = []
    for pkg, install_name in missing_packages:
        if pkg == 'gi':
            pip_packages.append('pygobject')
        else:
            pip_packages.append(pkg)
    
    try:
        # Instalar via pip
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + pip_packages)
        print("✅ Pacotes instalados com sucesso!")
        
        # Instruções adicionais para GTK no Windows
        if 'gi' in missing_packages:
            print("\n📝 Para GTK no Windows, você também pode:")
            print("   1. Baixar o GTK de: https://www.gtk.org/docs/installations/windows/")
            print("   2. Ou usar o MSYS2: pacman -S mingw-w64-x86_64-gtk3")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro na instalação: {e}")
        print("\n📝 Instalação manual necessária:")
        print("   1. Instale o Python: https://www.python.org/downloads/")
        print("   2. Instale o GTK: https://www.gtk.org/docs/installations/windows/")
        print("   3. Execute no prompt: pip install requests pillow pygobject")
        return False

def install_mac_requirements(missing_packages):
    """Instala requisitos no Mac"""
    print("\n🔄 Tentando instalar requisitos no macOS...")
    
    # Verificar se Homebrew está instalado
    try:
        subprocess.run(['brew', '--version'], check=True, capture_output=True)
        has_brew = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        has_brew = False
    
    pip_packages = []
    brew_packages = []
    
    for pkg, install_name in missing_packages:
        if pkg == 'gi':
            if has_brew:
                brew_packages.extend(['gtk+3', 'pygobject3'])
            else:
                pip_packages.append('pygobject')
        else:
            pip_packages.append(pkg)
    
    try:
        # Instalar pacotes Homebrew se disponível
        if brew_packages and has_brew:
            print("📦 Instalando pacotes com Homebrew...")
            subprocess.check_call(['brew', 'install'] + brew_packages)
        
        # Instalar pacotes pip
        if pip_packages:
            print("📦 Instalando pacotes com pip...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + pip_packages)
        
        print("✅ Pacotes instalados com sucesso!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro na instalação: {e}")
        print("\n📝 Instalação manual necessária:")
        if not has_brew:
            print("   1. Instale o Homebrew: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
        print("   2. Execute: brew install gtk+3 pygobject3")
        print("   3. Execute: pip3 install requests pillow")
        return False

def install_linux_requirements(missing_packages):
    """Instala requisitos no Linux"""
    print("\n🔄 Tentando instalar requisitos no Linux...")
    
    # Detectar gerenciador de pacotes
    package_managers = {
        'apt': ['apt-get', 'install', '-y'],
        'dnf': ['dnf', 'install', '-y'],
        'yum': ['yum', 'install', '-y'],
        'pacman': ['pacman', '-S', '--noconfirm'],
        'zypper': ['zypper', 'install', '-y']
    }
    
    pm = None
    for pm_name, pm_cmd in package_managers.items():
        try:
            subprocess.run([pm_cmd[0], '--version'], check=True, capture_output=True)
            pm = (pm_name, pm_cmd)
            break
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    if not pm:
        print("❌ Não foi possível detectar o gerenciador de pacotes")
        return install_with_pip_only(missing_packages)
    
    pm_name, pm_cmd = pm
    print(f"📦 Gerenciador de pacotes detectado: {pm_name}")
    
    # Mapear pacotes para cada distribuição
    package_map = {
        'apt': {
            'gi': 'python3-gi gir1.2-gtk-3.0',
            'requests': 'python3-requests',
            'pillow': 'python3-pil'
        },
        'dnf': {
            'gi': 'python3-gobject gtk3',
            'requests': 'python3-requests',
            'pillow': 'python3-pillow'
        },
        'yum': {
            'gi': 'pygobject3 gtk3',
            'requests': 'python-requests',
            'pillow': 'python-pillow'
        },
        'pacman': {
            'gi': 'python-gobject gtk3',
            'requests': 'python-requests',
            'pillow': 'python-pillow'
        },
        'zypper': {
            'gi': 'python3-gobject Gtk-3',
            'requests': 'python3-requests',
            'pillow': 'python3-Pillow'
        }
    }
    
    system_packages = []
    pip_packages = []
    
    for pkg, install_name in missing_packages:
        if pkg in package_map[pm_name]:
            system_packages.extend(package_map[pm_name][pkg].split())
        else:
            pip_packages.append(pkg)
    
    try:
        # Instalar pacotes do sistema
        if system_packages:
            print(f"📦 Instalando pacotes do sistema: {', '.join(system_packages)}")
            subprocess.check_call(['sudo'] + pm_cmd + system_packages)
        
        # Instalar pacotes pip
        if pip_packages:
            print(f"📦 Instalando pacotes pip: {', '.join(pip_packages)}")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + pip_packages)
        
        print("✅ Pacotes instalados com sucesso!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro na instalação com {pm_name}: {e}")
        return install_with_pip_only(missing_packages)

def install_with_pip_only(missing_packages):
    """Tenta instalar apenas com pip"""
    print("\n🔄 Tentando instalação apenas com pip...")
    
    pip_packages = []
    for pkg, install_name in missing_packages:
        if pkg == 'gi':
            pip_packages.append('pygobject')
        else:
            pip_packages.append(pkg)
    
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + pip_packages)
        print("✅ Pacotes instalados com pip!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro na instalação com pip: {e}")
        print("\n📝 Instalação manual necessária:")
        print("   Linux (Debian/Ubuntu): sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 python3-requests python3-pil")
        print("   Linux (Fedora): sudo dnf install python3-gobject gtk3 python3-requests python3-pillow")
        print("   Linux (Arch): sudo pacman -S python-gobject gtk3 python-requests python-pillow")
        print("   Windows: pip install requests pillow pygobject")
        print("   macOS: brew install gtk+3 pygobject3 && pip3 install requests pillow")
        return False

# Executar verificação de requisitos
if not check_and_install_requirements():
    print("\n❌ Não foi possível instalar todos os requisitos automaticamente.")
    print("📝 Por favor, instale manualmente seguindo as instruções acima.")
    sys.exit(1)

# =============================================================================
# CÓDIGO PRINCIPAL DO APLICATIVO
# =============================================================================

# Agora importamos as bibliotecas GTK após verificar os requisitos
try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GObject, GLib, GdkPixbuf
except Exception as e:
    print("❌ Erro ao carregar GTK após instalação:", e)
    sys.exit(1)

# Tentar importar Pillow para processamento de imagens
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    print("⚠️ Pillow não instalado. Avatares podem não funcionar corretamente.")
    HAS_PIL = False

GITHUB_API = "https://api.github.com/search/repositories"
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')  # opcional

# Config file onde salvamos a pasta escolhida
CONFIG_PATH = os.path.expanduser('~/.config/gimp_plugin_store.json')

# Pasta padrão de plugins do GIMP (ajuste se necessário)
DEFAULT_GIMP_PLUGIN_DIRS = [
    os.path.expanduser('~/.config/GIMP/2.10/plug-ins'),
    os.path.expanduser('~/.gimp-2.8/plug-ins'),
]

# Cache para avatares
AVATAR_CACHE_DIR = os.path.expanduser('~/.cache/gimp_plugin_store/avatars')
os.makedirs(AVATAR_CACHE_DIR, exist_ok=True)

# valor inicial, pode ser sobrescrito por pasta salva
PLUGIN_DEST = None
for p in DEFAULT_GIMP_PLUGIN_DIRS:
    if os.path.isdir(p):
        PLUGIN_DEST = p
        break
if not PLUGIN_DEST:
    PLUGIN_DEST = DEFAULT_GIMP_PLUGIN_DIRS[0]
    os.makedirs(PLUGIN_DEST, exist_ok=True)

CATEGORIES = {
    'Filtros': 'filter',
    'Fotografia': 'photo',
    'Efeitos': 'effect',
    'Texturas': 'texture',
    'IA': 'ai',
    'Exportação': 'export',
}


def load_saved_folder():
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r') as f:
                data = json.load(f)
            return data.get('plugin_folder')
    except Exception:
        pass
    return None


def save_folder(folder):
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, 'w') as f:
            json.dump({'plugin_folder': folder}, f)
    except Exception as e:
        print('Erro ao salvar configuração:', e)


def get_avatar_path(avatar_url, size=40):
    """Retorna o caminho do arquivo de avatar em cache"""
    import hashlib
    filename = hashlib.md5(avatar_url.encode()).hexdigest() + f"_{size}.png"
    return os.path.join(AVATAR_CACHE_DIR, filename)


def download_avatar(avatar_url, size=40):
    """Baixa e processa o avatar para o tamanho especificado"""
    cache_path = get_avatar_path(avatar_url, size)
    
    # Se já existe em cache, retorna
    if os.path.exists(cache_path):
        return cache_path
    
    try:
        response = requests.get(avatar_url, timeout=10)
        if response.status_code == 200:
            if HAS_PIL:
                # Processa a imagem com Pillow para redimensionar
                image = Image.open(BytesIO(response.content))
                
                # Converte para RGB se necessário
                if image.mode in ('RGBA', 'LA'):
                    # Cria fundo branco para imagens com transparência
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'RGBA':
                        background.paste(image, mask=image.split()[-1])
                    else:
                        background.paste(image, mask=image)
                    image = background
                elif image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Redimensiona mantendo proporção
                image.thumbnail((size, size), Image.Resampling.LANCZOS)
                
                # Salva em cache
                image.save(cache_path, 'PNG')
            else:
                # Sem Pillow, salva o arquivo original
                with open(cache_path, 'wb') as f:
                    f.write(response.content)
            
            return cache_path
    except Exception as e:
        print(f"Erro ao baixar avatar {avatar_url}: {e}")
    
    return None


def load_avatar_pixbuf(avatar_url, size=40):
    """Carrega um avatar como GdkPixbuf"""
    try:
        cache_path = download_avatar(avatar_url, size)
        if cache_path and os.path.exists(cache_path):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(cache_path, size, size)
            return pixbuf
    except Exception as e:
        print(f"Erro ao carregar avatar: {e}")
    
    # Avatar padrão se não conseguir carregar
    return create_default_avatar(size)


def create_default_avatar(size=40):
    """Cria um avatar padrão quando não há imagem disponível"""
    try:
        # Cria um pixbuf simples com cor de fundo e ícone
        pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, size, size)
        
        # Cor de fundo (cinza)
        pixbuf.fill(0x777777FF)
        
        return pixbuf
    except Exception:
        return None


def is_plugin_installed(plugin_name):
    """Verifica se um plugin já está instalado"""
    if not PLUGIN_DEST or not os.path.isdir(PLUGIN_DEST):
        return False
    plugin_path = os.path.join(PLUGIN_DEST, plugin_name)
    return os.path.exists(plugin_path)


def uninstall_plugin(plugin_name):
    """Remove um plugin da pasta de plugins"""
    if not PLUGIN_DEST or not os.path.isdir(PLUGIN_DEST):
        raise Exception('Pasta de plugins não configurada')
    
    plugin_path = os.path.join(PLUGIN_DEST, plugin_name)
    if not os.path.exists(plugin_path):
        raise Exception(f'Plugin {plugin_name} não encontrado')
    
    if os.path.isdir(plugin_path):
        shutil.rmtree(plugin_path)
    else:
        os.remove(plugin_path)
    
    return True


def build_github_headers():
    headers = {'Accept': 'application/vnd.github.v3+json', 'User-Agent': 'gimp-plugin-store/1.0'}
    if GITHUB_TOKEN:
        headers['Authorization'] = f'token {GITHUB_TOKEN}'
    return headers


def search_github(q, per_page=30):
    query = f"gimp plugin {q}"
    params = {'q': query, 'per_page': per_page}
    resp = requests.get(GITHUB_API, params=params, headers=build_github_headers(), timeout=15)
    if resp.status_code == 403:
        raise RuntimeError('Acesso negado ou limite de requests (rate limit). Considere usar GITHUB_TOKEN).')
    if resp.status_code != 200:
        raise RuntimeError(f'GitHub API erro: {resp.status_code} {resp.text[:200]}')
    data = resp.json()
    return data.get('items', [])


def install_repository_as_plugin(repo, dest_plugins_dir):
    owner = repo['owner']['login']
    name = repo['name']
    branch = repo.get('default_branch', 'main')
    zip_url = f"https://github.com/{owner}/{name}/archive/refs/heads/{branch}.zip"

    tmp = tempfile.mkdtemp(prefix='gimp_plugin_')
    try:
        r = requests.get(zip_url, headers=build_github_headers(), stream=True, timeout=60)
        if r.status_code != 200:
            raise RuntimeError(f'Não foi possível baixar {zip_url}: status {r.status_code}')
        zip_path = os.path.join(tmp, f'{name}.zip')
        with open(zip_path, 'wb') as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)

        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(tmp)

        # normalmente o zip extrai para <name>-<branch>/
        extracted_root = None
        for entry in os.listdir(tmp):
            full = os.path.join(tmp, entry)
            if os.path.isdir(full) and entry.startswith(name):
                extracted_root = full
                break
        if not extracted_root:
            extracted_root = tmp

        # target dir no plugins
        target_dir = os.path.join(dest_plugins_dir, name)
        if os.path.exists(target_dir):
            backup = target_dir + '.backup'
            if os.path.exists(backup):
                shutil.rmtree(backup)
            shutil.move(target_dir, backup)

        shutil.copytree(extracted_root, target_dir)

        # tornar .py executáveis
        for root, dirs, files in os.walk(target_dir):
            for fname in files:
                if fname.endswith('.py'):
                    fpath = os.path.join(root, fname)
                    st = os.stat(fpath)
                    os.chmod(fpath, st.st_mode | stat.S_IEXEC)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


class RepoRow(Gtk.ListBoxRow):
    def __init__(self, repo, main_window):
        super().__init__()
        self.repo = repo
        self.main_window = main_window
        
        # Card container
        card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        card.set_margin_top(8)
        card.set_margin_bottom(8)
        card.set_margin_start(12)
        card.set_margin_end(12)
        
        # Avatar do autor
        avatar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        avatar_box.set_size_request(50, 50)
        
        self.avatar_image = Gtk.Image()
        self.avatar_image.set_size_request(40, 40)
        
        # Carregar avatar em thread separada
        if repo.get('owner', {}).get('avatar_url') and repo.get('owner', {}).get('login') != 'local':
            threading.Thread(
                target=self._load_avatar,
                args=(repo['owner']['avatar_url'],),
                daemon=True
            ).start()
        else:
            # Avatar padrão para plugins locais
            default_avatar = create_default_avatar(40)
            if default_avatar:
                self.avatar_image.set_from_pixbuf(default_avatar)
            else:
                self.avatar_image.set_from_icon_name('user-available', Gtk.IconSize.DIALOG)
        
        avatar_box.pack_start(self.avatar_image, False, False, 0)
        
        # Nome do autor (pequeno)
        author_label = Gtk.Label()
        author_name = repo.get('owner',{}).get('login','')
        author_label.set_markup(f"<span size='x-small' color='#888'>{GLib.markup_escape_text(author_name)}</span>")
        author_label.set_max_width_chars(8)
        author_label.set_ellipsize(3)  # Truncate no meio se necessário
        author_label.set_justify(Gtk.Justification.CENTER)
        avatar_box.pack_start(author_label, False, False, 0)
        
        card.pack_start(avatar_box, False, False, 0)
        
        # Info box
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        info_box.set_hexpand(True)

        # Título
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        plugin_icon = Gtk.Label()
        plugin_icon.set_markup('<span size="large">🔌</span>')
        title_box.pack_start(plugin_icon, False, False, 0)
        
        title = Gtk.Label(xalign=0)
        repo_name = repo.get('name','')
        title.set_markup(f"<span size='large' weight='bold'>{GLib.markup_escape_text(repo_name)}</span>")
        title_box.pack_start(title, False, False, 0)
        
        info_box.pack_start(title_box, False, False, 0)

        # Descrição
        desc_text = repo.get('description') or 'Sem descrição'
        desc = Gtk.Label(label=desc_text, xalign=0)
        desc.set_line_wrap(True)
        desc.set_max_width_chars(80)
        info_box.pack_start(desc, False, False, 0)

        # Metadata com ícones
        meta_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        stars = Gtk.Label()
        stars.set_markup(f"<span size='small'>⭐ {repo.get('stargazers_count',0)}</span>")
        meta_box.pack_start(stars, False, False, 0)
        
        lang = repo.get('language') or 'N/A'
        language = Gtk.Label()
        language.set_markup(f"<span size='small'>💻 {lang}</span>")
        meta_box.pack_start(language, False, False, 0)
        
        # Data de atualização
        if repo.get('updated_at'):
            from datetime import datetime
            try:
                updated = datetime.strptime(repo['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
                updated_str = updated.strftime('%d/%m/%Y')
                updated_label = Gtk.Label()
                updated_label.set_markup(f"<span size='small'>🕒 {updated_str}</span>")
                meta_box.pack_start(updated_label, False, False, 0)
            except:
                pass
        
        info_box.pack_start(meta_box, False, False, 0)

        card.pack_start(info_box, True, True, 0)

        # Botão de ação estilizado
        self.btn = Gtk.Button()
        self.btn.set_size_request(160, 40)
        self.update_button_state()
        self.btn.connect('clicked', self.on_action_clicked)

        card.pack_start(self.btn, False, False, 0)
        self.add(card)

    def _load_avatar(self, avatar_url):
        """Carrega o avatar em uma thread separada"""
        try:
            pixbuf = load_avatar_pixbuf(avatar_url, 40)
            if pixbuf:
                GLib.idle_add(self.avatar_image.set_from_pixbuf, pixbuf)
        except Exception as e:
            print(f"Erro ao carregar avatar: {e}")

    def is_installed(self):
        global PLUGIN_DEST
        if not PLUGIN_DEST:
            return False
        # O diretório pode ter o nome exato ou prefixo (ex.: repo-branch). Procuramos por prefixo.
        for entry in os.listdir(PLUGIN_DEST):
            if entry == self.repo['name'] or entry.startswith(self.repo['name'] + '-'):
                return True
        # também pode existir pasta exata
        return os.path.isdir(os.path.join(PLUGIN_DEST, self.repo['name']))

    def get_installed_path(self):
        """Retorna o caminho do plugin instalado ou None"""
        global PLUGIN_DEST
        if not PLUGIN_DEST:
            return None
        for entry in os.listdir(PLUGIN_DEST):
            if entry == self.repo['name'] or entry.startswith(self.repo['name'] + '-'):
                return os.path.join(PLUGIN_DEST, entry)
        exact = os.path.join(PLUGIN_DEST, self.repo['name'])
        if os.path.exists(exact):
            return exact
        return None

    def update_button_state(self):
        """Atualiza o estado do botão baseado no status do plugin"""
        is_local = self.repo.get('owner', {}).get('login') == 'local'
        
        if self.is_installed():
            if is_local:
                # Plugin local - apenas desinstalar
                self.btn.set_label('🗑️ Desinstalar')
                self.btn.set_sensitive(True)
                self.btn.get_style_context().add_class('danger-button')
            else:
                # Plugin do GitHub - pode atualizar ou desinstalar
                self.btn.set_label('🔄 Gerenciar')
                self.btn.set_sensitive(True)
                self.btn.get_style_context().add_class('action-button')
        else:
            self.btn.set_label('⬇️ Instalar')
            self.btn.set_sensitive(True)
            self.btn.get_style_context().add_class('primary-button')

    def on_action_clicked(self, button):
        """Handler para o botão de ação"""
        label = button.get_label()
        is_local = self.repo.get('owner', {}).get('login') == 'local'
        
        if 'Instalar' in label:
            self.main_window.install_repo_handler(self.repo)
        
        elif 'Desinstalar' in label:
            self.show_uninstall_dialog()
        
        elif 'Gerenciar' in label:
            self.show_action_menu()

    def show_action_menu(self):
        """Mostra menu com opções de Atualizar ou Desinstalar"""
        menu = Gtk.Menu()
        
        # Opção Atualizar
        item_update = Gtk.MenuItem(label="Atualizar")
        item_update.connect('activate', lambda x: self.confirm_update())
        menu.append(item_update)
        
        # Separador
        menu.append(Gtk.SeparatorMenuItem())
        
        # Opção Desinstalar
        item_uninstall = Gtk.MenuItem(label="Desinstalar")
        item_uninstall.connect('activate', lambda x: self.show_uninstall_dialog())
        menu.append(item_uninstall)
        
        menu.show_all()
        menu.popup_at_widget(self.btn, 1, 1, None)

    def confirm_update(self):
        """Confirma a atualização do plugin"""
        dialog = Gtk.MessageDialog(
            transient_for=self.main_window,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Atualizar Plugin"
        )
        dialog.format_secondary_text(
            f"Deseja atualizar '{self.repo['name']}'?\n\n"
            "A versão atual será substituída pela mais recente."
        )
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            self.btn.set_label('Atualizando...')
            self.btn.set_sensitive(False)
            threading.Thread(
                target=self.main_window.update_repo_handler,
                args=(self.repo, self),
                daemon=True
            ).start()

    def show_uninstall_dialog(self):
        """Confirma a desinstalação do plugin"""
        dialog = Gtk.MessageDialog(
            transient_for=self.main_window,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Desinstalar Plugin"
        )
        dialog.format_secondary_text(
            f"Tem certeza que deseja desinstalar '{self.repo['name']}'?\n\n"
            "Esta ação não pode ser desfeita."
        )
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            self.btn.set_label('Desinstalando...')
            self.btn.set_sensitive(False)
            threading.Thread(
                target=self.main_window.uninstall_repo_handler,
                args=(self.repo, self),
                daemon=True
            ).start()


class MainWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title='🎨 pluStore GIMP - Gerenciador de Plugins')
        self.set_default_size(1100, 650)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_border_width(0)
        
        # Aplicar CSS customizado
        self.apply_dark_theme()

        # carrega pasta salva (se existir)
        saved = load_saved_folder()
        global PLUGIN_DEST
        if saved and os.path.isdir(saved):
            PLUGIN_DEST = saved

        # Container principal
        main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_container)
        
        # Header bar customizado
        header = self.create_header()
        main_container.pack_start(header, False, False, 0)
        
        # layout principal
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        main_container.pack_start(hbox, True, True, 0)

        # Sidebar
        side = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        side.set_size_request(240, -1)
        side.set_margin_top(16)
        side.set_margin_bottom(16)
        side.set_margin_start(16)
        side.set_margin_end(8)

        # Título da sidebar
        cat_label = Gtk.Label()
        cat_label.set_markup('<span size="large" weight="bold">📂 Categorias</span>')
        cat_label.set_xalign(0)
        cat_label.set_margin_bottom(8)
        side.pack_start(cat_label, False, False, 0)

        choose_btn = Gtk.Button(label='📁 Configurar Pasta de Plugins')
        choose_btn.connect('clicked', self.on_choose_plugin_folder)
        choose_btn.set_margin_bottom(12)
        side.pack_start(choose_btn, False, False, 0)

        # Scroll para lista de categorias
        cat_scroll = Gtk.ScrolledWindow()
        cat_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        cat_scroll.set_shadow_type(Gtk.ShadowType.NONE)
        
        self.cat_list = Gtk.ListBox()
        self.cat_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        
        # Ícones para categorias
        category_icons = {
            'Filtros': '🎨',
            'Fotografia': '📷',
            'Efeitos': '✨',
            'Texturas': '🎭',
            'IA': '🤖',
            'Exportação': '💾',
            'Instalados': '📦'
        }
        
        for name in list(CATEGORIES.keys()) + ['Instalados']:
            icon = category_icons.get(name, '📌')
            lbl = Gtk.Label()
            lbl.set_markup(f'<span size="medium">{icon} {name}</span>')
            lbl.set_xalign(0)
            lbl.set_margin_top(8)
            lbl.set_margin_bottom(8)
            lbl.set_margin_start(12)
            lbl.set_margin_end(12)
            lbrow = Gtk.ListBoxRow()
            lbrow.add(lbl)
            self.cat_list.add(lbrow)
        
        self.cat_list.connect('row-activated', self.on_category_selected)
        cat_scroll.add(self.cat_list)
        side.pack_start(cat_scroll, True, True, 0)

        # Área principal com conteúdo
        main_v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_v.set_margin_top(16)
        main_v.set_margin_bottom(16)
        main_v.set_margin_start(16)
        main_v.set_margin_end(16)

        # Área de pesquisa
        search_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        search_box.set_margin_bottom(8)
        
        search_label = Gtk.Label()
        search_label.set_markup('<span size="medium" weight="bold">🔍 Pesquisar Plugins</span>')
        search_label.set_xalign(0)
        search_box.pack_start(search_label, False, False, 0)
        
        search_h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text('Digite o nome do plugin (ex: gmic, resynthesizer, removebg...)')
        self.search_entry.connect('activate', self.on_search_clicked)
        
        search_btn = Gtk.Button(label='🔎 Pesquisar')
        search_btn.connect('clicked', self.on_search_clicked)
        search_btn.set_size_request(120, -1)
        
        search_h.pack_start(self.search_entry, True, True, 0)
        search_h.pack_start(search_btn, False, False, 0)
        
        search_box.pack_start(search_h, False, False, 0)
        main_v.pack_start(search_box, False, False, 0)

        # Área de resultados
        self.results_scroller = Gtk.ScrolledWindow()
        self.results_scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.results_scroller.set_shadow_type(Gtk.ShadowType.IN)
        
        self.results_box = Gtk.ListBox()
        self.results_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.results_scroller.add(self.results_box)
        main_v.pack_start(self.results_scroller, True, True, 0)

        hbox.pack_start(side, False, False, 0)
        hbox.pack_start(main_v, True, True, 0)
        
        # Status bar
        status_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        status_bar.set_size_request(-1, 32)
        
        # Ícone de status
        self.status_icon = Gtk.Label()
        self.status_icon.set_markup('<span>📍</span>')
        status_bar.pack_start(self.status_icon, False, False, 16)
        
        # Texto de status
        self.status = Gtk.Label(label=f'Pasta de plugins: {PLUGIN_DEST}', xalign=0)
        status_bar.pack_start(self.status, True, True, 0)
        
        # Info do GIMP
        gimp_info = Gtk.Label()
        gimp_info.set_markup('<span size="small">🎨 Para GIMP 2.10+ é GIMP 3.0+</span>')
        gimp_info.set_margin_end(16)
        status_bar.pack_end(gimp_info, False, False, 0)
        
        main_container.pack_start(status_bar, False, False, 0)

        # inicializar UI
        self.show_all()
        first_row = self.cat_list.get_row_at_index(0)
        if first_row:
            self.cat_list.select_row(first_row)
            # dispara a pesquisa inicial
            self.on_category_selected(self.cat_list, first_row)

    def set_status(self, text):
        """Atualiza o texto da barra de status"""
        def update():
            self.status.set_text(text)
            # Atualiza ícone baseado no status
            if 'Erro' in text or 'erro' in text:
                self.status_icon.set_markup('<span>❌</span>')
            elif 'Pesquisando' in text or 'Instalando' in text or 'Atualizando' in text:
                self.status_icon.set_markup('<span>⏳</span>')
            elif 'concluída' in text or 'Pronto' in text or 'exibidos' in text:
                self.status_icon.set_markup('<span>✅</span>')
            else:
                self.status_icon.set_markup('<span>📍</span>')
        GLib.idle_add(update)

    def on_choose_plugin_folder(self, button):
        dialog = Gtk.FileChooserDialog(title='Selecionar pasta de plugins', parent=self,
                                       action=Gtk.FileChooserAction.SELECT_FOLDER,
                                       buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                                'Selecionar', Gtk.ResponseType.OK))
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            global PLUGIN_DEST
            PLUGIN_DEST = dialog.get_filename()
            save_folder(PLUGIN_DEST)
            self.set_status(f'Nova pasta de plugins: {PLUGIN_DEST}')
            # quando selecionar, atualiza aba Instalados se estiver selecionada
            sel = self.cat_list.get_selected_row()
            if sel:
                row_content = sel.get_child().get_text()
                if 'Instalados' in row_content:
                    self.show_installed_plugins()
        dialog.destroy()

    def on_category_selected(self, listbox, row):
        label_widget = row.get_child()
        if not label_widget:
            return
            
        label_text = label_widget.get_text()
        if 'Instalados' in label_text:
            self.show_installed_plugins()
            return
            
        # Encontra a categoria correspondente
        for cat_name, cat_value in CATEGORIES.items():
            if cat_name in label_text:
                self.search_entry.set_text(cat_value)
                self.do_search(cat_value)
                return

    def on_search_clicked(self, button):
        q = self.search_entry.get_text().strip()
        if not q:
            return
        self.do_search(q)

    def do_search(self, q):
        self.set_status('Pesquisando no GitHub...')
        thread = threading.Thread(target=self._search_thread, args=(q,))
        thread.daemon = True
        thread.start()

    def _search_thread(self, q):
        try:
            results = search_github(q)
        except Exception as e:
            self.set_status(f'Erro na busca: {e}')
            return
        GLib.idle_add(self.populate_results, results)

    def populate_results(self, repos):
        # limpa
        for child in self.results_box.get_children():
            self.results_box.remove(child)

        if not repos:
            lbl = Gtk.Label(label='Nenhum resultado encontrado.')
            self.results_box.add(lbl)
        else:
            for r in repos:
                row = RepoRow(r, self)
                self.results_box.add(row)

        self.results_box.show_all()
        self.set_status(f'{len(repos)} resultados encontrados')

    def install_repo_handler(self, repo):
        """Handler para instalação de plugin"""
        dialog = Gtk.MessageDialog(transient_for=self, flags=0,
                                   message_type=Gtk.MessageType.QUESTION,
                                   buttons=Gtk.ButtonsType.OK_CANCEL,
                                   text=f"Instalar {repo['name']}?")
        dialog.format_secondary_text("O repositório será baixado como zip e extraído na pasta de plugins do GIMP.")
        response = dialog.run()
        dialog.destroy()
        if response != Gtk.ResponseType.OK:
            return

        t = threading.Thread(target=self._install_thread, args=(repo,))
        t.daemon = True
        t.start()

    def uninstall_repo_handler(self, repo, repo_row=None):
        """Handler para desinstalação de plugin"""
        t = threading.Thread(target=self._uninstall_thread, args=(repo, repo_row))
        t.daemon = True
        t.start()

    def update_repo_handler(self, repo, repo_row=None):
        """Handler para atualização de plugin"""
        t = threading.Thread(target=self._update_thread, args=(repo, repo_row))
        t.daemon = True
        t.start()

    def _install_thread(self, repo):
        try:
            self.set_status(f"Baixando {repo['full_name']}...")
            install_repository_as_plugin(repo, PLUGIN_DEST)
            self.set_status(f"Instalado: {repo['name']}")
            GLib.idle_add(show_info_dialog, self, 'Instalação concluída', f"{repo['name']} instalado em {PLUGIN_DEST}")
            # atualiza o botão correspondente na interface (procura por nome ou prefixo)
            GLib.idle_add(self._mark_repo_installed_in_ui, repo['name'])
            # se estivermos na aba Instalados, atualiza a lista
            sel = self.cat_list.get_selected_row()
            if sel:
                row_content = sel.get_child().get_text()
                if 'Instalados' in row_content:
                    GLib.idle_add(self.show_installed_plugins)
        except Exception as e:
            self.set_status(f"Erro: {e}")
            GLib.idle_add(show_error_dialog, self, 'Erro', str(e))

    def _uninstall_thread(self, repo, repo_row=None):
        """Thread para desinstalar plugin"""
        try:
            plugin_name = repo['name']
            self.set_status(f"Desinstalando {plugin_name}...")
            
            # Encontra o caminho exato do plugin instalado
            plugin_path = None
            if PLUGIN_DEST and os.path.isdir(PLUGIN_DEST):
                for entry in os.listdir(PLUGIN_DEST):
                    if entry == plugin_name or entry.startswith(plugin_name + '-'):
                        plugin_path = os.path.join(PLUGIN_DEST, entry)
                        break
                
                if not plugin_path:
                    exact = os.path.join(PLUGIN_DEST, plugin_name)
                    if os.path.exists(exact):
                        plugin_path = exact
            
            if not plugin_path:
                raise Exception(f'Plugin {plugin_name} não encontrado')
            
            # Remove o plugin
            if os.path.isdir(plugin_path):
                shutil.rmtree(plugin_path)
            else:
                os.remove(plugin_path)
            
            self.set_status(f"Desinstalado: {plugin_name}")
            GLib.idle_add(show_info_dialog, self, 'Desinstalação concluída', 
                         f"{plugin_name} foi removido com sucesso")
            
            # Atualiza a interface
            GLib.idle_add(self._mark_repo_installed_in_ui, plugin_name)
            
            # Se estiver na aba Instalados, atualiza a lista
            sel = self.cat_list.get_selected_row()
            if sel:
                row_content = sel.get_child().get_text()
                if 'Instalados' in row_content:
                    GLib.idle_add(self.show_installed_plugins)
                
        except Exception as e:
            self.set_status(f"Erro na desinstalação: {e}")
            GLib.idle_add(show_error_dialog, self, 'Erro na Desinstalação', str(e))
            if repo_row:
                GLib.idle_add(repo_row.update_button_state)

    def _update_thread(self, repo, repo_row=None):
        """Thread para atualizar plugin"""
        try:
            plugin_name = repo['name']
            self.set_status(f"Atualizando {plugin_name}...")
            
            # Primeiro remove a versão antiga
            plugin_path = None
            if PLUGIN_DEST and os.path.isdir(PLUGIN_DEST):
                for entry in os.listdir(PLUGIN_DEST):
                    if entry == plugin_name or entry.startswith(plugin_name + '-'):
                        plugin_path = os.path.join(PLUGIN_DEST, entry)
                        break
                
                if not plugin_path:
                    exact = os.path.join(PLUGIN_DEST, plugin_name)
                    if os.path.exists(exact):
                        plugin_path = exact
            
            if plugin_path and os.path.exists(plugin_path):
                # Cria backup antes de remover
                backup_path = plugin_path + '.backup'
                if os.path.exists(backup_path):
                    if os.path.isdir(backup_path):
                        shutil.rmtree(backup_path)
                    else:
                        os.remove(backup_path)
                
                shutil.move(plugin_path, backup_path)
                self.set_status(f"Backup criado, baixando nova versão...")
            
            # Instala a nova versão
            install_repository_as_plugin(repo, PLUGIN_DEST)
            
            # Remove o backup se a instalação foi bem-sucedida
            if plugin_path and os.path.exists(backup_path):
                if os.path.isdir(backup_path):
                    shutil.rmtree(backup_path)
                else:
                    os.remove(backup_path)
            
            self.set_status(f"Atualizado: {plugin_name}")
            GLib.idle_add(show_info_dialog, self, 'Atualização concluída', 
                         f"{plugin_name} foi atualizado com sucesso")
            
            # Atualiza a interface
            GLib.idle_add(self._mark_repo_installed_in_ui, plugin_name)
            
        except Exception as e:
            self.set_status(f"Erro na atualização: {e}")
            GLib.idle_add(show_error_dialog, self, 'Erro na Atualização', 
                         f"Falha ao atualizar: {str(e)}\n\nSe houver backup, ele foi preservado.")
            if repo_row:
                GLib.idle_add(repo_row.update_button_state)

    def _mark_repo_installed_in_ui(self, repo_name):
        for child in self.results_box.get_children():
            try:
                if hasattr(child, 'repo') and child.repo.get('name') == repo_name:
                    child.update_button_state()
            except Exception:
                pass

    def apply_dark_theme(self):
        """Aplica tema escuro moderno compatível com GTK3"""
        css_provider = Gtk.CssProvider()
        css = """
        /* Tema Escuro Moderno - pluStore GIMP - GTK3 Compatível */
        
        /* Fundo principal */
        window {
            background-color: #1e1e1e;
            color: #e0e0e0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        /* Header bar moderno */
        .header-bar {
            background: linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%);
            color: white;
            padding: 15px 25px;
            border-bottom: 1px solid #333;
        }
        
        .header-title {
            color: #ffffff;
            font-size: 20px;
            font-weight: bold;
        }
        
        .header-subtitle {
            color: #b0b0b0;
            font-size: 13px;
        }
        
        /* Sidebar escura */
        .sidebar {
            background: linear-gradient(180deg, #2d2d2d 0%, #252525 100%);
            border-right: 1px solid #333;
        }
        
        /* Lista de categorias */
        .category-list {
            background: transparent;
            border: 1px solid #333;
            border-radius: 8px;
            margin: 5px;
        }
        
        .category-list row {
            background: transparent;
            padding: 12px 16px;
            border-bottom: 1px solid #333;
        }
        
        .category-list row:first-child {
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        }
        
        .category-list row:last-child {
            border-bottom: none;
            border-bottom-left-radius: 8px;
            border-bottom-right-radius: 8px;
        }
        
        .category-list row:hover {
            background: #3a3a3a;
        }
        
        .category-list row:selected {
            background: #4a90e2;
            color: white;
        }
        
        /* Área de conteúdo */
        .content-area {
            background: #2d2d2d;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 20px;
        }
        
        /* Barra de pesquisa moderna */
        .search-entry {
            background: #3a3a3a;
            color: #e0e0e0;
            border: 2px solid #444;
            border-radius: 25px;
            padding: 12px 20px;
            font-size: 14px;
        }
        
        .search-entry:focus {
            border-color: #4a90e2;
            background: #404040;
        }
        
        /* Botões modernos */
        button {
            border: none;
            border-radius: 6px;
            padding: 10px 20px;
            font-weight: 600;
            font-size: 13px;
            background: #404040;
            color: #e0e0e0;
        }
        
        button:hover {
            background: #4a4a4a;
        }
        
        /* Botão primário */
        button.primary-button {
            background: #27ae60;
            color: white;
        }
        
        button.primary-button:hover {
            background: #219a52;
        }
        
        /* Botão de ação */
        button.action-button {
            background: #3498db;
            color: white;
        }
        
        button.action-button:hover {
            background: #2980b9;
        }
        
        /* Botão de perigo */
        button.danger-button {
            background: #e74c3c;
            color: white;
        }
        
        button.danger-button:hover {
            background: #c0392b;
        }
        
        /* Cards de plugins */
        .plugin-card {
            background: #3a3a3a;
            border: 1px solid #444;
            border-radius: 12px;
            padding: 20px;
            margin: 10px 5px;
        }
        
        .plugin-card:hover {
            border-color: #555;
        }
        
        /* Status bar escura */
        .status-bar {
            background: #2d2d2d;
            color: #b0b0b0;
            padding: 8px 20px;
            border-top: 1px solid #333;
            font-size: 12px;
        }
        
        /* Scrollbar personalizada */
        scrollbar {
            background: #2d2d2d;
        }
        
        scrollbar slider {
            background: #555;
            border-radius: 8px;
            min-width: 12px;
            min-height: 12px;
        }
        
        scrollbar slider:hover {
            background: #666;
        }
        
        scrollbar slider:active {
            background: #4a90e2;
        }
        
        scrollbar trough {
            background: #2d2d2d;
        }
        
        /* Labels e textos */
        label {
            color: #e0e0e0;
        }
        
        .dim-label {
            color: #888;
        }
        
        /* Separadores */
        separator {
            background: #444;
        }
        
        /* Menu dropdown */
        menu {
            background: #3a3a3a;
            border: 1px solid #555;
            border-radius: 6px;
        }
        
        menuitem {
            background: transparent;
            color: #e0e0e0;
            padding: 8px 20px;
        }
        
        menuitem:hover {
            background: #4a90e2;
            color: white;
        }
        
        /* Entrada de texto */
        entry {
            background: #3a3a3a;
            color: #e0e0e0;
            border: 1px solid #555;
            border-radius: 4px;
            padding: 8px 12px;
        }
        
        entry:focus {
            border-color: #4a90e2;
        }
        """
        
        try:
            css_provider.load_from_data(css.encode('utf-8'))
            screen = self.get_screen()
            style_context = Gtk.StyleContext()
            style_context.add_provider_for_screen(
                screen,
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        except Exception as e:
            print(f"Erro ao carregar CSS: {e}")
    
    def create_header(self):
        """Cria um header bar customizado"""
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        header_box.set_size_request(-1, 70)
        
        # Ícone e título
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title_box.set_margin_start(25)
        title_box.set_margin_top(12)
        title_box.set_margin_bottom(12)
        
        title = Gtk.Label()
        title.set_markup('<span size="x-large" weight="bold">🎨 pluStore GIMP</span>')
        title.set_xalign(0)
        
        subtitle = Gtk.Label()
        subtitle.set_markup('<span size="small">Gerenciador de Plugins para GIMP</span>')
        subtitle.set_xalign(0)
        
        title_box.pack_start(title, False, False, 0)
        title_box.pack_start(subtitle, False, False, 0)
        
        header_box.pack_start(title_box, True, True, 0)
        
        # Botão de info
        info_btn = Gtk.Button.new_from_icon_name('help-about', Gtk.IconSize.BUTTON)
        info_btn.set_relief(Gtk.ReliefStyle.NONE)
        info_btn.set_tooltip_text('Sobre o pluStore GIMP')
        info_btn.connect('clicked', self.show_about_dialog)
        info_btn.set_margin_end(15)
        header_box.pack_end(info_btn, False, False, 0)
        
        return header_box
    
    def show_about_dialog(self, button):
        """Mostra diálogo sobre"""
        dialog = Gtk.AboutDialog()
        dialog.set_transient_for(self)
        dialog.set_program_name('pluStore GIMP')
        dialog.set_version('2.0')
        dialog.set_comments('Gerenciador de Plugins para GIMP\n\nPesquise, instale, atualize e desinstale plugins facilmente.')
        dialog.set_website('https://github.com')
        dialog.set_website_label('GitHub')
        dialog.set_logo_icon_name('gimp')
        dialog.run()
        dialog.destroy()

    def list_installed(self):
        """Lista plugins instalados localmente"""
        items = []
        if not PLUGIN_DEST or not os.path.isdir(PLUGIN_DEST):
            return items
        for entry in sorted(os.listdir(PLUGIN_DEST)):
            p = os.path.join(PLUGIN_DEST, entry)
            if os.path.isdir(p):
                items.append({
                    'name': entry,
                    'owner': {'login': 'local', 'avatar_url': None},
                    'description': 'Plugin instalado localmente',
                    'stargazers_count': 0,
                    'language': ''
                })
        return items

    def show_installed_plugins(self):
        """Mostra plugins instalados na interface"""
        installed = self.list_installed()
        self.populate_results(installed)
        self.set_status(f'{len(installed)} plugins instalados exibidos')


def show_info_dialog(parent, title, message):
    d = Gtk.MessageDialog(transient_for=parent, flags=0, message_type=Gtk.MessageType.INFO,
                          buttons=Gtk.ButtonsType.OK, text=title)
    d.format_secondary_text(message)
    d.run()
    d.destroy()


def show_error_dialog(parent, title, message):
    d = Gtk.MessageDialog(transient_for=parent, flags=0, message_type=Gtk.MessageType.ERROR,
                          buttons=Gtk.ButtonsType.CLOSE, text=title)
    d.format_secondary_text(message)
    d.run()
    d.destroy()


def main():
    print("🚀 Iniciando pluStore GIMP...")
    win = MainWindow()
    win.connect('destroy', Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == '__main__':
    main()