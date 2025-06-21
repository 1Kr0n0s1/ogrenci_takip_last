import customtkinter as ctk

class YardimWindow(ctk.CTkToplevel): # Yardım penceresi - 5sn'de bir değişiyor
    def __init__(self, master):
        super().__init__(master)
        self.title("Yardım")
        self.geometry("400x300")
        self.transient(master)
        self.grab_set()

        ctk.CTkLabel(self, text="Yardım ve Destek", font=("Arial", 16, "bold")).pack(pady=10, padx=10)
        ctk.CTkLabel(self, text="Bu uygulama ile ödev, deneme ve performans takibi yapabilirsiniz.").pack(pady=5, padx=10)
        ctk.CTkLabel(self, text="Ana Özellikler:").pack(pady=5, padx=10)
        ctk.CTkLabel(self, text="- Sol menüden öğrenci seçin.").pack(pady=2, padx=20)
        ctk.CTkLabel(self, text="- Ödevler sekmesinde ödev ekleyip yönetin.").pack(pady=2, padx=20)
        ctk.CTkLabel(self, text="- Tur Rehberi ile uygulamayı keşfedin.").pack(pady=2, padx=20)

        ctk.CTkButton(self, text="Kapat", command=self.destroy).pack(pady=10, padx=10)