import sys
import os
import json
import subprocess
import webbrowser  # Добавили для открытия ссылки
import customtkinter as ctk
from tkinter import filedialog

# Добавляем пути к Core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.generator import OVPNGenerator
from core.ssh_client import MikroTikSSH
from core.keepass_client import KeePassProvider

# Настройки темы
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("MikroTik OVPN Deployer + KeePass")
        self.geometry("550x920") # Немного увеличил высоту для комфорта

        # Переменные путей
        self.excel_path = ""
        self.kp_db_path = ""
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.files_dir = os.path.join(self.base_dir, "files")
        self.config_path = os.path.join(self.base_dir, "config.json")

        # --- ВЕРХНЯЯ ПАНЕЛЬ (Кнопка 1 и Метка 2) ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=10, pady=(5, 0))

        # 1. Кнопка с ссылкой на инструкцию
        self.btn_help = ctk.CTkButton(
            self.header_frame,
            text="Инструкция",
            width=100,
            height=25,
            fg_color="#4A4A4A",
            hover_color="#666666",
            command=self.open_manual
        )
        self.btn_help.pack(side="left")

        # 2. Текстовая метка D.ihoshyn IOC
        self.label_author = ctk.CTkLabel(
            self.header_frame,
            text="D.ihoshyn IOC",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#888888"
        )
        self.label_author.pack(side="right")

        # --- UI Элементы ---
        self.label_title = ctk.CTkLabel(self, text="OVPN Account Generator", font=ctk.CTkFont(size=20, weight="bold"))
        self.label_title.pack(pady=(10, 15))

        # Секция выбора файла Excel
        self.file_frame = ctk.CTkFrame(self)
        self.file_frame.pack(pady=5, padx=20, fill="x")
        self.btn_select_file = ctk.CTkButton(self.file_frame, text="Выбрать Excel", command=self.select_file)
        self.btn_select_file.pack(pady=10, padx=10)
        self.label_file = ctk.CTkLabel(self.file_frame, text="Файл Excel не выбран", wraplength=400)
        self.label_file.pack(pady=5)

        # Секция: KeePass
        self.kp_frame = ctk.CTkFrame(self, fg_color="#2b2b2b")
        self.kp_frame.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(self.kp_frame, text="Интеграция с KeePass", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        self.btn_kp_file = ctk.CTkButton(self.kp_frame, text="Выбрать Базу .kdbx", command=self.select_kp_db, fg_color="#3d3d3d")
        self.btn_kp_file.pack(pady=5, padx=10)
        self.label_kp_file = ctk.CTkLabel(self.kp_frame, text="База не выбрана", font=ctk.CTkFont(size=11))
        self.label_kp_file.pack(pady=2)
        self.entry_kp_master = ctk.CTkEntry(self.kp_frame, placeholder_text="Мастер-пароль KeePass", show="*")
        self.entry_kp_master.pack(pady=10, padx=10, fill="x")

        # Секция параметров SSH
        self.ssh_frame = ctk.CTkFrame(self)
        self.ssh_frame.pack(pady=10, padx=20, fill="x")
        self.entry_host = ctk.CTkEntry(self.ssh_frame, placeholder_text="IP MikroTik (Host в KeePass)")
        self.entry_host.pack(pady=5, padx=10, fill="x")
        self.entry_user = ctk.CTkEntry(self.ssh_frame, placeholder_text="Логин SSH (если нет в KeePass)")
        self.entry_user.pack(pady=5, padx=10, fill="x")
        self.entry_password = ctk.CTkEntry(self.ssh_frame, placeholder_text="Пароль SSH (если нет в KeePass)", show="*")
        self.entry_password.pack(pady=5, padx=10, fill="x")

        # Секция выбора профиля
        self.profile_frame = ctk.CTkFrame(self)
        self.profile_frame.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(self.profile_frame, text="Профиль MikroTik:").pack(side="left", padx=15)
        self.profile_var = ctk.StringVar(value="UFD")
        self.profile_menu = ctk.CTkOptionMenu(self.profile_frame, values=["UFD", "Cascad"], variable=self.profile_var)
        self.profile_menu.pack(side="right", padx=15, pady=10)

        # Кнопки управления
        self.btn_run = ctk.CTkButton(self, text="Запустить процесс", command=self.start_process, fg_color="green", hover_color="#006400")
        self.btn_run.pack(pady=10)
        self.btn_open_creds = ctk.CTkButton(self, text="Открыть файл с паролями", command=self.open_credentials, fg_color="transparent", border_width=2)
        self.btn_open_creds.pack(pady=5)

        # Лог событий
        self.status_text = ctk.CTkTextbox(self, height=150)
        self.status_text.pack(pady=10, padx=20, fill="both", expand=True)

        self.load_config()

    def open_manual(self):
        # Замени на реальную ссылку
        webbrowser.open("https://github.com/DIhoshyn/GenerateAKK/blob/master/INSTRUCTIONS.md")

    def log(self, message):
        self.status_text.insert("end", message + "\n")
        self.status_text.see("end")

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    config = json.load(f)
                    self.entry_host.insert(0, config.get("host", ""))
                    self.entry_user.insert(0, config.get("user", ""))
                    self.kp_db_path = config.get("kp_path", "")
                    if self.kp_db_path:
                        self.label_kp_file.configure(text=os.path.basename(self.kp_db_path))
            except: pass

    def save_config(self, host, user, kp_path):
        with open(self.config_path, "w") as f:
            json.dump({"host": host, "user": user, "kp_path": kp_path}, f)

    def select_file(self):
        path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if path:
            self.excel_path = path
            self.label_file.configure(text=os.path.basename(path))
            self.log(f"📁 Excel: {os.path.basename(path)}")

    def select_kp_db(self):
        path = filedialog.askopenfilename(filetypes=[("KeePass DB", "*.kdbx")])
        if path:
            self.kp_db_path = path
            self.label_kp_file.configure(text=os.path.basename(path))
            self.log(f"🔑 KeePass: {os.path.basename(path)}")

    def open_credentials(self):
        creds_path = os.path.join(self.files_dir, "credentials.txt")
        if os.path.exists(creds_path):
            if sys.platform == "win32": os.startfile(creds_path)
            elif sys.platform == "darwin": subprocess.call(["open", creds_path])
            else: subprocess.call(["xdg-open", creds_path])
        else: self.log("⚠️ Файл паролей еще не создан.")

    def start_process(self):
        if not self.excel_path:
            self.log("❌ Ошибка: Выберите Excel!")
            return

        host = self.entry_host.get().strip()
        user = self.entry_user.get().strip()
        pwd = self.entry_password.get().strip()
        kp_master = self.entry_kp_master.get().strip()
        selected_profile = self.profile_var.get()

        if self.kp_db_path and kp_master:
            self.log("🔍 Поиск в KeePass...")
            kp = KeePassProvider(self.kp_db_path, kp_master)
            success_kp, msg_kp = kp.connect()
            if success_kp:
                creds = kp.get_credentials(host)
                if creds:
                    user, pwd = creds['username'], creds['password']
                    self.log(f"✅ Данные из KeePass получены.")
                else: self.log(f"⚠️ Запись '{host}' не найдена.")
            else:
                self.log(f"❌ {msg_kp}")
                return

        if not all([host, user, pwd]):
            self.log("❌ Ошибка: Нет данных SSH!")
            return

        self.save_config(host, user, self.kp_db_path)

        self.log(f"⏳ Генерация (Profile: {selected_profile})...")
        gen = OVPNGenerator(output_dir=self.files_dir)
        try:
            local_rsc, _ = gen.process_excel(self.excel_path, profile=selected_profile)
            self.log(f"✅ Скрипты готовы.")

            self.log(f"🔗 Подключение {host}...")
            mt = MikroTikSSH(host, user, pwd)
            success_conn, msg_conn = mt.connect()
            if not success_conn:
                self.log(f"❌ {msg_conn}")
                return

            self.log("🚀 Загрузка и импорт...")
            success_run, msg_run = mt.upload_and_run(local_rsc)
            self.log(f"{'🎉' if success_run else '❌'} {msg_run}")
        except Exception as e: self.log(f"🔥 Ошибка: {str(e)}")

if __name__ == "__main__":
    app = App()
    app.mainloop()