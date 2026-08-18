import requests
import datetime
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
        self.layout = BoxLayout(orientation="vertical", padding=10, spacing=10)

        self.cevap_label = Label(text="Merhaba, ben Niko. Bana bir sey sor!", size_hint_y=0.7)
        scroll = ScrollView(size_hint_y=0.7)
        scroll.add_widget(self.cevap_label)
        self.layout.add_widget(scroll)

        self.girdi = TextInput(hint_text="Sorunu yaz...", size_hint_y=0.15, multiline=False)
        self.layout.add_widget(self.girdi)

        gonder_btn = Button(text="Gonder", size_hint_y=0.15)
        gonder_btn.bind(on_press=self.soru_gonder)
        self.layout.add_widget(gonder_btn)

        return self.layout

    def soru_gonder(self, instance):
        soru = self.girdi.text.strip()
        if not soru:
            return
        self.cevap_label.text = "Dusunuyorum..."
        try:
            simdi = datetime.datetime.now()
            tarih_bilgisi = simdi.strf
cd ~/niko_app
cat > main.py << 'EOF'
import requests
import datetime
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
        self.layout = BoxLayout(orientation="vertical", padding=10, spacing=10)

        self.cevap_label = Label(text="Merhaba, ben Niko. Bana bir sey sor!", size_hint_y=0.7)
        scroll = ScrollView(size_hint_y=0.7)
        scroll.add_widget(self.cevap_label)
        self.layout.add_widget(scroll)

        self.girdi = TextInput(hint_text="Sorunu yaz...", size_hint_y=0.15, multiline=False)
        self.layout.add_widget(self.girdi)

        gonder_btn = Button(text="Gonder", size_hint_y=0.15)
        gonder_btn.bind(on_press=self.soru_gonder)
        self.layout.add_widget(gonder_btn)

        return self.layout

    def soru_gonder(self, instance):
        soru = self.girdi.text.strip()
        if not soru:
            return
        self.cevap_label.text = "Dusunuyorum..."
        try:
            simdi = datetime.datetime.now()
            tarih_bilgisi = simdi.strftime("Bugunun tarihi: %d %B %Y, saat %H:%M.")
            tam_soru = tarih_bilgisi + " Kullanicinin sorusu: " + soru
            body = {"contents": [{"parts": [{"text": tam_soru}]}]}
            r = requests.post(URL, json=body, timeout=30).json()
            cevap = r["candidates"][0]["content"]["parts"][0]["text"]
            self.cevap_label.text = cevap
        except Exception as e:
            self.cevap_label.text = "Hata olustu, tekrar dene."
        self.girdi.text = ""

NikoApp().run()
