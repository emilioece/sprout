import os
import threading
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

import api
from theme import theme
from components.utils import EMOJI_FONT, default_picture_dir
from components.widgets import RoundedBox, PillButton, EmojiLabel, IconButtonRow, SelectableCard, IconRow

QUICK_SPECIES = [
    ("Fern", "\U0001F33F", "easy · indirect"),
    ("Moss", "\U0001F343", "easy · low light"),
    ("Cactus", "\U0001F331", "expert · indirect"),
    ("Bamboo", "\U0001F33E", "easy · low light"),
]


class WaterToast(RoundedBox):
    def __init__(self, message="\U0001F4A7 Watered!", **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint=(None, None),
            size=(dp(220), dp(52)),
            padding=[dp(18), dp(12)],
            bg_color=theme.dark_green,
            border_color=theme.dark_green,
            radius=dp(26),
            **kwargs
        )
        self.opacity = 0
        self.add_widget(IconRow(
            icon="\U0001F4A7",
            text=message,
            text_color=[1, 1, 1, 1],
            icon_size="16sp",
            text_size="13sp",
            halign="center",
        ))

        Window.add_widget(self)
        self.center_x = Window.width / 2
        target_y = Window.height - dp(90)
        self.y = target_y - dp(20)

        anim = (
                Animation(opacity=1, y=target_y, duration=0.25, t="out_cubic")
                + Animation(duration=1.1)
                + Animation(opacity=0, y=target_y + dp(15), duration=0.35, t="in_cubic")
        )
        anim.bind(on_complete=lambda *a: self._remove())
        anim.start(self)

    def _remove(self, *args):
        if self.parent:
            Window.remove_widget(self)


class ErrorModal(ModalView):
    def __init__(self, message, **kwargs):
        width = min(dp(340), Window.width * 0.9)
        height = min(dp(180), Window.height * 0.85)
        super().__init__(size_hint=(None, None), size=(width, height), **kwargs)
        box = RoundedBox(orientation="vertical", padding=dp(16), spacing=dp(10), bg_color=theme.surface, border_color=theme.border, radius=dp(18))
        box.add_widget(Label(text=message, color=theme.text, font_size="12sp"))
        ok_btn = PillButton(text="OK", bg_color=theme.dark_green, radius=dp(14), size_hint_y=None, height=dp(40))
        ok_btn.bind(on_release=lambda *_: self.dismiss())
        box.add_widget(ok_btn)
        self.add_widget(box)


class AuthModal(ModalView):
    def __init__(self, on_login_success, **kwargs):
        width = min(dp(400), Window.width * 0.9)
        height = min(dp(450), Window.height * 0.8)
        super().__init__(size_hint=(None, None), size=(width, height), auto_dismiss=False, **kwargs)
        self.on_login_success = on_login_success
        self.is_login_mode = True
        self._build_ui()

    def _labeled_input(self, label_text, is_password=False):
        box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(54), spacing=dp(4))
        lbl = Label(text=label_text, font_size="11sp", bold=True, color=theme.muted2, size_hint_y=None, height=dp(16), halign="left")
        lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        box.add_widget(lbl)

        ti = TextInput(
            multiline=False, password=is_password, background_normal="", background_active="",
            background_color=theme.input_bg, foreground_color=theme.text,
            cursor_color=theme.dark_green, padding=(dp(14), dp(10)), size_hint_y=None, height=dp(40)
        )
        box.add_widget(ti)
        return box, ti

    def _build_ui(self):
        self.clear_widgets()
        root = RoundedBox(orientation="vertical", bg_color=theme.surface, border_color=theme.border, radius=dp(20), padding=dp(24), spacing=dp(16))

        title = "Welcome Back" if self.is_login_mode else "Create Account"
        title_lbl = Label(text=title, bold=True, font_size="20sp", color=theme.text, size_hint_y=None, height=dp(40))
        root.add_widget(title_lbl)

        email_box, self.email_input = self._labeled_input("Email")
        root.add_widget(email_box)

        pass_box, self.password_input = self._labeled_input("Password", is_password=True)
        root.add_widget(pass_box)

        action_text = "Log In" if self.is_login_mode else "Sign Up"
        self.submit_btn = PillButton(text=action_text, bg_color=theme.dark_green, radius=dp(14), size_hint_y=None, height=dp(50))
        self.submit_btn.bind(on_release=lambda *_: self._authenticate())
        root.add_widget(self.submit_btn)

        toggle_text = "Need an account? Sign up" if self.is_login_mode else "Already have an account? Log in"
        toggle_btn = Button(text=toggle_text, color=theme.dark_green, background_color=[0, 0, 0, 0], font_size="12sp", size_hint_y=None, height=dp(30))
        toggle_btn.bind(on_release=self._toggle_mode)
        root.add_widget(toggle_btn)

        self.add_widget(root)

    def _toggle_mode(self, *args):
        self.is_login_mode = not self.is_login_mode
        self._build_ui()

    def _authenticate(self):
        email = self.email_input.text.strip()
        password = self.password_input.text.strip()
        if not email or not password:
            return

        self.submit_btn.text = "Processing..."
        self.submit_btn.disabled = True

        def worker():
            try:
                if self.is_login_mode:
                    user_data = api.login(email, password)
                else:
                    user_data = api.register(email, password)
                Clock.schedule_once(lambda dt: self._on_success(user_data))
            except Exception as exc:
                Clock.schedule_once(lambda dt, err=exc: self._on_error(err))

        threading.Thread(target=worker, daemon=True).start()

    def _on_success(self, user_data):
        self.dismiss()
        if self.on_login_success:
            self.on_login_success(user_data)

    def _on_error(self, exc):
        self.submit_btn.text = "Log In" if self.is_login_mode else "Sign Up"
        self.submit_btn.disabled = False
        ErrorModal("Authentication failed. Please try again.").open()


