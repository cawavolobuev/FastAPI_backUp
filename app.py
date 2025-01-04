import os
import logging
import base64
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Request, Header, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, Response
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, declarative_base, relationship
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import List, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_public_key, load_pem_private_key
from starlette.responses import FileResponse
from datetime import datetime, timedelta
from hashlib import sha256
#from models import License, User
#from schemas import LicenseCreate, LicenseResponse
import uuid
from fastapi.staticfiles import StaticFiles

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("server.log"),  # Запись в файл
        logging.StreamHandler(),  # Вывод в консоль
    ],
)
logger = logging.getLogger(__name__)


# Настройка базы данных
DATABASE_URL = "sqlite:///./backup_system.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Хэширование паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройка OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

# Константы
BACKUP_DIR = "./backups"  # Основная папка для хранения резервных копий
os.makedirs(BACKUP_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Определение моделей базы данных
class Backup(Base):
    __tablename__ = "backups"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    size = Column(Float, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    checksum = Column(String, nullable=False)  # Новое поле

    user = relationship("User", back_populates="backups")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    encryption_key = Column(String)  # Уникальный ключ шифрования
    backups = relationship("Backup", back_populates="user")
    licenses = relationship("License", back_populates="user")

class License(Base):
    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False)  # Ключ активации
    is_active = Column(Boolean, default=False)  # Статус активации
    license_data = Column(String, nullable=True)  # Данные цифровой лицензии
    signature = Column(String, nullable=True)  # Подпись цифровой лицензии
    user_id = Column(Integer, ForeignKey("users.id"))  # Привязка к пользователю

    user = relationship("User", back_populates="licenses")

class LicenseActivationRequest(BaseModel):
    key: str

Base.metadata.create_all(bind=engine)

# Pydantic модели
class UserCreate(BaseModel):
    username: str
    password: str

class LicenseCreate(BaseModel):
    key: str

class LicenseResponse(BaseModel):
    id: int
    key: str
    is_active: bool
    user_id: int | None = None

    class Config:
        orm_mode = True


# Вспомогательные функции
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


"""
def generate_activation_key() -> str:
    return str(uuid.uuid4()).replace("-", "").upper()[:16]

def check_activation_key(user_id: int, license_key: str, db: SessionLocal) -> bool:
    license = db.query(License).filter(
        License.user_id == user_id,
        License.license_type == "activation_key",
        License.license_key == license_key,
        License.is_active == True
    ).first()

    if not license or (license.expires_at and license.expires_at < datetime.utcnow()):
        return False
    return True


def sign_license(data: str, private_key_path: str) -> bytes:
    with open(private_key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    signature = private_key.sign(
        data.encode(),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256()
    )
    return signature

def verify_license(data: str, signature: bytes, public_key_path: str) -> bool:
    with open(public_key_path, "rb") as f:
        public_key = serialization.load_pem_public_key(f.read())

    try:
        public_key.verify(
            signature,
            data.encode(),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False

def check_license(
    current_user: User,
    db: SessionLocal,
    license_key: Optional[str] = None,
    license_data: Optional[str] = None,
    signature: Optional[str] = None,
) -> str:
   
    if license_key and check_activation_key(current_user.id, license_key, db):
        return "activation_key"

    if license_data and signature and verify_license(license_data, bytes.fromhex(signature), "public_key.pem"):
        return "digital_signature"

    raise HTTPException(status_code=403, detail="Лицензия недействительна или истекла")
"""

def get_password_hash(password: str):
    return pwd_context.hash(password)

def generate_encryption_key():
    """Создает уникальный ключ шифрования."""
    return Fernet.generate_key().decode()

def authenticate_user(db, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        return False
    return user

def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    user = db.query(User).filter(User.id == int(token)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def get_user_backup_dir(user_id: int):
    """Получить путь к папке пользователя для хранения резервных копий."""
    user_dir = os.path.join(BACKUP_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

def sign_license(data: str, private_key_path: str) -> str:
    """
    Подписать данные лицензии с использованием приватного ключа.

    :param data: Строка данных лицензии.
    :param private_key_path: Путь к приватному ключу в формате PEM.
    :return: Подпись в виде строки Base64.
    """
    with open(private_key_path, "rb") as f:
        private_key = load_pem_private_key(f.read(), password=None)

    signature = private_key.sign(
        data.encode(),
        padding.PKCS1v15(),
        hashes.SHA256()
    )

    return base64.b64encode(signature).decode()



# Маршруты
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def admin_panel(request: Request, db: Session = Depends(get_db)):
    users = db.query(User).all()
    return templates.TemplateResponse("admin.html", {"request": request, "users": users})

@app.post("/licenses/activation-key", response_model=LicenseResponse)
def activate_license(request: LicenseActivationRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Активировать ключ активации."""
    license_entry = db.query(License).filter(License.key == request.key).first()
    if not license_entry:
        raise HTTPException(status_code=400, detail="Неверный ключ активации")

    if license_entry.is_active:
        raise HTTPException(status_code=400, detail="Лицензия уже активирована")

    # Активируем лицензию
    license_entry.is_active = True
    license_entry.user_id = current_user.id
    db.commit()
    db.refresh(license_entry)

    return LicenseResponse(
        id=license_entry.id,
        key=license_entry.key,
        is_active=license_entry.is_active,
        user_id=license_entry.user_id,
    )

@app.post("/licenses/generate", response_model=LicenseResponse)
def generate_license(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Генерация нового ключа активации для текущего пользователя."""
    key = str(uuid.uuid4())  # Генерация уникального ключа
    new_license = License(key=key, is_active=False, user_id=current_user.id)
    db.add(new_license)
    db.commit()
    db.refresh(new_license)
    return LicenseResponse(
        id=new_license.id,
        key=new_license.key,
        is_active=new_license.is_active,
        user_id=new_license.user_id,
    )

@app.get("/licenses/download")
def download_license(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Скачать файл лицензии для текущего пользователя."""
    # Получение активной лицензии пользователя
    license_entry = db.query(License).filter(
        License.user_id == current_user.id,
        License.is_active == True
    ).first()

    if not license_entry:
        raise HTTPException(status_code=404, detail="Активная лицензия не найдена")

    # Формирование данных лицензии
    license_data = f"USER:{current_user.id};LICENSE:{license_entry.key}"

    # Подпись лицензии
    signature = sign_license(license_data, "private_key.pem")

    # Формирование содержимого файла
    license_file_content = f"{license_data}\n{signature}"

    # Возврат файла в ответе
    return Response(
        content=license_file_content,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=license_{current_user.id}.lic"}
    )


@app.post("/licenses/verify")
def verify_license(license_data: str, signature: str):
    """Проверить цифровую подпись лицензии."""
    try:
        # Загрузка публичного ключа с сервера
        with open("public_key.pem", "rb") as f:
            public_key_obj = load_pem_public_key(f.read())

        public_key_obj.verify(
            base64.b64decode(signature.encode()),
            license_data.encode(),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return {"valid": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Недействительная цифровая подпись")

@app.get("/user/{user_id}", response_class=HTMLResponse)
def user_backups(user_id: int, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

    user_dir = os.path.join(BACKUP_DIR, str(user_id))
    backups = os.listdir(user_dir) if os.path.exists(user_dir) else []
    return templates.TemplateResponse("user_backups.html", {"request": request, "user": user, "backups": backups})


@app.post("/register", status_code=201)
def register_user(user: UserCreate, db: SessionLocal = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        logger.warning(f"Попытка регистрации с уже существующим именем пользователя: {user.username}")
        raise HTTPException(status_code=400, detail="Username already registered")

    encryption_key = generate_encryption_key()
    new_user = User(
        username=user.username,
        hashed_password=get_password_hash(user.password),
        encryption_key=encryption_key,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info(f"Пользователь {user.username} успешно зарегистрирован")
    return {"msg": "User created successfully", "encryption_key": encryption_key}


@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: SessionLocal = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": str(user.id), "token_type": "bearer", "encryption_key": user.encryption_key}



@app.post("/backups/upload")
async def upload_backup(files: List[UploadFile], current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Загрузка файлов с проверкой лицензии."""
    active_license = db.query(License).filter(License.user_id == current_user.id, License.is_active == True).first()
    if not active_license:
        raise HTTPException(status_code=403, detail="Нет активной лицензии")

    # Проверка цифровой лицензии
    if active_license.license_data and active_license.signature:
        public_key = ...  # Загрузить открытый ключ сервера
        verify_license(active_license.license_data, active_license.signature, public_key)


    user_dir = get_user_backup_dir(current_user.id)
    saved_files = []

    for file in files:
        # Чтение содержимого файла
        contents = await file.read()
        file_size = len(contents)
        logger.info(f"Получен файл {file.filename}, размер: {file_size} байт")

        if file_size == 0:
            logger.error(f"Файл {file.filename} пустой")
            raise HTTPException(status_code=400, detail="Файл пустой")

        # Вычисляем контрольную сумму
        new_checksum = sha256(contents).hexdigest()
        logger.info(f"Контрольная сумма файла {file.filename}: {new_checksum}")

        # Проверяем существование файла с таким же именем
        file_path = os.path.join(user_dir, file.filename)
        if os.path.exists(file_path):
            # Вычисляем контрольную сумму существующего файла
            with open(file_path, "rb") as existing_file:
                existing_checksum = sha256(existing_file.read()).hexdigest()

            if existing_checksum != new_checksum:
                # Файлы разные, генерируем новое имя
                base, ext = os.path.splitext(file.filename)
                new_filename = f"{base}_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}"
                file_path = os.path.join(user_dir, new_filename)
                logger.warning(f"Файл {file.filename} уже существует, но содержимое отличается. Используется имя {new_filename}")
            else:
                logger.info(f"Файл {file.filename} уже существует и идентичен новому. Пропускаем загрузку.")
                return {"msg": f"Файл {file.filename} уже существует и идентичен новому"}

        # Сохраняем файл
        with open(file_path, "wb") as buffer:
            buffer.write(contents)
        logger.info(f"Файл {file.filename} успешно сохранён")

        # Сохранение метаинформации в базу данных
        new_backup = Backup(
            filename=file.filename,
            size=file_size,
            user_id=current_user.id,
            checksum=new_checksum,
        )
        db.add(new_backup)
        db.commit()
        db.refresh(new_backup)

        # Добавление информации о файле в ответ
        saved_files.append({"filename": file.filename, "size": file_size, "upload_date": new_backup.upload_date})

    return {"msg": "Files uploaded successfully", "files": saved_files}


@app.get("/backups/")
def list_backups(current_user: User = Depends(get_current_user), db: SessionLocal = Depends(get_db)):
    backups = db.query(Backup).filter(Backup.user_id == current_user.id).all()
    return [
        {
            "id": backup.id,
            "filename": backup.filename,
            "size": backup.size,
            "upload_date": backup.upload_date.isoformat(),
        }
        for backup in backups
    ]

@app.get("/backups/download/{filename}")
def download_backup(filename: str, current_user: User = Depends(get_current_user)):
    user_dir = get_user_backup_dir(current_user.id)
    file_path = os.path.join(user_dir, filename)

    if not os.path.exists(file_path):
        logger.error(f"Файл {filename} не найден для пользователя {current_user.username}")
        raise HTTPException(status_code=404, detail="File not found")

    logger.info(f"Файл {filename} отправлен пользователю {current_user.username}")
    print(filename)
    return FileResponse(file_path, media_type="application/octet-stream", filename=filename)


@app.delete("/backups/{filename}")
def delete_backup(filename: str, current_user: User = Depends(get_current_user)):
    user_dir = get_user_backup_dir(current_user.id)
    file_path = os.path.join(user_dir, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    os.remove(file_path)
    return {"msg": "File deleted successfully"}