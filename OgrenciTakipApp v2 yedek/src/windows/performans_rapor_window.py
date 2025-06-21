# src/windows/performans_rapor_window.py dosyası oluştur:
import customtkinter as ctk
from src.core.data_manager import DataManager
from fpdf import FPDF
from tkinter import filedialog
import datetime

class PerformansRaporWindow(ctk.CTkToplevel):
    def __init__(self, master, ogrenci_id, ogrenci_adi):
        super().__init__(master)
        self.title(f"{ogrenci_adi} Performans Raporu")
        self.geometry("800x600")
        self.transient(master)
        self.grab_set()
        self.ogrenci_id = ogrenci_id
        self.ogrenci_adi = ogrenci_adi
        self.data_manager = DataManager(master.user_role, master.user_id)

        # Verileri çek
        self.trials = self.data_manager.get_student_trials_performance(ogrenci_id)
        self.sessions = self.data_manager.get_student_problem_sessions_performance(ogrenci_id)
        self.assignments = self.data_manager.get_student_assignments_performance(ogrenci_id)

        # Grafik alanları
        self.deneme_grafik = ctk.CTkLabel(self, text="Deneme Puanları Grafiği")
        self.deneme_grafik.pack(pady=10, padx=10, fill="both", expand=True)
        self.soru_grafik = ctk.CTkLabel(self, text="Soru Çözümü İlerleme Grafiği")
        self.soru_grafik.pack(pady=10, padx=10, fill="both", expand=True)
        self.odev_grafik = ctk.CTkLabel(self, text="Ödev Tamamlama Oranı Grafiği")
        self.odev_grafik.pack(pady=10, padx=10, fill="both", expand=True)

        # Grafikleri oluştur
        self.grafikleri_olustur()

        # İndirme butonu
        ctk.CTkButton(self, text="PDF İndir", command=self.pdf_indir).pack(pady=10, padx=10)

    def grafikleri_olustur(self):
        # Deneme Puanları (Çubuk Grafik)
        deneme_veriler = {t["deneme_adi"]: t["puan"] for t in self.trials}
        if deneme_veriler:
            self.deneme_grafik.configure(text="")
            chart_config = {
                "type": "bar",
                "data": {
                    "labels": list(deneme_veriler.keys()),
                    "datasets": [{
                        "label": "Puan",
                        "data": list(deneme_veriler.values()),
                        "backgroundColor": ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0"]
                    }]
                },
                "options": {
                    "responsive": True,
                    "maintainAspectRatio": False,
                    "scales": {"y": {"beginAtZero": True}}
                }
            }
            self.deneme_grafik.configure(text=chart_config)

        # Soru Çözümü İlerleme (Çizgi Grafik)
        session_veriler = {s["seans_adi"]: s["sure"] for s in self.sessions}
        if session_veriler:
            self.soru_grafik.configure(text="")
            chart_config = {
                "type": "line",
                "data": {
                    "labels": list(session_veriler.keys()),
                    "datasets": [{
                        "label": "Süre (dk)",
                        "data": list(session_veriler.values()),
                        "borderColor": "#36A2EB",
                        "fill": False
                    }]
                },
                "options": {
                    "responsive": True,
                    "maintainAspectRatio": False,
                    "scales": {"y": {"beginAtZero": True}}
                }
            }
            self.soru_grafik.configure(text=chart_config)

        # Ödev Tamamlama Oranı (Çember Grafik)
        if self.assignments["toplam"] > 0:
            self.odev_grafik.configure(text="")
            chart_config = {
                "type": "doughnut",
                "data": {
                    "labels": ["Tamamlandı", "Tamamlanmadı"],
                    "datasets": [{
                        "data": [self.assignments["tamamlanan"], self.assignments["toplam"] - self.assignments["tamamlanan"]],
                        "backgroundColor": ["#4BC0C0", "#FF6384"]
                    }]
                },
                "options": {
                    "responsive": True,
                    "maintainAspectRatio": False
                }
            }
            self.odev_grafik.configure(text=chart_config)

    def pdf_indir(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Document", "*.pdf")], title="Raporu PDF Olarak Kaydet")
        if not file_path:
            return
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, f"{self.ogrenci_adi} Performans Raporu", ln=True, align="C")
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
        pdf.ln(10)
        # Deneme Puanları
        pdf.cell(0, 10, "Deneme Puanları", ln=True, align="L")
        for trial in self.trials:
            pdf.cell(0, 10, f"{trial['deneme_adi']} ({trial['tarih']}): {trial['puan']} puan", ln=True)
        pdf.ln(10)
        # Soru Çözümü
        pdf.cell(0, 10, "Soru Çözümü Seansları", ln=True, align="L")
        for session in self.sessions:
            pdf.cell(0, 10, f"{session['seans_adi']} ({session['tarih']}): {session['sure']} dk", ln=True)
        pdf.ln(10)
        # Ödev Tamamlama
        pdf.cell(0, 10, "Ödev Tamamlama Oranı", ln=True, align="L")
        pdf.cell(0, 10, f"Tamamlanan: {self.assignments['tamamlanan']} / Toplam: {self.assignments['toplam']}", ln=True)
        pdf.output(file_path)