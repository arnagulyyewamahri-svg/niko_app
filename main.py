import os
import datetime
import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

API_KEY = "PLACEHOLDER_API_KEY"
URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key=" + API_KEY
KISILIK = "Sen Niko'sun, kullanicinin samimi ve bilgili yapay zeka arkadasisin. Kisa ve anlasilir cevap ver, gereksiz uzatma."


class NikoApp(App):
    def build(self):
        kok = BoxLayout(orientation="vertical", padding=10, spacing=10)
        self.sohbet = Label(text="Niko: Merhaba! Bana sor, ya da 'not al: ...' yaz.",
                            size_hint_y=None, halign="left", valign="top")
        self.sohbet.bind(width=self.metin_genislik, texture_size=self.metin_boyut)
        self.kaydir = ScrollView(size_hint_y=0.75)
        self.kaydir.add_widget(self.sohbet)
        kok.add_widget(self.kaydir)

        self.girdi = TextInput(hint_text="Yaz...", size_hint_y=0.12, multiline=False)
        kok.add_widget(self.girdi)

        btn = Button(text="Gonder", size_hint_y=0.13)
        btn.bind(on_press=self.gonder)
        kok.add_widget(btn)
        return kok

    def metin_genislik(self, label, width):
        label.text_size = (width, None)

    def metin_boyut(self, label, size):
        label.height = size[1]

    def not_dosyasi(self):
        return os.path.join(self.user_data_dir, "notlar.txt")

    def ekle(self, soru, cevap):
        self.sohbet.text += "\n\nSen: " + soru + "\nNiko: " + cevap
        self.kaydir.scroll_y = 0

    def gonder(self, instance):
        soru = self.girdi.text.strip()
        if not soru:
            return
        self.girdi.text = ""
        kucuk = soru.lower()

        if kucuk.startswith("not al:"):
            metin = soru.split(":", 1)[1].strip()
            with open(self.not_dosyasi(), "a", encoding="utf-8") as f:
                f.write(metin + "\n")
            self.ekle(soru, "Notu kaydettim.")
            return

        if kucuk in ("notlarim", "notlarimi goster", "notlarım"):
            if os.path.exists(self.not_dosyasi()):
                with open(self.not_dosyasi(), "r", encoding="utf-8") as f:
                    satirlar = [s.strip() for s in f if s.strip()]
                cevap = "\n".join(str(i) + ". " + s for i, s in enumerate(satirlar, 1)) or "Henuz not yok."
            else:
                cevap = "Henuz not yok."
            self.ekle(soru, cevap)
            return

        try:
            simdi = datetime.datetime.now().strftime("%d.%m.%Y saat %H:%M")
            body = {
                "system_instruction": {"parts": [{"text": KISILIK + " Bugunun tarihi ve saati: " + simdi}]},
                "contents": [{"parts": [{"text": soru}]}],
            }
            r = requests.post(URL, json=body, timeout=30).json()
            if "candidates" in r:
                cevap = r["candidates"][0]["content"]["parts"][0]["text"]
            else:
                cevap = "Hata: " + str(r.get("error", {}).get("message", "bilinmeyen"))[:150]
        except Exception as e:
            cevap = "Baglanti hatasi: " + str(e)[:150]
        self.ekle(soru, cevap)


NikoApp().run()
