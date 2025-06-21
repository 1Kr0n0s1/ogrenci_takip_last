import customtkinter as ctk
from src.core.data_manager import DataManager

class IstatistiklerWindow(ctk.CTkToplevel):
    def __init__(self, master, user_id):
        super().__init__(master)
        self.title("İstatistikler ve Raporlama")
        self.geometry("800x600")
        self.transient(master)
        self.grab_set()
        self.user_id = user_id
        self.data_manager = DataManager(master.user_role, user_id)

        # Sınıf seçimi
        ctk.CTkLabel(self, text="Sınıf Seç:").pack(pady=5, padx=10)
        self.sinif_var = ctk.StringVar(value="Tüm Sınıflar")
        ctk.CTkOptionMenu(self, variable=self.sinif_var, values=["Tüm Sınıflar", "9A", "9B", "10A", "10B"]).pack(pady=5, padx=10)

        # Tarih aralığı
        ctk.CTkLabel(self, text="Tarih Aralığı:").pack(pady=5, padx=10)
        self.baslangic_entry = ctk.CTkEntry(self, placeholder_text="Başlangıç (YYYY-MM-DD)")
        self.baslangic_entry.pack(pady=5, padx=10)
        self.bitis_entry = ctk.CTkEntry(self, placeholder_text="Bitiş (YYYY-MM-DD)")
        self.bitis_entry.pack(pady=5, padx=10)

        # Grafik alanları
        self.deneme_grafik = ctk.CTkLabel(self, text="Deneme Ortalamaları")
        self.deneme_grafik.pack(pady=10, padx=10, fill="both", expand=True)
        self.tamamlama_grafik = ctk.CTkLabel(self, text="Tamamlama Oranları")
        self.tamamlama_grafik.pack(pady=10, padx=10, fill="both", expand=True)

        # Güncelle butonu
        ctk.CTkButton(self, text="İstatistikleri Güncelle", command=self.grafikleri_olustur).pack(pady=10, padx=10)

    def grafikleri_olustur(self):
        sinif = self.sinif_var.get()
        baslangic = self.baslangic_entry.get().strip()
        bitis = self.bitis_entry.get().strip()

        # Deneme Ortalamaları (Çubuk Grafik)
        averages = self.data_manager.get_class_trial_averages(sinif if sinif != "Tüm Sınıflar" else None)
        if averages:
            self.deneme_grafik.configure(text="")
            chart_config = {
                "type": "bar",
                "data": {
                    "labels": [a["deneme_ani"] for a in averages],
                    "datasets": [{
                        "label": "Ortalama Puan",
                        "data": [a["ortalama"] for a in averages],
                        "backgroundColor": ["#36A2EB", "#FF6384", "#FFCE56"]
                    }]
                },
                "options": {
                    "responsive": True,
                    "maintainAspectRatio": False,
                    "scales": {"y": {"beginAtZero": True}}
                }
            }
            self.deneme_grafik.configure(text=chart_config)

        # Tamamlama Oranları (Çember Grafik)
        rates = self.data_manager.get_completion_rates(self.user_id)
        if rates["odev"] > 0 or rates["soru"] > 0:
            self.tamamlama_grafik.configure(text="")
            chart_config = {
                "type": "doughnut",
                "data": {
                    "labels": ["Ödev Tamamlama", "Soru Çözümü Tamamlama"],
                    "datasets": [{
                        "data": [rates["odev"], rates["soru"]],
                        "backgroundColor": ["#4BC0C0", "#FFCE56"]
                    }]
                },
                "options": {
                    "responsive": True,
                    "maintainAspectRatio": False
                }
            }
            self.tamamlama_grafik.configure(text=chart_config)