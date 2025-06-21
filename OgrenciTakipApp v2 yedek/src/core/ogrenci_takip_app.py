# src/core/ogrenci_takip_app.py

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import date, datetime
from fpdf import FPDF

# Proje içi importlar
from src.core.utilities import API_URL, show_error
from src.windows.ogrenci_editor_popup import OgrenciEditorPopup
from src.windows.ogrenci_detay_popup import OgrenciDetayPopup
from src.windows.ogrenci_secme_popup import OgrenciSecmePopup
from src.windows.deneme_detay_window import DenemeDetayWindow
from src.windows.deneme_editor_window import DenemeEditorWindow
from src.windows.soru_cozum_editor_window import SoruCozumEditorWindow
from src.windows.program_ayarlari_window import ProgramAyarlariWindow

# --- YARDIMCI PENCERE SINIFLARI ---
class SinifDetayWindow(ctk.CTkToplevel):
    def __init__(self, master, sinif_adi):
        super().__init__(master)
        self.title(f"{sinif_adi} Sınıfı Öğrencileri")
        self.geometry("350x450")
        self.transient(master)
        self.grab_set()
        
        list_frame = ctk.CTkScrollableFrame(self, label_text="Öğrenciler")
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        try:
            response = requests.get(f"{API_URL}/sinif/{sinif_adi}/ogrenciler"); response.raise_for_status()
            ogrenciler = response.json()
            if not ogrenciler:
                ctk.CTkLabel(list_frame, text="Bu sınıfta kayıtlı öğrenci bulunmamaktadır.").pack(pady=20)
            else:
                for ogrenci in ogrenciler:
                    ctk.CTkLabel(list_frame, text=ogrenci['ad_soyad'], anchor="w").pack(fill="x", padx=10, pady=2)
        except requests.exceptions.RequestException as e:
            show_error("API Hatası", f"Öğrenciler alınamadı: {e}", self)

class SinifYonetimWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master_app = master
        self.title("Sınıfları Yönet"); self.geometry("450x500"); self.transient(master); self.grab_set()
        
        ekle_cerceve = ctk.CTkFrame(self); ekle_cerceve.pack(pady=10, padx=10, fill="x")
        self.sinif_adi_entry = ctk.CTkEntry(ekle_cerceve, placeholder_text="Yeni Sınıf Adı")
        self.sinif_adi_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.ogretmen_adi_entry = ctk.CTkEntry(ekle_cerceve, placeholder_text="Öğretmen Adı")
        self.ogretmen_adi_entry.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(ekle_cerceve, text="Ekle", width=60, command=self.yeni_sinif_ekle).pack(side="left")
        
        self.sinif_list_frame = ctk.CTkScrollableFrame(self, label_text="Mevcut Sınıflar")
        self.sinif_list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.sinif_listesini_yenile()

    def sinif_listesini_yenile(self):
        for widget in self.sinif_list_frame.winfo_children(): widget.destroy()
        try:
            response = requests.get(f"{API_URL}/siniflar"); response.raise_for_status()
            for sinif in response.json():
                cerceve = ctk.CTkFrame(self.sinif_list_frame)
                cerceve.pack(fill="x", pady=4, padx=5)
                label_text = f"{sinif['sinif_adi']} (Öğretmen: {sinif.get('ogretmen_adi') or 'Belirtilmemiş'})"
                ctk.CTkLabel(cerceve, text=label_text, anchor="w").pack(side="left", padx=10, fill="x", expand=True)
                ctk.CTkButton(cerceve, text="Görüntüle", width=80, command=lambda s_adi=sinif['sinif_adi']: SinifDetayWindow(self, s_adi)).pack(side="right", padx=5)
                ctk.CTkButton(cerceve, text="Sil", fg_color="red", width=50, command=lambda s_id=sinif['id']: self.sinif_sil(s_id)).pack(side="right", padx=5)
        except requests.exceptions.RequestException as e: show_error("API Hatası", f"Sınıf listesi alınamadı: {e}", self)

    def yeni_sinif_ekle(self):
        sinif_adi = self.sinif_adi_entry.get().strip(); ogretmen_adi = self.ogretmen_adi_entry.get().strip()
        if not sinif_adi: return
        try:
            payload = {"sinif_adi": sinif_adi, "ogretmen_adi": ogretmen_adi}
            response = requests.post(f"{API_URL}/sinif-ekle", json=payload); response.raise_for_status()
            data = response.json()
            if data.get("hata"): show_error("Mantık Hatası", data["hata"], self)
            else:
                self.sinif_adi_entry.delete(0, 'end'); self.ogretmen_adi_entry.delete(0, 'end')
                self.sinif_listesini_yenile()
        except requests.exceptions.RequestException as e: show_error("API Hatası", f"Sınıf eklenemedi: {e}", self)

    def sinif_sil(self, sinif_id):
        if messagebox.askyesno("Onay", "Bu sınıfı silmek istediğinize emin misiniz? Sınıftaki öğrencilerin sınıf bilgisi kaldırılacaktır."):
            try:
                requests.delete(f"{API_URL}/sinif-sil/{sinif_id}").raise_for_status()
                self.sinif_listesini_yenile()
                self.master_app.sinif_listesini_yenile()
                self.master_app.ogrenci_listesini_yenile()
            except requests.exceptions.RequestException as e: show_error("API Hatası", f"Sınıf silinemedi: {e}", self)

