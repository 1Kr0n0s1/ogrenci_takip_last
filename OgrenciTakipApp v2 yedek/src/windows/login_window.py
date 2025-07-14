import customtkinter as ctk
import requests
from src.core.utilities import show_error
from src.windows.register_window import RegisterWindow
from src.core.ogrenci_takip_app import OgrenciTakipApp

class LoginWindow(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.api_url = "http://yigithandereli.pythonanywhere.com"

        self.title("Öğrenci Takip Sistemi - Giriş")
        self.geometry("400x300")
        self.eval('tk::PlaceWindow . center')

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        self.title_label = ctk.CTkLabel(self.main_frame, text="Giriş Yap", font=ctk.CTkFont(size=16, weight="bold"))
        self.title_label.pack(pady=10)

        self.username_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Kullanıcı Adı")
        self.username_entry.pack(pady=10, padx=20, fill="x")

        self.password_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Şifre", show="*")
        self.password_entry.pack(pady=10, padx=20, fill="x")

        self.login_button = ctk.CTkButton(self.main_frame, text="Giriş Yap", command=self.login)
        self.login_button.pack(pady=10, padx=20)

        self.register_button = ctk.CTkButton(self.main_frame, text="Yeni Hesap Oluştur", command=self.open_register_window, fg_color="transparent", border_width=1)
        self.register_button.pack(pady=5, padx=20)

    def open_register_window(self):
        register_win = RegisterWindow(self)
        register_win.grab_set()

    # src/windows/login_window.py

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            show_error("Giriş Hatası", "Kullanıcı adı ve şifre boş bırakılamaz.")
            return

        try:
            response = requests.post(f"{self.api_url}/login", json={"username": username, "password": password})
            data = response.json()

            if response.status_code == 200 and data.get("status") == "success":
                self.withdraw()
                
                # --- KALICI DÜZELTME ---
                # Ana uygulamayı doğru ve tutarlı argümanlarla çağırıyoruz.
                main_app = OgrenciTakipApp(user_id=data.get("user_id"), role=data.get("role"))
                main_app.mainloop()

            else:
                show_error("Giriş Başarısız", data.get("message", "Geçersiz kullanıcı adı veya şifre."))

        except requests.exceptions.RequestException as e:
            show_error("API Hatası", f"Sunucuya bağlanırken bir hata oluştu: {e}")