from tkinter import messagebox
import requests
import winreg
import platform
import winsound
import logging
from logging.handlers import RotatingFileHandler

# --- API AYARLARI ---
API_URL = "http://yigithandereli.pythonanywhere.com"

def get_system_theme():
    if platform.system() != "Windows":
        return "Light"  # Diğer sistemler için varsayılan
    try:
        registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return "Light" if value == 1 else "Dark"
    except Exception:
        return "Light"  # Hata durumunda varsayılan olarak açık tema

# --- YARDIMCI FONKSİYONLAR ---
def show_error(title, message):
    """Kullanıcıya bir hata mesajı penceresi gösterir."""
    messagebox.showerror(title, f"{title}\n\n{message}")

def show_info(title, message):
    """Kullanıcıya bir bilgi mesajı penceresi gösterir."""
    messagebox.showinfo(title, message)

def login(username, password):
    """API üzerinden kullanıcı girişi yapar ve rol bilgisi döner."""
    try:
        response = requests.post(f"{API_URL}/login", json={"username": username, "password": password})
        if response.status_code == 200:
            data = response.json()
            return {"status": "success", "role": data.get("role", "student"), "user_id": data.get("user_id")}
        else:
            return {"status": "error", "message": response.json().get("hata", "Bilinmeyen hata")}
    except requests.exceptions.RequestException:
        return {"status": "error", "message": "API'ye bağlanılamadı"}

def restrict_access(user_role, required_role):
    """
    Kullanıcı rolünü kontrol eder. Gerekli rol yoksa False döner.
    required_role: "admin", "teacher", "student" veya liste (örneğin, ["admin", "teacher"])
    """
    role_hierarchy = {"admin": 3, "teacher": 2, "student": 1}
    if isinstance(required_role, list):
        return any(role_hierarchy.get(user_role, 0) >= role_hierarchy.get(role, 0) for role in required_role)
    return role_hierarchy.get(user_role, 0) >= role_hierarchy.get(required_role, 0)

def play_notification_sound():
    winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)

def setup_logger(name, log_file, level=logging.INFO):
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        logger.setLevel(level)
        handler = RotatingFileHandler(log_file, maxBytes=1024*1024, backupCount=5)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger