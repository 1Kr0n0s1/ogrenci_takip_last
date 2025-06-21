# src/windows/register_window.py

import customtkinter as ctk
import requests
from tkinter import messagebox
from src.core.utilities import API_URL, show_error, show_info

class RegisterWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.title("Yeni Hesap Oluştur")
        self.geometry("350x450")
        self.transient(master)
        self.grab_set()

        ctk.CTkLabel(self, text="Hesap Oluştur", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=15)

        # Rol seçimi
        ctk.CTkLabel(self, text="Kayıt Tipi:").pack(pady=(10,0))
        self.role_var = ctk.StringVar(value="Öğrenci")
        self.role_selector = ctk.CTkSegmentedButton(self, values=["Öğrenci", "Öğretmen"],
                                                     variable=self.role_var,
                                                     command=self.rol_degisti)
        self.role_selector.pack(pady=5, padx=20, fill="x")

        # Öğrenciye özel alanlar için çerçeve
        self.ogrenci_alanlari_cerceve = ctk.CTkFrame(self, fg_color="transparent")
        self.ad_soyad_entry = ctk.CTkEntry(self.ogrenci_alanlari_cerceve, placeholder_text="Ad Soyad")
        self.ad_soyad_entry.pack(pady=5, fill="x")
        self.sinif_entry = ctk.CTkEntry(self.ogrenci_alanlari_cerceve, placeholder_text="Sınıf (Örn: 11-A)")
        self.sinif_entry.pack(pady=5, fill="x")
        
        # Ortak alanlar
        self.username_entry = ctk.CTkEntry(self, placeholder_text="Kullanıcı Adı")
        self.username_entry.pack(pady=5, padx=20, fill="x")
        self.password_entry = ctk.CTkEntry(self, placeholder_text="Şifre", show="*")
        self.password_entry.pack(pady=5, padx=20, fill="x")
        
        ctk.CTkButton(self, text="Kayıt Ol", command=self.register).pack(pady=20, padx=20, fill="x")
        
        self.rol_degisti("Öğrenci") # Başlangıç durumunu ayarla

    def rol_degisti(self, secilen_rol):
        """Rol değişimine göre öğrenciye özel alanları gösterir veya gizler."""
        if secilen_rol == "Öğretmen":
            self.ogrenci_alanlari_cerceve.pack_forget()
        else:
            self.ogrenci_alanlari_cerceve.pack(pady=5, padx=20, fill="x")

    def register(self):
        """Kayıt bilgilerini toplayıp API'ye gönderir."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        role = "ogrenci" if self.role_var.get() == "Öğrenci" else "ogretmen"

        if not username or not password:
            show_error("Eksik Bilgi", "Kullanıcı adı ve şifre boş bırakılamaz.", self)
            return

        payload = {
            "username": username,
            "password": password,
            "role": role
        }

        if role == 'ogrenci':
            ad_soyad = self.ad_soyad_entry.get().strip()
            if not ad_soyad:
                show_error("Eksik Bilgi", "Öğrenci kaydı için Ad Soyad gereklidir.", self)
                return
            payload["ad_soyad"] = ad_soyad
            payload["sinif"] = self.sinif_entry.get().strip()

        try:
            response = requests.post(f"{API_URL}/register", json=payload)
            response.raise_for_status()
            data = response.json()

            if data.get("hata"):
                show_error("Kayıt Hatası", data["hata"], self)
            elif data.get("success"):
                show_info("Başarılı", "Hesap başarıyla oluşturuldu. Şimdi giriş yapabilirsiniz.", self)
                self.destroy()

        except requests.exceptions.RequestException as e:
            try:
                error_detail = e.response.json().get('hata', str(e))
            except:
                error_detail = str(e)
            show_error("API Hatası", f"Kayıt sırasında bir hata oluştu: {error_detail}", self)