class DeleteConfirmModal(ModalView):
    def __init__(self, plant_id, plant_name, on_deleted, **kwargs):
        width = min(dp(360), Window.width * 0.9)
        height = min(dp(280), Window.height * 0.85)
        super().__init__(size_hint=(None, None), size=(width, height), auto_dismiss=False, **kwargs)
        self.plant_id = plant_id
        self.on_deleted = on_deleted

        root = RoundedBox(orientation="vertical", padding=dp(20), spacing=dp(12), bg_color=theme.surface, border_color=theme.border, radius=dp(20))
        root.add_widget(EmojiLabel(text="\U0001F5D1", font_size="20sp", size_hint=(None, None), size=(dp(28), dp(28)), pos_hint={"center_x": 0.5}))
        root.add_widget(Label(text=f"Remove {plant_name}?", bold=True, font_size="16sp", color=theme.text, size_hint_y=None, height=dp(28)))
        root.add_widget(Label(text="Are you sure you want to delete this plant?", font_size="11sp", color=theme.muted2, size_hint_y=None, height=dp(50)))

        btn_row = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(46))
        cancel_btn = PillButton(text="Cancel", bg_color=theme.input_bg, fg_color=theme.muted2, radius=dp(16))
        cancel_btn.bind(on_release=lambda *_: self.dismiss())
        self.delete_btn = PillButton(text="Delete Plant", bg_color=theme.red, radius=dp(16))
        self.delete_btn.bind(on_release=lambda *_: self._confirm())
        btn_row.add_widget(cancel_btn)
        btn_row.add_widget(self.delete_btn)
        root.add_widget(btn_row)
        self.add_widget(root)

    def _confirm(self):
        self.delete_btn.text = "Deleting..."
        self.delete_btn.disabled = True

        def worker():
            try:
                api.delete_plant(self.plant_id)
                Clock.schedule_once(lambda dt: self._on_success())
            except Exception as exc:
                Clock.schedule_once(lambda dt, err=exc: self._on_error(err))

        threading.Thread(target=worker, daemon=True).start()

    def _on_success(self):
        self.dismiss()
        if self.on_deleted:
            self.on_deleted(self.plant_id)

    def _on_error(self, exc):
        self.delete_btn.text = "Delete Plant"
        self.delete_btn.disabled = False
        ErrorModal("Could not delete plant.").open()


