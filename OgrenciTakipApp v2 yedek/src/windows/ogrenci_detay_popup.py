import customtkinter as ctk

class OgrenciDetayPopup(ctk.CTkToplevel):
    def __init__(self, master, ogrenci_data):
        super().__init__(master)
        self.title("Öğrenci Detayları")
        self.geometry("350x250"); self.transient(master); self.grab_set()
        ad = ogrenci_data.get('ad_soyad', 'N/A'); sinif = ogrenci_data.get('sinif', 'N/A'); veli = ogrenci_data.get('veli_iletisim', 'N/A')
        ctk.CTkLabel(self, text="Ad Soyad:", font=ctk.CTkFont(weight="bold")).pack(pady=(10,0)); ctk.CTkLabel(self, text=ad).pack()
        ctk.CTkLabel(self, text="Sınıfı:", font=ctk.CTkFont(weight="bold")).pack(pady=(10,0)); ctk.CTkLabel(self, text=sinif).pack()
        ctk.CTkLabel(self, text="Veli İletişim:", font=ctk.CTkFont(weight="bold")).pack(pady=(10,0)); ctk.CTkLabel(self, text=veli).pack()
        ctk.CTkButton(self, text="Kapat", command=self.destroy).pack(pady=20)