import customtkinter as ctk
import requests
from src.core.utilities import show_error

class OgrenciEditorPopup(ctk.CTkToplevel):
    def __init__(self, parent, ogrenci=None, siniflar=None):
        super().__init__(parent)
        self.parent = parent
        self.ogrenci = ogrenci
        self.api_url = parent.api_url
        self.siniflar = siniflar if siniflar else []

        # Pencere ayarları
        is_editing = self.ogrenci is not None
        self.title("Öğrenci Düzenle" if is_editing else "Yeni Öğrenci Ekle")
        self.geometry("350x500" if not is_editing else "350x300")
        self.transient(parent)
        self.grab_set()

        # Widget'lar
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        ctk.CTkLabel(self.main_frame, text="Adı Soyadı:").pack(anchor="w", padx=20)
        self.ad_soyad_entry = ctk.CTkEntry(self.main_frame)
        self.ad_soyad_entry.pack(pady=(0, 10), padx=20, fill="x")

        ctk.CTkLabel(self.main_frame, text="Sınıf:").pack(anchor="w", padx=20)
        self.sinif_combobox = ctk.CTkComboBox(self.main_frame, values=self.siniflar)
        self.sinif_combobox.pack(pady=(0, 10), padx=20, fill="x")
        self.sinif_combobox.set("") # Başlangıçta boş

        ctk.CTkLabel(self.main_frame, text="Veli İletişim (İsteğe bağlı):").pack(anchor="w", padx=20)
        self.veli_iletisim_entry = ctk.CTkEntry(self.main_frame)
        self.veli_iletisim_entry.pack(pady=(0, 10), padx=20, fill="x")

        # --- YENİ EKLENEN ALANLAR (Sadece yeni öğrenci eklerken görünür) ---
        if not is_editing:
            ctk.CTkLabel(self.main_frame, text="Öğrenci Kullanıcı Adı:").pack(anchor="w", padx=20)
            self.kullanici_adi_entry = ctk.CTkEntry(self.main_frame)
            self.kullanici_adi_entry.pack(pady=(0, 10), padx=20, fill="x")

            ctk.CTkLabel(self.main_frame, text="Öğrenci Şifresi:").pack(anchor="w", padx=20)
            self.sifre_entry = ctk.CTkEntry(self.main_frame, show="*")
            self.sifre_entry.pack(pady=(0, 20), padx=20, fill="x")

        self.kaydet_button = ctk.CTkButton(self.main_frame, text="Kaydet", command=self.kaydet)
        self.kaydet_button.pack(pady=10, padx=20)

        # Mevcut öğrenci verilerini yükle (düzenleme modunda)
        if is_editing:
            self.ad_soyad_entry.insert(0, self.ogrenci.get("ad_soyad", ""))
            self.sinif_combobox.set(self.ogrenci.get("sinif", ""))
            self.veli_iletisim_entry.insert(0, self.ogrenci.get("veli_iletisim", ""))

    def kaydet(self):
        ad = self.ad_soyad_entry.get().strip()
        sinif = self.sinif_combobox.get().strip()
        veli = self.veli_iletisim_entry.get().strip()

        if not ad:
            show_error("Eksik Bilgi", "Öğrenci adı boş bırakılamaz.")
            return

        is_editing = self.ogrenci is not None

        if is_editing:
            # DÜZENLEME MODU (Mevcut mantık korunuyor)
            payload = {
                "ad_soyad": ad,
                "sinif": sinif,
                "veli_iletisim": veli
            }
            url = f"{self.api_url}/ogrenci-duzenle/{self.ogrenci['id']}"
            method = 'put'
        else:
            # YENİ HESAP OLUŞTURMA MODU (Yeni mantık)
            kullanici_adi = self.kullanici_adi_entry.get().strip()
            sifre = self.sifre_entry.get().strip()
            
            if not all([kullanici_adi, sifre]):
                show_error("Eksik Bilgi", "Yeni öğrenci için Kullanıcı Adı ve Şifre alanları boş bırakılamaz.")
                return

            payload = {
                "ad_soyad": ad,
                "sinif": sinif,
                "veli_iletisim": veli,
                "username": kullanici_adi,
                "password": sifre
            }
            url = f"{self.api_url}/ogrenci-hesabi-olustur"
            method = 'post'

        try:
            if method == 'post':
                response = requests.post(url, json=payload)
            else:
                response = requests.put(url, json=payload)

            response.raise_for_status()
            self.parent.ogrenci_listesini_yenile() # Ana pencereyi güncelle
            self.destroy()

        except requests.exceptions.HTTPError as err:
            error_detail = f"Sunucu hatası: {err.response.status_code}"
            try:
                error_detail = err.response.json().get('hata', error_detail)
            except ValueError:
                pass
            show_error("API Hatası", f"İşlem sırasında bir hata oluştu: {error_detail}")
        except requests.exceptions.RequestException as e:
            show_error("Bağlantı Hatası", f"API sunucusuna bağlanılamadı: {e}")