class PhotoPickerModal(ModalView):
    """
    the popup for choosing a plant photo

    it opens on a friendly upload panel instead of throwing the user
    straight into a file browser, because nobody wants to see their
    whole c drive. the browser only shows up if they ask for it

    on_picked(path) fires once, with the path of the file they chose
    """

    def __init__(self, on_picked, **kwargs):
        width = min(dp(460), Window.width * 0.92)
        height = min(dp(420), Window.height * 0.85)
        super().__init__(size_hint=(None, None), size=(width, height), **kwargs)
        self.on_picked = on_picked
        self._poll_event = None   # the repeating clock that checks for the photo
        self._qr_path = None      # temp png of the qr code, cleaned up on close
        self._photo_handled = False   # stops duplicate downloads from overlapping polls
        self.bind(on_dismiss=lambda *_: self._stop_polling())
        self._build_landing()

    def _shell(self):
        """
        wipes whatever is on screen and gives back a fresh rounded box
        we use this to swap between the upload panel and the file browser
        without building a second popup
        """
        box = RoundedBox(
            orientation="vertical", padding=dp(18), spacing=dp(12),
            bg_color=theme.surface, border_color=theme.border, radius=dp(18),
        )
        self.clear_widgets()
        self.add_widget(box)
        return box

    def _build_landing(self):
        """the first screen, with the upload box and the two buttons"""
        box = self._shell()

        # title row with an x to close
        head = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(8))
        title = Label(text="Add a photo", bold=True, font_size="17sp",
                      color=theme.text, halign="left", valign="middle")
        title.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        head.add_widget(title)
        close_btn = PillButton(text="X", size_hint=(None, None), size=(dp(30), dp(30)),
                               bg_color=theme.chip, fg_color=theme.muted2, radius=dp(15))
        close_btn.bind(on_release=lambda *_: self.dismiss())
        head.add_widget(close_btn)
        box.add_widget(head)

        # the big upload looking box in the middle
        drop = RoundedBox(
            orientation="vertical", spacing=dp(6), padding=dp(16),
            bg_color=theme.accent_soft, border_color=theme.dark_green, radius=dp(16),
        )
        drop.add_widget(EmojiLabel(text="\U0001F5BC\uFE0F", font_size="34sp",
                                   size_hint_y=None, height=dp(44)))
        hint = Label(text="Choose a photo of your plant", font_size="13sp",
                     color=theme.muted2, size_hint_y=None, height=dp(20))
        drop.add_widget(hint)
        sub = Label(text="JPG, PNG or WEBP  \u00b7  up to 5 MB", font_size="10sp",
                    color=theme.muted, size_hint_y=None, height=dp(16))
        drop.add_widget(sub)
        box.add_widget(drop)

        browse_btn = PillButton(text="Browse my computer", bg_color=theme.dark_green,
                                radius=dp(14), size_hint_y=None, height=dp(46))
        browse_btn.bind(on_release=lambda *_: self._build_browser())
        box.add_widget(browse_btn)

        # placeholder for now. the qr code phone upload plugs in here later
        self.phone_btn = PillButton(
            text="\U0001F4F1  Upload from my phone", bg_color=theme.chip,
            fg_color=theme.dark_green, radius=dp(14),
            size_hint_y=None, height=dp(46), font_name=EMOJI_FONT,
        )
        self.phone_btn.bind(on_release=lambda *_: self._build_phone())
        box.add_widget(self.phone_btn)

    def _stop_polling(self):
        """stops the status checks and deletes the temp qr image"""
        if self._poll_event:
            self._poll_event.cancel()
            self._poll_event = None
        if self._qr_path and os.path.exists(self._qr_path):
            os.remove(self._qr_path)
            self._qr_path = None

    def _build_phone(self):
        """
        the qr screen

        asks the backend for a token, draws the url as a qr code, then checks
        once a second to see if the phone has sent anything yet
        """
        import tempfile

        box = self._shell()

        head = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(8))
        title = Label(text="Scan with your phone", bold=True, font_size="16sp",
                      color=theme.text, halign="left", valign="middle")
        title.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        head.add_widget(title)
        close_btn = PillButton(text="X", size_hint=(None, None), size=(dp(28), dp(28)),
                               bg_color=theme.chip, fg_color=theme.muted2, radius=dp(14))
        close_btn.bind(on_release=lambda *_: self.dismiss())
        head.add_widget(close_btn)
        box.add_widget(head)

        self.qr_image = Image(size_hint_y=None, height=dp(210))
        box.add_widget(self.qr_image)

        self.qr_status = Label(text="Getting your code ready...", font_size="12sp",
                               color=theme.muted2, size_hint_y=None, height=dp(34),
                               halign="center", valign="middle")
        self.qr_status.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        box.add_widget(self.qr_status)

        back_btn = PillButton(text="Back", bg_color=theme.chip, fg_color=theme.muted2,
                              radius=dp(14), size_hint_y=None, height=dp(42))
        back_btn.bind(on_release=lambda *_: (self._stop_polling(), self._build_landing()))
        box.add_widget(back_btn)

        # getting the token is a network call, so it goes on a thread to keep
        # the window from freezing while it waits
        def worker():
            try:
                token, url = api.start_phone_upload()
                path = os.path.join(tempfile.gettempdir(), f"sprout_qr_{token}.png")
                api.make_qr_png(url, path)
                Clock.schedule_once(
                    lambda dt, t=token, u=url, p=path: self._qr_ready(t, u, p)
                )
            except Exception:
                Clock.schedule_once(lambda dt: self._qr_failed())

        threading.Thread(target=worker, daemon=True).start()

    def _qr_ready(self, token, url, path):
        """qr code is drawn, now start watching for the photo to land"""
        self._qr_path = path
        self.qr_image.source = path
        self.qr_image.reload()
        self.qr_status.text = ("Point your camera at the code\n"
                               "Your phone must be on the same wifi")
        self._poll_event = Clock.schedule_interval(
            lambda dt, t=token: self._check_phone(t), 1.0
        )

    def _qr_failed(self):
        self.qr_status.text = ("Could not start the phone upload.\n"
                               "Is the backend running?")

    def _check_phone(self, token):
        """
        runs once a second while the qr code is showing

        the flag matters. a phone photo takes longer than a second to come
        down, so the next tick fires while the first download is still going
        and both would hand back a photo. that produced a stack of identical
        dialogs that each had to be dismissed
        """
        if self._photo_handled:
            return

        def worker():
            try:
                if self._photo_handled:
                    return
                if api.phone_upload_ready(token):
                    # claim it before the slow part starts, so a tick landing
                    # mid download turns back straight away
                    self._photo_handled = True
                    path = api.download_phone_photo(token)
                    Clock.schedule_once(lambda dt, p=path: self._phone_photo_arrived(p))
            except Exception:
                self._photo_handled = False   # let it try again next tick

        threading.Thread(target=worker, daemon=True).start()

    def _phone_photo_arrived(self, path):
        """
        photo is downloaded and sitting in a temp file

        show it on the qr screen for a moment first, otherwise the modal just
        vanishes and it is not obvious anything happened. after that it is
        handed back as a plain file path, exactly like one picked off the hard
        drive, so nothing downstream needs to know it came from a phone
        """
        self._stop_polling()

        # swap the qr code out for the photo that just arrived
        self.qr_image.source = path
        self.qr_image.reload()
        self.qr_status.text = "Photo received"
        self.qr_status.color = theme.dark_green
        self.qr_status.bold = True

        def finish(dt):
            self.dismiss()
            if self.on_picked:
                self.on_picked(path)

        # long enough to register as confirmation, short enough not to annoy
        Clock.schedule_once(finish, 1.2)

    def _build_browser(self):
        """the second screen, an actual file browser starting in pictures"""
        from kivy.uix.filechooser import FileChooserIconView

        box = self._shell()
        chooser = FileChooserIconView(
            filters=["*.jpg", "*.jpeg", "*.png", "*.webp"],
            path=default_picture_dir(),
        )
        box.add_widget(chooser)

        row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))
        back_btn = PillButton(text="Back", bg_color=theme.chip, fg_color=theme.muted2,
                              radius=dp(14))
        back_btn.bind(on_release=lambda *_: self._build_landing())
        choose_btn = PillButton(text="Choose", bg_color=theme.dark_green, radius=dp(14))

        def _choose(*_):
            # selection is a list, and it is empty if they clicked choose
            # without actually picking anything
            if chooser.selection:
                path = chooser.selection[0]
                self.dismiss()
                if self.on_picked:
                    self.on_picked(path)

        choose_btn.bind(on_release=_choose)
        row.add_widget(back_btn)
        row.add_widget(choose_btn)
        box.add_widget(row)


