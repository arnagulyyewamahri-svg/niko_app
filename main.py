import os
import json
import time
import threading
import datetime
import requests
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

API_KEY = "PLACEHOLDER_API_KEY"
URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key=" + API_KEY
KISILIK = "Sen Niko'sun, kullanicinin samimi ve bilgili yapay zeka arkadasisin. Kisa ve anlasilir cevap ver, gereksiz uzatma."
HAFIZA_LIMIT = 8


class NikoApp(App):
    def build(self):
        self.gecmis = self.yukle()
        kok = BoxLayout(orientation="vertical", padding=10, spacing=10)
        self.sohbet = Label(text="", size_hint_y=None, halign="left", valign="top")
        self.sohbet.bind(width=self.metin_genislik, texture_size=self.metin_boyut)
        self.kaydir = ScrollView(size_hint_y=0.75)
        self.kaydir.add_widget(self.sohbet)
        kok.add_widget(self.kaydir)

        self.girdi = TextInput(hint_text="Yaz...", size_hint_y=0.12, multiline=False)
        kok.add_widget(self.girdi)

        btn = Button(text="Gonder", size_hint_y=0.13)
        btn.bind(on_press=self.gonder)
        kok.add_widget(btn)
        self.goster()
        return kok

    def metin_genislik(self, label, width):
        label.text_size = (width, None)

    def metin_boyut(self, label, size):
        label.height = size[1]

    def hafiza_dosyasi(self):
        return os.path.join(self.user_data_dir, "hafiza.json")

    def not_dosyasi(self):
        return os.path.join(self.user_data_dir, "notlar.txt")

    def yukle(self):
        try:
            with open(self.hafiza_dosyasi(), "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def kaydet(self):
        try:
            with open(self.hafiza_dosyasi(), "w", encoding="utf-8") as f:
                json.dump(self.gecmis[-100:], f, ensure_ascii=False)
        except Exception:
            pass

    def goster(self, ek=""):
        metin = "Niko: Merhaba! Bana sor, 'not al: ...', 'notlarim' ya da 'not sil: 1' yaz."
        for g in self.gecmis:
            metin += "\n\nSen: " + g["u"] + "\nNiko: " + g["n"]
        self.sohbet.text = metin + ek
        self.kaydir.scroll_y = 0

    def notlari_oku(self):
        if os.path.exists(self.not_dosyasi()):
            with open(self.not_dosyasi(), "r", encoding="utf-8") as f:
                return [s.strip() for s in f if s.strip()]
        return []

    def notlari_yaz(self, satirlar):
        with open(self.not_dosyasi(), "w", encoding="utf-8") as f:
            for s in satirlar:
                f.write(s + "\n")

    def yerel_cevap(self, soru, cevap):
        self.gecmis.append({"u": soru, "n": cevap})
        self.kaydet()
        self.goster()

    def gonder(self, instance):
        soru = self.girdi.text.strip()
        if not soru:
            return
        self.girdi.text = ""
        kucuk = soru.lower()

        if kucuk.startswith("not al:"):
            metin = soru.split(":", 1)[1].strip()
            satirlar = self.notlari_oku()
            satirlar.append(metin)
            self.notlari_yaz(satirlar)
            self.yerel_cevap(soru, "Notu kaydettim.")
            return

        if kucuk.startswith("not sil:"):
            try:
                no = int(soru.split(":", 1)[1].strip())
                satirlar = self.notlari_oku()
                silinen = satirlar.pop(no - 1)
                self.notlari_yaz(satirlar)
                cevap = "Sildim: " + silinen
            except Exception:
                cevap = "Gecerli bir not numarasi yaz. Ornek: not sil: 2"
            self.yerel_cevap(soru, cevap)
            return

        if kucuk in ("notlarim", "notlarımı göster", "notlarimi goster", "notlarım"):
            satirlar = self.notlari_oku()
            cevap = "\n".join(str(i) + ". " + s for i, s in enumerate(satirlar, 1)) or "Henuz not yok."
            self.yerel_cevap(soru, cevap)
            return

        if kucuk in ("hafizayi temizle", "hafızayı temizle"):
            self.gecmis = []
            self.kaydet()
            self.goster()
            return

        self.goster("\n\nSen: " + soru + "\nNiko: Dusunuyorum...")
        threading.Thread(target=self.sor, args=(soru,), daemon=True).start()

    def sor(self, soru):
        simdi = datetime.datetime.now().strftime("%d.%m.%Y saat %H:%M")
        contents = []
        for g in self.gecmis[-HAFIZA_LIMIT:]:
            contents.append({"role": "user", "parts": [{"text": g["u"]}]})
            contents.append({"role": "model", "parts": [{"text": g["n"]}]})
        contents.append({"role": "user", "parts": [{"text": soru}]})
        body = {
            "system_instruction": {"parts": [{"text": KISILIK + " Bugunun tarihi ve saati: " + simdi}]},
            "contents": contents,
        }
        cevap = None
        hata = ""
        for deneme in range(3):
            try:
                r = requests.post(URL, json=body, timeout=30).json()
                if "candidates" in r:
                    cevap = r["candidates"][0]["content"]["parts"][0]["text"]
                    break
                hata = str(r.get("error", {}).get("message", "bilinmeyen"))[:150]
            except Exception as e:
                hata = "Baglanti hatasi: " + str(e)[:150]
            time.sleep(3)
        Clock.schedule_once(lambda dt: self.bitir(soru, cevap, hata), 0)

    def bitir(self, soru, cevap, hata):
        if cevap is not None:
            self.gecmis.append({"u": soru, "n": cevap})
            self.kaydet()
            self.goster()
        else:
            self.goster("\n\nSen: " + soru + "\nNiko: Hata: " + hata)


NikoApp().run()
