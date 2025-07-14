import customtkinter as ctk

class OgrenciSecmePopup(ctk.CTkToplevel):
    def __init__(self, master, callback):
        super().__init__(master)
        self.master_app = master; self.callback = callback
        self.title("Öğrenci Seç"); self.geometry("300x400"); self.transient(master); self.grab_set()
        ctk.CTkLabel(self, text="Lütfen İşlem Yapılacak\nÖğrenciyi Seçin", font=ctk.CTkFont(size=14)).pack(pady=10)
        scroll_frame = ctk.CTkScrollableFrame(self); scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        if self.master_app.guncel_ogrenci_cache:
            for ogrenci in self.master_app.guncel_ogrenci_cache:
                ctk.CTkButton(scroll_frame, text=ogrenci['ad_soyad'], command=lambda id=ogrenci['id']: self.ogrenci_secildi(id)).pack(fill="x", pady=2)
    def ogrenci_secildi(self, ogrenci_id):
        self.callback(ogrenci_id); self.destroy()