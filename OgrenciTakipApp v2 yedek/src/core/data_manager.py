import sqlite3
import requests
import json
from datetime import datetime
from src.core.utilities import API_URL, show_error, restrict_access
import os

class DataManager:
    def __init__(self, user_role, user_id):
        self.user_role = user_role
        self.user_id = user_id
        self.db_path = "offline_data.db"
        self.is_online = self.check_online()
        self.init_db()

    def check_online(self):
        try:
            response = requests.get(f"{API_URL}/ping", timeout=2)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def init_db(self):
        if not os.path.exists(self.db_path):
            open(self.db_path, 'a').close()
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY,
                ad_soyad TEXT,
                sinif TEXT,
                user_id INTEGER,
                synced INTEGER,
                deleted INTEGER
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY,
                ogrenci_id INTEGER,
                ders TEXT,
                konu TEXT,
                baslangic_tarihi TEXT,
                verilis_tarihi TEXT,
                bitis_tarihi TEXT,
                durum TEXT,
                synced INTEGER,
                deleted INTEGER
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS trials (
                id INTEGER PRIMARY KEY,
                ogrenci_id INTEGER,
                deneme_adi TEXT,
                tarih TEXT,
                ad_soyad TEXT,
                synced INTEGER,
                deleted INTEGER
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS problem_sessions (
                id INTEGER PRIMARY KEY,
                ogrenci_id INTEGER,
                seans_adi TEXT,
                tarih TEXT,
                ad_soyad TEXT,
                synced INTEGER,
                deleted INTEGER
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS schedules (
                ogrenci_id INTEGER PRIMARY KEY,
                grid_data TEXT,
                synced INTEGER
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation TEXT,
                table_name TEXT,
                record_id INTEGER,
                data TEXT,
                timestamp TEXT
            )''')
            conn.commit()

    def execute_offline(self, operation, table_name, record_id=None, data=None):
        if operation in ["insert", "update", "delete"]:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                if operation == "insert":
                    if table_name == "students":
                        c.execute("INSERT INTO students (id, ad_soyad, sinif, user_id, synced, deleted) VALUES (?, ?, ?, ?, 0, 0)",
                                  (data["id"], data["ad_soyad"], data["sinif"], self.user_id))
                    elif table_name == "assignments":
                        c.execute("INSERT INTO assignments (id, ogrenci_id, ders, konu, verilis_tarihi, bitis_tarihi, durum, synced, deleted) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0)",
                                  (data["id"], data["ogrenci_id"], data["ders"], data["konu"], data["verilis_tarihi"], data["bitis_tarihi"], data["durum"]))
                    elif table_name == "trials":
                        c.execute("INSERT INTO trials (id, ogrenci_id, deneme_adi, tarih, ad_soyad, synced, deleted) VALUES (?, ?, ?, ?, ?, 0, 0)",
                                  (data["id"], data["ogrenci_id"], data["deneme_adi"], data["tarih"], data["ad_soyad"]))
                    elif table_name == "problem_sessions":
                        c.execute("INSERT INTO problem_sessions (id, ogrenci_id, seans_adi, tarih, ad_soyad, synced, deleted) VALUES (?, ?, ?, ?, ?, 0, 0)",
                                  (data["id"], data["ogrenci_id"], data["seans_adi"], data["tarih"], data["ad_soyad"]))
                    elif table_name == "schedules":
                        c.execute("INSERT OR REPLACE INTO schedules (ogrenci_id, grid_data, synced) VALUES (?, ?, 0)",
                                  (data["ogrenci_id"], json.dumps(data["grid_data"])))
                    record_id = c.lastrowid if table_name != "schedules" else data["ogrenci_id"]
                elif operation == "update":
                    if table_name == "assignments":
                        c.execute("UPDATE assignments SET durum = ?, synced = 0 WHERE id = ?", (data["durum"], record_id))
                elif operation == "delete":
                    c.execute(f"UPDATE {table_name} SET deleted = 1, synced = 0 WHERE id = ?", (record_id,))
                c.execute("INSERT INTO sync_queue (operation, table_name, record_id, data, timestamp) VALUES (?, ?, ?, ?, ?)",
                          (operation, table_name, record_id, json.dumps(data) if data else None, datetime.now().isoformat()))
                conn.commit()
        return record_id
    def sync_data(self):
        if not self.is_online:
            return
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM sync_queue ORDER BY timestamp")
            queue = c.fetchall()
            for q in queue:
                q_id, operation, table_name, record_id, data, _ = q
                data = json.loads(data) if data else {}
                try:
                    if operation == "insert":
                        if table_name == "students":
                            response = requests.post(f"{API_URL}/ogrenci-ekle", json={"ad_soyad": data["ad_soyad"], "sinif": data["sinif"], "user_id": self.user_id})
                        elif table_name == "assignments":
                            response = requests.post(f"{API_URL}/odev-ekle", json=data)
                        elif table_name == "trials":
                            response = requests.post(f"{API_URL}/deneme-ekle", json=data)
                        elif table_name == "problem_sessions":
                            response = requests.post(f"{API_URL}/soru-cozumu-ekle", json=data)
                        elif table_name == "schedules":
                            response = requests.post(f"{API_URL}/program-kaydet/{record_id}", json=data["grid_data"])
                        response.raise_for_status()
                    elif operation == "update":
                        if table_name == "assignments":
                            response = requests.put(f"{API_URL}/odev-durum-guncelle/{record_id}", json={"durum": data["durum"]})
                            response.raise_for_status()
                    elif operation == "delete":
                        if table_name == "students":
                            response = requests.delete(f"{API_URL}/ogrenci-sil/{record_id}")
                        elif table_name == "assignments":
                            response = requests.delete(f"{API_URL}/odev-sil/{record_id}")
                        elif table_name == "trials":
                            response = requests.delete(f"{API_URL}/deneme-sil/{record_id}")
                        elif table_name == "problem_sessions":
                            response = requests.delete(f"{API_URL}/soru-cozumu-sil/{record_id}")
                        response.raise_for_status()
                    c.execute("UPDATE {} SET synced = 1 WHERE id = ?".format(table_name), (record_id,))
                    c.execute("DELETE FROM sync_queue WHERE id = ?", (q_id,))
                    conn.commit()
                except requests.exceptions.RequestException as e:
                    show_error("Senkronizasyon Hatası", f"Veri senkronize edilemedi: {e}")
                    break

    def get_students(self):
        if self.is_online:
            try:
                params = {"user_id": self.user_id} if self.user_role == "teacher" else {}
                response = requests.get(f"{API_URL}/ogrenciler", params=params)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException:
                self.is_online = False
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM students WHERE deleted = 0")
            students = [{"id": row[0], "ad_soyad": row[1], "sinif": row[2], "user_id": row[3]} for row in c.fetchall()]
            return students

    def get_assignments(self, ogrenci_id):
        if self.is_online:
            try:
                response = requests.get(f"{API_URL}/odevler/{ogrenci_id}")
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                show_error("API Hatası", f"Ödevler yüklenemedi: {e}")
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT id, ders, konu, baslangic_tarihi, verilis_tarihi, bitis_tarihi, durum FROM assignments WHERE ogrenci_id = ? AND synced = 1 AND deleted = 0", (ogrenci_id,))
            assignments = c.fetchall()
            return [{"id": row[0], "ders": row[1], "konu": row[2], "baslangic_tarihi": row[3], "verilis_tarihi": row[4], "bitis_tarihi": row[5], "durum": row[6]} for row in assignments]
    
    def get_assignment(self, odev_id):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT id, ogrenci_id, ders, konu, baslangic_tarihi, verilis_tarihi, bitis_tarihi, durum FROM assignments WHERE id = ? AND synced = 1 AND deleted = 0", (odev_id,))
            row = c.fetchone()
            return {"id": row[0], "ogrenci_id": row[1], "ders": row[2], "konu": row[3], "baslangic_tarihi": row[4], "verilis_tarihi": row[5], "bitis_tarihi": row[6], "durum": row[7]} if row else None
        
    def get_trials(self, params):
        if self.is_online:
            try:
                response = requests.get(f"{API_URL}/denemeler", params=params)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException:
                self.is_online = False
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            query = "SELECT * FROM trials WHERE deleted = 0"
            if "ogrenci_id" in params:
                query += " AND ogrenci_id = ?"
                c.execute(query, (params["ogrenci_id"],))
            else:
                c.execute(query)
            trials = [{"id": row[0], "ogrenci_id": row[1], "deneme_adi": row[2], "tarih": row[3], "ad_soyad": row[4]} for row in c.fetchall()]
            return trials

    def get_problem_sessions(self, params):
        if self.is_online:
            try:
                response = requests.get(f"{API_URL}/soru-cozumleri", params=params)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException:
                self.is_online = False
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            query = "SELECT * FROM problem_sessions WHERE deleted = 0"
            if "ogrenci_id" in params:
                query += " AND ogrenci_id = ?"
                c.execute(query, (params["ogrenci_id"],))
            else:
                c.execute(query)
            sessions = [{"id": row[0], "ogrenci_id": row[1], "seans_adi": row[2], "tarih": row[3], "ad_soyad": row[4]} for row in c.fetchall()]
            return sessions

    def get_schedule(self, ogrenci_id):
        if self.is_online:
            try:
                response = requests.get(f"{API_URL}/program/{ogrenci_id}")
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException:
                self.is_online = False
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT grid_data FROM schedules WHERE ogrenci_id = ?", (ogrenci_id,))
            result = c.fetchone()
            return json.loads(result[0]) if result else []

    def add_student(self, data):
        if not restrict_access(self.user_role, ["admin", "teacher"]):
            show_error("Yetki Hatası", "Öğrenci eklemek için yetkiniz yok.")
            return
        data["id"] = int(datetime.now().timestamp() * 1000)  # Geçici ID
        if self.is_online:
            try:
                response = requests.post(f"{API_URL}/ogrenci-ekle", json={"ad_soyad": data["ad_soyad"], "sinif": data["sinif"], "user_id": self.user_id})
                response.raise_for_status()
                return response.json()["id"]
            except requests.exceptions.RequestException:
                self.is_online = False
        return self.execute_offline("insert", "students", data=data)

    def delete_student(self, ogrenci_id):
        if not restrict_access(self.user_role, "admin"):
            show_error("Yetki Hatası", "Öğrenci silmek için yönetici yetkisi gerekir.")
            return
        if self.is_online:
            try:
                response = requests.delete(f"{API_URL}/ogrenci-sil/{ogrenci_id}")
                response.raise_for_status()
            except requests.exceptions.RequestException:
                self.is_online = False
                self.execute_offline("delete", "students", record_id=ogrenci_id)
        else:
            self.execute_offline("delete", "students", record_id=ogrenci_id)

    def add_assignment(self, data):
        if not restrict_access(self.user_role, ["admin", "teacher"]):
            self.logger.warning("Yetkisiz ödev ekleme attempted: role=%s", self.user_role)
            show_error("Yetki Hatası", "Ödev eklemek için yetkiniz yok.")
            return
        data["id"] = int(datetime.now().timestamp() * 1000)  # Geçici ID
        if self.is_online:
            try:
                self.logger.info("API ile ödev ekleme attempted: ogrenci_id=%d", data["ogrenci_id"])
                response = requests.post(f"{API_URL}/odev-ekle", json=data)
                response.raise_for_status()
                return response.json()["id"]
            except requests.exceptions.RequestException as e:
                self.logger.error("API hatası: %s", str(e))
                show_error("API Hatası", f"Ödev eklenemedi: {e}")
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO assignments (id, ogrenci_id, ders, konu, baslangic_tarihi, verilis_tarihi, bitis_tarihi, durum) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (data["id"], data["ogrenci_id"], data["ders"], data["konu"], data.get("baslangic_tarihi"), data["verilis_tarihi"], data["bitis_tarihi"], data["durum"]))
            conn.commit()
            assignment_id = data["id"] 
            self.logger.info("Çevrimdışı ödev eklendi: ID=%d", assignment_id)
        if not self.is_online:
            self.execute_offline("INSERT", "assignments", assignment_id, data)
        return assignment_id

    def update_assignment_status(self, odev_id, durum):
        if not restrict_access(self.user_role, ["admin", "teacher"]):
            show_error("Yetki Hatası", "Ödev durumu güncellemek için yetkiniz yok.")
            return
        if self.is_online:
            try:
                response = requests.put(f"{API_URL}/odev-durum-guncelle/{odev_id}", json={"durum": durum})
                response.raise_for_status()
            except requests.exceptions.RequestException:
                self.is_online = False
                self.execute_offline("update", "assignments", record_id=odev_id, data={"durum": durum})
        else:
            self.execute_offline("update", "assignments", record_id=odev_id, data={"durum": durum})

    def delete_assignment(self, odev_id):
        if not restrict_access(self.user_role, ["admin", "teacher"]):
            show_error("Yetki Hatası", "Ödev silmek için yetkiniz yok.")
            return
        if self.is_online:
            try:
                response = requests.delete(f"{API_URL}/odev-sil/{odev_id}")
                response.raise_for_status()
            except requests.exceptions.RequestException:
                self.is_online = False
                self.execute_offline("delete", "assignments", record_id=odev_id)
        else:
            self.execute_offline("delete", "assignments", record_id=odev_id)

    def add_trial(self, data):
        if not restrict_access(self.user_role, ["admin", "teacher"]):
            show_error("Yetki Hatası", "Deneme eklemek için yetkiniz yok.")
            return
        data["id"] = int(datetime.now().timestamp() * 1000)
        if self.is_online:
            try:
                response = requests.post(f"{API_URL}/deneme-ekle", json=data)
                response.raise_for_status()
                return response.json()["id"]
            except requests.exceptions.RequestException:
                self.is_online = False
        return self.execute_offline("insert", "trials", data=data)

    def delete_trial(self, deneme_id):
        if not restrict_access(self.user_role, ["admin", "teacher"]):
            show_error("Yetki Hatası", "Deneme silmek için yetkiniz yok.")
            return
        if self.is_online:
            try:
                response = requests.delete(f"{API_URL}/deneme-sil/{deneme_id}")
                response.raise_for_status()
            except requests.exceptions.RequestException:
                self.is_online = False
                self.execute_offline("delete", "trials", record_id=deneme_id)
        else:
            self.execute_offline("delete", "trials", record_id=deneme_id)

    def add_problem_session(self, data):
        if not restrict_access(self.user_role, ["admin", "teacher"]):
            show_error("Yetki Hatası", "Seans eklemek için yetkiniz yok.")
            return
        data["id"] = int(datetime.now().timestamp() * 1000)
        if self.is_online:
            try:
                response = requests.post(f"{API_URL}/soru-cozumu-ekle", json=data)
                response.raise_for_status()
                return response.json()["id"]
            except requests.exceptions.RequestException:
                self.is_online = False
        return self.execute_offline("insert", "problem_sessions", data=data)

    def delete_problem_session(self, seans_id):
        if not restrict_access(self.user_role, ["admin", "teacher"]):
            show_error("Yetki Hatası", "Seans silmek için yetkiniz yok.")
            return
        if self.is_online:
            try:
                response = requests.delete(f"{API_URL}/soru-cozumu-sil/{seans_id}")
                response.raise_for_status()
            except requests.exceptions.RequestException:
                self.is_online = False
                self.execute_offline("delete", "problem_sessions", record_id=seans_id)
        else:
            self.execute_offline("delete", "problem_sessions", record_id=seans_id)

    def save_schedule(self, ogrenci_id, grid_data):
        if not restrict_access(self.user_role, ["admin", "teacher"]):
            show_error("Yetki Hatası", "Program kaydetmek için yetkiniz yok.")
            return
        if self.is_online:
            try:
                response = requests.post(f"{API_URL}/program-kaydet/{ogrenci_id}", json=grid_data)
                response.raise_for_status()
            except requests.exceptions.RequestException:
                self.is_online = False
                self.execute_offline("insert", "schedules", data={"ogrenci_id": ogrenci_id, "grid_data": grid_data})
        else:
            self.execute_offline("insert", "schedules", data={"ogrenci_id": ogrenci_id, "grid_data": grid_data})
    
    def get_student_trials_performance(self, ogrenci_id):
        if self.is_online:
            try:
                response = requests.get(f"{API_URL}/trials/performance?ogrenci_id={ogrenci_id}")
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException:
                return []
        else:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute("SELECT deneme_adi, tarih FROM trials WHERE ogrenci_id = ? AND synced = 1 AND deleted = 0", (ogrenci_id,))
                return [{"deneme_adi": row[0], "tarih": row[1], "puan": 0} for row in c.fetchall()]  # Puan placeholder, API'den gelecek

    def get_student_problem_sessions_performance(self, ogrenci_id):
        if self.is_online:
            try:
                response = requests.get(f"{API_URL}/problem_sessions/performance?ogrenci_id={ogrenci_id}")
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException:
                return []
        else:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute("SELECT seans_adi, tarih FROM problem_sessions WHERE ogrenci_id = ? AND synced = 1 AND deleted = 0", (ogrenci_id,))
                return [{"seans_adi": row[0], "tarih": row[1], "sure": 0} for row in c.fetchall()]  # Süre placeholder

    def get_student_assignments_performance(self, ogrenci_id):
        if self.is_online:
            try:
                response = requests.get(f"{API_URL}/assignments/performance?ogrenci_id={ogrenci_id}")
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException:
                return []
        else:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute("SELECT durum FROM assignments WHERE ogrenci_id = ? AND synced = 1 AND deleted = 0", (ogrenci_id,))
                assignments = c.fetchall()
                total = len(assignments)
                completed = sum(1 for a in assignments if a[0] == "Kontrol Edildi")
                return {"toplam": total, "tamamlanan": completed}
            

    def get_trial_results(self, ogrenci_id):
        if self.is_online:
            try:
                response = requests.get(f"{API_URL}/trials/results?ogrenci_id={ogrenci_id}")
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException:
                return []
        else:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute("SELECT deneme_adi, tarih FROM trials WHERE ogrenci_id = ? AND synced = 1 AND deleted = 0", (ogrenci_id,))
                return [{"deneme_adi": row[0], "tarih": row[1], "result_available": 0} for row in c.fetchall()]  # Placeholder

    def get_system_updates(self):
        if self.is_online:
            try:
                response = requests.get(f"{API_URL}/system/updates")
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException:
                return {"update_available": False}
        return {"update_available": False}
    
    def get_class_trial_averages(self, sinif):
        if self.is_online:
            try:
                response = requests.get(f"{API_URL}/statistics/trial-averages?sinif={sinif}")
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException:
                return []
        else:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute("SELECT t.deneme_adi, AVG(t.puan) as average FROM trials t JOIN students s ON t.ogrenci_id = s.id WHERE s.sinif = ? AND t.synced = 1 AND t.deleted = 0 GROUP BY t.deneme_adi", (sinif,))
                return [{"deneme_adi": row[0], "ortalama": row[1] or 0} for row in c.fetchall()]

    def get_completion_rates(self, user_id):
        if self.is_online:
            try:
                response = requests.get(f"{API_URL}/statistics/completion-rates?user_id={user_id}")
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException:
                return {"odev": 0, "soru": 0}
        else:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM assignments WHERE ogrenci_id IN (SELECT id FROM students WHERE user_id = ?) AND durum = 'Kontrol Edildi' AND synced = 1 AND deleted = 0", (user_id,))
                odev_tamamlanan = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM assignments WHERE ogrenci_id IN (SELECT id FROM students WHERE user_id = ?) AND synced = 1 AND deleted = 0", (user_id,))
                odev_toplam = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM problem_sessions WHERE ogrenci_id IN (SELECT id FROM students WHERE user_id = ?) AND synced = 1 AND deleted = 0", (user_id,))
                soru_toplam = c.fetchone()[0]
                return {
                    "odev": (odev_tamamlanan / odev_toplam * 100) if odev_toplam > 0 else 0,
                    "soru": (soru_toplam / odev_toplam * 100) if odev_toplam > 0 else 0
                }