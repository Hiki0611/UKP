
# admin.py  (PyQt5 admin UI - generated)
import sys, json, base64, os, requests
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
                             QTextEdit, QHBoxLayout, QComboBox, QListWidget, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from getpass import getpass

CONFIG_FILE = "config.json"
API_BASE = "https://api.github.com"
OWNER = "Hiki0611"
REPO = "UKP"
BRANCH = "main"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        raise RuntimeError("config.json not found. Run setup_github.py first.")
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def gh_headers(token):
    return {"Authorization": f"token {token}", "Accept":"application/vnd.github.v3+json", "User-Agent":"admin-py"}

def get_file_sha_and_content(token, path):
    url = f"{API_BASE}/repos/{OWNER}/{REPO}/contents/{path}?ref={BRANCH}"
    r = requests.get(url, headers=gh_headers(token))
    if r.status_code == 200:
        j = r.json()
        content = base64.b64decode(j["content"]).decode("utf-8")
        return content, j["sha"]
    elif r.status_code == 404:
        return None, None
    else:
        raise Exception(f"Error fetching {path}: {r.status_code} {r.text}")

def put_file(token, path, text_content, message, sha=None):
    url = f"{API_BASE}/repos/{OWNER}/{REPO}/contents/{path}"
    payload = {"message": message, "content": base64.b64encode(text_content.encode("utf-8")).decode("utf-8"), "branch": BRANCH}
    if sha: payload["sha"] = sha
    r = requests.put(url, headers=gh_headers(token), json=payload)
    if r.status_code not in (200,201):
        raise Exception(f"Failed to put {path}: {r.status_code} {r.text}")
    return r.json()

def delete_file(token, path, sha, message):
    url = f"{API_BASE}/repos/{OWNER}/{REPO}/contents/{path}"
    payload = {"message": message, "sha": sha, "branch": BRANCH}
    r = requests.delete(url, headers=gh_headers(token), json=payload)
    if r.status_code not in (200,202):
        raise Exception(f"Failed to delete {path}: {r.status_code} {r.text}")
    return r.json()

# Admin login
class Login(QWidget):
    def __init__(self, on_success):
        super().__init__(); self.on_success = on_success
        self.setWindowTitle("Admin — Вход"); self.setMinimumSize(420,220)
        self._build_ui()
    def _build_ui(self):
        v = QVBoxLayout()
        title = QLabel("Вход администратора"); title.setFont(QFont("Arial",16)); title.setAlignment(Qt.AlignCenter)
        v.addWidget(title)
        self.user = QLineEdit(); self.user.setPlaceholderText("Логин")
        self.pwd = QLineEdit(); self.pwd.setPlaceholderText("Пароль"); self.pwd.setEchoMode(QLineEdit.Password)
        v.addWidget(self.user); v.addWidget(self.pwd)
        btn = QPushButton("Войти"); btn.clicked.connect(self.try_login); v.addWidget(btn)
        self.setLayout(v)
    def try_login(self):
        username = self.user.text().strip(); password = self.pwd.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Введите логин и пароль"); return
        token = load_config().get("token")
        try:
            txt, _ = get_file_sha_and_content(token, "admins.json")
            admins = json.loads(txt)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить admins.json: {e}"); return
        ent = admins.get(username)
        if ent and ent.get("password")==password:
            self.on_success(username); self.close()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверные данные")

