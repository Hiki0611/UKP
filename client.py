
# client.py  (PyQt5 UI - generated)
import sys, json, requests, os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
                             QPushButton, QComboBox, QTextEdit, QHBoxLayout, QListWidget, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

CONFIG_FILE = "config.json"
RAW_BASE = "https://raw.githubusercontent.com/Hiki0611/UKP/main/"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        raise RuntimeError("config.json not found. Run setup_github.py first.")
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_raw(path):
    url = RAW_BASE + path
    r = requests.get(url)
    r.raise_for_status()
    return r.text

def fetch_index():
    txt = get_raw("index.json")
    return json.loads(txt)

def fetch_issue(brand, model, issue):
    path = f"data/brands/{brand}/{model}/{issue}.json"
    txt = get_raw(path)
    return json.loads(txt)

class LoginWindow(QWidget):
    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success
        self.setWindowTitle("Клиент — Вход")
        self.setMinimumSize(420, 220)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        title = QLabel("Клиент — Вход")
        title.setFont(QFont("Arial", 16))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.login_input = QLineEdit(); self.login_input.setPlaceholderText("Логин")
        self.pass_input = QLineEdit(); self.pass_input.setPlaceholderText("Пароль"); self.pass_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.login_input); layout.addWidget(self.pass_input)

        btn = QPushButton("Войти"); btn.clicked.connect(self.try_login)
        layout.addWidget(btn)
        self.setLayout(layout)

    def try_login(self):
        login = self.login_input.text().strip(); pwd = self.pass_input.text().strip()
        if not login or not pwd:
            QMessageBox.warning(self, "Ошибка", "Введите логин и пароль")
            return
        try:
            txt = get_raw("clients.json")
            clients = json.loads(txt)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить clients.json: {e}")
            return
        entry = clients.get(login)
        if entry and entry.get("password") == pwd:
            self.on_success(login)
            self.close()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")

class ClientApp(QWidget):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.setWindowTitle(f"Клиент — {username}")
        self.setMinimumSize(920, 640)
        self._build_ui()
        self.load_index()

    def _build_ui(self):
        self.setStyleSheet("background:#071225;color:#EAF3F8;font-family:Segoe UI;")
        main = QVBoxLayout(); main.setContentsMargins(12,12,12,12)
        title = QLabel(f"Добро пожаловать, {self.username}"); title.setFont(QFont("Arial", 16)); title.setAlignment(Qt.AlignCenter)
        main.addWidget(title)
        # search
        sr = QHBoxLayout()
        self.search_input = QLineEdit(); self.search_input.setPlaceholderText("Поиск по бренду/модели/проблеме...")
        self.search_input.textChanged.connect(self.on_search)
        self.search_scope = QComboBox(); self.search_scope.addItems(["all","brands","models","issues"])
        sr.addWidget(self.search_input); sr.addWidget(self.search_scope)
        main.addLayout(sr)
        # results
        self.results = QListWidget(); self.results.setMaximumHeight(140)
        self.results.itemClicked.connect(self.on_result_clicked)
        main.addWidget(self.results)
        # combos
        combos = QHBoxLayout()
        self.brand_combo = QComboBox(); self.brand_combo.currentIndexChanged.connect(self.update_models)
        self.model_combo = QComboBox(); self.model_combo.currentIndexChanged.connect(self.update_issues)
        self.issue_combo = QComboBox(); self.issue_combo.currentIndexChanged.connect(self.show_instruction)
        combos.addWidget(self.brand_combo,2); combos.addWidget(self.model_combo,2); combos.addWidget(self.issue_combo,3)
        main.addLayout(combos)
        # instruction
        main.addWidget(QLabel("Инструкция:"))
        self.instr = QTextEdit(); self.instr.setReadOnly(True); self.instr.setMinimumHeight(280)
        main.addWidget(self.instr)
        self.setLayout(main)

    def load_index(self):
        try:
            idx = fetch_index()
            self.index = idx
            self.brand_combo.blockSignals(True)
            self.brand_combo.clear()
            for b in sorted(idx.get("brands", {}).keys()):
                self.brand_combo.addItem(b)
            self.brand_combo.blockSignals(False)
            if self.brand_combo.count()>0:
                self.update_models()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить index.json: {e}")

    def update_models(self):
        brand = self.brand_combo.currentText()
        self.model_combo.blockSignals(True); self.model_combo.clear()
        if not brand:
            self.model_combo.blockSignals(False); return
        models = self.index["brands"].get(brand, {}).get("models", {})
        for m in sorted(models.keys()):
            self.model_combo.addItem(m)
        self.model_combo.blockSignals(False)
        if self.model_combo.count()>0:
            self.update_issues()

    def update_issues(self):
        brand = self.brand_combo.currentText(); model = self.model_combo.currentText()
        self.issue_combo.blockSignals(True); self.issue_combo.clear()
        if not brand or not model:
            self.issue_combo.blockSignals(False); return
        issues = self.index["brands"][brand]["models"].get(model, {}).get("issues", [])
        for it in issues:
            self.issue_combo.addItem(it)
        self.issue_combo.blockSignals(False)
        if self.issue_combo.count()>0:
            self.show_instruction()

    def show_instruction(self):
        brand = self.brand_combo.currentText(); model = self.model_combo.currentText(); issue = self.issue_combo.currentText()
        if not brand or not model or not issue:
            self.instr.clear(); return
        try:
            data = fetch_issue(brand, model, issue)
            desc = data.get("description",""); instr = data.get("instruction","")
            text = ""
            if desc: text += f"Описание: {desc}\n\n"
            text += instr
            self.instr.setPlainText(text)
        except Exception as e:
            self.instr.setPlainText(f"Не удалось загрузить инструкцию: {e}")

    def on_search(self, text):
        q = (text or "").strip().lower()
        self.results.clear()
        if not q:
            return
        scope = self.search_scope.currentText()
        for brand, bdata in self.index.get("brands", {}).items():
            if scope in ("all","brands") and q in brand.lower():
                self.results.addItem(f"{brand}")
            for model, mdata in bdata.get("models", {}).items():
                if scope in ("all","models") and q in model.lower():
                    self.results.addItem(f"{brand} / {model}")
                for issue in mdata.get("issues", []):
                    if scope in ("all","issues") and q in issue.lower():
                        self.results.addItem(f"{brand} / {model} / {issue}")

    def on_result_clicked(self, item):
        txt = item.text(); parts = [p.strip() for p in txt.split(" / ")]
        if len(parts)==1:
            b = parts[0]; idx = self.brand_combo.findText(b); 
            if idx>=0: self.brand_combo.setCurrentIndex(idx)
        elif len(parts)==2:
            b,m = parts
            bidx = self.brand_combo.findText(b)
            if bidx>=0:
                self.brand_combo.setCurrentIndex(bidx)
                midx = self.model_combo.findText(m)
                if midx>=0: self.model_combo.setCurrentIndex(midx)
        elif len(parts)==3:
            b,m,i = parts
            bidx = self.brand_combo.findText(b)
            if bidx>=0:
                self.brand_combo.setCurrentIndex(bidx)
                midx = self.model_combo.findText(m)
                if midx>=0:
                    self.model_combo.setCurrentIndex(midx)
                    iidx = self.issue_combo.findText(i)
                    if iidx>=0:
                        self.issue_combo.setCurrentIndex(iidx)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    def on_ok(login):
        w = ClientApp(login); w.show(); sys.exit(app.exec_())
    lw = LoginWindow(on_ok); lw.show(); app.exec_()
