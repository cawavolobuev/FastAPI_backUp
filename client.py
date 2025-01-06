import tkinter as tk
from tkinter import messagebox, filedialog
import requests
import json
import os
import logging
from cryptography.fernet import Fernet

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("client.log"),  # Логирование в файл
        logging.StreamHandler(),  # Логирование в консоль
    ],
)
logger = logging.getLogger("BackupClient")

CONFIG_FILE = "config.json"


def load_config():
    """Загрузка конфигурации."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def save_config(config):
    """Сохранение конфигурации."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Клиент резервного копирования")
        self.geometry("500x400")
        self.config = load_config()

        # Хранилище токена и ключей
        self.token = None
        self.license_key = self.config.get("license_key", "")

        # Контейнер для страниц
        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)

        # Словарь страниц
        self.frames = {}

        # Инициализация страниц
        for Page in (RegisterPage, LoginPage, MainPage, LicensePage):
            page_name = Page.__name__
            frame = Page(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Переход на страницу входа
        self.show_frame("LoginPage")

    def show_frame(self, page_name):
        """Отображение страницы по имени."""
        frame = self.frames[page_name]
        frame.tkraise()
        logger.info(f"Переход на страницу: {page_name}")


class RegisterPage(tk.Frame):
    """Страница регистрации."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Регистрация", font=("Arial", 16)).pack(pady=10)

        tk.Label(self, text="Логин").pack(pady=5)
        self.username_entry = tk.Entry(self, width=30)
        self.username_entry.pack()

        tk.Label(self, text="Пароль").pack(pady=5)
        self.password_entry = tk.Entry(self, show="*", width=30)
        self.password_entry.pack()

        tk.Button(self, text="Зарегистрироваться", command=self.register).pack(pady=10)
        tk.Button(self, text="Назад", command=lambda: controller.show_frame("LoginPage")).pack()

    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        try:
            response = requests.post(f"http://127.0.0.1:8000/register",
                                     json={"username": username, "password": password})
            response.raise_for_status()
            messagebox.showinfo("Успех", "Регистрация выполнена!")
            logger.info(f"Регистрация пользователя {username} выполнена успешно")
            self.controller.show_frame("LoginPage")
        except requests.RequestException as e:
            logger.error(f"Ошибка регистрации пользователя {username}: {e}")
            messagebox.showerror("Ошибка", f"Ошибка регистрации: {e}")


class LoginPage(tk.Frame):
    """Страница входа."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.encryption_key = None
        self.controller = controller

        tk.Label(self, text="Вход в систему", font=("Arial", 16)).pack(pady=10)

        tk.Label(self, text="Логин").pack(pady=5)
        self.username_entry = tk.Entry(self, width=30)
        self.username_entry.pack()

        tk.Label(self, text="Пароль").pack(pady=5)
        self.password_entry = tk.Entry(self, show="*", width=30)
        self.password_entry.pack()

        tk.Button(self, text="Войти", command=self.login).pack(pady=10)
        tk.Button(self, text="Регистрация", command=lambda: controller.show_frame("RegisterPage")).pack()

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        try:
            response = requests.post(f"http://127.0.0.1:8000/token", data={"username": username, "password": password})
            response.raise_for_status()
            data = response.json()
            self.controller.token = data["access_token"]
            self.controller.encryption_key = data["encryption_key"]
            messagebox.showinfo("Успех", "Вход выполнен успешно!")
            logger.info(f"Пользователь {username} вошёл в систему")
            self.controller.show_frame("MainPage")
        except requests.RequestException as e:
            logger.error(f"Ошибка входа пользователя {username}: {e}")
            messagebox.showerror("Ошибка", f"Ошибка входа: {e}")


"""
class LicenseRequestPage(tk.Frame):
    Страница получения лицензии или цифровой подписи.

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Запрос лицензии", font=("Arial", 16)).pack(pady=10)

        tk.Button(self, text="Получить ключ активации", command=self.get_license_key).pack(pady=5)
        tk.Button(self, text="Скачать файл лицензии", command=self.download_license_file).pack(pady=5)
        tk.Button(self, text="Назад", command=lambda: controller.show_frame("LicensePage")).pack(pady=10)

    def get_license_key(self):
        Запрос ключа активации с сервера.
        headers = {"Authorization": f"Bearer {self.controller.token}"}
        try:
            response = requests.post(f"http://127.0.0.1:8000/licenses/generate", headers=headers)
            response.raise_for_status()
            license_data = response.json()
            messagebox.showinfo("Успех", f"Ключ активации: {license_data['key']}")
            logger.info(f"Получен ключ активации: {license_data['key']}")
        except requests.RequestException as e:
            logger.error(f"Ошибка получения ключа активации: {e}")
            messagebox.showerror("Ошибка", f"Ошибка получения ключа активации: {e}")

    def download_license_file(self):
        Скачать файл лицензии с сервера.
        headers = {"Authorization": f"Bearer {self.controller.token}"}
        try:
            response = requests.get(f"http://127.0.0.1:8000/licenses/download", headers=headers)
            response.raise_for_status()
            file_data = response.content

            save_path = filedialog.asksaveasfilename(defaultextension=".lic", title="Сохранить файл лицензии")
            if save_path:
                with open(save_path, "wb") as f:
                    f.write(file_data)
                messagebox.showinfo("Успех", "Файл лицензии успешно сохранён!")
                logger.info(f"Файл лицензии сохранён в {save_path}")
        except requests.RequestException as e:
            logger.error(f"Ошибка скачивания файла лицензии: {e}")
            messagebox.showerror("Ошибка", f"Ошибка скачивания файла лицензии: {e}")
"""


class MainPage(tk.Frame):
    """Главная страница."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Заголовок страницы
        tk.Label(self, text="Главная страница", font=("Arial", 16)).pack(pady=10)

        # Кнопки операций
        button_frame = tk.Frame(self)
        button_frame.pack(pady=5)

        tk.Button(button_frame, text="Выбрать файл для загрузки", command=self.upload_file).grid(row=0, column=0,
                                                                                                 padx=5)
        tk.Button(button_frame, text="Показать резервные копии", command=self.list_backups).grid(row=0, column=1,
                                                                                                 padx=5)

        # Список резервных копий
        self.backup_listbox = tk.Listbox(self, width=80, height=10)
        self.backup_listbox.pack(pady=10)

        # Кнопки для работы с резервными копиями
        operation_frame = tk.Frame(self)
        operation_frame.pack(pady=5)

        tk.Button(operation_frame, text="Скачать выбранную резервную копию", command=self.download_backup).grid(row=0,
                                                                                                                column=0,
                                                                                                                padx=5)
        tk.Button(operation_frame, text="Удалить выбранную резервную копию", command=self.delete_backup).grid(row=0,
                                                                                                              column=1,
                                                                                                              padx=5)

        # Кнопка активации лицензии
        tk.Button(self, text="Активировать лицензию", command=lambda: controller.show_frame("LicensePage")).pack(
            pady=10)

    def encrypt_file(self, file_path, key):
        """Шифрование файла перед отправкой на сервер."""
        cipher = Fernet(key)
        with open(file_path, 'rb') as f:
            encrypted_data = cipher.encrypt(f.read())
        encrypted_file_path = file_path + ".enc"
        with open(encrypted_file_path, 'wb') as f:
            f.write(encrypted_data)
        return encrypted_file_path

    def decrypt_file(self, file_path, key):
        """Расшифровка файла после скачивания."""
        cipher = Fernet(key)
        with open(file_path, 'rb') as f:
            decrypted_data = cipher.decrypt(f.read())
        with open(file_path[:-4], 'wb') as f:
            f.write(decrypted_data)
        os.remove(file_path)

    def upload_file(self):
        """Загрузка файла на сервер."""
        file_path = filedialog.askopenfilename()
        if not file_path:
            logger.warning("Попытка загрузки файла без выбора файла")
            return

        if not self.controller.encryption_key:
            logger.error("Отсутствует ключ шифрования")
            messagebox.showerror("Ошибка", "Не удалось загрузить файл: отсутствует ключ шифрования")
            return

        headers = {"Authorization": f"Bearer {self.controller.token}"}
        try:
            file_path = self.encrypt_file(file_path, self.controller.encryption_key)
            with open(file_path, "rb") as f:
                file_data = f.read()
            files = {"files": (os.path.basename(file_path), file_data)}
            response = requests.post(f"http://127.0.0.1:8000/backups/upload", headers=headers, files=files)
            response.raise_for_status()
            messagebox.showinfo("Успех", "Файл успешно загружен!")
            logger.info(f"Файл {os.path.basename(file_path)} успешно загружен")
        except requests.RequestException as e:
            logger.error(f"Ошибка загрузки файла {os.path.basename(file_path)}: {e}")
            messagebox.showerror("Ошибка", f"Ошибка загрузки файла: {e}")

    def list_backups(self):
        """Получение списка резервных копий с сервера и обновление интерфейса."""
        headers = {"Authorization": f"Bearer {self.controller.token}"}
        try:
            # Получение данных с сервера
            response = requests.get(f"http://127.0.0.1:8000/backups", headers=headers)
            response.raise_for_status()

            backups = response.json()  # Обновлённый список резервных копий
            logger.info("Список резервных копий успешно получен")

            # Очистка списка
            self.backup_listbox.delete(0, tk.END)

            # Обновление списка
            for backup in backups:
                display_text = f"{backup['filename']} | {backup['size']} байт | {backup['upload_date']}"
                self.backup_listbox.insert(tk.END, display_text)

        except requests.RequestException as e:
            logger.error(f"Ошибка получения списка резервных копий: {e}")
            messagebox.showerror("Ошибка", f"Ошибка получения списка: {e}")

    def delete_backup(self):
        """Удаление выбранной резервной копии."""
        selection = self.backup_listbox.curselection()
        if not selection:
            messagebox.showerror("Ошибка", "Выберите резервную копию для удаления!")
            return

        selected_item = self.backup_listbox.get(selection[0])
        filename = selected_item.split(" | ")[0]  # Извлекаем имя файла из строки

        headers = {"Authorization": f"Bearer {self.controller.token}"}
        try:
            response = requests.delete(f"http://127.0.0.1:8000/backups/{filename}", headers=headers)
            response.raise_for_status()
            messagebox.showinfo("Успех", f"Резервная копия {filename} успешно удалена!")
            logger.info(f"Резервная копия {filename} успешно удалена")

            # Обновляем список резервных копий
            self.list_backups()
        except requests.RequestException as e:
            logger.error(f"Ошибка удаления резервной копии {filename}: {e}")
            messagebox.showerror("Ошибка", f"Ошибка удаления резервной копии: {e}")

    def download_backup(self):
        """Скачивание выбранной резервной копии."""
        selection = self.backup_listbox.curselection()
        if not selection:
            messagebox.showerror("Ошибка", "Выберите резервную копию для скачивания!")
            return

        selected_item = self.backup_listbox.get(selection[0])
        filename = selected_item.split(" | ")[0]  # Извлекаем имя файла из строки

        headers = {"Authorization": f"Bearer {self.controller.token}"}
        try:
            response = requests.get(f"http://127.0.0.1:8000/backups/download/{filename}", headers=headers)
            response.raise_for_status()

            save_path = filedialog.asksaveasfilename(defaultextension=".enc", initialfile=filename)
            if save_path:
                with open(save_path, "wb") as f:
                    f.write(response.content)
                self.decrypt_file(save_path, self.controller.encryption_key)
                messagebox.showinfo("Успех", f"Резервная копия {filename} успешно загружена!")
                logger.info(f"Резервная копия {filename} успешно загружена и сохранена в {save_path}")
        except requests.RequestException as e:
            logger.error(f"Ошибка скачивания резервной копии {filename}: {e}")
            messagebox.showerror("Ошибка", f"Ошибка скачивания резервной копии: {e}")


class LicensePage(tk.Frame):
    """Страница активации лицензии."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Активация лицензии", font=("Arial", 16)).pack(pady=10)

        tk.Label(self, text="Ключ лицензии").pack(pady=5)
        self.license_entry = tk.Entry(self, width=30)
        self.license_entry.pack()

        tk.Button(self, text="Активировать ключ", command=self.activate_license).pack(pady=10)
        tk.Label(self, text="Или загрузите файл лицензии:").pack(pady=10)

        tk.Button(self, text="Выбрать файл лицензии", command=self.select_license_file).pack(pady=5)
        self.file_label = tk.Label(self, text="Файл не выбран", font=("Arial", 10))
        self.file_label.pack()

        tk.Button(self, text="Активировать через файл", command=self.activate_license_from_file).pack(pady=10)
        tk.Button(self, text="Перейти к главной", command=lambda: controller.show_frame("MainPage")).pack()

        self.selected_file = None  # Выбранный файл лицензии

    def activate_license(self):
        """Активация лицензии по ключу."""
        license_key = self.license_entry.get()
        if not license_key:
            messagebox.showerror("Ошибка", "Введите ключ лицензии!")
            logger.warning("Попытка активации без ввода ключа лицензии")
            return

        headers = {"Authorization": f"Bearer {self.controller.token}"}
        try:
            response = requests.post(
                f"http://127.0.0.1:8000/licenses/activation-key",
                headers=headers,
                json={"key": license_key}
            )
            response.raise_for_status()
            self.controller.license_key = license_key
            messagebox.showinfo("Успех", "Лицензия активирована!")
            logger.info(f"Лицензия с ключом {license_key} активирована")
        except requests.RequestException as e:
            logger.error(f"Ошибка активации лицензии: {e}")
            messagebox.showerror("Ошибка", f"Ошибка активации лицензии: {e}")

    def select_license_file(self):
        """Выбор файла лицензии."""
        self.selected_file = filedialog.askopenfilename(
            title="Выберите файл лицензии",
            filetypes=[("License Files", "*.lic")]
        )
        if self.selected_file:
            self.file_label.config(text=f"Выбран файл: {os.path.basename(self.selected_file)}")
            logger.info(f"Выбран файл лицензии: {self.selected_file}")

    def activate_license_from_file(self):
        """Активация лицензии через файл."""
        if not self.selected_file:
            messagebox.showerror("Ошибка", "Файл лицензии не выбран!")
            logger.warning("Попытка активации без выбора файла лицензии")
            return

        try:
            # Читаем файл лицензии
            with open(self.selected_file, "r") as f:
                license_data = f.read()

            # Разделяем данные и подпись
            try:
                data, signature = license_data.rsplit("\n", 1)
            except ValueError:
                raise ValueError("Формат файла лицензии неверный!")

            headers = {"Authorization": f"Bearer {self.controller.token}"}
            payload = {"license_data": data, "signature": signature}

            # Отправляем данные для проверки
            response = requests.post(f"http://127.0.0.1:8000/licenses/verify", headers=headers, json=payload)
            response.raise_for_status()

            # Проверяем ответ
            if response.json().get("valid"):
                messagebox.showinfo("Успех", "Лицензия успешно активирована!")
                logger.info(f"Лицензия из файла {self.selected_file} успешно активирована")
            else:
                messagebox.showerror("Ошибка", "Лицензия недействительна!")
                logger.error(f"Лицензия из файла {self.selected_file} недействительна")
        except FileNotFoundError:
            logger.error("Файл лицензии не найден")
            messagebox.showerror("Ошибка", "Файл лицензии не найден!")
        except ValueError as e:
            logger.error(f"Ошибка формата файла лицензии: {e}")
            messagebox.showerror("Ошибка", "Формат файла лицензии неверный!")
        except requests.RequestException as e:
            logger.error(f"Ошибка активации лицензии через файл: {e}")
            messagebox.showerror("Ошибка", f"Ошибка активации лицензии: {e}")


if __name__ == "__main__":
    app = Application()
    app.mainloop()
