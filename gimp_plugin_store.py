#!/usr/bin/env python3
"""
GIMP Plugin Store - versão corrigida (Python + GTK3)

Funcionalidades principais:
- pesquisa no GitHub por "gimp plugin + categoria"
- instala repositórios baixando o zip do branch padrão e copiando para a pasta de plugins
- permite escolher e salvar a pasta de plugins do usuário
- aba INSTALADOS que mostra plugins já presentes na pasta escolhida
- botão Instalar muda para Instalado após a instalação

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
    def __init__(self, repo, install_cb):
        super().__init__()
        self.repo = repo
        self.install_cb = install_cb

        h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        title = Gtk.Label(xalign=0)
        title.set_markup(f"<b>{GObject.markup_escape_text(repo.get('name',''))}</b> — {GObject.markup_escape_text(repo.get('owner',{}).get('login',''))}")
        desc = Gtk.Label(label=repo.get('description') or 'Sem descrição', xalign=0)
        desc.set_line_wrap(True)
        meta = Gtk.Label(label=f"★ {repo.get('stargazers_count',0)} • {repo.get('language')}", xalign=0)

        v.pack_start(title, False, False, 0)
        v.pack_start(desc, False, False, 0)
        v.pack_start(meta, False, False, 0)

        self.btn = Gtk.Button()
        self.update_button_state()
        self.btn.connect('clicked', self.on_install_clicked)

        h.pack_start(v, True, True, 6)
        h.pack_start(self.btn, False, False, 6)
        self.add(h)

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

    def update_button_state(self):
        if self.is_installed():
            self.btn.set_label('Instalado')
            self.btn.set_sensitive(False)
        else:
            self.btn.set_label('Instalar')
            self.btn.set_sensitive(True)

    def on_install_clicked(self, button):
        self.install_cb(self.repo)


class MainWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title='GIMP Plugin Store')
        self.set_default_size(900, 540)

        # carrega pasta salva (se existir)
        saved = load_saved_folder()
        global PLUGIN_DEST
        if saved and os.path.isdir(saved):
            PLUGIN_DEST = saved

        # layout
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.add(hbox)

        side = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        side.set_size_request(200, -1)
        side.set_margin_top(6)
        side.set_margin_bottom(6)
        side.set_margin_start(6)
        side.set_margin_end(6)

        cat_label = Gtk.Label(label='Categorias', xalign=0)
        side.pack_start(cat_label, False, False, 6)

        choose_btn = Gtk.Button(label='Escolher pasta de plugins')
        choose_btn.connect('clicked', self.on_choose_plugin_folder)
        side.pack_start(choose_btn, False, False, 6)

        self.cat_list = Gtk.ListBox()
        for name in list(CATEGORIES.keys()) + ['Instalados']:
            lbl = Gtk.Label(label=name, xalign=0)
            # evitar método deprecated set_padding: usar margens
            lbl.set_margin_top(6)
            lbl.set_margin_bottom(6)
            lbrow = Gtk.ListBoxRow()
            lbrow.add(lbl)
            self.cat_list.add(lbrow)
        self.cat_list.connect('row-activated', self.on_category_selected)
        side.pack_start(self.cat_list, True, True, 0)

        main_v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        main_v.set_margin_top(6)
        main_v.set_margin_bottom(6)
        main_v.set_margin_start(6)
        main_v.set_margin_end(6)

        search_h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text('Pesquisar (ex: gmic, resynthesizer, removebg...)')
        search_btn = Gtk.Button(label='Pesquisar')
        search_btn.connect('clicked', self.on_search_clicked)
        search_h.pack_start(self.search_entry, True, True, 0)
        search_h.pack_start(search_btn, False, False, 0)
        main_v.pack_start(search_h, False, False, 0)

        self.results_scroller = Gtk.ScrolledWindow()
        self.results_box = Gtk.ListBox()
        self.results_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.results_scroller.add(self.results_box)
        main_v.pack_start(self.results_scroller, True, True, 0)

        # status / caminho atual
        self.status = Gtk.Label(label=f'Pasta de plugins: {PLUGIN_DEST}', xalign=0)
        main_v.pack_start(self.status, False, False, 0)

        hbox.pack_start(side, False, False, 0)
        hbox.pack_start(main_v, True, True, 0)

        # inicializar UI
        self.show_all()
        first_row = self.cat_list.get_row_at_index(0)
        if first_row:
            self.cat_list.select_row(first_row)
            # dispara a pesquisa inicial
            self.on_category_selected(self.cat_list, first_row)

    def set_status(self, text):
        GLib.idle_add(self.status.set_text, text)

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
            if sel and sel.get_child().get_text() == 'Instalados':
                self.show_installed_plugins()
        dialog.destroy()

    def on_category_selected(self, listbox, row):
        label = row.get_child().get_text()
        if label == 'Instalados':
            self.show_installed_plugins()
            return
        genero = CATEGORIES.get(label, '')
        self.search_entry.set_text(genero)
        self.do_search(genero)

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
                row = RepoRow(r, self.install_repo)
                self.results_box.add(row)

        self.results_box.show_all()
        self.set_status('Pronto')

    def install_repo(self, repo):
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
            if sel and sel.get_child().get_text() == 'Instalados':
                GLib.idle_add(self.show_installed_plugins)
        except Exception as e:
            self.set_status(f"Erro: {e}")
            GLib.idle_add(show_error_dialog, self, 'Erro', str(e))

    def _mark_repo_installed_in_ui(self, repo_name):
        for child in self.results_box.get_children():
            try:
                if hasattr(child, 'repo') and child.repo.get('name') == repo_name:
                    child.update_button_state()
            except Exception:
                pass

    def list_installed(self):
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
        installed = self.list_installed()
        self.populate_results(installed)
        self.set_status('Plugins instalados exibidos')

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