class AdminApp(QWidget):
    def __init__(self, username):
        super().__init__(); self.username = username
        self.setWindowTitle(f"Admin — {username}"); self.setMinimumSize(1000,720)
        self.token = load_config().get("token")
        self._build_ui(); self.load_index()
    def _build_ui(self):
        v = QVBoxLayout(); v.setContentsMargins(12,12,12,12)
        title = QLabel("Панель администратора"); title.setFont(QFont("Arial",16)); title.setAlignment(Qt.AlignCenter)
        v.addWidget(title)
        # clients list
        v.addWidget(QLabel("Клиенты (логин | пароль)"))
        hl = QHBoxLayout()
        self.clients_list = QListWidget(); self.clients_list.setMaximumWidth(320)
        hl.addWidget(self.clients_list)
        right_v = QVBoxLayout()
        self.search_input = QLineEdit(); self.search_input.setPlaceholderText("Поиск по брендам/моделям/проблемам..."); self.search_input.textChanged.connect(self.on_search)
        right_v.addWidget(self.search_input)
        combos = QHBoxLayout()
        self.brand_combo = QComboBox(); self.brand_combo.currentIndexChanged.connect(self.on_brand_changed)
        self.model_combo = QComboBox(); self.model_combo.currentIndexChanged.connect(self.on_model_changed)
        self.issue_combo = QComboBox(); self.issue_combo.currentIndexChanged.connect(self.on_issue_changed)
        combos.addWidget(self.brand_combo); combos.addWidget(self.model_combo); combos.addWidget(self.issue_combo)
        right_v.addLayout(combos)
        # add controls
        ar = QHBoxLayout()
        self.new_brand = QLineEdit(); self.new_brand.setPlaceholderText("Новый бренд")
        btn_add_brand = QPushButton("Добавить бренд"); btn_add_brand.clicked.connect(self.add_brand)
        ar.addWidget(self.new_brand); ar.addWidget(btn_add_brand)
        right_v.addLayout(ar)
        ar2 = QHBoxLayout()
        self.new_model = QLineEdit(); self.new_model.setPlaceholderText("Новая модель")
        btn_add_model = QPushButton("Добавить модель"); btn_add_model.clicked.connect(self.add_model)
        ar2.addWidget(self.new_model); ar2.addWidget(btn_add_model)
        right_v.addLayout(ar2)
        ar3 = QHBoxLayout()
        self.new_issue = QLineEdit(); self.new_issue.setPlaceholderText("Новая проблема (issue)")
        btn_add_issue = QPushButton("Добавить проблему"); btn_add_issue.clicked.connect(self.add_issue)
        ar3.addWidget(self.new_issue); ar3.addWidget(btn_add_issue)
        right_v.addLayout(ar3)
        right_v.addWidget(QLabel("Инструкция:"))
        self.instr = QTextEdit(); self.instr.setMinimumHeight(200)
        right_v.addWidget(self.instr)
        instr_buttons = QHBoxLayout()
        btn_save = QPushButton("Сохранить инструкцию"); btn_save.clicked.connect(self.save_instruction)
        btn_delete = QPushButton("Удалить проблему"); btn_delete.clicked.connect(self.delete_issue)
        instr_buttons.addWidget(btn_save); instr_buttons.addWidget(btn_delete)
        right_v.addLayout(instr_buttons)
        hl.addLayout(right_v)
        v.addLayout(hl)
        # clients control
        clients_ctrl = QHBoxLayout()
        self.client_new_user = QLineEdit(); self.client_new_user.setPlaceholderText("Логин клиента")
        self.client_new_pwd = QLineEdit(); self.client_new_pwd.setPlaceholderText("Пароль"); self.client_new_pwd.setEchoMode(QLineEdit.Password)
        btn_add_client = QPushButton("Добавить клиента"); btn_add_client.clicked.connect(self.add_client)
        btn_remove_client = QPushButton("Удалить выбранного"); btn_remove_client.clicked.connect(self.remove_selected_client)
        clients_ctrl.addWidget(self.client_new_user); clients_ctrl.addWidget(self.client_new_pwd); clients_ctrl.addWidget(btn_add_client); clients_ctrl.addWidget(btn_remove_client)
        v.addLayout(clients_ctrl)
        self.setLayout(v)

    def load_index(self):
        try:
            txt, _ = get_file_sha_and_content(self.token, "index.json")
            self.index = json.loads(txt)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить index.json: {e}")
            self.index = {"brands":{}}
        try:
            clients_txt, _ = get_file_sha_and_content(self.token, "clients.json")
            self.clients = json.loads(clients_txt)
        except Exception:
            self.clients = {}
        self.refresh_clients_list()
        self.brand_combo.blockSignals(True); self.brand_combo.clear()
        for b in sorted(self.index.get("brands", {}).keys()):
            self.brand_combo.addItem(b)
        self.brand_combo.blockSignals(False)
        if self.brand_combo.count()>0:
            self.on_brand_changed(None)

    def refresh_clients_list(self):
        self.clients_list.clear()
        for login, info in sorted(self.clients.items()):
            self.clients_list.addItem(f"{login} | {info.get('password','')}")

    def add_client(self):
        u = self.client_new_user.text().strip(); p = self.client_new_pwd.text().strip()
        if not u or not p:
            QMessageBox.warning(self, "Ошибка", "Введите логин и пароль"); return
        if u in self.clients:
            QMessageBox.warning(self, "Ошибка", "Клиент уже существует"); return
        self.clients[u] = {"password": p}
        try:
            _, sha = get_file_sha_and_content(self.token, "clients.json")
            put_file(self.token, "clients.json", json.dumps(self.clients, ensure_ascii=False, indent=2), f"Add client {u}", sha=sha)
            QMessageBox.information(self, "Успех", "Клиент добавлен")
            self.client_new_user.clear(); self.client_new_pwd.clear(); self.refresh_clients_list()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить clients.json: {e}")

    def remove_selected_client(self):
        it = self.clients_list.currentItem()
        if not it:
            QMessageBox.warning(self, "Ошибка", "Выберите клиента"); return
        login = it.text().split(" | ")[0].strip()
        if login not in self.clients:
            QMessageBox.warning(self, "Ошибка", "Клиент не найден"); return
        ok = QMessageBox.question(self, "Подтвердите", f"Удалить клиента {login}?", QMessageBox.Yes|QMessageBox.No)
        if ok != QMessageBox.Yes: return
        del self.clients[login]
        try:
            _, sha = get_file_sha_and_content(self.token, "clients.json")
            put_file(self.token, "clients.json", json.dumps(self.clients, ensure_ascii=False, indent=2), f"Remove client {login}", sha=sha)
            QMessageBox.information(self, "Успех", "Клиент удалён"); self.refresh_clients_list()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить clients.json: {e}")

    def on_brand_changed(self, _):
        brand = self.brand_combo.currentText()
        self.model_combo.blockSignals(True); self.model_combo.clear()
        models = self.index.get("brands", {}).get(brand, {}).get("models", {})
        for m in sorted(models.keys()):
            self.model_combo.addItem(m)
        self.model_combo.blockSignals(False)
        if self.model_combo.count()>0:
            self.on_model_changed(None)

    def on_model_changed(self, _):
        brand = self.brand_combo.currentText(); model = self.model_combo.currentText()
        self.issue_combo.blockSignals(True); self.issue_combo.clear()
        issues = self.index.get("brands", {}).get(brand, {}).get("models", {}).get(model, {}).get("issues", [])
        for i in issues:
            self.issue_combo.addItem(i)
        self.issue_combo.blockSignals(False)
        if self.issue_combo.count()>0:
            self.on_issue_changed(None)

    def on_issue_changed(self, _):
        brand = self.brand_combo.currentText(); model = self.model_combo.currentText(); issue = self.issue_combo.currentText()
        if not brand or not model or not issue:
            self.instr.clear(); return
        try:
            txt, _ = get_file_sha_and_content(self.token, f"data/brands/{brand}/{model}/{issue}.json")
            data = json.loads(txt)
            desc = data.get("description",""); ins = data.get("instruction","")
            text = ""
            if desc: text += f"Описание: {desc}\n\n"
            text += ins
            self.instr.setPlainText(text)
        except Exception as e:
            self.instr.setPlainText(f"Не удалось загрузить инструкцию: {e}")

    def add_brand(self):
        name = self.new_brand.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название бренда"); return
        if name in self.index.get("brands", {}):
            QMessageBox.warning(self, "Ошибка", "Бренд уже существует"); return
        self.index["brands"][name] = {"models": {}}
        self.push_index(f"Add brand {name}")
        self.new_brand.clear(); self.load_index()

    def add_model(self):
        name = self.new_model.text().strip(); brand = self.brand_combo.currentText()
        if not name or not brand:
            QMessageBox.warning(self, "Ошибка", "Введите имя модели и выберите бренд"); return
        models = self.index["brands"].get(brand, {}).get("models", {})
        if name in models:
            QMessageBox.warning(self, "Ошибка", "Модель уже существует"); return
        self.index["brands"][brand]["models"][name] = {"issues": []}
        # create placeholder file to ensure path exists
        sample = {"description":"placeholder","instruction":"placeholder"}
        try:
            put_file(self.token, f"data/brands/{brand}/{name}/Placeholder.json", json.dumps(sample, ensure_ascii=False, indent=2), f"Create placeholder for model {brand}/{name}")
        except Exception:
            pass
        self.push_index(f"Add model {brand}/{name}")
        self.new_model.clear(); self.load_index()

    def add_issue(self):
        name = self.new_issue.text().strip(); brand = self.brand_combo.currentText(); model = self.model_combo.currentText()
        if not name or not brand or not model:
            QMessageBox.warning(self, "Ошибка", "Введите имя проблемы и выберите бренд/модель"); return
        issues = self.index["brands"][brand]["models"][model]["issues"]
        if name in issues:
            QMessageBox.warning(self, "Ошибка", "Проблема уже существует"); return
        data = {"description":"","instruction":"Новая инструкция"}
        try:
            put_file(self.token, f"data/brands/{brand}/{model}/{name}.json", json.dumps(data, ensure_ascii=False, indent=2), f"Add issue {brand}/{model}/{name}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать issue файл: {e}"); return
        self.index["brands"][brand]["models"][model]["issues"].append(name)
        self.push_index(f"Add issue {brand}/{model}/{name}")
        self.new_issue.clear(); self.load_index()

    def save_instruction(self):
        brand = self.brand_combo.currentText(); model = self.model_combo.currentText(); issue = self.issue_combo.currentText()
        if not brand or not model or not issue:
            QMessageBox.warning(self, "Ошибка", "Выберите бренд/модель/проблему"); return
        text = self.instr.toPlainText().strip()
        desc = ""; instr = text
        if text.lower().startswith("описание:"):
            parts = text.split("\n\n",1)
            if len(parts)==2:
                desc = parts[0].replace("Описание:","").strip()
                instr = parts[1].strip()
        data = {"description":desc, "instruction":instr}
        try:
            _, sha = get_file_sha_and_content(self.token, f"data/brands/{brand}/{model}/{issue}.json")
            put_file(self.token, f"data/brands/{brand}/{model}/{issue}.json", json.dumps(data, ensure_ascii=False, indent=2), f"Update instruction {brand}/{model}/{issue}", sha=sha)
            QMessageBox.information(self, "Успех", "Инструкция сохранена")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить инструкцию: {e}")

    def delete_issue(self):
        brand = self.brand_combo.currentText(); model = self.model_combo.currentText(); issue = self.issue_combo.currentText()
        if not brand or not model or not issue:
            QMessageBox.warning(self, "Ошибка", "Выберите проблему"); return
        ok = QMessageBox.question(self, "Подтвердите", f"Удалить проблему {issue}?", QMessageBox.Yes|QMessageBox.No)
        if ok != QMessageBox.Yes: return
        try:
            _, sha = get_file_sha_and_content(self.token, f"data/brands/{brand}/{model}/{issue}.json")
            delete_file(self.token, f"data/brands/{brand}/{model}/{issue}.json", sha, f"Delete issue {brand}/{model}/{issue}")
            self.index["brands"][brand]["models"][model]["issues"].remove(issue)
            self.push_index(f"Remove issue {brand}/{model}/{issue}")
            QMessageBox.information(self, "Успех", "Проблема удалена"); self.load_index()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить проблему: {e}")

    def push_index(self, msg):
        txt = json.dumps(self.index, ensure_ascii=False, indent=2)
        try:
            _, sha = get_file_sha_and_content(self.token, "index.json")
            put_file(self.token, "index.json", txt, msg, sha=sha)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить index.json: {e}")

    def on_search(self, text):
        q = (text or "").strip().lower()
        # naive search: open index in memory
        if not q:
            return
        results = []
        for brand, bdata in self.index.get("brands", {}).items():
            if q in brand.lower(): results.append(f"{brand}")
            for model, mdata in bdata.get("models", {}).items():
                if q in model.lower(): results.append(f"{brand} / {model}")
                for issue in mdata.get("issues", []):
                    if q in issue.lower(): results.append(f"{brand} / {model} / {issue}")
        # show first 10 results as popup for quick navigation
        if results:
            msg = "\\n".join(results[:20])
            QMessageBox.information(self, "Результаты поиска (первые 20)", msg)
        else:
            QMessageBox.information(self, "Результаты поиска", "Ничего не найдено")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    def on_ok(login):
        w = AdminApp(login); w.show(); sys.exit(app.exec_())
    lw = Login(on_ok); lw.show(); app.exec_()
