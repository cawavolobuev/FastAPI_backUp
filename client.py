import tkinter as tk
from tkinter import filedialog, messagebox
import requests
from cryptography.fernet import Fernet
import logging
import os
import json

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("client.log"),  # Запись в файл
        logging.StreamHandler(),  # Вывод в консоль
    ],
)
logger = logging.getLogger(__name__)

#BASE_URL = "http://127.0.0.1:8000"
CONFIG_FILE = "config.json"


def load_config():
    """Загрузка конфигурации из локального файла."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def save_config(config):
    """Сохранение конфигурации в локальный файл."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)



class BackupClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Клиент резервного копирования")

        # Загрузка настроек
        self.config = load_config()
        self.base_url = self.config.get("server_url", "http://127.0.0.1:8000")
        self.username = self.config.get("username", "")
        self.password = self.config.get("password", "")
        self.license_key = self.config.get("license_key", "")
        self.license_data = None
        self.signature = None
        self.token = None
        self.encryption_key = None

        # Интерфейс
        self.setup_ui()

    def setup_ui(self):
        """Создание элементов интерфейса."""
        # Поля для сервера, логина и пароля
        tk.Label(self.root, text="Адрес сервера").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.server_entry = tk.Entry(self.root, width=40)
        self.server_entry.insert(0, self.base_url)
        self.server_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self.root, text="Логин").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.username_entry = tk.Entry(self.root, width=40)
        self.username_entry.insert(0, self.username)
        self.username_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(self.root, text="Пароль").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.password_entry = tk.Entry(self.root, show="*", width=40)
        self.password_entry.insert(0, self.password)
        self.password_entry.grid(row=2, column=1, padx=5, pady=5)

        tk.Button(self.root, text="Войти", command=self.login).grid(row=3, column=0, padx=5, pady=10)
        tk.Button(self.root, text="Регистрация", command=self.register).grid(row=3, column=1, padx=5, pady=10)

        # Лицензирование
        tk.Label(self.root, text="Ключ активации").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.license_entry = tk.Entry(self.root, width=40)
        self.license_entry.insert(0, self.license_key)
        self.license_entry.grid(row=4, column=1, padx=5, pady=5)

        tk.Button(self.root, text="Активировать ключ", command=self.activate_license).grid(row=5, column=0, columnspan=2, pady=10)
        tk.Button(self.root, text="Загрузить цифровую лицензию", command=self.load_digital_license).grid(row=6, column=0, columnspan=2, pady=5)

        # Работа с файлами
        tk.Label(self.root, text="Работа с файлами").grid(row=7, column=0, columnspan=2, pady=10)
        tk.Button(self.root, text="Выбрать файл", command=self.select_file).grid(row=8, column=0, padx=5, pady=5)
        tk.Button(self.root, text="Загрузить файл", command=self.upload_file).grid(row=8, column=1, padx=5, pady=5)
        tk.Button(self.root, text="Показать резервные копии", command=self.list_backups).grid(row=9, column=0, columnspan=2, pady=5)

        self.selected_file = None
        self.backup_list = []

    def register(self):
        """Регистрация пользователя."""
        username = self.username_entry.get()
        password = self.password_entry.get()
        try:
            response = requests.post(f"{self.base_url}/register", json={"username": username, "password": password})
            response.raise_for_status()
            data = response.json()
            self.encryption_key = data.get("encryption_key")
            save_config(self.config)
            messagebox.showinfo("Успех", "Регистрация успешна!")
            logger.info(f"Регистрация пользователя {username} выполнена успешно")
        except requests.RequestException as e:
            messagebox.showerror("Ошибка", str(e))
            logger.error(f"Ошибка регистрации: {e}")

    def login(self):
        """Авторизация пользователя."""
        username = self.username_entry.get()
        password = self.password_entry.get()
        try:
            response = requests.post(f"{self.base_url}/token", data={"username": username, "password": password})
            response.raise_for_status()
            data = response.json()
            self.token = data["access_token"]
            self.encryption_key = data["encryption_key"]
            messagebox.showinfo("Успех", "Вход выполнен успешно!")
            logger.info(f"Вход пользователя {username} выполнен успешно")
        except requests.RequestException as e:
            messagebox.showerror("Ошибка", str(e))
            logger.error(f"Ошибка входа: {e}")


    def select_file(self):
        self.selected_file = filedialog.askopenfilename()
        if self.selected_file:
            self.file_label.config(text=f"Выбран файл: {self.selected_file}")
            logger.info(f"Выбран файл {self.selected_file}")

    def upload_file(self):
        if not self.selected_file:
            logger.warning("Попытка загрузки без выбора файла")
            messagebox.showerror("Ошибка", "Файл не выбран")
            return

        try:
            # Шаг 1: Открыть и считать файл
            with open(self.selected_file, "rb") as file:
                data = file.read()
                logger.info(f"Исходный файл считан, размер: {len(data)} байт")

            # Шаг 2: Зашифровать файл
            fernet = Fernet(self.encryption_key.encode())
            encrypted_data = fernet.encrypt(data)
            logger.info(f"Файл зашифрован, размер зашифрованных данных: {len(encrypted_data)} байт")

            # Шаг 3: Подготовить файл для отправки
            files = {"files": (self.selected_file.split("/")[-1], encrypted_data)}
            headers = {"Authorization": f"Bearer {self.token}"}
            if self.license_key:
                headers["License-Key"] = self.license_key
            if self.license_data and self.signature:
                headers.update({"License-Data": self.license_data, "Signature": self.signature})

            # Шаг 4: Отправить файл на сервер
            response = requests.post(f"{self.base_url}/backups/upload", files=files, headers=headers)
            response.raise_for_status()  # Вызывает ошибку, если статус-код != 200
            logger.info(f"Файл {self.selected_file} успешно загружен на сервер")

            # Уведомить пользователя об успехе
            messagebox.showinfo("Успех", "Файл успешно загружен!")

        except requests.RequestException as e:
            logger.error(f"Ошибка при загрузке файла: {e}")
            messagebox.showerror("Ошибка", f"Ошибка при загрузке файла: {e}")

        except Exception as e:
            logger.error(f"Неизвестная ошибка: {e}")
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")

    def list_backups(self):
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/backups/", headers=headers)
            response.raise_for_status()

            # Здесь response.json() возвращает список объектов
            self.backup_list = response.json()

            # Очистить предыдущие кнопки
            for widget in self.backups_frame.winfo_children():
                widget.destroy()

            if not self.backup_list:
                tk.Label(self.backups_frame, text="Нет резервных копий", **self.label_style).pack()
            else:
                for backup in self.backup_list:
                    filename = backup["filename"]  # Извлекаем имя файла
                    btn = tk.Button(
                        self.backups_frame,
                        text=filename,
                        command=lambda b=filename: self.download_backup(b),  # Передаём только имя файла
                        **self.button_style,
                    )
                    btn.pack(pady=2)

        except requests.RequestException as e:
            logger.error(f"Ошибка получения списка резервных копий: {e}")
            messagebox.showerror("Ошибка", str(e))

    def download_backup(self, backup_name):
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/backups/download/{backup_name}", headers=headers)
            response.raise_for_status()
            print("123456")
            print(response)
            # Расшифровка данных
            #fernet = Fernet(self.encryption_key.encode())
            #decrypted_data = fernet.decrypt(response.content)
            print("gfghj")

            # Сохранение файла
            save_path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=backup_name)
            if save_path:
                with open(save_path, "wb") as file:
                    fernet = Fernet(self.encryption_key.encode())
                    decrypted_data = fernet.decrypt(response.content)
                    file.write(decrypted_data)
                logger.info(f"Файл {backup_name} успешно загружен и сохранён в {save_path}")
                messagebox.showinfo("Успех", "Резервная копия загружена и расшифрована!")
        except requests.RequestException as e:
            logger.error(f"Ошибка при скачивании файла {backup_name}: {e}")
            messagebox.showerror("Ошибка", str(e))
        except Exception as e:
            logger.error(f"Ошибка расшифровки файла {backup_name}: {e}")
            messagebox.showerror("Ошибка", f"Ошибка расшифровки: {str(e)}")

    def activate_license(self):
        """Активирует лицензию."""
        self.license_key = self.license_entry.get()
        if not self.license_key:
            messagebox.showerror("Ошибка", "Введите ключ активации!")
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(f"{self.base_url}/licenses/activation-key", headers=headers,
                                 json={"key": self.license_key})
        if response.status_code == 200:
            self.config["license_key"] = self.license_key
            save_config(self.config)
            messagebox.showinfo("Успех", "Лицензия активирована!")
        else:
            messagebox.showerror("Ошибка", f"Не удалось активировать лицензию: {response.text}")

    def load_digital_license(self):
        """Загружает цифровую лицензию из файла."""
        license_path = filedialog.askopenfilename(title="Выберите файл цифровой лицензии",
                                                  filetypes=[("License Files", "*.lic")])
        if not license_path:
            return

        try:
            with open(license_path, "r") as f:
                data = f.read().splitlines()
                self.license_data, self.signature = data[0], data[1]
                self.config.update({"license_data": self.license_data, "signature": self.signature})
                save_config(self.config)
                messagebox.showinfo("Успех", "Цифровая лицензия успешно загружена!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки цифровой лицензии: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = BackupClientApp(root)
    root.mainloop()