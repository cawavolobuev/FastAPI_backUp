import tkinter as tk
from tkinter import filedialog, messagebox
import requests
from cryptography.fernet import Fernet
import logging

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

BASE_URL = "http://127.0.0.1:8000"


class BackupClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Клиент резервного копирования")
        self.encryption_key = None
        self.token = None

        # Цвета
        self.bg_color = "#F5F5F5"  # Светло-серый фон
        self.button_bg_color = "#4CAF50"  # Зелёный для кнопок
        self.button_fg_color = "#FFFFFF"  # Белый текст на кнопках
        self.label_color = "#212121"  # Тёмно-серый текст
        self.window_bg_color = "#FFFFFF"  # Белый фон окна

        # Стили
        self.button_style = {
            "padx": 10,
            "pady": 5,
            "bg": self.button_bg_color,
            "fg": self.button_fg_color,
            "font": ("Arial", 12),
            "relief": "raised",
            "borderwidth": 2,
        }
        self.label_style = {"font": ("Arial", 14), "fg": self.label_color, "bg": self.bg_color}
        self.frame_style = {"padx": 10, "pady": 10, "bg": self.bg_color}

        # Настройка окна
        self.root.configure(bg=self.window_bg_color)

        # Основной интерфейс
        self.login_frame = tk.Frame(root, **self.frame_style)
        self.main_frame = tk.Frame(root, **self.frame_style)

        # Логин
        tk.Label(self.login_frame, text="Имя пользователя:", **self.label_style).grid(row=0, column=0, sticky="w")
        self.username_entry = tk.Entry(self.login_frame, font=("Arial", 12))
        self.username_entry.grid(row=0, column=1)

        tk.Label(self.login_frame, text="Пароль:", **self.label_style).grid(row=1, column=0, sticky="w")
        self.password_entry = tk.Entry(self.login_frame, font=("Arial", 12), show="*")
        self.password_entry.grid(row=1, column=1)

        self.login_button = tk.Button(self.login_frame, text="Войти", command=self.login, **self.button_style)
        self.login_button.grid(row=2, column=0)

        self.register_button = tk.Button(self.login_frame, text="Регистрация", command=self.register, **self.button_style)
        self.register_button.grid(row=2, column=1)

        self.login_frame.pack()

        # Основные действия
        self.file_label = tk.Label(self.main_frame, text="Файл не выбран", **self.label_style)
        self.file_label.pack()

        self.select_button = tk.Button(self.main_frame, text="Выбрать файл", command=self.select_file, **self.button_style)
        self.select_button.pack()

        self.encrypt_button = tk.Button(self.main_frame, text="Зашифровать и отправить", command=self.upload_file, **self.button_style)
        self.encrypt_button.pack()

        self.list_button = tk.Button(self.main_frame, text="Показать резервные копии", command=self.list_backups, **self.button_style)
        self.list_button.pack()

        self.backups_frame = tk.Frame(self.main_frame, **self.frame_style)
        self.backups_frame.pack()

        self.selected_file = None
        self.backup_list = []

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        try:
            response = requests.post(f"{BASE_URL}/token", data={"username": username, "password": password})
            response.raise_for_status()
            data = response.json()
            self.token = data["access_token"]
            self.encryption_key = data["encryption_key"]
            messagebox.showinfo("Успех", "Вход выполнен успешно!")
            logger.info(f"Вход пользователя {username} выполнен успешно")
            self.login_frame.pack_forget()
            self.main_frame.pack()
        except requests.RequestException as e:
            messagebox.showerror("Ошибка", str(e))
            logger.warning(f"Неудачная попытка входа c логином {username}")

    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        try:
            response = requests.post(f"{BASE_URL}/register", json={"username": username, "password": password})
            response.raise_for_status()
            data = response.json()
            self.encryption_key = data["encryption_key"]
            messagebox.showinfo("Успех", "Регистрация успешна!")
            logger.info(f"Регистрация пользователя {username} выполнена успешно")
        except requests.RequestException as e:
            messagebox.showerror("Ошибка", str(e))
            logger.info("Неудачная регистрация пользователя")

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
            headers = {
                "Authorization": f"Bearer {self.token}",
                "License-Key": license_key,  # Если используется ключ активации
                "License-Data": license_data,  # Если используется цифровая лицензия
                "Signature": signature,  # Подпись для цифровой лицензии
            }
            # Шаг 4: Отправить файл на сервер
            response = requests.post(f"{BASE_URL}/backups/upload", files=files, headers=headers)
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
            response = requests.get(f"{BASE_URL}/backups/", headers=headers)
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
            response = requests.get(f"{BASE_URL}/backups/download/{backup_name}", headers=headers)
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


if __name__ == "__main__":
    root = tk.Tk()
    app = BackupClientApp(root)
    root.mainloop()