class AddPlantModal(ModalView):
    def __init__(self, on_saved, **kwargs):
        width = min(dp(480), Window.width * 0.92)
        height = min(dp(620), Window.height * 0.9)
        super().__init__(size_hint=(None, None), size=(width, height), auto_dismiss=False, **kwargs)
        self.on_saved = on_saved
        self.species = ""
        self.nickname_input = None
        self.location_input = None
        self.photo_path = None
        self.care_guide = None
        self.light_requirement = None
        self.step = 1
        self._build_step_1()

    def _header(self, title, subtitle, show_back=False):
        header = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8), padding=(dp(4), 0))
        if show_back:
            back_btn = PillButton(text="<", size_hint=(None, None), size=(dp(32), dp(32)), bg_color=theme.chip, fg_color=theme.muted2, radius=dp(16))
            back_btn.bind(on_release=lambda *_: self._build_step_1())
            header.add_widget(back_btn)

        title_box = BoxLayout(orientation="vertical")
        title_lbl = Label(text=title, bold=True, font_size="18sp", color=theme.text, halign="left", valign="bottom")
        title_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        sub_lbl = Label(text=subtitle, font_size="11sp", color=theme.muted, halign="left", valign="top")
        sub_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        title_box.add_widget(title_lbl)
        title_box.add_widget(sub_lbl)
        header.add_widget(title_box)

        close_btn = PillButton(text="X", size_hint=(None, None), size=(dp(32), dp(32)), bg_color=theme.chip, fg_color=theme.muted2, radius=dp(16))
        close_btn.bind(on_release=lambda *_: self.dismiss())
        header.add_widget(close_btn)
        return header

    def _labeled_input(self, label_text, placeholder="", multiline=False):
        box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(74) if multiline else dp(54), spacing=dp(4))
        if label_text:
            lbl = Label(text=label_text, font_size="11sp", bold=True, color=theme.muted2, size_hint_y=None, height=dp(16), halign="left")
            lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
            box.add_widget(lbl)

        ti = TextInput(
            hint_text=placeholder, multiline=multiline, background_normal="", background_active="",
            background_disabled_normal="", background_color=theme.input_bg,
            foreground_color=theme.text, hint_text_color=theme.hint,
            cursor_color=theme.dark_green, padding=(dp(14), dp(10)),
            size_hint_y=None, height=dp(40) if not multiline else dp(50)
        )
        box.add_widget(ti)
        return box, ti


    def _identify_from_photo(self):
        """
        the Photo tab. opens the picker, sends whatever comes back to the
        identify endpoint, and fills in the species from the answer

        the same photo is kept as the plant's photo afterwards, so one picture
        does both jobs and the user is not asked for it twice
        """
        PhotoPickerModal(on_picked=self._on_identify_photo).open()

    def _on_identify_photo(self, path):
        """runs once a photo has been chosen or sent over from a phone"""
        busy = ModalView(size_hint=(None, None), size=(dp(300), dp(170)))
        busy_box = RoundedBox(orientation="vertical", padding=dp(20), spacing=dp(10),
                              bg_color=theme.surface, border_color=theme.border,
                              radius=dp(16))
        busy_msg = Label(text="Identifying your plant...", font_size="14sp",
                         bold=True, color=theme.text, halign="center",
                         valign="middle")
        busy_msg.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        busy_box.add_widget(busy_msg)

        busy_btn = PillButton(text="Cancel", bg_color=theme.chip,
                              fg_color=theme.muted2, size_hint_y=None,
                              height=dp(40))
        busy_btn.bind(on_release=lambda *_: busy.dismiss())
        busy_box.add_widget(busy_btn)
        busy.add_widget(busy_box)
        busy.open()

        def on_identified(data):
            busy.dismiss()

            if not data.get("is_plant", True):
                ErrorModal("That does not look like a plant. Try another photo.").open()
                return

            self.species = data.get("species", "")
            # keep the photo, it is already a picture of this plant
            self.photo_path = path
            if data.get("light_requirement"):
                self.light_requirement = data["light_requirement"]

            # now that we know the species, ask for a real care schedule so the
            # form stops showing the same seven days for every plant
            self._fetch_care_guide()
            self._build_step_1()

        def on_failed(message):
            busy.dismiss()
            if "503" in message:
                ErrorModal("AI is not set up. A GEMINI_API_KEY is needed "
                           "in the .env file.").open()
            elif "400" in message:
                ErrorModal("That file type is not supported. "
                           "Use a JPEG, PNG or WebP image.").open()
            else:
                ErrorModal("Could not identify the plant.").open()

        def worker():
            try:
                data = api.identify_plant(path)
                Clock.schedule_once(lambda dt, d=data: on_identified(d))
            except Exception as exc:
                Clock.schedule_once(lambda dt, e=str(exc): on_failed(e))

        threading.Thread(target=worker, daemon=True).start()

    def _describe_not_available(self):
        """
        the Describe tab has no endpoint behind it yet. saying so is better
        than a button that silently does nothing
        """
        ErrorModal("Coming soon! Working on it.").open()


    def _fetch_care_guide(self):
        """
        asks gemini for a real care schedule for the identified species

        runs in the background because the form should still be usable while
        it loads. if it fails the plant can still be saved, it just falls back
        to the default interval the server uses
        """
        species = self.species
        if not species:
            return

        def worker():
            try:
                guide = api.get_care_preview(species, species)
                Clock.schedule_once(lambda dt, g=guide: self._on_care_guide(g))
            except Exception:
                pass          # not fatal, the plant saves either way

        threading.Thread(target=worker, daemon=True).start()

    def _on_care_guide(self, guide):
        """the guide has arrived, redraw so the real numbers replace Loading"""
        self.care_guide = guide
        if self.step == 2:
            self._build_step_2()


    def _build_step_1(self):
        self.step = 1
        self.clear_widgets()

        root = RoundedBox(orientation="vertical", bg_color=theme.surface, border_color=theme.border, radius=dp(20), padding=dp(20))
        root.add_widget(self._header("Identify your plant", "Step 1 of 2"))

        scroll = ScrollView(do_scroll_x=False)
        body = BoxLayout(orientation="vertical", spacing=dp(12), size_hint_y=None, padding=[0, dp(10), 0, dp(10)])
        body.bind(minimum_height=body.setter("height"))

        tab_bar = RoundedBox(orientation="horizontal", size_hint_y=None, height=dp(42), padding=dp(3), spacing=dp(2), bg_color=theme.surface_alt, border_color=theme.surface_alt, radius=dp(12))
        search_tab = IconButtonRow(icon="\U0001F50D", label_text="Search", bg_color=theme.dark_green, fg_color=[1, 1, 1, 1], radius=dp(10))
        photo_tab = IconButtonRow(icon="\U0001F4F7", label_text="Photo", bg_color=[0, 0, 0, 0], fg_color=theme.muted2, radius=dp(10))
        describe_tab = IconButtonRow(icon="\U0001F4AC", label_text="Describe", bg_color=[0, 0, 0, 0], fg_color=theme.muted2, radius=dp(10))

        # these three were built but never wired to anything, so they looked
        # clickable and did nothing. search is already the screen you are on
        photo_tab.bind(on_release=lambda *_: self._identify_from_photo())
        describe_tab.bind(on_release=lambda *_: self._describe_not_available())

        tab_bar.add_widget(search_tab)
        tab_bar.add_widget(photo_tab)
        tab_bar.add_widget(describe_tab)
        body.add_widget(tab_bar)

        search_box, search_input = self._labeled_input("", "e.g. fern, moss, cactus...")
        search_input.text = self.species
        body.add_widget(search_box)

        for name, icon, tags in QUICK_SPECIES:
            is_selected = (self.species == name)

            card = SelectableCard(
                size_hint_y=None, height=dp(64),
                padding=[dp(14), dp(10)], spacing=dp(12),
                bg_color=theme.accent_soft if is_selected else theme.surface_alt,
                border_color=theme.dark_green if is_selected else theme.surface_alt,
                border_width=1.5 if is_selected else 0,
                radius=dp(16)
            )

            icon_lbl = EmojiLabel(
                text=icon, font_size="20sp",
                size_hint=(None, None), size=(dp(28), dp(28)),
                pos_hint={"center_y": 0.5}
            )
            card.add_widget(icon_lbl)

            text_box = BoxLayout(orientation="vertical", spacing=dp(2))
            title_lbl = Label(text=name, bold=True, font_size="14sp", color=theme.text, halign="left", valign="bottom")
            title_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))

            sub_lbl = Label(text=tags, font_size="11sp", color=theme.muted, halign="left", valign="top")
            sub_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))

            text_box.add_widget(title_lbl)
            text_box.add_widget(sub_lbl)
            card.add_widget(text_box)

            def make_cb(n=name):
                def _cb(*_):
                    self.species = n
                    search_input.text = n
                    self._build_step_1()
                return _cb

            card.bind(on_release=make_cb())
            body.add_widget(card)

        scroll.add_widget(body)
        root.add_widget(scroll)

        footer = BoxLayout(size_hint_y=None, height=dp(54), padding=[0, dp(8), 0, 0])
        continue_btn = PillButton(text="Continue ->", bg_color=theme.dark_green if self.species else theme.disabled_accent, radius=dp(14))

        def go_next(*_):
            self.species = search_input.text.strip() or self.species
            if self.species:
                self._build_step_2()

        continue_btn.bind(on_release=go_next)
        footer.add_widget(continue_btn)
        root.add_widget(footer)

        self.add_widget(root)

    def _build_step_2(self):
        self.step = 2
        self.clear_widgets()

        root = RoundedBox(orientation="vertical", bg_color=theme.surface, border_color=theme.border, radius=dp(20), padding=dp(20))
        root.add_widget(self._header("Plant details", "Step 2 of 2", show_back=True))

        scroll = ScrollView(do_scroll_x=False)
        body = BoxLayout(orientation="vertical", spacing=dp(12), size_hint_y=None, padding=[0, dp(10), 0, dp(10)])
        body.bind(minimum_height=body.setter("height"))

        summary = RoundedBox(
            orientation="horizontal", size_hint_y=None, height=dp(56),
            padding=[dp(14), dp(10)], spacing=dp(12),
            bg_color=theme.accent_soft, border_color=theme.accent_soft, radius=dp(14)
        )

        icon_lbl = EmojiLabel(
            text="\U0001F335" if self.species == "Cactus" else "\U0001F33F",
            font_size="20sp", size_hint=(None, None), size=(dp(28), dp(28)),
            pos_hint={"center_y": 0.5}
        )
        summary.add_widget(icon_lbl)

        summary_text = BoxLayout(orientation="vertical", spacing=dp(2))
        title_lbl = Label(text=self.species, bold=True, font_size="14sp", color=theme.dark_green, halign="left", valign="bottom")
        title_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))

        sub_lbl = Label(text="Care data auto-filled · easy", font_size="11sp", color=theme.muted2, halign="left", valign="top")
        sub_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))

        summary_text.add_widget(title_lbl)
        summary_text.add_widget(sub_lbl)
        summary.add_widget(summary_text)
        body.add_widget(summary)

        photo_box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(100), spacing=dp(4))
        photo_lbl = Label(text="Plant photo", font_size="11sp", bold=True, color=theme.muted2, size_hint_y=None, height=dp(16), halign="left")
        photo_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        photo_box.add_widget(photo_lbl)

        # this holds either the add photo button or, once a photo is chosen,
        # a thumbnail of it. we keep a reference so it can be swapped later
        self.photo_area = RoundedBox(
            bg_color=theme.accent_soft, border_color=theme.accent_soft,
            radius=dp(14), size_hint_y=None, height=dp(80),
        )
        self._render_photo_area()
        photo_box.add_widget(self.photo_area)
        body.add_widget(photo_box)

        nick_box, nick_input = self._labeled_input("Nickname *", "e.g. Big Leaf, Monty, Corner Plant")
        nick_input.text = self.species
        self.nickname_input = nick_input
        body.add_widget(nick_box)

        loc_box, loc_input = self._labeled_input("Location in home", "e.g. Living room window, Bedroom shelf")
        self.location_input = loc_input
        body.add_widget(loc_box)

        schedule = RoundedBox(
            orientation="vertical", size_hint_y=None, height=dp(105),
            padding=dp(12), spacing=dp(6),
            bg_color=theme.surface_alt, border_color=theme.surface_alt, radius=dp(14)
        )

        sched_title = Label(text="Auto-filled care schedule", bold=True, font_size="11sp", color=theme.text, halign="left", size_hint_y=None, height=dp(16))
        sched_title.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        schedule.add_widget(sched_title)

        if self.care_guide:
            water = self.care_guide["watering_schedule"]["interval_days"]
            fert = self.care_guide["fertilizing"]["interval_days"]
            repot = self.care_guide["repotting"]["interval_months"]
            schedule_items = [
                ("\U0001F4A7", "Watering", f"Every {water} days"),
                ("\U0001F33F", "Fertilizing", f"Every {fert} days"),
                ("\U0001FAB4", "Repotting", f"Every {repot} months"),
            ]
        else:
            schedule_items = [
                ("\U0001F4A7", "Watering", "Loading..."),
                ("\U0001F33F", "Fertilizing", "Loading..."),
                ("\U0001FAB4", "Repotting", "Loading..."),
            ]

        for icon, name, freq in schedule_items:
            row = BoxLayout(size_hint_y=None, height=dp(20))
            item_box = BoxLayout(orientation="horizontal", spacing=dp(6))
            ic_lbl = EmojiLabel(text=icon, font_size="14sp", size_hint=(None, None), size=(dp(18), dp(18)), pos_hint={"center_y": 0.5})
            nm_lbl = Label(text=name, font_size="11sp", color=theme.muted2, halign="left", valign="middle")
            nm_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
            item_box.add_widget(ic_lbl)
            item_box.add_widget(nm_lbl)
            row.add_widget(item_box)

            freq_lbl = Label(text=freq, font_size="11sp", color=theme.text, halign="right", valign="middle")
            freq_lbl.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
            row.add_widget(freq_lbl)
            schedule.add_widget(row)

        body.add_widget(schedule)

        notes_box, notes_input = self._labeled_input("Notes (optional)", "Any quirks about this specific plant?", multiline=True)
        body.add_widget(notes_box)

        scroll.add_widget(body)
        root.add_widget(scroll)

        footer = BoxLayout(size_hint_y=None, height=dp(54), padding=[0, dp(8), 0, 0])
        self.save_btn = PillButton(text="Add to my collection", bg_color=theme.dark_green, radius=dp(14))
        self.save_btn.bind(on_release=lambda *_: self._save())
        footer.add_widget(self.save_btn)
        root.add_widget(footer)

        self.add_widget(root)


    def _render_photo_area(self):
        """
        draws whatever belongs in the photo box right now

        with no photo chosen that is just the add photo button. once one is
        chosen it becomes a thumbnail with the file name and a way to change
        it, so there is visible proof the photo actually arrived
        """
        self.photo_area.clear_widgets()

        if not self.photo_path:
            self.photo_btn = PillButton(
                text="+ Add photo", bg_color=[0, 0, 0, 0],
                fg_color=theme.dark_green, font_size="12sp",
            )
            self.photo_btn.bind(on_release=lambda *_: self._open_photo_picker())
            self.photo_area.add_widget(self.photo_btn)
            return

        row = BoxLayout(orientation="horizontal", spacing=dp(10),
                        padding=dp(8))

        thumb = Image(source=self.photo_path, size_hint=(None, 1),
                      width=dp(64), allow_stretch=True, keep_ratio=True)
        row.add_widget(thumb)

        text_col = BoxLayout(orientation="vertical", spacing=dp(2))

        ok = Label(text="Photo added", font_size="12sp", bold=True,
                   color=theme.dark_green, halign="left", valign="bottom")
        ok.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        text_col.add_widget(ok)

        name = Label(text=self._short_filename(), font_size="10sp",
                     color=theme.muted2, halign="left", valign="top")
        name.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        text_col.add_widget(name)

        row.add_widget(text_col)

        change = PillButton(text="Change", bg_color=theme.chip,
                            fg_color=theme.muted2, font_size="10sp",
                            size_hint=(None, None), size=(dp(64), dp(28)),
                            radius=dp(14))
        change.bind(on_release=lambda *_: self._open_photo_picker())
        row.add_widget(change)

        self.photo_area.add_widget(row)

    def _short_filename(self):
        """trims a long file name so it does not overflow the box"""
        name = os.path.basename(self.photo_path or "")
        return name if len(name) <= 24 else name[:21] + "..."

    def _open_photo_picker(self):
        PhotoPickerModal(on_picked=self._on_photo_picked).open()

    def _on_photo_picked(self, path):
        """called by the picker once a file has been chosen or sent from a phone"""
        self.photo_path = path
        self._render_photo_area()


    def _save(self):
        nickname = self.nickname_input.text.strip()
        if not nickname:
            return
        location = self.location_input.text.strip()
        species = self.species

        self.save_btn.text = "Adding..."
        self.save_btn.disabled = True

        # grab these before the thread starts so the worker is not reaching
        # back into the widget while the user might still be clicking around
        photo_path = self.photo_path
        care_guide = self.care_guide
        light_requirement = self.light_requirement

        def worker():
            try:
                plant = api.create_plant(
                    nickname, species, location,
                    care_guide=care_guide,
                    light_requirement=light_requirement,
                )

                # the photo endpoint needs a plant id, so the plant has to
                # exist first. if the photo fails we still keep the plant,
                # because losing someones plant over a bad jpeg would be
                # pretty annoying
                photo_failed = False
                if photo_path:
                    try:
                        plant = api.upload_plant_photo(plant["id"], photo_path)
                    except Exception:
                        photo_failed = True

                Clock.schedule_once(
                    lambda dt, p=plant, f=photo_failed: self._on_success(p, f)
                )
            except Exception as exc:
                Clock.schedule_once(lambda dt, err=exc: self._on_error(err))

        threading.Thread(target=worker, daemon=True).start()
    def _on_success(self, plant, photo_failed=False):
        self.dismiss()
        if self.on_saved:
            self.on_saved(plant)
        # the plant did save, so this is a warning and not an error
        if photo_failed:
            ErrorModal("Plant saved, but the photo could not be uploaded.").open()

    def _on_error(self, exc):
        self.save_btn.text = "Add to my collection"
        self.save_btn.disabled = False
        ErrorModal("Could not save plant.").open()