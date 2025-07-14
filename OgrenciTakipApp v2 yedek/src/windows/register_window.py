import customtkinter as ctk
import requests
from src.core.utilities import show_error, show_info

class RegisterWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.api_url = parent.api_url

        self.title("Yeni Hesap Oluştur")
        self.geometry("350x350")
        self.transient(parent)
        self.grab_set()

        # Ana çerçeve, pencereyi dolduracak şekilde ayarlandı
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # Widget'lar ana çerçevenin içine yerleştiriliyor
        self.title_label = ctk.CTkLabel(self.main_frame, text="Öğretmen Kaydı", font=ctk.CTkFont(size=16, weight="bold"))
        self.title_label.pack(pady=10)

        self.username_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Kullanıcı Adı")
        self.username_entry.pack(pady=10, padx=20, fill="x")

        self.password_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Şifre", show="*")
        self.password_entry.pack(pady=10, padx=20, fill="x")

        self.auth_code_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Yetki Kodu")
        self.auth_code_entry.pack(pady=10, padx=20, fill="x")

        self.register_button = ctk.CTkButton(self.main_frame, text="Hesap Oluştur", command=self.register)
        self.register_button.pack(pady=20, padx=20)

    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        auth_code = self.auth_code_entry.get()
        role = "ogretmen"

        if not all([username, password, auth_code]):
            show_error("Eksik Bilgi", "Kullanıcı adı, şifre ve yetki kodu boş bırakılamaz.")
            return

        payload = {
            "username": username,
            "password": password,
            "role": role,
            "yetki_kodu": auth_code
        }

        try:
            response = requests.post(f"{self.api_url}/register", json=payload)
            response.raise_for_status()
            data = response.json()

            if data.get("success"):
                show_info("Başarılı", "Öğretmen hesabı başarıyla oluşturuldu!")
                self.destroy()
            else:
                show_error("Kayıt Hatası", data.get("hata", "Bilinmeyen bir hata oluştu."))

        except requests.exceptions.HTTPError as err:
            error_detail = "Bilinmeyen sunucu hatası."
            try:
                error_detail = err.response.json().get('hata', error_detail)
            except ValueError:
                pass
            show_error("API Hatası", f"Kayıt sırasında bir hata oluştu: {error_detail}")
        except requests.exceptions.RequestException as e:
            show_error("Bağlantı Hatası", f"API sunucusuna bağlanılamadı: {e}")