# src/windows/ogrenci_editor_popup.py

import customtkinter as ctk
import requests
from src.core.utilities import API_URL, show_error

class OgrenciEditorPopup(ctk.CTkToplevel):
    def __init__(self, master, siniflar_listesi, ogrenci_data=None, varsayilan_sinif=None): # Değişiklik 1: Yeni argüman eklendi
        super().__init__(master)
        self.master_app = master
        self.ogrenci_data = ogrenci_data
        
        # Sınıf adlarını API'den gelen listeden al
        self.sinif_adlari = [s['sinif_adi'] for s in siniflar_listesi]

        # Pencere başlığını ayarla
        if self.ogrenci_data and isinstance(self.ogrenci_data, dict):
            self.title("Öğrenci Bilgilerini Düzenle")
            ad = self.ogrenci_data.get('ad_soyad', '')
            veli = self.ogrenci_data.get('veli_iletisim', '')
        else:
            self.title("Yeni Öğrenci Ekle")
            ad, veli = "", ""
            
        self.geometry("350x300")
        self.transient(master)
        self.grab_set()

        # Arayüz elemanlarını oluştur
        ctk.CTkLabel(self, text="Ad Soyad:").pack(pady=(10,0))
        self.ad_entry = ctk.CTkEntry(self, placeholder_text="Ad Soyad", width=250)
        self.ad_entry.insert(0, ad)
        self.ad_entry.pack()

        ctk.CTkLabel(self, text="Sınıfı:").pack(pady=(10,0))
        self.sinif_combo = ctk.CTkComboBox(self, width=250, values=self.sinif_adlari)
        
        # Değişiklik 2: Sınıf seçme mantığı güncellendi
        if not self.sinif_adlari:
            self.sinif_combo.set("Önce Sınıf Ekleyin!")
            self.sinif_combo.configure(state="disabled")
        else:
            # Düzenleme modunda öğrencinin kendi sınıfını seç
            mevcut_sinif = self.ogrenci_data.get('sinif') if self.ogrenci_data else None
            if mevcut_sinif and mevcut_sinif in self.sinif_adlari:
                self.sinif_combo.set(mevcut_sinif)
            # Dışarıdan bir varsayılan sınıf geldiyse onu seç
            elif varsayilan_sinif and varsayilan_sinif in self.sinif_adlari:
                self.sinif_combo.set(varsayilan_sinif)
            # Diğer durumlarda ilk sınıfı seç
            else:
                self.sinif_combo.set(self.sinif_adlari[0])
        
        self.sinif_combo.pack()

        ctk.CTkLabel(self, text="Veli İletişim Bilgisi:").pack(pady=(10,0))
        self.veli_entry = ctk.CTkEntry(self, placeholder_text="Veli Telefon Numarası", width=250)
        self.veli_entry.insert(0, veli or "")
        self.veli_entry.pack()

        self.kaydet_butonu = ctk.CTkButton(self, text="Kaydet", command=self.kaydet)
        if not self.sinif_adlari:
            self.kaydet_butonu.configure(state="disabled") # Sınıf yoksa kaydetmeyi engelle
        self.kaydet_butonu.pack(pady=20)

    def kaydet(self):
        """Öğrenci bilgilerini API'ye göndererek kaydeder."""
        ad = self.ad_entry.get().strip()
        sinif = self.sinif_combo.get()
        veli = self.veli_entry.get().strip()
        
        if not ad:
            show_error("Eksik Bilgi", "Öğrenci adı boş bırakılamaz.", self)
            return

        data_to_send = {"ad_soyad": ad, "sinif": sinif, "veli_iletisim": veli}
        try:
            if self.ogrenci_data and 'id' in self.ogrenci_data:
                # Düzenleme modu
                response = requests.put(f"{API_URL}/ogrenci-duzenle/{self.ogrenci_data['id']}", json=data_to_send)
            else:
                # Ekleme modu
                response = requests.post(f"{API_URL}/ogrenci-ekle", json=data_to_send)
            
            response.raise_for_status()
            
            # Ana uygulamadaki listeleri yenile
            self.master_app.ogrenci_listesini_yenile()
            self.destroy()
        except requests.exceptions.RequestException as e:
            error_text = f"Öğrenci kaydedilemedi: {e}"
            try:
                error_detail = e.response.json().get('hata')
                if error_detail: error_text = error_detail
            except: pass
            show_error("API Hatası", error_text, self)