# --- ANA UYGULAMA SINIFI ---
class OgrenciTakipApp(ctk.CTk):
    def __init__(self, user_role, user_id):
        super().__init__()
        self.aktif_ogrenci_id = None
        self.aktif_ogrenci_adi = ""
        self.guncel_ogrenci_cache = []
        self.siniflar_cache = []
        self.user_role = user_role
        self.user_id = user_id

        self.ayarlari_bellege_yukle()
        self.title("Öğrenci Takip Sistemi (Cloud)"); self.geometry("1200x750")
        
        # Rol tabanlı arayüzü başlat
        if self.user_role == 'ogretmen':
            self.ogretmen_arayuzu_olustur()
        elif self.user_role == 'ogrenci':
            self.ogrenci_arayuzu_olustur()
        
    def ogretmen_arayuzu_olustur(self):
        """Öğretmen için tam yetkili arayüzü çizer."""
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(0, weight=1)
        self.ogrenci_paneli_olustur()
        self.sekmeleri_olustur(role='ogretmen')
        self.sinif_listesini_yenile() # Pop-up'lar için sınıf listesini hazırla
        self.ogrenci_listesini_yenile()

    def ogrenci_arayuzu_olustur(self):
        """Öğrenci için kısıtlı, sadece görüntüleme arayüzünü çizer."""
        self.grid_columnconfigure(0, weight=1); self.grid_rowconfigure(1, weight=1)
        
        try:
            response = requests.get(f"{API_URL}/kullanici/{self.user_id}/ogrenci-detay"); response.raise_for_status()
            ogrenci_bilgileri = response.json()
            if ogrenci_bilgileri.get("hata"):
                show_error("Öğrenci Bulunamadı", ogrenci_bilgileri["hata"]); self.destroy(); return
            
            self.aktif_ogrenci_id = ogrenci_bilgileri.get('id')
            self.aktif_ogrenci_adi = ogrenci_bilgileri.get('ad_soyad')
            ogrenci_sinif = ogrenci_bilgileri.get('sinif') or "Belirtilmemiş"
        except requests.exceptions.RequestException as e:
            show_error("Veri Hatası", f"Öğrenci bilgileri alınamadı. {e}"); self.destroy(); return

        ust_bilgi_cerceve = ctk.CTkFrame(self, height=80); ust_bilgi_cerceve.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        ctk.CTkLabel(ust_bilgi_cerceve, text=f"Hoş Geldin, {self.aktif_ogrenci_adi}", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left", padx=20)
        ctk.CTkLabel(ust_bilgi_cerceve, text=f"Sınıf: {ogrenci_sinif}", font=ctk.CTkFont(size=16)).pack(side="right", padx=20)
        
        self.sekmeleri_olustur(role='ogrenci')
        self.tab_view.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        # Öğrencinin kendi verilerini yükle
        self.deneme_listesini_yenile()
        self.soru_cozumu_listesini_yenile()
        self.odev_listesini_yenile()

    def ayarlari_bellege_yukle(self):
        try:
            response = requests.get(f"{API_URL}/ayarlar"); response.raise_for_status(); ayarlar = response.json()
            self.gunler = json.loads(ayarlar.get("program_gunler", '["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]'))
            self.saatler = json.loads(ayarlar.get("program_saatler", '["08:00", "09:00"]'))
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            show_error("API Başlatma Hatası", f"Ayarlar yüklenemedi: {e}\nVarsayılan ayarlar kullanılıyor.")
            self.gunler = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]; self.saatler = [f"{h:02d}:00" for h in range(8, 22)]
        
    def ayarlari_kaydet(self, anahtar, deger):
        try:
            response = requests.post(f"{API_URL}/ayarlar-kaydet", json={"anahtar": anahtar, "deger": deger}); response.raise_for_status()
        except requests.exceptions.RequestException as e: show_error("API Hatası", f"Ayar kaydedilemedi: {e}")
        
    def ogrenci_paneli_olustur(self):
        sol_menu_cerceve = ctk.CTkFrame(self, width=300); sol_menu_cerceve.grid(row=0, column=0, padx=10, pady=10, sticky="ns"); sol_menu_cerceve.grid_propagate(False)
        ctk.CTkLabel(sol_menu_cerceve, text="Öğrenciler", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        self.ogrenci_list_frame = ctk.CTkScrollableFrame(sol_menu_cerceve); self.ogrenci_list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        buton_cerceve_alt = ctk.CTkFrame(sol_menu_cerceve); buton_cerceve_alt.pack(pady=5, padx=5, fill="x")
        ctk.CTkButton(buton_cerceve_alt, text="Yeni Öğrenci Ekle", command=self.yeni_ogrenci_penceresi).pack(pady=2, fill="x")
        ctk.CTkButton(buton_cerceve_alt, text="Sınıfları Yönet", command=lambda: SinifYonetimWindow(self)).pack(pady=2, fill="x")

        tema_cerceve = ctk.CTkFrame(sol_menu_cerceve); tema_cerceve.pack(side="bottom", fill="x", padx=5, pady=5)
        ctk.CTkLabel(tema_cerceve, text="Tema:").pack(side="left", padx=5)
        self.tema_secici = ctk.CTkSegmentedButton(tema_cerceve, values=["Açık", "Karanlık"], command=self.tema_degistir)
        self.tema_secici.set("Açık" if ctk.get_appearance_mode() == "Light" else "Karanlık"); self.tema_secici.pack(side="left", expand=True, fill="x")
        
    def tema_degistir(self, value):
        mode = "Light" if value == "Açık" else "Dark"; ctk.set_appearance_mode(mode); self.ogrenci_listesini_yenile()
        
    def sekmeleri_olustur(self, role='ogretmen'):
        self.tab_view = ctk.CTkTabview(self)
        if role == 'ogretmen':
            self.tab_view.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.tab_view.add("Denemeler")
        self.tab_view.add("Soru Çözümleri")
        self.tab_view.add("Ödevler")
        if role == 'ogretmen':
            self.tab_view.add("Haftalık Program")

        self.denemeler_sekmesini_olustur(role)
        self.soru_cozumleri_sekmesini_olustur(role)
        self.odevler_sekmesini_olustur(role)
        if role == 'ogretmen':
            self.haftalik_program_sekmesini_olustur()

    def sinif_listesini_yenile(self):
        try:
            response = requests.get(f"{API_URL}/siniflar"); response.raise_for_status()
            self.siniflar_cache = response.json()
        except requests.exceptions.RequestException as e:
            show_error("API Hatası", f"Sınıf listesi alınamadı: {e}")

    def ogrenci_listesini_yenile(self):
        for widget in self.ogrenci_list_frame.winfo_children(): widget.destroy()
        try:
            response = requests.get(f"{API_URL}/ogrenciler"); response.raise_for_status()
            self.guncel_ogrenci_cache = response.json(); self.guncel_ogrenci_cache.sort(key=lambda x: x['ad_soyad'])
            font = ctk.CTkFont(size=14); max_width = 280 - 50 
            for ogrenci in self.guncel_ogrenci_cache:
                satir_cerceve = ctk.CTkFrame(self.ogrenci_list_frame); satir_cerceve.pack(fill="x", pady=2); satir_cerceve.grid_columnconfigure(0, weight=1)
                label_text = ogrenci['ad_soyad']
                if font.measure(label_text) > max_width:
                    while font.measure(label_text + "...") > max_width and len(label_text) > 1: label_text = label_text[:-1]
                    label_text += "..."
                text_color = ctk.ThemeManager.theme["CTkLabel"]["text_color"]
                ogrenci_butonu = ctk.CTkButton(satir_cerceve, text=f"{label_text} ({ogrenci.get('sinif') or 'N/A'})", text_color=text_color, anchor="w", fg_color="transparent", command=lambda data=ogrenci: self.ogrenci_sec(data))
                ogrenci_butonu.grid(row=0, column=0, sticky="ew", padx=5)
                menu_button = ctk.CTkButton(satir_cerceve, text="...", width=30, command=lambda data=ogrenci, btn=ogrenci_butonu: self.ogrenci_menusu_goster(data, btn))
                menu_button.grid(row=0, column=1, padx=(0,5))
            
            ogrenci_isimleri_filtre = ["Tüm Öğrenciler"] + [o['ad_soyad'] for o in self.guncel_ogrenci_cache]
            odev_ogrenci_isimleri = ["Öğrenci Seçin"] + [o['ad_soyad'] for o in self.guncel_ogrenci_cache]

            if hasattr(self, 'deneme_ogrenci_filtre'): self.deneme_ogrenci_filtre.configure(values=ogrenci_isimleri_filtre)
            if hasattr(self, 'soru_cozumu_ogrenci_filtre'): self.soru_cozumu_ogrenci_filtre.configure(values=ogrenci_isimleri_filtre)
            if hasattr(self, 'odev_ogrenci_secim_combo'): self.odev_ogrenci_secim_combo.configure(values=odev_ogrenci_isimleri)

        except requests.exceptions.RequestException as e: show_error("API Hatası", f"Öğrenciler yüklenemedi: {e}")

    def ogrenci_sec(self, ogrenci_data):
        self.aktif_ogrenci_id = ogrenci_data['id']; self.aktif_ogrenci_adi = ogrenci_data['ad_soyad']
        current_tab = self.tab_view.get()
        if current_tab == "Denemeler":
            if self.user_role == 'ogretmen': self.deneme_ogrenci_filtre.set(self.aktif_ogrenci_adi)
            self.deneme_listesini_yenile()
        elif current_tab == "Soru Çözümleri":
            if self.user_role == 'ogretmen': self.soru_cozumu_ogrenci_filtre.set(self.aktif_ogrenci_adi)
            self.soru_cozumu_listesini_yenile()
        elif current_tab == "Ödevler":
            self.odevler_baslik.configure(text=f"{self.aktif_ogrenci_adi} - Ödevler")
            self.odev_listesini_yenile()
        elif current_tab == "Haftalık Program":
            self.program_baslik.configure(text=f"{self.aktif_ogrenci_adi} - Haftalık Program")
            self.program_yukle()
            
    def ogrenci_menusu_goster(self, ogrenci_data, button):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Bilgileri Görüntüle", command=lambda: OgrenciDetayPopup(self, ogrenci_data=ogrenci_data))
        menu.add_command(label="Bilgileri Düzenle", command=lambda: self.yeni_ogrenci_penceresi(ogrenci_data))
        menu.add_separator(); menu.add_command(label="Öğrenciyi Sil", command=lambda: self.ogrenci_sil(ogrenci_data['id']))
        x, y = button.winfo_rootx(), button.winfo_rooty() + button.winfo_height(); menu.tk_popup(x, y)

    def yeni_ogrenci_penceresi(self, ogrenci_data=None):
        self.sinif_listesini_yenile() # Pop-up açılmadan hemen önce sınıf listesini yenile
        OgrenciEditorPopup(self, self.siniflar_cache, ogrenci_data=ogrenci_data)
    
    def ogrenci_sil(self, ogrenci_id):
        if messagebox.askyesno("Onay", "Bu öğrenciyi ve ilişkili tüm verilerini (kullanıcı hesabı dahil) kalıcı olarak silmek istediğinizden emin misiniz?"):
            try:
                response = requests.delete(f"{API_URL}/ogrenci-sil/{ogrenci_id}"); response.raise_for_status(); self.ogrenci_listesini_yenile()
            except requests.exceptions.RequestException as e: show_error("API Hatası", f"Öğrenci silinemedi: {e}")
            
    # --- EKLENEN DÜZELTME ---
    def get_ogrenci_adi_from_cache(self, ogrenci_id):
        """
        Öğrenci ID'sini kullanarak cache'lenmiş öğrenci listesinden öğrencinin adını bulur.
        Bu metot, alt pencerelerin (popup/toplevel) ID'sini bildiği bir öğrencinin
        adını kolayca alabilmesi için gereklidir.
        """
        for ogrenci in self.guncel_ogrenci_cache:
            if ogrenci.get('id') == ogrenci_id:
                return ogrenci.get('ad_soyad', 'İsim Bulunamadı')
        return "Bilinmeyen Öğrenci"
    
    # --- Sekme Oluşturma ve Yönetim Metodları ---
    # Bu metodlar rol kontrolü mantığıyla güncellenmiştir.
    
    def denemeler_sekmesini_olustur(self, role='ogretmen'):
        tab = self.tab_view.tab("Denemeler")
        label_text = "Kaydedilen Denemeler" if role == 'ogretmen' else "Deneme Sınavların"
        
        if role == 'ogretmen':
            ust_cerceve = ctk.CTkFrame(tab); ust_cerceve.pack(pady=10, padx=10, fill="x")
            self.deneme_arama_entry = ctk.CTkEntry(ust_cerceve, placeholder_text="Deneme veya öğrenci ara..."); self.deneme_arama_entry.pack(side="left", padx=5, fill="x", expand=True)
            self.deneme_arama_entry.bind("<KeyRelease>", lambda event: self.deneme_listesini_yenile())
            self.deneme_ogrenci_filtre = ctk.CTkComboBox(ust_cerceve, values=["Tüm Öğrenciler"], command=self.deneme_listesini_yenile); self.deneme_ogrenci_filtre.set("Tüm Öğrenciler"); self.deneme_ogrenci_filtre.pack(side="left", padx=10)
            ctk.CTkButton(ust_cerceve, text="Yeni Deneme Ekle", command=self.yeni_deneme_penceresi).pack(side="right", padx=10)
        
        self.deneme_list_cerceve = ctk.CTkScrollableFrame(tab, label_text=label_text); self.deneme_list_cerceve.pack(pady=10, padx=10, fill="both", expand=True)

    def deneme_listesini_yenile(self, secim=None):
        for widget in self.deneme_list_cerceve.winfo_children(): widget.destroy()
        
        params = {}
        if self.user_role == 'ogretmen':
            params = {"ogrenci_adi": self.deneme_ogrenci_filtre.get()}
            arama_terimi = self.deneme_arama_entry.get().lower()
        else: # Öğrenci kendi denemelerini görür
            params = {"ogrenci_adi": self.aktif_ogrenci_adi}
            arama_terimi = ""
            
        try:
            response = requests.get(f"{API_URL}/denemeler", params=params); response.raise_for_status(); denemeler = response.json()
            for deneme in denemeler:
                label_text_ogrenci = f" ({deneme['ad_soyad']})" if self.user_role == 'ogretmen' else ""
                label_text = f"{deneme['deneme_adi']} ({deneme['tarih']}){label_text_ogrenci}"
                if arama_terimi in label_text.lower():
                    satir = ctk.CTkFrame(self.deneme_list_cerceve); satir.pack(fill="x", pady=2)
                    ctk.CTkLabel(satir, text=label_text, anchor="w").pack(side="left", fill="x", expand=True, padx=5)
                    ctk.CTkButton(satir, text="Aç", width=50, command=lambda d_id=deneme['id']: DenemeDetayWindow(self, d_id)).pack(side="left", padx=5)
                    if self.user_role == 'ogretmen':
                        menu_btn = ctk.CTkButton(satir, text="...", width=30, command=lambda d_id=deneme['id'], o_id=deneme['ogrenci_id'], btn=satir: self.deneme_menusu_goster(d_id, o_id, btn)); menu_btn.pack(side="left", padx=5)
        except requests.exceptions.RequestException as e: ctk.CTkLabel(self.deneme_list_cerceve, text=f"Denemeler yüklenemedi: {e}").pack()
    
    def yeni_deneme_penceresi(self): OgrenciSecmePopup(self, callback=self.deneme_editorunu_ac)
    def deneme_editorunu_ac(self, ogrenci_id): DenemeEditorWindow(self, ogrenci_id=ogrenci_id)
    def deneme_menusu_goster(self, deneme_id, ogrenci_id, button):
        menu = tk.Menu(self, tearoff=0); menu.add_command(label="Düzenle", command=lambda: DenemeEditorWindow(self, ogrenci_id, deneme_id=deneme_id))
        menu.add_separator(); menu.add_command(label="Denemeyi Sil", command=lambda: self.deneme_sil(deneme_id))
        x, y = button.winfo_rootx() + button.winfo_width(), button.winfo_rooty(); menu.tk_popup(x, y)
    def deneme_sil(self, deneme_id):
        if messagebox.askyesno("Onay", "Bu deneme kaydını silmek istediğinizden emin misiniz?"):
            try:
                requests.delete(f"{API_URL}/deneme-sil/{deneme_id}").raise_for_status(); self.deneme_listesini_yenile()
            except requests.exceptions.RequestException as e: show_error("API Hatası", f"Deneme silinemedi: {e}")

    def soru_cozumleri_sekmesini_olustur(self, role='ogretmen'):
        tab = self.tab_view.tab("Soru Çözümleri")
        label_text = "Kaydedilen Soru Çözüm Seansları" if role == 'ogretmen' else "Soru Çözüm Seansların"
        if role == 'ogretmen':
            ust_cerceve = ctk.CTkFrame(tab); ust_cerceve.pack(pady=10, padx=10, fill="x")
            self.soru_cozumu_arama_entry = ctk.CTkEntry(ust_cerceve, placeholder_text="Seans veya öğrenci ara..."); self.soru_cozumu_arama_entry.pack(side="left", padx=5, fill="x", expand=True)
            self.soru_cozumu_arama_entry.bind("<KeyRelease>", lambda event: self.soru_cozumu_listesini_yenile())
            self.soru_cozumu_ogrenci_filtre = ctk.CTkComboBox(ust_cerceve, values=["Tüm Öğrenciler"], command=self.soru_cozumu_listesini_yenile)
            self.soru_cozumu_ogrenci_filtre.set("Tüm Öğrenciler"); self.soru_cozumu_ogrenci_filtre.pack(side="left", padx=10)
            ctk.CTkButton(ust_cerceve, text="Yeni Seans Ekle", command=self.yeni_soru_cozumu_penceresi).pack(side="right", padx=10)
        self.soru_cozumu_list_cerceve = ctk.CTkScrollableFrame(tab, label_text=label_text); self.soru_cozumu_list_cerceve.pack(pady=10, padx=10, fill="both", expand=True)

    def soru_cozumu_listesini_yenile(self, secim=None):
        for widget in self.soru_cozumu_list_cerceve.winfo_children(): widget.destroy()
        params = {}
        if self.user_role == 'ogretmen':
            params = {"ogrenci_adi": self.soru_cozumu_ogrenci_filtre.get()}
            arama_terimi = self.soru_cozumu_arama_entry.get().lower()
        else: # Öğrenci kendi seanslarını görür
            params = {"ogrenci_adi": self.aktif_ogrenci_adi}
            arama_terimi = ""
        try:
            response = requests.get(f"{API_URL}/soru-cozumleri", params=params); response.raise_for_status(); seanslar = response.json()
            for seans in seanslar:
                label_text_ogrenci = f" ({seans['ad_soyad']})" if self.user_role == 'ogretmen' else ""
                label_text = f"{seans['seans_adi']} ({seans['tarih']}){label_text_ogrenci}"
                if arama_terimi in label_text.lower():
                    satir = ctk.CTkFrame(self.soru_cozumu_list_cerceve); satir.pack(fill="x", pady=2)
                    ctk.CTkLabel(satir, text=label_text, anchor="w").pack(side="left", fill="x", expand=True, padx=5)
                    if self.user_role == 'ogretmen':
                        menu_btn = ctk.CTkButton(satir, text="...", width=30, command=lambda s_id=seans['id'], o_id=seans['ogrenci_id'], btn=satir: self.soru_cozumu_menusu_goster(s_id, o_id, btn)); menu_btn.pack(side="left", padx=5)
        except requests.exceptions.RequestException as e: ctk.CTkLabel(self.soru_cozumu_list_cerceve, text=f"Seanslar yüklenemedi: {e}").pack()

    def yeni_soru_cozumu_penceresi(self): OgrenciSecmePopup(self, callback=self.soru_cozumu_editorunu_ac)
    def soru_cozumu_editorunu_ac(self, ogrenci_id): SoruCozumEditorWindow(self, ogrenci_id=ogrenci_id)
    def soru_cozumu_menusu_goster(self, seans_id, ogrenci_id, button):
        menu = tk.Menu(self, tearoff=0); menu.add_command(label="Düzenle", command=lambda: SoruCozumEditorWindow(self, ogrenci_id, seans_id=seans_id))
        menu.add_separator(); menu.add_command(label="Seansı Sil", command=lambda: self.soru_cozumu_sil(seans_id))
        x, y = button.winfo_rootx() + button.winfo_width(), button.winfo_rooty(); menu.tk_popup(x, y)
    def soru_cozumu_sil(self, seans_id):
        if messagebox.askyesno("Onay", "Bu seansı silmek istediğinizden emin misiniz?"):
            try:
                requests.delete(f"{API_URL}/soru-cozumu-sil/{seans_id}").raise_for_status(); self.soru_cozumu_listesini_yenile()
            except requests.exceptions.RequestException as e: show_error("API Hatası", f"Seans silinemedi: {e}")

    def odevler_sekmesini_olustur(self, role='ogretmen'):
        tab = self.tab_view.tab("Ödevler")
        baslik_text = "Lütfen Bir Öğrenci Seçin veya Aşağıdan Seçim Yapın" if role == 'ogretmen' else "Ödevlerin"
        self.odevler_baslik = ctk.CTkLabel(tab, text=baslik_text, font=ctk.CTkFont(size=16, weight="bold")); self.odevler_baslik.pack(pady=10)
        
        if role == 'ogretmen':
            ekleme_cerceve = ctk.CTkFrame(tab); ekleme_cerceve.pack(pady=10, padx=10, fill="x")
            self.odev_ogrenci_secim_combo = ctk.CTkComboBox(ekleme_cerceve, values=["Öğrenci Seçin"]); self.odev_ogrenci_secim_combo.pack(side="left", padx=5)
            self.odev_ders_entry = ctk.CTkEntry(ekleme_cerceve, placeholder_text="Ders"); self.odev_ders_entry.pack(side="left", padx=5, expand=True, fill="x")
            self.odev_konu_entry = ctk.CTkEntry(ekleme_cerceve, placeholder_text="Konu"); self.odev_konu_entry.pack(side="left", padx=5, expand=True, fill="x")
            self.odev_bitis_entry = ctk.CTkEntry(ekleme_cerceve, placeholder_text="Bitiş (YYYY-MM-DD)"); self.odev_bitis_entry.pack(side="left", padx=5)
            ctk.CTkButton(ekleme_cerceve, text="Ekle", command=self.odev_ekle).pack(side="left", padx=5)
        
        self.odev_list_cerceve = ctk.CTkScrollableFrame(tab, label_text="Ödevler"); self.odev_list_cerceve.pack(pady=10, padx=10, fill="both", expand=True)

    def odev_ekle(self):
        ogrenci_adi = self.odev_ogrenci_secim_combo.get()
        ogrenci_id = next((o['id'] for o in self.guncel_ogrenci_cache if o['ad_soyad'] == ogrenci_adi), None)
        if not ogrenci_id: show_error("Öğrenci Seçilmedi", "Lütfen ödev vermek için bir öğrenci seçin."); return
        
        ders = self.odev_ders_entry.get().strip(); konu = self.odev_konu_entry.get().strip(); bitis = self.odev_bitis_entry.get().strip()
        if not all([ders, konu, bitis]): show_error("Eksik Bilgi", "Lütfen Ders, Konu ve Bitiş Tarihi alanlarını doldurun."); return
        try:
            verilis = date.today().strftime("%Y-%m-%d"); datetime.strptime(bitis, "%Y-%m-%d")
            data = {"ogrenci_id": ogrenci_id, "ders": ders, "konu": konu, "verilis_tarihi": verilis, "bitis_tarihi": bitis, "durum": "Verildi"}
            requests.post(f"{API_URL}/odev-ekle", json=data).raise_for_status()
            self.odev_ders_entry.delete(0, 'end'); self.odev_konu_entry.delete(0, 'end'); self.odev_bitis_entry.delete(0, 'end')
            if self.aktif_ogrenci_id == ogrenci_id: self.odev_listesini_yenile()
        except requests.exceptions.RequestException as e: show_error("API Hatası", f"Ödev eklenemedi: {e}")
        except ValueError: show_error("Hatalı Tarih", "Lütfen bitiş tarihini YYYY-MM-DD formatında girin.")

    def odev_listesini_yenile(self):
        for widget in self.odev_list_cerceve.winfo_children(): widget.destroy()
        if not self.aktif_ogrenci_id: return
        try:
            response = requests.get(f"{API_URL}/odevler/{self.aktif_ogrenci_id}"); response.raise_for_status(); odevler = response.json()
            today = date.today()
            for odev in odevler:
                bitis = datetime.strptime(odev['bitis_tarihi'], "%Y-%m-%d").date()
                durum = odev['durum']; bg_color = "transparent"
                if durum == "Kontrol Edildi": bg_color = ("#2E4B3E", "#1B352A")
                elif durum == "Yapıldı": bg_color = ("#b09000", "#695500") 
                elif durum != "Kontrol Edildi" and bitis < today: bg_color = ("#603030", "#402525")
                satir = ctk.CTkFrame(self.odev_list_cerceve, fg_color=bg_color); satir.pack(fill="x", pady=2, padx=2)
                label_text = f"Bitiş: {odev['bitis_tarihi']}  |  {odev['ders']}: {odev['konu']}"
                ctk.CTkLabel(satir, text=label_text, anchor="w").pack(side="left", padx=10, pady=5, expand=True, fill="x")
                
                durum_combo = ctk.CTkComboBox(satir, values=["Verildi", "Yapıldı", "Kontrol Edildi"], command=lambda choice, o_id=odev['id']: self.odev_durum_guncelle(o_id, choice))
                durum_combo.set(durum)
                if self.user_role == 'ogrenci': durum_combo.configure(state="disabled")
                durum_combo.pack(side="left", padx=10)
                
                if self.user_role == 'ogretmen':
                    ctk.CTkButton(satir, text="Sil", width=40, fg_color="transparent", border_width=1, command=lambda o_id=odev['id']: self.odev_sil(o_id)).pack(side="left", padx=5)
        except requests.exceptions.RequestException as e: ctk.CTkLabel(self.odev_list_cerceve, text=f"Ödevler yüklenemedi: {e}").pack()

    def odev_durum_guncelle(self, odev_id, yeni_durum):
        try:
            requests.put(f"{API_URL}/odev-durum-guncelle/{odev_id}", json={"durum": yeni_durum}).raise_for_status(); self.odev_listesini_yenile()
        except requests.exceptions.RequestException as e: show_error("API Hatası", f"Ödev durumu güncellenemedi: {e}")
        
    def odev_sil(self, odev_id):
        if messagebox.askyesno("Onay", "Bu ödevi silmek istediğinizden emin misiniz?"):
            try:
                requests.delete(f"{API_URL}/odev-sil/{odev_id}").raise_for_status(); self.odev_listesini_yenile()
            except requests.exceptions.RequestException as e: show_error("API Hatası", f"Ödev silinemedi: {e}")

    def haftalik_program_sekmesini_olustur(self):
        program_tab = self.tab_view.tab("Haftalık Program")
        self.program_baslik = ctk.CTkLabel(program_tab, text="Lütfen Bir Öğrenci Seçin", font=ctk.CTkFont(size=16, weight="bold")); self.program_baslik.pack(pady=10)
        buton_cerceve = ctk.CTkFrame(program_tab); buton_cerceve.pack(pady=5)
        ctk.CTkButton(buton_cerceve, text="Programı Kaydet", command=self.program_kaydet).pack(side="left", padx=5)
        ctk.CTkButton(buton_cerceve, text="JPG İndir", command=lambda: self.program_indir('jpg')).pack(side="left", padx=5)
        ctk.CTkButton(buton_cerceve, text="PDF İndir", command=lambda: self.program_indir('pdf')).pack(side="left", padx=5)
        ctk.CTkButton(buton_cerceve, text="Zamanlamayı Düzenle", command=self.program_ayarlari_ac).pack(side="left", padx=5)
        self.program_grid_cerceve = ctk.CTkFrame(program_tab); self.program_grid_cerceve.pack(fill="both", expand=True, padx=10, pady=10)
        self.program_gridini_yeniden_ciz()

    def program_gridini_yeniden_ciz(self):
        for widget in self.program_grid_cerceve.winfo_children(): widget.destroy()
        self.grid_entries = []
        for c, gun in enumerate(self.gunler): ctk.CTkLabel(self.program_grid_cerceve, text=gun, font=ctk.CTkFont(weight="bold")).grid(row=0, column=c+1, padx=1, pady=1)
        for r, saat in enumerate(self.saatler):
            self.grid_entries.append([])
            ctk.CTkLabel(self.program_grid_cerceve, text=saat).grid(row=r+1, column=0, padx=1, pady=1)
            for c in range(len(self.gunler)):
                entry = ctk.CTkEntry(self.program_grid_cerceve, width=110); entry.grid(row=r+1, column=c+1, padx=1, pady=1); self.grid_entries[r].append(entry)
        self.program_yukle()

    def program_ayarlari_ac(self): ProgramAyarlariWindow(self)

    def program_kaydet(self):
        if not self.aktif_ogrenci_id: return
        grid_data = [[entry.get() for entry in row] for row in self.grid_entries]
        try:
            requests.post(f"{API_URL}/program-kaydet/{self.aktif_ogrenci_id}", json=grid_data).raise_for_status()
            messagebox.showinfo("Başarılı", "Program başarıyla kaydedildi.")
        except requests.exceptions.RequestException as e: show_error("API Hatası", f"Program kaydedilemedi: {e}")

    def program_yukle(self):
        if hasattr(self, 'grid_entries'):
            for row in self.grid_entries:
                for entry in row: entry.delete(0, 'end')
        if not self.aktif_ogrenci_id: return
        try:
            response = requests.get(f"{API_URL}/program/{self.aktif_ogrenci_id}"); response.raise_for_status(); grid_data = response.json()
            if grid_data:
                for r, row_data in enumerate(grid_data):
                    for c, cell_data in enumerate(row_data):
                        if r < len(self.grid_entries) and c < len(self.grid_entries[r]): self.grid_entries[r][c].insert(0, cell_data)
        except requests.exceptions.RequestException: pass

    def program_indir(self, format_tipi):
        if not self.aktif_ogrenci_id: return
        if format_tipi == 'jpg': self.program_indir_jpg()
        elif format_tipi == 'pdf': self.program_indir_pdf()

    def program_indir_jpg(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=[("JPEG Image", "*.jpg")], title="Programı Resim Olarak Kaydet")
        if not file_path: return
        # ... (JPG indirme kodu önceki cevapla aynı) ...
        pass
        
    def program_indir_pdf(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Document", "*.pdf")], title="Programı PDF Olarak Kaydet")
        if not file_path: return
        # ... (PDF indirme kodu önceki cevapla aynı) ...
        pass