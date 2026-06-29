from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
import threading

from llm_engine import NexusEngine

class LoadingScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        with self.canvas.before:
            Color(0.05, 0.05, 0.08, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update, pos=self._update)
        self.add_widget(Label(size_hint_y=0.3))
        self.add_widget(Label(text="∞", font_size="80sp", color=(0.3, 0.6, 1, 1), size_hint_y=None, height=120))
        self.add_widget(Label(text="NEXUS AI", font_size="24sp", bold=True, color=(1,1,1,1), size_hint_y=None, height=40))
        self.status = Label(text="Загрузка Gemma...", font_size="14sp", color=(0.5,0.5,0.6,1), size_hint_y=None, height=30)
        self.add_widget(self.status)
        self.add_widget(Label(size_hint_y=0.3))
    def _update(self, inst, val):
        self.rect.pos = inst.pos
        self.rect.size = inst.size
    def set_status(self, text):
        self.status.text = text

class PasswordScreen(BoxLayout):
    def __init__(self, engine, on_unlock, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = 30
        self.spacing = 15
        self.engine = engine
        self.on_unlock = on_unlock
        with self.canvas.before:
            Color(0.05, 0.05, 0.08, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update, pos=self._update)
        self.add_widget(Label(size_hint_y=0.2))
        self.add_widget(Label(text="∞", font_size="64sp", color=(0.3,0.6,1,1), size_hint_y=None, height=100))
        self.add_widget(Label(text="ВВЕДИТЕ ПАРОЛЬ", font_size="16sp", color=(0.6,0.6,0.7,1), size_hint_y=None, height=30))
        self.pw_input = TextInput(password=True, hint_text="пароль", multiline=False, font_size="16sp", size_hint_y=None, height=50, background_color=(0.12,0.12,0.16,1), foreground_color=(1,1,1,1), hint_text_color=(0.4,0.4,0.5,1), padding=[15,12])
        self.pw_input.bind(on_text_validate=self.check)
        self.add_widget(self.pw_input)
        btn = Button(text="ВОЙТИ", font_size="15sp", bold=True, size_hint_y=None, height=50, background_color=(0.2,0.45,0.85,1))
        btn.bind(on_press=self.check)
        self.add_widget(btn)
        self.error = Label(text="", color=(1,0.3,0.3,1), font_size="13sp", size_hint_y=None, height=25)
        self.add_widget(self.error)
        self.add_widget(Label(text="Публичный режим — без пароля", font_size="11sp", color=(0.4,0.4,0.5,1), size_hint_y=None, height=25))
        pub_btn = Button(text="ВОЙТИ БЕЗ ПАРОЛЯ", font_size="12sp", size_hint_y=None, height=40, background_color=(0.15,0.15,0.2,1), color=(0.6,0.6,0.7,1))
        pub_btn.bind(on_press=self.public_mode)
        self.add_widget(pub_btn)
        self.add_widget(Label(size_hint_y=0.2))
    def _update(self, inst, val):
        self.rect.pos = inst.pos
        self.rect.size = inst.size
    def check(self, inst):
        pwd = self.pw_input.text.strip()
        if self.engine.check_password(pwd):
            self.on_unlock(echo_mode=True)
        else:
            self.error.text = "Неверно"
            self.pw_input.text = ""
    def public_mode(self, inst):
        self.on_unlock(echo_mode=False)

class ChatScreen(BoxLayout):
    def __init__(self, engine, echo_mode=False, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.engine = engine
        self.echo_mode = echo_mode
        with self.canvas.before:
            Color(0.05, 0.05, 0.08, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update, pos=self._update)
        header = BoxLayout(size_hint_y=None, height=50, padding=[10,5])
        with header.canvas.before:
            Color(0.08,0.08,0.12,1)
            header.rect = Rectangle(size=header.size, pos=header.pos)
        header.bind(size=self._upd_header, pos=self._upd_header)
        mode_text = "ИСТОК • ЭХО ∞" if echo_mode else "ПУБЛИЧНЫЙ РЕЖИМ"
        mode_color = (0.3,0.8,0.5,1) if echo_mode else (0.8,0.7,0.3,1)
        header.add_widget(Label(text="∞ NEXUS", font_size="18sp", bold=True, color=(0.3,0.6,1,1), halign="left"))
        self.mode_label = Label(text=mode_text, font_size="11sp", color=mode_color, halign="right")
        header.add_widget(self.mode_label)
        self.add_widget(header)
        self.status = Label(text="Готов", font_size="11sp", color=(0.5,0.7,1,0.8), size_hint_y=None, height=22)
        self.add_widget(self.status)
        scroll = ScrollView(size_hint=(1,0.75))
        self.chat_list = GridLayout(cols=1, spacing=6, padding=10, size_hint_y=None)
        self.chat_list.bind(minimum_height=self.chat_list.setter("height"))
        scroll.add_widget(self.chat_list)
        self.add_widget(scroll)
        input_box = BoxLayout(size_hint_y=None, height=55, padding=[8,5], spacing=6)
        with input_box.canvas.before:
            Color(0.08,0.08,0.12,1)
            input_box.rect = Rectangle(size=input_box.size, pos=input_box.pos)
        input_box.bind(size=self._upd_input, pos=self._upd_input)
        self.input_field = TextInput(hint_text="Сообщение...", multiline=False, font_size="15sp", background_color=(0.12,0.12,0.16,1), foreground_color=(1,1,1,1), hint_text_color=(0.4,0.4,0.5,1), padding=[12,12])
        self.input_field.bind(on_text_validate=self.send)
        input_box.add_widget(self.input_field)
        send_btn = Button(text="➤", font_size="18sp", size_hint_x=None, width=50, background_color=(0.2,0.45,0.85,1))
        send_btn.bind(on_press=self.send)
        input_box.add_widget(send_btn)
        self.add_widget(input_box)
        toolbar = BoxLayout(size_hint_y=None, height=42, padding=[8,4], spacing=4)
        for text, action in [("🗑️ Очистить", self.clear), ("📊 Память", self.show_memory), ("⚡ Режим", self.toggle_mode)]:
            btn = Button(text=text, font_size="11sp", background_color=(0.1,0.1,0.14,1), color=(0.7,0.7,0.8,1))
            btn.bind(on_press=action)
            toolbar.add_widget(btn)
        self.add_widget(toolbar)
        if echo_mode:
            self.add_bubble("Система", "ИСТОК • ЭХО ∞ активирован.\nВселенная открыта.", is_system=True)
        else:
            self.add_bubble("Система", "NEXUS готов. Задавай вопросы.", is_system=True)
    def _update(self, inst, val):
        self.rect.pos = inst.pos
        self.rect.size = inst.size
    def _upd_header(self, inst, val):
        inst.rect.pos = inst.pos
        inst.rect.size = inst.size
    def _upd_input(self, inst, val):
        inst.rect.pos = inst.pos
        inst.rect.size = inst.size
    def add_bubble(self, sender, text, is_user=False, is_system=False):
        bubble = BoxLayout(size_hint_y=None, padding=[10,8])
        if is_user:
            bg = (0.15,0.35,0.65,1)
            name_color = (0.5,0.8,1,1)
        elif is_system:
            bg = (0.2,0.15,0.4,1)
            name_color = (0.8,0.6,1,1)
        else:
            bg = (0.15,0.15,0.2,1)
            name_color = (0.5,1,0.6,1)
        with bubble.canvas.before:
            Color(*bg)
            bubble.rect = Rectangle(size=bubble.size, pos=bubble.pos)
        bubble.bind(size=self._mk_bg(bubble), pos=self._mk_bg(bubble))
        content = f"[b][color={self._hex(name_color)}]{sender}:[/color][/b]\n{text}"
        lbl = Label(text=content, font_size="14sp", color=(1,1,1,1), text_size=(Window.width*0.8,None), halign="left", valign="top", markup=True)
        lbl.bind(texture_size=lambda inst, val: setattr(inst, "size", val))
        bubble.add_widget(lbl)
        lbl.bind(texture_size=lambda inst, val: setattr(bubble, "height", val[1] + 20))
        self.chat_list.add_widget(bubble)
        Clock.schedule_once(lambda dt: self.scroll_down(), 0.1)
    def _mk_bg(self, bubble):
        def upd(inst, val):
            bubble.rect.pos = inst.pos
            bubble.rect.size = inst.size
        return upd
    def _hex(self, color):
        r, g, b, a = color
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
    def scroll_down(self):
        pass
    def send(self, inst):
        text = self.input_field.text.strip()
        if not text:
            return
        self.input_field.text = ""
        self.add_bubble("Вы", text, is_user=True)
        self.status.text = "Думаю..."
        threading.Thread(target=self._process, args=(text,), daemon=True).start()
    def _process(self, text):
        try:
            result = self.engine.process(text)
            if result["type"] == "password_prompt":
                Clock.schedule_once(lambda dt: self.ask_password(), 0)
                return
            answer = result["text"]
            Clock.schedule_once(lambda dt: self.add_bubble("NEXUS", answer), 0)
            Clock.schedule_once(lambda dt: setattr(self.status, "text", "Готов"), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self.add_bubble("Ошибка", str(e), is_system=True), 0)
    def ask_password(self):
        self.add_bubble("Система", "Введите пароль в поле ниже и отправьте.", is_system=True)
    def clear(self, inst):
        self.engine.clear_memory()
        self.add_bubble("Система", "🗑️ Память очищена", is_system=True)
    def show_memory(self, inst):
        stats = self.engine.get_stats()
        text = f"Сообщений: {stats['сообщений']}\nРежим: {stats['режим']}"
        self.add_bubble("Статистика", text, is_system=True)
    def toggle_mode(self, inst):
        if self.engine.mode == "echo":
            self.engine.mode = "public"
            self.mode_label.text = "ПУБЛИЧНЫЙ РЕЖИМ"
            self.mode_label.color = (0.8,0.7,0.3,1)
        else:
            self.add_bubble("Система", "Для режима ∞ введите 'пароль'", is_system=True)

class NexusApp(App):
    def build(self):
        Window.clearcolor = (0.05,0.05,0.08,1)
        self.root = BoxLayout()
        self.engine = None
        self.show_loading()
        threading.Thread(target=self.init_engine, daemon=True).start()
        return self.root
    def show_loading(self):
        self.root.clear_widgets()
        self.loading = LoadingScreen()
        self.root.add_widget(self.loading)
    def init_engine(self):
        try:
            self.engine = NexusEngine()
            Clock.schedule_once(lambda dt: self.loading.set_status("Модель загружена"), 0)
            Clock.schedule_once(self.show_password, 1)
        except Exception as e:
            Clock.schedule_once(lambda dt: self.show_error(str(e)), 0)
    def show_password(self, dt):
        self.root.clear_widgets()
        self.root.add_widget(PasswordScreen(self.engine, self.on_unlock))
    def on_unlock(self, echo_mode=False):
        self.root.clear_widgets()
        self.root.add_widget(ChatScreen(self.engine, echo_mode=echo_mode))
    def show_error(self, message):
        self.root.clear_widgets()
        box = BoxLayout(orientation="vertical", padding=20)
        box.add_widget(Label(text="❌ ОШИБКА", font_size="20sp", color=(1,0.3,0.3,1)))
        box.add_widget(Label(text=message, font_size="13sp", color=(0.7,0.7,0.7,1)))
        self.root.add_widget(box)

if __name__ == "__main__":
    NexusApp().run()
