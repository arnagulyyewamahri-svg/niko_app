import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

API_KEY = "PLACEHOLDER_API_KEY"
URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key=" + API_KEY


class NikoApp(App):
    def build(self):
        kok = BoxLayout(orientation="vertical", padding=10, spacing=10)

        self.sohbet = Label(text="Niko: Merhaba! Bana bir sey sor.", size_hint_y=None,
                            halign="left", valign="top")
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

    def gonder(self, instance):
        soru = self.girdi.text.strip()
        if not soru:
            return
        self.girdi.text = ""
        try:
            body = {"contents": [{"parts": [{"text": soru}]}]}
            r = requests.post(URL, json=body, timeout=30).json()
            cevap = r["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            cevap = "Hata oldu, tekrar dene."
        self.sohbet.text += "\n\nSen: " + soru + "\nNiko: " + cevap
        self.kaydir.scroll_y = 0


NikoApp().run()
