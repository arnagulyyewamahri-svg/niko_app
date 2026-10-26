import os
import json
import time
import threading
import datetime
import requests
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.utils import get_color_from_hex
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition

API_KEY = "PLACEHOLDER_API_KEY"
URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key=" + API_KEY
KISILIK = "Sen Niko'sun, kullanicinin samimi ve bilgili yapay zeka arkadasisin. Kisa ve anlasilir cevap ver, gereksiz uzatma."
HAFIZA_LIMIT = 30

MODLAR = {
    "Sohbet": "Dogal, samimi ve gerektiginde esprili konus.",
    "Ders": "Aciklayici, sabirli ve duzenli ol. Konulari adim adim anlat.",
    "Görev": "Kisa, dogrudan ve cozum odakli ol. Yapilacaklari liste halinde ver.",
    "Gece": "Sakin ve yumusak bir dille konus.",
}
SIRA = list(MODLAR)

ZEMIN = get_color_from_hex("#0d1020")
KART = get_color_from_hex("#181c33")
KART2 = get_color_from_hex("#12162b")
MOR = get_color_from_hex("#5b52e0")
YAZI = get_color_from_hex("#e8e9f5")
SOLUK = get_color_from_hex("#8b8fb0")
BEYAZ = (1, 1, 1, 1)

Window.softinput_mode = "resize"
Window.clearcolor = ZEMIN


def etiket(metin, boyut=15, renk=YAZI, h="left", yuk=None):
    l = Label(text=metin, font_size=sp(boyut), color=renk, halign=h, valign="middle")
    l.bind(size=lambda w, s: setattr(w, "text_size", s))
    if yuk:
        l.size_hint_y = None
        l.height = yuk
    return l


class Kart(BoxLayout):
    def __init__(self, bg=KART, radius=14, **kw):
        super().__init__(**kw)
        with self.canvas.before:
            Color(*bg)
            self._r = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(radius)])
        self.bind(pos=self._guncelle, size=self._guncelle)

    def _guncelle(self, *a):
        self._r.pos = self.pos
        self._r.size = self.size


class Dugme(ButtonBehavior, Kart):
    def __init__(self, yazisi, komut, bg=KART, renk=YAZI, boyut=15, **kw):
        super().__init__(bg=bg, **kw)
        self.komut = komut
        self.add_widget(etiket(yazisi, boyut, renk, "center"))

    def on_release(self):
        self.komut()


class Balon(BoxLayout):
    def __init__(self, metin, benim, **kw):
        super().__init__(size_hint_y=None, height=dp(44), **kw)
        kart = Kart(bg=MOR if benim else KART, padding=dp(10), size_hint=(0.82, None), height=dp(44))
        et = Label(text=metin, font_size=sp(15), color=BEYAZ if benim else YAZI,
                   halign="left", valign="top", size_hint_y=None)
        et.bind(width=lambda w, v: setattr(w, "text_size", (v, None)))

        def boyut(w, s):
            w.height = s[1]
            kart.height = s[1] + dp(20)
            self.height = s[1] + dp(20)
        et.bind(texture_size=boyut)
        kart.add_widget(et)
        bosluk = Widget(size_hint_x=0.18)
        if benim:
            self.add_widget(bosluk)
            self.add_widget(kart)
        else:
            self.add_widget(kart)
            self.add_widget(bosluk)


