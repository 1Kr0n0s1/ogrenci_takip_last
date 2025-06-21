import customtkinter as ctk
import json

class ProgramAyarlariWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master_app = master; self.title("Zamanlama Ayarları"); self.geometry("600x500"); self.transient(master); self.grab_set()
        gun_cerceve = ctk.CTkFrame(self); gun_cerceve.pack(pady=10, padx=10, fill="x"); ctk.CTkLabel(gun_cerceve, text="Günler").pack()
        ctk.CTkButton(gun_cerceve, text="Yeni Gün Ekle", command=lambda: self.gun_ekle()).pack(pady=2)
        self.gunler_scroll_cerceve = ctk.CTkScrollableFrame(gun_cerceve, height=80); self.gunler_scroll_cerceve.pack(fill="x", expand=True)
        saat_cerceve = ctk.CTkFrame(self); saat_cerceve.pack(pady=10, padx=10, fill="both", expand=True); ctk.CTkLabel(saat_cerceve, text="Saatler").pack()
        ctk.CTkButton(saat_cerceve, text="Yeni Saat Ekle", command=lambda: self.saat_ekle()).pack(pady=2)
        self.saatler_scroll_cerceve = ctk.CTkScrollableFrame(saat_cerceve); self.saatler_scroll_cerceve.pack(fill="both", expand=True)
        ctk.CTkButton(self, text="Kaydet ve Kapat", command=self.kaydet).pack(pady=10); self.ayarlari_yukle()
    def ayarlari_yukle(self):
        self.gun_entryleri = []; 
        for gun in self.master_app.gunler: self.gun_ekle(gun)
        for saat in self.master_app.saatler: self.saat_ekle(saat)
    def gun_ekle(self, gun_metni=""):
        entry = ctk.CTkEntry(self.gunler_scroll_cerceve); entry.insert(0, gun_metni); entry.pack(fill="x", padx=5, pady=2); self.gun_entryleri.append(entry)
    def saat_ekle(self, saat_metni=""):
        satir = ctk.CTkFrame(self.saatler_scroll_cerceve); satir.pack(fill="x", padx=5, pady=2)
        entry = ctk.CTkEntry(satir); entry.insert(0, saat_metni); entry.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(satir, text="Sil", width=50, fg_color="transparent", border_width=1, command=satir.destroy).pack(side="left", padx=5)
    def kaydet(self):
        yeni_gunler = [entry.get() for entry in self.gun_entryleri if entry.winfo_exists() and entry.get().strip()]
        yeni_saatler = [entry.get() for satir in self.saatler_scroll_cerceve.winfo_children() if satir.winfo_exists() for entry in satir.winfo_children() if isinstance(entry, ctk.CTkEntry) and entry.get().strip()]
        self.master_app.ayarlari_kaydet("program_gunler", json.dumps(yeni_gunler)); self.master_app.ayarlari_kaydet("program_saatler", json.dumps(yeni_saatler))
        self.master_app.ayarlari_bellege_yukle(); self.master_app.program_gridini_yeniden_ciz(); self.destroy()
