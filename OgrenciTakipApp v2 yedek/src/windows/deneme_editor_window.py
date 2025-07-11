# src/windows/deneme_editor_window.py

import customtkinter as ctk
import requests
from src.core.utilities import API_URL, show_error

class DenemeEditorWindow(ctk.CTkToplevel):
    def __init__(self, master, ogrenci_id, deneme_id=None):
        super().__init__(master)
        self.master_app = master
        self.ogrenci_id = ogrenci_id
        self.deneme_id = deneme_id
        self.ders_satirlari_widget = []

        ogrenci_adi = self.master_app.get_ogrenci_adi_from_cache(ogrenci_id)
        if self.deneme_id:
            self.title(f"{ogrenci_adi} - Deneme Düzenle")
        else:
            self.title(f"{ogrenci_adi} - Yeni Deneme Ekle")
        
        self.geometry("600x500")
        self.transient(master)
        self.grab_set()
        
        ctk.CTkLabel(self, text="Deneme Adı:").pack(pady=(10,0))
        self.deneme_adi_entry = ctk.CTkEntry(self, placeholder_text="Örn: TYT Genel Deneme 1", width=300)
        self.deneme_adi_entry.pack()
        
        self.dersler_cerceve = ctk.CTkScrollableFrame(self, label_text="Ders Sonuçları")
        self.dersler_cerceve.pack(pady=10, padx=10, fill="both", expand=True)
        
        ctk.CTkButton(self, text="Yeni Ders Ekle", command=lambda: self.ders_satiri_ekle()).pack(pady=5)
        ctk.CTkButton(self, text="Kaydet", command=self.kaydet).pack(pady=10)
        
        if self.deneme_id:
            self.mevcut_dersleri_yukle()
        else: # Yeni deneme ise varsayılan bir ders satırı ekle
            self.ders_satiri_ekle()

    def ders_satiri_ekle(self, ders="", d=0, y=0, b=0):
        satir_cerceve = ctk.CTkFrame(self.dersler_cerceve)
        satir_cerceve.pack(fill="x", pady=4, padx=5)
        
        # Ders Adı
        ders_cerceve = ctk.CTkFrame(satir_cerceve); ders_cerceve.pack(side="left", padx=5, fill="x", expand=True)
        ctk.CTkLabel(ders_cerceve, text="Ders Adı").pack(anchor="w")
        ders_entry = ctk.CTkEntry(ders_cerceve, placeholder_text="Ders Adı"); ders_entry.insert(0, ders); ders_entry.pack(fill="x")
        
        # Doğru
        dogru_cerceve = ctk.CTkFrame(satir_cerceve); dogru_cerceve.pack(side="left", padx=5)
        ctk.CTkLabel(dogru_cerceve, text="Doğru").pack(anchor="w")
        d_entry = ctk.CTkEntry(dogru_cerceve, width=70); d_entry.insert(0, str(d)); d_entry.pack()
        
        # Yanlış
        yanlis_cerceve = ctk.CTkFrame(satir_cerceve); yanlis_cerceve.pack(side="left", padx=5)
        ctk.CTkLabel(yanlis_cerceve, text="Yanlış").pack(anchor="w")
        y_entry = ctk.CTkEntry(yanlis_cerceve, width=70); y_entry.insert(0, str(y)); y_entry.pack()
        
        # Boş
        bos_cerceve = ctk.CTkFrame(satir_cerceve); bos_cerceve.pack(side="left", padx=5)
        ctk.CTkLabel(bos_cerceve, text="Boş").pack(anchor="w")
        b_entry = ctk.CTkEntry(bos_cerceve, width=70); b_entry.insert(0, str(b)); b_entry.pack()

        # Sil Butonu
        sil_butonu = ctk.CTkButton(satir_cerceve, text="Sil", width=40, fg_color="red", command=lambda s=satir_cerceve: self.ders_satiri_sil(s))
        sil_butonu.pack(side="right", padx=5, pady=15)
        
        widget_tuple = (satir_cerceve, ders_entry, d_entry, y_entry, b_entry)
        self.ders_satirlari_widget.append(widget_tuple)

    def ders_satiri_sil(self, satir_cerceve_to_delete):
        for i, widget_tuple in enumerate(self.ders_satirlari_widget):
            if widget_tuple[0] == satir_cerceve_to_delete:
                del self.ders_satirlari_widget[i]
                break
        satir_cerceve_to_delete.destroy()

    def mevcut_dersleri_yukle(self):
        try:
            response = requests.get(f"{API_URL}/deneme/{self.deneme_id}"); response.raise_for_status()
            deneme_data = response.json()
            if deneme_data.get("hata"):
                show_error("Hata", deneme_data["hata"], self); self.destroy(); return
            self.deneme_adi_entry.insert(0, deneme_data.get('deneme_adi', ''))
            for ders in deneme_data.get('dersler', []):
                self.ders_satiri_ekle(ders['ders_adi'], ders['dogru'], ders['yanlis'], ders['bos'])
        except requests.exceptions.RequestException as e:
            show_error("API Hatası", f"Deneme verileri yüklenemedi: {e}", self)

    def kaydet(self):
        deneme_adi = self.deneme_adi_entry.get().strip()
        if not deneme_adi:
            show_error("Eksik Bilgi", "Deneme adı boş bırakılamaz.", self)
            return
            
        dersler_data = []
        try:
            for _, ders_w, d_w, y_w, b_w in self.ders_satirlari_widget:
                dersler_data.append({
                    "ders_adi": ders_w.get(), 
                    "dogru": int(d_w.get() or 0), 
                    "yanlis": int(y_w.get() or 0), 
                    "bos": int(b_w.get() or 0)
                })
            
            data_to_send = {"ogrenci_id": self.ogrenci_id, "deneme_adi": deneme_adi, "dersler": dersler_data}
            
            if self.deneme_id:
                response = requests.put(f"{API_URL}/deneme-duzenle/{self.deneme_id}", json=data_to_send)
            else:
                response = requests.post(f"{API_URL}/deneme-ekle", json=data_to_send)
            
            response.raise_for_status()
            self.master_app.deneme_listesini_yenile()
            self.destroy()
        except ValueError:
            show_error("Değer Hatası", "Doğru, yanlış, boş alanlarına sayısal değer girin.", self)
        except requests.exceptions.RequestException as e:
            show_error("API Hatası", f"Deneme kaydedilemedi: {e}", self)