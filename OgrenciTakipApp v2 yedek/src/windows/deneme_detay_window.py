import customtkinter as ctk
import requests
from src.core.utilities import API_URL, show_error

class DenemeDetayWindow(ctk.CTkToplevel):
    def __init__(self, master, deneme_id):
        super().__init__(master)
        try:
            response = requests.get(f"{API_URL}/deneme/{deneme_id}"); response.raise_for_status(); deneme_data = response.json()
            if deneme_data.get("hata"): show_error("Veri Hatası", deneme_data["hata"]); self.destroy(); return
            deneme_adi, tarih, ogrenci_adi = deneme_data.get('deneme_adi'), deneme_data.get('tarih'), deneme_data.get('ad_soyad')
            self.title(f"Deneme Detayı"); self.geometry("400x400"); self.transient(master); self.grab_set()
            ctk.CTkLabel(self, text=deneme_adi, font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10,0))
            ctk.CTkLabel(self, text=f"Öğrenci: {ogrenci_adi} - Tarih: {tarih}").pack()
            dersler_cerceve = ctk.CTkScrollableFrame(self, label_text="Ders Sonuçları"); dersler_cerceve.pack(pady=10, padx=10, fill="both", expand=True)
            toplam_net = 0
            for ders in deneme_data.get('dersler', []):
                d = ders.get('dogru',0) or 0; y = ders.get('yanlis',0) or 0; b = ders.get('bos',0) or 0
                net = d - (y / 4); toplam_net += net
                sonuc_str = f"• {ders['ders_adi']}: D: {d}, Y: {y}, B: {b} (Net: {net:.2f})"
                ctk.CTkLabel(dersler_cerceve, text=sonuc_str, anchor="w").pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(self, text=f"Toplam Net: {toplam_net:.2f}", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        except requests.exceptions.RequestException as e: show_error("API Hatası", f"Deneme detayı alınamadı: {e}"); self.destroy()