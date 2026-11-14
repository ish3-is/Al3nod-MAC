from __future__ import annotations

import queue
import sys
import threading
import time
import tkinter as tk
from collections import deque
from tkinter import ttk

import cv2
from PIL import Image, ImageTk

from ai.holistic_tracker import HolisticTracker
from ai.saudi_number_recognizer import NumberStabilizer, format_digit
from ai.translator import TranslationEngine, TranslationResult
from config import (
    APP_NAME,
    ASSET_DIR,
    COLORS,
    COURSE_CODE,
    COURSE_NAME,
    DB_PATH,
    DEMO_PASSWORD,
    DEMO_USERNAME,
    INSTRUCTOR,
    MODEL_DIR,
    PROJECT_TITLE,
    STUDENTS,
    TARGET_PHRASES,
)
from core.auth import AuthService
from core.camera import CameraDevice
from core.session import Session


class IsharaTkApp:
    """Functional dependency-free fallback used when PySide6 cannot be installed."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1280x780")
        self.root.minsize(1000, 650)
        self.root.configure(bg=COLORS["background"])
        self.auth = AuthService(DB_PATH)
        self.auth.initialize(DEMO_USERNAME, DEMO_PASSWORD)
        self.session = Session()
        self.engine = TranslationEngine(MODEL_DIR)
        self.camera = CameraDevice()
        self.tracker: HolisticTracker | None = None
        self.camera_running = False
        self.camera_thread: threading.Thread | None = None
        self.frame_queue: queue.Queue = queue.Queue(maxsize=2)
        self.sequence = deque(maxlen=900)
        self.timestamps = deque(maxlen=900)
        self.number_stabilizer = NumberStabilizer()
        self.detected_digit = None
        self.digit_stability = 0.0
        self.pages: dict[str, tk.Frame] = {}
        self._configure_styles()
        self._build_pages()
        self.show_page("login")
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(40, self._poll_frames)

    def _configure_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground=COLORS["surface_alt"], background=COLORS["surface_alt"], foreground=COLORS["text"], arrowcolor=COLORS["accent"], padding=8)

    def _label(self, parent, text="", size=12, color=None, bold=False, **kwargs):
        return tk.Label(parent, text=text, bg=kwargs.pop("bg", parent.cget("bg")), fg=color or COLORS["text"], font=("Segoe UI", size, "bold" if bold else "normal"), **kwargs)

    def _button(self, parent, text, command, primary=False, danger=False, **kwargs):
        bg = COLORS["accent"] if primary else COLORS["surface_alt"]
        fg = "#041014" if primary else (COLORS["danger"] if danger else COLORS["text"])
        return tk.Button(parent, text=text, command=command, bg=bg, fg=fg, activebackground=COLORS["accent"], activeforeground="#041014", bd=0, padx=18, pady=10, cursor="hand2", font=("Segoe UI", 11, "bold"), **kwargs)

    def _card(self, parent):
        return tk.Frame(parent, bg=COLORS["surface"], highlightthickness=1, highlightbackground="#1F344C", padx=24, pady=22)

    def _build_pages(self):
        container = tk.Frame(self.root, bg=COLORS["background"])
        container.pack(fill="both", expand=True)
        for name in ("login", "translation", "result", "guide", "about"):
            frame = tk.Frame(container, bg=COLORS["background"])
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.pages[name] = frame
        self._build_login(self.pages["login"])
        self._build_translation(self.pages["translation"])
        self._build_result(self.pages["result"])
        self._build_guide(self.pages["guide"])
        self._build_about(self.pages["about"])

    def _build_login(self, page):
        left = tk.Frame(page, bg=COLORS["background"])
        left.place(relx=.07, rely=.15, relwidth=.48, relheight=.7)
        self._label(left, "ISHARA  إشارة", 34, COLORS["accent"], True, anchor="w").pack(fill="x", pady=(80, 12))
        self._label(left, "تواصل أوضح عند نقطة الدفع", 24, bold=True, anchor="w").pack(fill="x", pady=8)
        description = "تطبيق مكتبي يربط بث الكاميرا بمعمارية ترجمة عصبية قابلة للتطوير. عند غياب النموذج المدرب يعمل وضع محاكاة معلن بوضوح."
        self._label(left, description, 13, COLORS["secondary"], wraplength=530, justify="left", anchor="w").pack(fill="x")
        card = self._card(page)
        card.place(relx=.62, rely=.2, relwidth=.3, relheight=.58)
        self._label(card, "تسجيل دخول الكاشير", 19, bold=True).pack(anchor="e", pady=(8, 24))
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.login_error = tk.StringVar()
        self._label(card, "اسم المستخدم", 10, COLORS["secondary"]).pack(anchor="e")
        self.username_entry = tk.Entry(card, textvariable=self.username_var, bg=COLORS["surface_alt"], fg=COLORS["text"], insertbackground=COLORS["accent"], relief="flat", font=("Segoe UI", 12), justify="right")
        self.username_entry.pack(fill="x", ipady=10, pady=(4, 14))
        self._label(card, "كلمة المرور", 10, COLORS["secondary"]).pack(anchor="e")
        self.password_entry = tk.Entry(card, textvariable=self.password_var, show="•", bg=COLORS["surface_alt"], fg=COLORS["text"], insertbackground=COLORS["accent"], relief="flat", font=("Segoe UI", 12), justify="right")
        self.password_entry.pack(fill="x", ipady=10, pady=(4, 10))
        self.password_entry.bind("<Return>", lambda _: self.login())
        self._button(card, "إظهار / إخفاء كلمة المرور", self.toggle_password).pack(fill="x", pady=4)
        self._label(card, textvariable=self.login_error, size=10, color=COLORS["danger"], wraplength=320).pack(pady=5)
        self._button(card, "تسجيل الدخول", self.login, primary=True).pack(fill="x", pady=4)

    def _build_translation(self, page):
        top = tk.Frame(page, bg=COLORS["background"])
        top.pack(fill="x", padx=34, pady=(22, 14))
        self._label(top, APP_NAME, 23, COLORS["accent"], True).pack(side="left")
        self._button(top, "تسجيل الخروج", self.logout, danger=True).pack(side="right", padx=5)
        self._button(top, "عن المشروع", lambda: self.show_page("about")).pack(side="right", padx=5)
        self._button(top, "دليل الإشارات", lambda: self.show_page("guide")).pack(side="right", padx=5)
        body = tk.Frame(page, bg=COLORS["background"])
        body.pack(fill="both", expand=True, padx=34)
        self.video_label = self._label(body, "الكاميرا متوقفة\nابدأ الترجمة لفتح البث", 16, COLORS["secondary"], bg="#030914")
        self.video_label.place(relx=0, rely=0, relwidth=.65, relheight=.88)
        side = tk.Frame(body, bg=COLORS["background"])
        side.place(relx=.68, rely=0, relwidth=.32, relheight=.88)
        self.mode_var = tk.StringVar(value="\u062a\u0631\u062c\u0645\u0629 \u0627\u0644\u062c\u0645\u0644")
        self._label(side, "\u0648\u0636\u0639 \u0627\u0644\u062a\u0639\u0631\u0641", 11, COLORS["secondary"]).pack(fill="x", anchor="e")
        mode_combo = ttk.Combobox(
            side,
            values=("\u062a\u0631\u062c\u0645\u0629 \u0627\u0644\u062c\u0645\u0644", "\u0627\u0644\u0623\u0631\u0642\u0627\u0645 \u0660-\u0669"),
            textvariable=self.mode_var,
            state="readonly",
            justify="right",
        )
        mode_combo.pack(fill="x", pady=(4, 10))
        mode_combo.bind("<<ComboboxSelected>>", lambda _: self._change_recognition_mode())
        self.camera_status_var = tk.StringVar(value="● الكاميرا: متوقفة")
        self.model_status_var = tk.StringVar(value=f"● النموذج: {self.engine.status}")
        self.tracker_status_var = tk.StringVar(value="● التتبع: في انتظار التشغيل")
        for var in (self.camera_status_var, self.model_status_var, self.tracker_status_var):
            self._label(side, textvariable=var, size=11, color=COLORS["secondary"], wraplength=370, justify="right").pack(fill="x", anchor="e", pady=8)
        self.live_result_var = tk.StringVar(value="لا توجد نتيجة مؤكدة")
        self._label(side, textvariable=self.live_result_var, size=20, bold=True, bg="#0B1726", wraplength=340).pack(fill="x", ipady=24, pady=16)
        self.number_preview_var = tk.StringVar(value="\u2014")
        self.number_preview = self._label(
            side, textvariable=self.number_preview_var, size=48,
            color=COLORS["accent"], bold=True, bg="#071827"
        )
        demo = self._card(side)
        demo.pack(fill="both", expand=True, pady=4)
        self._label(demo, "Demo Simulation", 14, COLORS["warning"], True).pack(anchor="w")
        self._label(demo, "اختبار للواجهة فقط. لا تمثل الخيارات تعريفات لإشارات سعودية.", 10, COLORS["secondary"], wraplength=320, justify="right").pack(fill="x", pady=8)
        self.demo_var = tk.StringVar(value=TARGET_PHRASES[0])
        combo = ttk.Combobox(demo, values=TARGET_PHRASES, textvariable=self.demo_var, state="readonly", justify="right")
        combo.pack(fill="x", pady=8)
        self._button(demo, "تشغيل المحاكاة المعلنة", self.run_demo).pack(fill="x", pady=5)
        actions = tk.Frame(page, bg=COLORS["background"])
        actions.pack(fill="x", padx=34, pady=(8, 22))
        self.start_button = self._button(actions, "بدء الترجمة", self.start_camera, primary=True)
        self.start_button.pack(side="left", padx=(0, 8))
        self.stop_button = self._button(actions, "إيقاف الترجمة", self.stop_camera)
        self.stop_button.pack(side="left", padx=8)
        self._button(actions, "إعادة الضبط", self.reset).pack(side="left", padx=8)

    def _build_result(self, page):
        content = tk.Frame(page, bg=COLORS["background"])
        content.place(relx=.18, rely=.12, relwidth=.64, relheight=.76)
        self._label(content, "نتيجة الترجمة", 28, bold=True).pack(pady=(20, 70))
        self.result_phrase_var = tk.StringVar(value="—")
        self.result_confidence_var = tk.StringVar(value="")
        self.result_status_var = tk.StringVar(value="")
        self._label(content, textvariable=self.result_phrase_var, size=30, bold=True, bg="#0B1726").pack(fill="x", ipady=35)
        self._label(content, textvariable=self.result_confidence_var, size=12, color=COLORS["secondary"]).pack(pady=16)
        self._label(content, textvariable=self.result_status_var, size=12, color=COLORS["warning"], wraplength=700).pack(pady=4)
        buttons = tk.Frame(content, bg=COLORS["background"])
        buttons.pack(pady=50)
        self._button(buttons, "إعادة المحاولة", self.retry).pack(side="left", padx=8)
        self._button(buttons, "العودة للكاميرا", lambda: self.show_page("translation"), primary=True).pack(side="left", padx=8)

    def _build_about(self, page):
        top = tk.Frame(page, bg=COLORS["background"])
        top.pack(fill="x", padx=60, pady=28)
        self._label(top, "عن المشروع", 27, bold=True).pack(side="left")
        self._button(top, "العودة", lambda: self.show_page("translation")).pack(side="right")
        card = self._card(page)
        card.pack(fill="both", expand=True, padx=70, pady=(0, 40))
        details = [
            ("Project Title", PROJECT_TITLE),
            ("Course", COURSE_NAME),
            ("Course Code", COURSE_CODE),
            ("Instructor", INSTRUCTOR),
            ("Technology Stack", "Python, PySide6, OpenCV, MediaPipe optional, SQLite, NumPy"),
            ("System", "Camera Input → Frame Processing → Hand Landmark Detection → Sequence Normalization → Neural Classification → Arabic Phrase Mapping"),
        ]
        for key, value in details:
            row = tk.Frame(card, bg=COLORS["surface"])
            row.pack(fill="x", pady=5)
            self._label(row, key, 11, COLORS["accent"], True, width=18, anchor="w").pack(side="left")
            self._label(row, value, 11, wraplength=800, justify="left", anchor="w").pack(side="left", fill="x", expand=True)
        self._label(card, "Student Team", 13, COLORS["accent"], True).pack(anchor="w", pady=(16, 5))
        for name, sid in STUDENTS:
            self._label(card, f"{name}     {sid}", 11, anchor="e").pack(fill="x", pady=2)

    def _build_guide(self, page):
        top = tk.Frame(page, bg=COLORS["background"])
        top.pack(fill="x", padx=42, pady=(22, 10))
        self._label(top, "دليل الإشارات", 27, bold=True).pack(side="left")
        self._button(
            top, "العودة للكاميرا", lambda: self.show_page("translation")
        ).pack(side="right")

        notice = self._label(
            page,
            "دليل مرجعي للتعلّم والعرض فقط — لا تُعرض هذه الإشارات كنتيجة AI إلا إذا دعمها النموذج.",
            11,
            COLORS["warning"],
            True,
            bg="#172238",
            wraplength=1050,
            justify="right",
        )
        notice.pack(fill="x", padx=42, ipady=12, pady=(0, 12))

        notebook = ttk.Notebook(page)
        notebook.pack(fill="both", expand=True, padx=42, pady=(0, 28))
        self._guide_photos = []
        assets = ASSET_DIR / "sign_guides"
        self._add_guide_tab(
            notebook,
            "عبارات يومية",
            assets / "social_signs.png",
            (860, 610),
        )
        self._add_guide_tab(
            notebook,
            "إشارات الكاشير",
            assets / "cashier_signs.png",
            (680, 610),
        )

    def _add_guide_tab(self, notebook, title, image_path, max_size):
        tab = tk.Frame(notebook, bg=COLORS["surface"])
        notebook.add(tab, text=title)
        image_label = self._label(tab, "", 12, bg=COLORS["surface"])
        image_label.pack(fill="both", expand=True, padx=18, pady=18)
        try:
            image = Image.open(image_path).convert("RGB")
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            self._guide_photos.append(photo)
            image_label.configure(image=photo)
        except (OSError, ValueError):
            image_label.configure(
                text=f"تعذر تحميل صورة الدليل: {image_path.name}",
                fg=COLORS["danger"],
            )

    def show_page(self, name: str):
        if name != "login" and not self.session.authenticated:
            name = "login"
        self.pages[name].tkraise()

    def toggle_password(self):
        self.password_entry.configure(show="" if self.password_entry.cget("show") else "•")

    def login(self):
        user = self.auth.authenticate(self.username_var.get(), self.password_var.get())
        if user:
            self.session.login(user)
            self.login_error.set("")
            self.password_var.set("")
            self.show_page("translation")
        else:
            self.login_error.set("اسم المستخدم أو كلمة المرور غير صحيحة")

    def logout(self):
        self.stop_camera(process=False)
        self.session.logout()
        self.show_page("login")

    def start_camera(self):
        if self.camera_running:
            return
        ok, message = self.camera.open()
        self.camera_status_var.set(f"● الكاميرا: {message}")
        if not ok:
            self.video_label.configure(text="تعذر فتح الكاميرا\nتحقق من الجهاز والصلاحيات", image="")
            return
        self.sequence.clear()
        self.timestamps.clear()
        self.number_stabilizer.reset()
        self.detected_digit = None
        self.digit_stability = 0.0
        self.number_preview_var.set("\u2014")
        self.live_result_var.set("جاري تسجيل مقطع الإشارة…")
        self.tracker = HolisticTracker()
        self.tracker_status_var.set(f"● التتبع: {self.tracker.status}")
        self.camera_running = True
        self.camera_thread = threading.Thread(target=self._camera_loop, daemon=True)
        self.camera_thread.start()

    def _camera_loop(self):
        while self.camera_running:
            read = self.camera.read()
            if not read.ok:
                self.frame_queue.put(("error", read.message))
                break
            tracked = self.tracker.process(read.frame) if self.tracker else None
            frame = tracked.frame if tracked else read.frame
            feature = tracked.feature if tracked else None
            if feature is not None:
                self.sequence.append(feature)
                self.timestamps.append(tracked.timestamp_ms)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(rgb)
            if self.frame_queue.full():
                try:
                    self.frame_queue.get_nowait()
                except queue.Empty:
                    pass
            self.frame_queue.put(("frame", (image, tracked.digit if tracked else None)))
            time.sleep(.02)
        self.camera.release()

    def _poll_frames(self):
        try:
            while True:
                kind, payload = self.frame_queue.get_nowait()
                if kind == "frame":
                    payload, digit = payload
                    width = max(self.video_label.winfo_width(), 640)
                    height = max(self.video_label.winfo_height(), 360)
                    payload.thumbnail((width, height), Image.Resampling.LANCZOS)
                    self._video_photo = ImageTk.PhotoImage(payload)
                    self.video_label.configure(image=self._video_photo, text="")
                    if self._number_mode():
                        stable, stability = self.number_stabilizer.update(digit)
                        self.digit_stability = stability
                        if stable is not None:
                            self.detected_digit = stable
                            shown = format_digit(stable)
                            self.number_preview_var.set(shown)
                            self.live_result_var.set(f"\u0627\u0644\u0631\u0642\u0645 \u0627\u0644\u0645\u0643\u062a\u0634\u0641: {shown}")
                        else:
                            self.number_preview_var.set("\u2026")
                else:
                    self.camera_status_var.set(f"● الكاميرا: {payload}")
                    self.camera_running = False
        except queue.Empty:
            pass
        self.root.after(40, self._poll_frames)

    def stop_camera(self, process=True):
        features = list(self.sequence)
        timestamps = list(self.timestamps)
        self.camera_running = False
        self.camera.release()
        if self.tracker:
            self.tracker.close()
            self.tracker = None
        self.camera_status_var.set("● الكاميرا: متوقفة")
        if hasattr(self, "video_label"):
            self.video_label.configure(image="", text="الكاميرا متوقفة")
        if process and self._number_mode():
            if self.detected_digit is not None:
                result = TranslationResult(
                    format_digit(self.detected_digit), self.digit_stability,
                    "\u062a\u0645 \u0627\u0644\u062a\u0639\u0631\u0641 \u0639\u0644\u0649 \u0627\u0644\u0631\u0642\u0645 \u0628\u0639\u062f \u062b\u0628\u0627\u062a \u0627\u0644\u0625\u0634\u0627\u0631\u0629.",
                    "number", True,
                )
            else:
                result = TranslationResult(
                    None, self.digit_stability or None,
                    "\u0644\u0645 \u064a\u062b\u062a \u0631\u0642\u0645. \u062b\u0628\u0651\u062a \u064a\u062f\u0643 \u0623\u0645\u0627\u0645 \u0627\u0644\u0643\u0627\u0645\u064a\u0631\u0627.",
                    "number", False,
                )
            self.show_result(result)
        elif process and features and self.engine.mode == "model":
            self.live_result_var.set("Processing… جارٍ تنفيذ الاستدلال")
            threading.Thread(
                target=self._run_real_inference,
                args=(features, timestamps),
                daemon=True,
            ).start()
        elif process:
            # Avoid a silent Stop action when tracking/model data is missing.
            self.show_result(self.engine.classify(None))

    def _run_real_inference(self, features, timestamps):
        result = self.engine.classify(features, timestamps)
        self.root.after(0, lambda: self.show_result(result))

    def run_demo(self):
        self.show_result(self.engine.simulate(self.demo_var.get()))

    def show_result(self, result):
        self.result_phrase_var.set(result.phrase or "إشارة غير معروفة")
        self.result_confidence_var.set(f"ثقة النموذج: {result.confidence:.1%}" if result.confidence is not None else "لا توجد درجة ثقة في وضع المحاكاة")
        self.result_status_var.set(result.status)
        self.show_page("result")

    def retry(self):
        self.reset()
        self.show_page("translation")

    def reset(self):
        self.sequence.clear()
        self.timestamps.clear()
        self.number_stabilizer.reset()
        self.detected_digit = None
        self.digit_stability = 0.0
        self.number_preview_var.set("\u2014")
        self.live_result_var.set("لا توجد نتيجة مؤكدة")

    def _number_mode(self):
        return self.mode_var.get().startswith("\u0627\u0644\u0623\u0631\u0642\u0627\u0645")

    def _change_recognition_mode(self):
        self.number_stabilizer.reset()
        self.detected_digit = None
        self.digit_stability = 0.0
        if self._number_mode():
            self.number_preview.pack(fill="x", ipady=10, pady=(0, 10))
            self.live_result_var.set("\u0627\u0639\u0631\u0636 \u0631\u0642\u0645\u064b\u0627 \u0645\u0646 \u0660 \u0625\u0644\u0649 \u0669")
        else:
            self.number_preview.pack_forget()
            self.live_result_var.set("\u0644\u0627 \u062a\u0648\u062c\u062f \u0646\u062a\u064a\u062c\u0629 \u0628\u0639\u062f")

    def close(self):
        self.stop_camera(process=False)
        self.root.destroy()


def run(smoke_seconds: float | None = None) -> int:
    root = tk.Tk()
    app = IsharaTkApp(root)
    if smoke_seconds:
        root.after(int(smoke_seconds * 1000), app.close)
    root.mainloop()
    return 0
