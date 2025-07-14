# src/windows/soru_cozum_editor_window.py

import customtkinter as ctk
import requests
from src.core.utilities import API_URL, show_error

class SoruCozumEditorWindow(ctk.CTkToplevel):
    def __init__(self, master, ogrenci_id, seans_id=None):
        super().__init__(master)
        self.master_app = master
        self.ogrenci_id = ogrenci_id
        self.seans_id = seans_id
        self.ders_satirlari_widget = []

        ogrenci_adi = self.master_app.get_ogrenci_adi_from_cache(ogrenci_id)
        if self.seans_id:
            self.title(f"{ogrenci_adi} - Soru Çözüm Seansı Düzenle")
        else:
            self.title(f"{ogrenci_adi} - Yeni Soru Çözüm Seansı Ekle")
        
        self.geometry("500x450")
        self.transient(master)
        self.grab_set()
        
        ctk.CTkLabel(self, text="Seans Adı:").pack(pady=(10,0))
        self.seans_adi_entry = ctk.CTkEntry(self, placeholder_text="Örn: Hafta Sonu TYT Tekrarı", width=300)
        self.seans_adi_entry.pack()
        
        self.dersler_cerceve = ctk.CTkScrollableFrame(self, label_text="Dersler ve Soru Sayıları")
        self.dersler_cerceve.pack(pady=10, padx=10, fill="both", expand=True)
        
        ctk.CTkButton(self, text="Yeni Ders Ekle", command=lambda: self.ders_satiri_ekle()).pack(pady=5)
        ctk.CTkButton(self, text="Kaydet", command=self.kaydet).pack(pady=10)
        
        if self.seans_id:
            self.mevcut_seans_verilerini_yukle()
        else:
            self.ders_satiri_ekle()

    def ders_satiri_ekle(self, ders="", soru_sayisi=0):
        satir_cerceve = ctk.CTkFrame(self.dersler_cerceve)
        satir_cerceve.pack(fill="x", pady=4, padx=5)
        
        # Ders Adı
        ders_cerceve = ctk.CTkFrame(satir_cerceve)
        ders_cerceve.pack(side="left", padx=5, fill="x", expand=True)
        ctk.CTkLabel(ders_cerceve, text="Ders Adı").pack(anchor="w")
        ders_entry = ctk.CTkEntry(ders_cerceve, placeholder_text="Ders Adı")
        ders_entry.insert(0, ders)
        ders_entry.pack(fill="x")
        
        # Soru Sayısı
        soru_cerceve = ctk.CTkFrame(satir_cerceve)
        soru_cerceve.pack(side="left", padx=5)
        ctk.CTkLabel(soru_cerceve, text="Soru Sayısı").pack(anchor="w")
        soru_entry = ctk.CTkEntry(soru_cerceve, width=100)
        soru_entry.insert(0, str(soru_sayisi))
        soru_entry.pack()

        # Sil Butonu
        sil_butonu = ctk.CTkButton(satir_cerceve, text="Sil", width=40, fg_color="red", command=lambda s=satir_cerceve: self.ders_satiri_sil(s))
        sil_butonu.pack(side="right", padx=5, pady=15)
        
        widget_tuple = (satir_cerceve, ders_entry, soru_entry)
        self.ders_satirlari_widget.append(widget_tuple)

    def ders_satiri_sil(self, satir_cerceve_to_delete):
        for i, widget_tuple in enumerate(self.ders_satirlari_widget):
            if widget_tuple[0] == satir_cerceve_to_delete:
                del self.ders_satirlari_widget[i]
                break
        satir_cerceve_to_delete.destroy()

    def mevcut_seans_verilerini_yukle(self):
        # Bu fonksiyonun çalışması için backend'de GET /soru-cozumu/<seans_id> endpoint'i olmalıdır.
        # Örnek olarak bırakılmıştır, backend'e eklenmesi gerekir.
        show_error("Henüz Tamamlanmadı", "Düzenleme modu için sunucu desteği eklenmelidir.")
        self.destroy()

    def kaydet(self):
        seans_adi = self.seans_adi_entry.get().strip()
        if not seans_adi:
   	     show_error("Eksik Bilgi", "Seans adı boş bırakılamaz.")
   	     return
            
        dersler_data = []
        try:
            for _, ders_w, soru_w in self.ders_satirlari_widget:
                dersler_data.append({
                    "ders_adi": ders_w.get(), 
                    "soru_sayisi": int(soru_w.get() or 0)
                })
                
            data_to_send = {"ogrenci_id": self.ogrenci_id, "seans_adi": seans_adi, "dersler": dersler_data}
            
            if self.seans_id:
                # response = requests.put(f"{API_URL}/soru-cozumu-duzenle/{self.seans_id}", json=data_to_send)
                # Backend'de PUT endpoint'i oluşturulmalı
                pass
            else:
                response = requests.post(f"{API_URL}/soru-cozumu-ekle", json=data_to_send)
            
            response.raise_for_status()
            self.master_app.soru_cozumu_listesini_yenile()
            self.destroy()
        except ValueError:
            show_error("Değer Hatası", "Soru sayısı alanlarına sayısal değer girin.", self)
        except requests.exceptions.RequestException as e:
            show_error("API Hatası", f"Soru çözüm seansı kaydedilemedi: {e}")