class NikoApp(App):
    def build(self):
        self.title = "Niko"
        self.gecmis = self.yukle()
        self.mod = "Sohbet"
        self.son_niko = None
        kok = BoxLayout(orientation="vertical")
        self.yonetici = ScreenManager(transition=NoTransition())
        self.yonetici.add_widget(self.ana_ekran())
        self.yonetici.add_widget(self.sohbet_ekrani())
        self.yonetici.add_widget(self.not_ekrani())
        self.yonetici.add_widget(self.hafiza_ekrani())
        self.yonetici.add_widget(self.yakinda_ekrani())
        kok.add_widget(self.yonetici)
        kok.add_widget(self.alt_menu())
        return kok

    # ---------- dosyalar ----------
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

    def notlari_oku(self):
        if os.path.exists(self.not_dosyasi()):
            with open(self.not_dosyasi(), "r", encoding="utf-8") as f:
                return [s.strip() for s in f if s.strip()]
        return []

    def notlari_yaz(self, satirlar):
        with open(self.not_dosyasi(), "w", encoding="utf-8") as f:
            for s in satirlar:
                f.write(s + "\n")

    # ---------- gezinme ----------
    def git(self, ad):
        self.yonetici.current = ad
        if ad == "notlar":
            self.notlari_ciz()
        elif ad == "hafiza":
            self.hafiza_ciz()
        elif ad == "sohbet":
            self.sohbet_goster()
            Clock.schedule_once(lambda dt: self.alta_git(), 0.2)

    def yakinda(self, ad):
        self.yakinda_et.text = ad + "\n\nBu bölüm yakında gelecek."
        self.yonetici.current = "yakinda"

    def sohbete_gir(self):
        self.git("sohbet")
        Clock.schedule_once(lambda dt: setattr(self.girdi, "focus", True), 0.3)

    # ---------- ekranlar ----------
    def ana_ekran(self):
        e = Screen(name="ana")
        k = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(12))
        k.add_widget(etiket("Niko", 26, YAZI, "center", dp(44)))
        sel = Kart(size_hint_y=None, height=dp(64), padding=dp(14))
        sel.add_widget(etiket("Bugün nasıl yardımcı olabilirim?", 16))
        k.add_widget(sel)
        grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(3 * 90 + 2 * 10))
        grid.add_widget(Dugme("Planım", lambda: self.yakinda("Planım")))
        grid.add_widget(Dugme("Notlarım", lambda: self.git("notlar")))
        grid.add_widget(Dugme("Müzik", lambda: self.yakinda("Müzik")))
        grid.add_widget(Dugme("Fotoğraf", lambda: self.yakinda("Fotoğraf")))
        grid.add_widget(Dugme("Alarm", lambda: self.yakinda("Alarm")))
        grid.add_widget(Dugme("Ayarlar", lambda: self.yakinda("Ayarlar")))
        k.add_widget(grid)
        k.add_widget(Widget())
        k.add_widget(Dugme("Bana bir şey söyle...", self.sohbete_gir, renk=SOLUK,
                           size_hint_y=None, height=dp(52), radius=26))
        e.add_widget(k)
        return e

    def sohbet_ekrani(self):
        e = Screen(name="sohbet")
        k = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        ust = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        ust.add_widget(etiket("Niko", 22))
        self.mod_dugme = Dugme(self.mod, self.mod_degistir, bg=MOR, renk=BEYAZ,
                               size_hint_x=None, width=dp(100))
        ust.add_widget(self.mod_dugme)
        k.add_widget(ust)
        self.kutu = GridLayout(cols=1, size_hint_y=None, spacing=dp(8))
        self.kutu.bind(minimum_height=self.kutu.setter("height"))
        self.kaydir = ScrollView()
        self.kaydir.add_widget(self.kutu)
        k.add_widget(self.kaydir)
        alt = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        self.girdi = TextInput(hint_text="Yaz...", multiline=False, background_normal="",
                               background_active="", background_color=KART, foreground_color=YAZI,
                               hint_text_color=SOLUK, cursor_color=YAZI, padding=[dp(12), dp(14)])
        self.girdi.bind(on_text_validate=self.gonder)
        alt.add_widget(self.girdi)
        alt.add_widget(Dugme("Gönder", lambda: self.gonder(), bg=MOR, renk=BEYAZ,
                             size_hint_x=None, width=dp(90)))
        k.add_widget(alt)
        e.add_widget(k)
        return e

    def not_ekrani(self):
        e = Screen(name="notlar")
        k = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(8))
        k.add_widget(etiket("Notlarım", 24, YAZI, "left", dp(44)))
        self.not_kutu = GridLayout(cols=1, size_hint_y=None, spacing=dp(6))
        self.not_kutu.bind(minimum_height=self.not_kutu.setter("height"))
        sv = ScrollView()
        sv.add_widget(self.not_kutu)
        k.add_widget(sv)
        alt = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        self.not_girdi = TextInput(hint_text="Yeni not...", multiline=False, background_normal="",
                                   background_active="", background_color=KART, foreground_color=YAZI,
                                   hint_text_color=SOLUK, cursor_color=YAZI, padding=[dp(12), dp(14)])
        alt.add_widget(self.not_girdi)
        alt.add_widget(Dugme("Ekle", self.not_ekle, bg=MOR, renk=BEYAZ, size_hint_x=None, width=dp(80)))
        k.add_widget(alt)
        e.add_widget(k)
        return e

    def hafiza_ekrani(self):
        e = Screen(name="hafiza")
        k = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        k.add_widget(etiket("Hafıza", 24, YAZI, "left", dp(44)))
        self.hafiza_bilgi = etiket("", 16, SOLUK, "left", dp(36))
        k.add_widget(self.hafiza_bilgi)
        self.hafiza_sonuc = etiket("", 16, YAZI, "left")
        self.hafiza_sonuc.valign = "top"
        k.add_widget(self.hafiza_sonuc)
        k.add_widget(Dugme("İlk sorum", lambda: self.hafiza_islem("ilk"), size_hint_y=None, height=dp(48)))
        k.add_widget(Dugme("Son sorum", lambda: self.hafiza_islem("son"), size_hint_y=None, height=dp(48)))
        k.add_widget(Dugme("Hafızayı temizle", lambda: self.hafiza_islem("temizle"), size_hint_y=None, height=dp(48)))
        e.add_widget(k)
        return e

    def yakinda_ekrani(self):
        e = Screen(name="yakinda")
        self.yakinda_et = etiket("", 20, YAZI, "center")
        e.add_widget(self.yakinda_et)
        return e

    def alt_menu(self):
        bar = Kart(bg=KART2, radius=0, size_hint_y=None, height=dp(56), padding=[dp(6), dp(4)], spacing=dp(6))
        bar.add_widget(Dugme("Ana Sayfa", lambda: self.git("ana"), bg=KART2))
        bar.add_widget(Dugme("Hafıza", lambda: self.git("hafiza"), bg=KART2))
        bar.add_widget(Dugme("Profil", lambda: self.yakinda("Profil"), bg=KART2))
        return bar

    # ---------- notlar ve hafıza ekranı ----------
    def notlari_ciz(self):
        self.not_kutu.clear_widgets()
        satirlar = self.notlari_oku()
        if not satirlar:
            self.not_kutu.add_widget(etiket("Henüz not yok.", 15, SOLUK, "left", dp(40)))
        for i, s in enumerate(satirlar, 1):
            satir = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8))
            satir.add_widget(etiket(str(i) + ". " + s, 15))
            satir.add_widget(Dugme("Sil", lambda n=i: self.not_sil(n), size_hint_x=None, width=dp(70)))
            self.not_kutu.add_widget(satir)

    def not_ekle(self):
        metin = self.not_girdi.text.strip()
        if metin:
            satirlar = self.notlari_oku()
            satirlar.append(metin)
            self.notlari_yaz(satirlar)
            self.not_girdi.text = ""
            self.notlari_ciz()

    def not_sil(self, no):
        satirlar = self.notlari_oku()
        if 1 <= no <= len(satirlar):
            satirlar.pop(no - 1)
            self.notlari_yaz(satirlar)
        self.notlari_ciz()

    def hafiza_ciz(self):
        self.hafiza_bilgi.text = "Kayıtlı konuşma: " + str(len(self.gecmis))
        self.hafiza_sonuc.text = ""

    def hafiza_islem(self, ne):
        if ne == "temizle":
            self.gecmis = []
            self.kaydet()
            self.hafiza_ciz()
            self.hafiza_sonuc.text = "Hafıza temizlendi."
            return
        if not self.gecmis:
            self.hafiza_sonuc.text = "Henüz konuşma yok."
        elif ne == "ilk":
            self.hafiza_sonuc.text = "İlk sorun:\n" + self.gecmis[0]["u"]
        else:
            self.hafiza_sonuc.text = "Son sorun:\n" + self.gecmis[-1]["u"]

    # ---------- sohbet ----------
    def mod_degistir(self):
        self.mod = SIRA[(SIRA.index(self.mod) + 1) % len(SIRA)]
        for c in self.mod_dugme.children:
            c.text = self.mod

    def sohbet_goster(self, bekleyen=None, hata=None):
        self.kutu.clear_widgets()
        self.kutu.add_widget(Balon("Merhaba! Bana sor, 'not al: ...', 'notlarim', 'not sil: 1', 'ilk sorum' ya da 'son sorum' yaz.", False))
        self.son_niko = None
        for g in self.gecmis:
            self.kutu.add_widget(Balon(g["u"], True))
            self.son_niko = Balon(g["n"], False)
            self.kutu.add_widget(self.son_niko)
        if bekleyen:
            self.kutu.add_widget(Balon(bekleyen, True))
            self.son_niko = Balon(hata if hata else "Düşünüyorum...", False)
            self.kutu.add_widget(self.son_niko)

    def alta_git(self):
        self.kaydir.scroll_y = 0

    def cevap_basina_git(self):
        w = self.son_niko
        if w is None:
            return
        ch = self.kutu.height
        vh = self.kaydir.height
        if ch <= vh:
            self.kaydir.scroll_y = 1
            return
        ust = (w.y + w.height) - self.kutu.y
        self.kaydir.scroll_y = max(0, min(1, (ust - vh) / float(ch - vh)))

    def yerel_cevap(self, soru, cevap):
        self.gecmis.append({"u": soru, "n": cevap})
        self.kaydet()
        self.sohbet_goster()
        Clock.schedule_once(lambda dt: self.alta_git(), 0.2)

    def gonder(self, *args):
        soru = self.girdi.text.strip()
        self.girdi.focus = False
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
                cevap = "Geçerli bir not numarası yaz. Örnek: not sil: 2"
            self.yerel_cevap(soru, cevap)
            return

        if kucuk in ("notlarim", "notlarımı göster", "notlarimi goster", "notlarım"):
            satirlar = self.notlari_oku()
            cevap = "\n".join(str(i) + ". " + s for i, s in enumerate(satirlar, 1)) or "Henüz not yok."
            self.yerel_cevap(soru, cevap)
            return

        if kucuk == "ilk sorum":
            cevap = ("İlk sorun: " + self.gecmis[0]["u"]) if self.gecmis else "Henüz başka soru sormadın."
            self.yerel_cevap(soru, cevap)
            return

        if kucuk == "son sorum":
            cevap = ("Son sorun: " + self.gecmis[-1]["u"]) if self.gecmis else "Henüz başka soru sormadın."
            self.yerel_cevap(soru, cevap)
            return

        if kucuk in ("hafizayi temizle", "hafızayı temizle"):
            self.gecmis = []
            self.kaydet()
            self.sohbet_goster()
            return

        self.sohbet_goster(bekleyen=soru)
        Clock.schedule_once(lambda dt: self.alta_git(), 0.2)
        threading.Thread(target=self.sor, args=(soru,), daemon=True).start()

    def sor(self, soru):
        simdi = datetime.datetime.now().strftime("%d.%m.%Y saat %H:%M")
        contents = []
        for g in self.gecmis[-HAFIZA_LIMIT:]:
            contents.append({"role": "user", "parts": [{"text": g["u"]}]})
            contents.append({"role": "model", "parts": [{"text": g["n"]}]})
        contents.append({"role": "user", "parts": [{"text": soru}]})
        talimat = KISILIK + " " + MODLAR[self.mod] + " Bugunun tarihi ve saati: " + simdi
        body = {"system_instruction": {"parts": [{"text": talimat}]}, "contents": contents}
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
                hata = "Bağlantı hatası: " + str(e)[:150]
            time.sleep(3)
        Clock.schedule_once(lambda dt: self.bitir(soru, cevap, hata), 0)

    def bitir(self, soru, cevap, hata):
        if cevap is not None:
            self.gecmis.append({"u": soru, "n": cevap})
            self.kaydet()
            self.sohbet_goster()
            Clock.schedule_once(lambda dt: self.cevap_basina_git(), 0.3)
        else:
            self.sohbet_goster(bekleyen=soru, hata="Hata: " + hata)
            Clock.schedule_once(lambda dt: self.alta_git(), 0.2)


NikoApp().run()
