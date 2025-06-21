import customtkinter as ctk
from src.core.data_manager import DataManager
from src.core.utilities import show_info, play_notification_sound
import datetime
import winsound
import pystray
from PIL import Image

class NotificationManager:
    def __init__(self, user_role, user_id, data_manager):
        self.user_role = user_role
        self.user_id = user_id
        self.data_manager = data_manager
        self.icon = Image.open("simge.ico")
        self.tray = pystray.Icon("Öğrenci Takip", self.icon, "Öğrenci Takip Sistemi", menu=pystray.Menu(pystray.MenuItem("Çıkış", self.quit)))

    def check_assignments_deadlines(self, ogrenci_id):
        if ogrenci_id:
            assignments = self.data_manager.get_assignments(ogrenci_id)
            today = datetime.date.today()
            for assignment in assignments:
                deadline = datetime.datetime.strptime(assignment['bitis_tarihi'], "%Y-%m-%d").date()
                days_left = (deadline - today).days
                if 0 < days_left <= 3 and assignment['durum'] != "Kontrol Edildi":
                    self.show_notification(f"Ödev Hatırlatma: {assignment['ders']} - {assignment['konu']} bitişine {days_left} gün kaldı!")
                    play_notification_sound()

    def check_trial_results(self):
        if self.user_role in ["admin", "teacher"]:
            trials = self.data_manager.get_trials({"user_id": self.user_id})
            results = self.data_manager.get_trial_results(self.user_id if self.user_role == "student" else None)
            for trial in trials:
                for result in results:
                    if trial['deneme_adi'] == result['deneme_adi'] and result['result_available']:
                        self.show_notification(f"Deneme Sonucu Hazır: {trial['deneme_ani']} ({trial['tarih']})")
                        play_notification_sound()

    def check_system_updates(self):
        updates = self.data_manager.get_system_updates()
        if updates["update_available"]:
            self.show_notification("Sistem Güncellemesi: Yeni bir güncelleme mevcut!")
            play_notification_sound()

    def show_notification(self, message):
        show_info("Bildirim", message)
        self.tray.notify(message)

    def quit(self, icon, item):
        icon.stop()