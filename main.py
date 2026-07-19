from kivy.app import App
from kivy.uix.label import Label

class NikoApp(App):
    def build(self):
        return Label(text="Merhaba, Niko calisiyor!")

NikoApp().run()
