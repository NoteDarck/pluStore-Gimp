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

Dependências:
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
pip3 install requests
"""

import os
import sys
import tempfile
import zipfile
import stat
import shutil
import threading
import requests
import json
from urllib.parse import quote_plus

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GObject, GLib
except Exception as e:
    print("Erro ao carregar GTK. Instale python3-gi e gir1.2-gtk-3.0.")
    raise

GITHUB_API = "https://api.github.com/search/repositories"
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')  # opcional

# Config file onde salvamos a pasta escolhida
CONFIG_PATH = os.path.expanduser('~/.config/gimp_plugin_store.json')

# Pasta padrão de plugins do GIMP (ajuste se necessário)
DEFAULT_GIMP_PLUGIN_DIRS = [
    os.path.expanduser('~/.config/GIMP/2.10/plug-ins'),
    os.path.expanduser('~/.gimp-2.8/plug-ins'),
]

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
        
        # Info box
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        info_box.set_hexpand(True)

        # Título com ícone
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        plugin_icon = Gtk.Label()
        plugin_icon.set_markup('<span size="large">🔌</span>')
        title_box.pack_start(plugin_icon, False, False, 0)
        
        title = Gtk.Label(xalign=0)
        title.set_markup(f"<span size='large' weight='bold'>{GObject.markup_escape_text(repo.get('name',''))}</span>")
        title_box.pack_start(title, False, False, 0)
        
        # Badge do autor
        author_badge = Gtk.Label()
        author_badge.set_markup(f"<span size='small' color='#666'>por {GObject.markup_escape_text(repo.get('owner',{}).get('login',''))}</span>")
        title_box.pack_start(author_badge, False, False, 8)
        
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
        
        info_box.pack_start(meta_box, False, False, 0)

        card.pack_start(info_box, True, True, 0)

        # Botão de ação estilizado
        self.btn = Gtk.Button()
        self.btn.set_size_request(160, 40)
        self.update_button_state()
        self.btn.connect('clicked', self.on_action_clicked)

        card.pack_start(self.btn, False, False, 0)
        self.add(card)

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
            else:
                # Plugin do GitHub - pode atualizar ou desinstalar
                self.btn.set_label('🔄 Gerenciar')
                self.btn.set_sensitive(True)
        else:
            self.btn.set_label('⬇️ Instalar')
            self.btn.set_sensitive(True)

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
        self.apply_custom_css()

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
        gimp_info.set_markup('<span size="small">🎨 Para GIMP 2.10+</span>')
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

    def apply_custom_css(self):
        """Aplica CSS customizado para melhorar a aparência"""
        css_provider = Gtk.CssProvider()
        css = """
        window {
            background-color: #f5f5f5;
            font-family: sans-serif;
        }
        
        .header-bar {
            background: linear-gradient(to bottom, #4a90e2, #357abd);
            color: white;
            padding: 12px 20px;
            border-bottom: 2px solid #2d5a8c;
        }
        
        .header-title {
            color: white;
            font-size: 18px;
            font-weight: bold;
        }
        
        .header-subtitle {
            color: rgba(255, 255, 255, 0.9);
            font-size: 12px;
        }
        
        button {
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: 500;
            transition: all 0.2s;
        }
        
        button:hover {
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        }
        
        list row:selected {
            background-color: #4a90e2;
            color: white;
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
        header_box.set_size_request(-1, 60)
        
        # Ícone e título
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title_box.set_margin_start(20)
        title_box.set_margin_top(8)
        title_box.set_margin_bottom(8)
        
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
        info_btn.set_margin_end(10)
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
                    'owner': {'login': 'local'},
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
    win = MainWindow()
    win.connect('destroy', Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == '__main__':
    main()