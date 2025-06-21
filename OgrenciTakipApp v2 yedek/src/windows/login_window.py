import customtkinter as ctk
import requests
from src.windows.register_window import RegisterWindow
from src.core.ogrenci_takip_app import OgrenciTakipApp
from src.core.utilities import API_URL, show_error, login
import sys
import os

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Giriş Yap")
        self.geometry("300x350")
        self.iconbitmap(resource_path("simge.ico"))
        
        ctk.CTkLabel(self, text="Öğrenci Takip Sistemi", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
        
        ctk.CTkLabel(self, text="Kullanıcı Adı").pack(pady=(10,0))
        self.username_entry = ctk.CTkEntry(self, width=200)
        self.username_entry.pack()
        
        ctk.CTkLabel(self, text="Şifre").pack(pady=(10,0))
        self.password_entry = ctk.CTkEntry(self, width=200, show="*")
        self.password_entry.pack()
        
        ctk.CTkButton(self, text="Giriş Yap", command=self.login).pack(pady=20, padx=20, fill="x")
        ctk.CTkButton(self, text="Yeni Hesap Oluştur", fg_color="transparent", command=self.open_register_window).pack(pady=5)
        
        self.status_label = ctk.CTkLabel(self, text="")
        self.status_label.pack()

        self.tema_secici = ctk.CTkSegmentedButton(self, values=["Açık", "Karanlık", "Sistem Varsayılanı"], command=self.tema_degistir)
        self.tema_secici.set("Açık" if ctk.get_appearance_mode() == "Light" else "Karanlık")
        self.tema_secici.pack(pady=5)

    def open_register_window(self):
        RegisterWindow(self)

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            self.status_label.configure(text="Lütfen tüm alanları doldurun.", text_color="orange")
            return
        
        result = login(username, password)
        if result["status"] == "success":
            self.destroy()
            main_app = OgrenciTakipApp(user_role=result["role"], user_id=result["user_id"])
            main_app.mainloop()
        else:
            self.status_label.configure(text=result["message"], text_color="red")
    
    def tema_degistir(self, value):
        if value == "Sistem Varsayılanı":
            import winreg
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                apps_use_light_theme = winreg.QueryValueEx(key, "AppsUseLightTheme")[0]
                mode = "Light" if apps_use_light_theme else "Dark"
                winreg.CloseKey(key)
            except Exception:
                mode = "Light"
        else:
            mode = "Light" if value == "Açık" else "Dark"
        ctk.set_appearance_mode(mode)