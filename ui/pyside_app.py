from __future__ import annotations

import sys
import time
from collections import deque

import cv2
import numpy as np
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

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


STYLE = f"""
QWidget {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #06101D,stop:0.55 #091827,stop:1 #07111F); color: {COLORS['text']}; font-family: 'Segoe UI', 'Arial'; font-size: 15px; }}
QFrame#card {{ background: rgba(16,29,45,235); border: 1px solid #244761; border-radius: 22px; }}
QLabel#brand {{ color: {COLORS['accent']}; font-size: 35px; font-weight: 700; }}
QLabel#title {{ font-size: 26px; font-weight: 700; }}
QLabel#muted {{ color: {COLORS['secondary']}; }}
QLabel#result {{ background: rgba(6,17,31,235); border: 1px solid #1E796F; border-radius: 18px; padding: 20px; font-size: 29px; font-weight: 700; }}
QLabel#numberPreview {{ color: {COLORS['accent']}; background: rgba(5,18,29,235); border: 2px solid {COLORS['accent']}; border-radius: 22px; padding: 18px; font-size: 72px; font-weight: 800; }}
QLineEdit, QComboBox {{ background: #12263A; border: 1px solid #31516D; border-radius: 12px; padding: 12px; min-height: 25px; }}
QLineEdit:focus, QComboBox:focus {{ border: 1px solid {COLORS['accent']}; }}
QPushButton {{ background: #12263A; border: 1px solid #31516D; border-radius: 12px; padding: 12px 20px; font-weight: 650; }}
QPushButton:hover {{ background: #183249; border-color: {COLORS['accent']}; }}
QPushButton#primary {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #13D8C3,stop:1 #58F2D3); color: #041014; border: none; }}
QPushButton#danger {{ color: {COLORS['danger']}; }}
QPushButton:disabled {{ color: #52667B; background: #0C1724; border-color: #17283A; }}
"""


class CameraThread(QThread):
    frame_ready = Signal(QImage)
    status_changed = Signal(bool, str)
    tracking_changed = Signal(str)
    feature_ready = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self.camera = CameraDevice()
        self.tracker = HolisticTracker()

    def run(self):
        ok, message = self.camera.open()
        self.status_changed.emit(ok, message)
        self.tracking_changed.emit(self.tracker.status)
        if not ok:
            return
        self._running = True
        while self._running:
            read = self.camera.read()
            if not read.ok:
                self.status_changed.emit(False, read.message)
                break
            tracked = self.tracker.process(read.frame)
            self.feature_ready.emit((tracked.feature, tracked.timestamp_ms, tracked.digit))
            frame = cv2.cvtColor(tracked.frame, cv2.COLOR_BGR2RGB)
            h, w, channels = frame.shape
            image = QImage(frame.data, w, h, channels * w, QImage.Format.Format_RGB888).copy()
            self.frame_ready.emit(image)
            self.msleep(20)
        self.camera.release()
        self.status_changed.emit(False, "Camera stopped")

    def stop(self):
        self._running = False
        self.wait(1800)
        self.camera.release()
        self.tracker.close()


class InferenceThread(QThread):
    completed = Signal(object)

    def __init__(self, engine, features, timestamps, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.features = np.asarray(features, dtype=np.float32)
        self.timestamps = list(timestamps)

    def run(self):
        self.completed.emit(self.engine.classify(self.features, self.timestamps))


class LoginPage(QWidget):
    authenticated = Signal(object)

    def __init__(self, auth: AuthService):
        super().__init__()
        self.auth = auth
        outer = QHBoxLayout(self)
        outer.setContentsMargins(110, 60, 110, 60)
        intro = QVBoxLayout()
        brand = QLabel("ISHARA  إشارة")
        brand.setObjectName("brand")
        title = QLabel("تواصل أوضح عند نقطة الدفع")
        title.setObjectName("title")
        desc = QLabel("تطبيق مكتبي يربط بث الكاميرا بمعمارية ترجمة عصبية قابلة للتطوير، مع وضع محاكاة معلن عند غياب النموذج المدرب.")
        desc.setObjectName("muted")
        desc.setWordWrap(True)
        intro.addStretch()
        intro.addWidget(brand)
        intro.addSpacing(16)
        intro.addWidget(title)
        intro.addWidget(desc)
        intro.addStretch()
        card = QFrame()
        card.setObjectName("card")
        form = QVBoxLayout(card)
        form.setContentsMargins(34, 34, 34, 34)
        form.addWidget(QLabel("تسجيل دخول الكاشير"))
        self.username = QLineEdit()
        self.username.setPlaceholderText("اسم المستخدم")
        self.password = QLineEdit()
        self.password.setPlaceholderText("كلمة المرور")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.returnPressed.connect(self.login)
        self.toggle = QPushButton("إظهار كلمة المرور")
        self.toggle.clicked.connect(self.toggle_password)
        self.error = QLabel("")
        self.error.setStyleSheet(f"color:{COLORS['danger']}")
        submit = QPushButton("تسجيل الدخول")
        submit.setObjectName("primary")
        submit.clicked.connect(self.login)
        form.addSpacing(18)
        form.addWidget(self.username)
        form.addWidget(self.password)
        form.addWidget(self.toggle)
        form.addWidget(self.error)
        form.addWidget(submit)
        outer.addLayout(intro, 3)
        outer.addSpacing(70)
        outer.addWidget(card, 2)

    def toggle_password(self):
        hidden = self.password.echoMode() == QLineEdit.EchoMode.Password
        self.password.setEchoMode(QLineEdit.EchoMode.Normal if hidden else QLineEdit.EchoMode.Password)
        self.toggle.setText("إخفاء كلمة المرور" if hidden else "إظهار كلمة المرور")

    def login(self):
        user = self.auth.authenticate(self.username.text(), self.password.text())
        if user:
            self.error.clear()
            self.password.clear()
            self.authenticated.emit(user)
        else:
            self.error.setText("اسم المستخدم أو كلمة المرور غير صحيحة")


class TranslationPage(QWidget):
    logout_requested = Signal()
    about_requested = Signal()
    guide_requested = Signal()
    result_ready = Signal(object)

    def __init__(self, engine: TranslationEngine):
        super().__init__()
        self.engine = engine
        self.camera_thread: CameraThread | None = None
        self.sequence = deque(maxlen=900)
        self.timestamps = deque(maxlen=900)
        self.number_stabilizer = NumberStabilizer()
        self.detected_digit = None
        self.digit_stability = 0.0
        self.inference_thread: InferenceThread | None = None
        root = QVBoxLayout(self)
        root.setContentsMargins(34, 24, 34, 30)
        top = QHBoxLayout()
        brand = QLabel(APP_NAME)
        brand.setObjectName("brand")
        brand.setStyleSheet("font-size:25px")
        about = QPushButton("عن المشروع")
        about.clicked.connect(self.about_requested)
        guide = QPushButton("دليل الإشارات")
        guide.clicked.connect(self.guide_requested)
        logout = QPushButton("تسجيل الخروج")
        logout.setObjectName("danger")
        logout.clicked.connect(self.logout_requested)
        top.addWidget(brand)
        top.addStretch()
        top.addWidget(guide)
        top.addWidget(about)
        top.addWidget(logout)
        root.addLayout(top)
        body = QGridLayout()
        body.setHorizontalSpacing(22)
        self.video = QLabel("الكاميرا متوقفة\nابدأ الترجمة لفتح البث")
        self.video.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video.setMinimumSize(720, 430)
        self.video.setStyleSheet("background:#030914;border:1px solid #1F344C;border-radius:18px;color:#91A3B8")
        body.addWidget(self.video, 0, 0, 8, 1)
        self.camera_status = QLabel("● الكاميرا: متوقفة")
        self.model_status = QLabel(f"● النموذج: {self.engine.status}")
        self.tracker_status = QLabel("● التتبع: في انتظار التشغيل")
        mode_title = QLabel("\u0648\u0636\u0639 \u0627\u0644\u062a\u0639\u0631\u0641")
        mode_title.setObjectName("muted")
        self.mode_selector = QComboBox()
        self.mode_selector.addItem("\u062a\u0631\u062c\u0645\u0629 \u0627\u0644\u062c\u0645\u0644", "sentences")
        self.mode_selector.addItem("\u0627\u0644\u0623\u0631\u0642\u0627\u0645 \u0660-\u0669", "numbers")
        self.mode_selector.currentIndexChanged.connect(self.change_recognition_mode)
        body.addWidget(mode_title, 0, 1)
        body.addWidget(self.mode_selector, 1, 1)
        for label in (self.camera_status, self.model_status, self.tracker_status):
            label.setObjectName("muted")
        body.addWidget(self.camera_status, 2, 1)
        body.addWidget(self.model_status, 3, 1)
        body.addWidget(self.tracker_status, 4, 1)
        self.number_preview = QLabel("\u2014")
        self.number_preview.setObjectName("numberPreview")
        self.number_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.number_preview.hide()
        body.addWidget(self.number_preview, 5, 1)
        self.result = QLabel("لا توجد نتيجة مؤكدة")
        self.result.setObjectName("result")
        self.result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.addWidget(self.result, 6, 1)
        demo_card = QFrame()
        demo_card.setObjectName("card")
        demo_layout = QVBoxLayout(demo_card)
        demo_title = QLabel("Demo Simulation")
        demo_title.setStyleSheet(f"color:{COLORS['warning']};font-weight:700")
        demo_note = QLabel("اختبار للواجهة فقط. لا تمثل الخيارات تعريفات لإشارات سعودية.")
        demo_note.setWordWrap(True)
        demo_note.setObjectName("muted")
        self.demo_phrase = QComboBox()
        self.demo_phrase.addItems(TARGET_PHRASES)
        demo_button = QPushButton("تشغيل المحاكاة المعلنة")
        demo_button.clicked.connect(self.run_demo)
        demo_layout.addWidget(demo_title)
        demo_layout.addWidget(demo_note)
        demo_layout.addWidget(self.demo_phrase)
        demo_layout.addWidget(demo_button)
        body.addWidget(demo_card, 7, 1)
        body.setColumnStretch(0, 4)
        body.setColumnStretch(1, 2)
        root.addLayout(body, 1)
        actions = QHBoxLayout()
        self.start = QPushButton("بدء الترجمة")
        self.start.setObjectName("primary")
        self.start.clicked.connect(self.start_camera)
        self.stop = QPushButton("إيقاف الترجمة")
        self.stop.clicked.connect(self.stop_camera)
        self.stop.setEnabled(False)
        reset = QPushButton("إعادة الضبط")
        reset.clicked.connect(self.reset)
        actions.addWidget(self.start)
        actions.addWidget(self.stop)
        actions.addWidget(reset)
        actions.addStretch()
        root.addLayout(actions)

    def start_camera(self):
        if self.camera_thread and self.camera_thread.isRunning():
            return
        self.sequence.clear()
        self.timestamps.clear()
        self.number_stabilizer.reset()
        self.detected_digit = None
        self.digit_stability = 0.0
        self.number_preview.setText("\u2014")
        self.result.setText("جاري تسجيل مقطع الإشارة…")
        self.camera_thread = CameraThread(self)
        self.camera_thread.frame_ready.connect(self.update_frame)
        self.camera_thread.status_changed.connect(self.update_camera_status)
        self.camera_thread.tracking_changed.connect(lambda s: self.tracker_status.setText(f"● التتبع: {s}"))
        self.camera_thread.feature_ready.connect(self.consume_feature)
        self.camera_thread.start()
        self.start.setEnabled(False)
        self.stop.setEnabled(True)

    def stop_camera(self):
        if self.camera_thread:
            self.camera_thread.stop()
            self.camera_thread = None
        self.start.setEnabled(True)
        self.stop.setEnabled(False)
        self.video.setPixmap(QPixmap())
        self.video.setText("الكاميرا متوقفة")
        if self.current_mode() == "numbers":
            if self.detected_digit is not None:
                result = TranslationResult(
                    format_digit(self.detected_digit),
                    self.digit_stability,
                    "\u062a\u0645 \u0627\u0644\u062a\u0639\u0631\u0641 \u0639\u0644\u0649 \u0627\u0644\u0631\u0642\u0645 \u0628\u0639\u062f \u062b\u0628\u0627\u062a \u0627\u0644\u0625\u0634\u0627\u0631\u0629.",
                    "number",
                    True,
                )
            else:
                result = TranslationResult(
                    None,
                    self.digit_stability or None,
                    "\u0644\u0645 \u064a\u062b\u062a \u0631\u0642\u0645. \u0627\u0639\u0631\u0636 \u0625\u0634\u0627\u0631\u0629 \u0648\u0627\u062d\u062f\u0629 \u0628\u0648\u0636\u0648\u062d \u0623\u0645\u0627\u0645 \u0627\u0644\u0643\u0627\u0645\u064a\u0631\u0627.",
                    "number",
                    False,
                )
            self.result_ready.emit(result)
            return
        if self.sequence and self.engine.mode == "model":
            self.result.setText("Processing… جارٍ تنفيذ الاستدلال")
            self.start.setEnabled(False)
            self.inference_thread = InferenceThread(
                self.engine, list(self.sequence), list(self.timestamps), self
            )
            self.inference_thread.completed.connect(self.finish_inference)
            self.inference_thread.start()
        else:
            # Stop always leads to a result page, including a clear tracker or
            # model diagnostic when no SF1 sequence was captured.
            self.result_ready.emit(self.engine.classify(None))

    def update_frame(self, image: QImage):
        pixmap = QPixmap.fromImage(image).scaled(self.video.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.video.setPixmap(pixmap)

    def update_camera_status(self, active: bool, message: str):
        color = COLORS['success'] if active else COLORS['danger']
        self.camera_status.setText(f"● الكاميرا: {message}")
        self.camera_status.setStyleSheet(f"color:{color}")
        if not active:
            self.start.setEnabled(True)
            self.stop.setEnabled(False)

    def consume_feature(self, payload):
        feature, timestamp_ms, digit = payload
        if feature is not None:
            self.sequence.append(feature)
            self.timestamps.append(timestamp_ms)
        if self.current_mode() == "numbers":
            stable, stability = self.number_stabilizer.update(digit)
            self.digit_stability = stability
            if stable is not None:
                self.detected_digit = stable
                arabic_digit = format_digit(stable)
                self.number_preview.setText(arabic_digit)
                self.result.setText(f"\u0627\u0644\u0631\u0642\u0645 \u0627\u0644\u0645\u0643\u062a\u0634\u0641: {arabic_digit}")
            else:
                self.number_preview.setText("\u2026")
                self.result.setText("\u062b\u0628\u0651\u062a \u064a\u062f\u0643 \u0644\u062d\u0638\u0629 \u0623\u0645\u0627\u0645 \u0627\u0644\u0643\u0627\u0645\u064a\u0631\u0627")

    def current_mode(self):
        return self.mode_selector.currentData() or "sentences"

    def change_recognition_mode(self):
        numbers = self.current_mode() == "numbers"
        self.number_preview.setVisible(numbers)
        self.demo_phrase.setEnabled(not numbers)
        self.number_stabilizer.reset()
        self.detected_digit = None
        self.digit_stability = 0.0
        self.result.setText(
            "\u0627\u0639\u0631\u0636 \u0631\u0642\u0645\u064b\u0627 \u0645\u0646 \u0660 \u0625\u0644\u0649 \u0669"
            if numbers
            else "\u0644\u0627 \u062a\u0648\u062c\u062f \u0646\u062a\u064a\u062c\u0629 \u0628\u0639\u062f"
        )

    def finish_inference(self, result):
        self.start.setEnabled(True)
        self.model_status.setText(f"● النموذج: {self.engine.status}")
        self.result_ready.emit(result)
        self.sequence.clear()
        self.timestamps.clear()
        self.inference_thread = None

    def run_demo(self):
        self.result_ready.emit(self.engine.simulate(self.demo_phrase.currentText()))

    def reset(self):
        self.sequence.clear()
        self.timestamps.clear()
        self.number_stabilizer.reset()
        self.detected_digit = None
        self.digit_stability = 0.0
        self.number_preview.setText("\u2014")
        self.result.setText("لا توجد نتيجة مؤكدة")

    def shutdown(self):
        self.stop_camera()


class ResultPage(QWidget):
    retry_requested = Signal()
    camera_requested = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(170, 100, 170, 100)
        title = QLabel("نتيجة الترجمة")
        title.setObjectName("title")
        self.phrase = QLabel("—")
        self.phrase.setObjectName("result")
        self.phrase.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.confidence = QLabel("")
        self.confidence.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status = QLabel("")
        self.status.setObjectName("muted")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        buttons = QHBoxLayout()
        retry = QPushButton("إعادة المحاولة")
        retry.clicked.connect(self.retry_requested)
        back = QPushButton("العودة للكاميرا")
        back.setObjectName("primary")
        back.clicked.connect(self.camera_requested)
        buttons.addStretch()
        buttons.addWidget(retry)
        buttons.addWidget(back)
        buttons.addStretch()
        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(self.phrase)
        layout.addWidget(self.confidence)
        layout.addWidget(self.status)
        layout.addStretch()
        layout.addLayout(buttons)

    def show_result(self, result: TranslationResult):
        self.phrase.setText(result.phrase or "إشارة غير معروفة")
        self.confidence.setText(
            f"ثقة النموذج: {result.confidence:.1%}" if result.confidence is not None else "لا توجد درجة ثقة في وضع المحاكاة"
        )
        self.status.setText(result.status)


class AboutPage(QWidget):
    back_requested = Signal()

    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(70, 38, 70, 38)
        header = QHBoxLayout()
        title = QLabel("عن المشروع")
        title.setObjectName("title")
        back = QPushButton("العودة")
        back.clicked.connect(self.back_requested)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(back)
        root.addLayout(header)
        card = QFrame()
        card.setObjectName("card")
        grid = QGridLayout(card)
        grid.setContentsMargins(28, 24, 28, 24)
        details = [
            ("Project Title", PROJECT_TITLE),
            ("Course", COURSE_NAME),
            ("Course Code", COURSE_CODE),
            ("Instructor", INSTRUCTOR),
            ("Technology Stack", "Python, PySide6, OpenCV, MediaPipe optional, SQLite, NumPy"),
            ("System", "Camera Input → Frame Processing → Hand Landmarks → Sequence Normalization → Neural Classification → Arabic Result"),
        ]
        for row, (key, value) in enumerate(details):
            key_label = QLabel(key)
            key_label.setStyleSheet(f"color:{COLORS['accent']};font-weight:700")
            value_label = QLabel(value)
            value_label.setWordWrap(True)
            grid.addWidget(key_label, row, 0)
            grid.addWidget(value_label, row, 1)
        student_text = "\n".join(f"{name}    {student_id}" for name, student_id in STUDENTS)
        students = QLabel(student_text)
        students.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        students.setStyleSheet("line-height:1.5")
        grid.addWidget(QLabel("Student Team"), len(details), 0)
        grid.addWidget(students, len(details), 1)
        root.addWidget(card, 1)


class GuidePage(QWidget):
    """Visual reference supplied by the user; it is not an AI training set."""

    back_requested = Signal()

    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(42, 28, 42, 32)

        header = QHBoxLayout()
        title = QLabel("دليل الإشارات")
        title.setObjectName("title")
        back = QPushButton("العودة للكاميرا")
        back.clicked.connect(self.back_requested)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(back)
        root.addLayout(header)

        notice = QLabel(
            "دليل مرجعي للتعلّم والعرض فقط. لا يعرض التطبيق هذه الإشارات كنتيجة ذكاء "
            "اصطناعي إلا إذا كانت مدعومة ومتحققًا منها داخل النموذج."
        )
        notice.setWordWrap(True)
        notice.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        notice.setStyleSheet(
            f"background:#172238;border:1px solid {COLORS['warning']};"
            f"border-radius:14px;padding:14px;color:{COLORS['warning']};font-weight:650"
        )
        root.addWidget(notice)

        tabs = QTabWidget()
        assets = ASSET_DIR / "sign_guides"
        tabs.addTab(
            self._image_tab(
                assets / "social_signs.png",
                "عبارات يومية: مرحبًا، لا، موافق، عمل جيد، سؤال وغيرها.",
            ),
            "عبارات يومية",
        )
        tabs.addTab(
            self._image_tab(
                assets / "cashier_signs.png",
                "إشارات مرجعية مرتبطة بالمشروبات وخدمة الكاشير.",
            ),
            "إشارات الكاشير",
        )
        root.addWidget(tabs, 1)

    def _image_tab(self, image_path: Path, description: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        description_label = QLabel(description)
        description_label.setObjectName("muted")
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(description_label)

        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setStyleSheet("background:#F7F7F4;border-radius:18px;padding:12px")
        pixmap = QPixmap(str(image_path))
        if pixmap.isNull():
            image_label.setText(f"تعذر تحميل صورة الدليل:\n{image_path.name}")
            image_label.setStyleSheet(
                f"background:#0B1726;border:1px solid {COLORS['danger']};"
                "border-radius:18px;padding:30px"
            )
        else:
            image_label.setPixmap(
                pixmap.scaled(
                    1080,
                    720,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(image_label)
        layout.addWidget(scroll, 1)
        return page


class IsharaWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1280, 780)
        self.setMinimumSize(1050, 680)
        self.setStyleSheet(STYLE)
        self.auth = AuthService(DB_PATH)
        self.auth.initialize(DEMO_USERNAME, DEMO_PASSWORD)
        self.session = Session()
        self.engine = TranslationEngine(MODEL_DIR)
        self.stack = QStackedWidget()
        self.login_page = LoginPage(self.auth)
        self.translation_page = TranslationPage(self.engine)
        self.result_page = ResultPage()
        self.guide_page = GuidePage()
        self.about_page = AboutPage()
        for page in (
            self.login_page,
            self.translation_page,
            self.result_page,
            self.guide_page,
            self.about_page,
        ):
            self.stack.addWidget(page)
        self.setCentralWidget(self.stack)
        self.login_page.authenticated.connect(self.on_login)
        self.translation_page.logout_requested.connect(self.logout)
        self.translation_page.about_requested.connect(lambda: self.stack.setCurrentWidget(self.about_page))
        self.translation_page.guide_requested.connect(lambda: self.stack.setCurrentWidget(self.guide_page))
        self.translation_page.result_ready.connect(self.show_result)
        self.result_page.retry_requested.connect(self.retry)
        self.result_page.camera_requested.connect(lambda: self.stack.setCurrentWidget(self.translation_page))
        self.about_page.back_requested.connect(lambda: self.stack.setCurrentWidget(self.translation_page))
        self.guide_page.back_requested.connect(lambda: self.stack.setCurrentWidget(self.translation_page))

    def on_login(self, user):
        self.session.login(user)
        self.stack.setCurrentWidget(self.translation_page)

    def show_result(self, result):
        self.result_page.show_result(result)
        self.stack.setCurrentWidget(self.result_page)

    def retry(self):
        self.translation_page.reset()
        self.stack.setCurrentWidget(self.translation_page)

    def logout(self):
        self.translation_page.shutdown()
        self.session.logout()
        self.stack.setCurrentWidget(self.login_page)

    def closeEvent(self, event):
        self.translation_page.shutdown()
        super().closeEvent(event)


def run(smoke_seconds: float | None = None) -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    window = IsharaWindow()
    window.show()
    if smoke_seconds:
        from PySide6.QtCore import QTimer
        QTimer.singleShot(int(smoke_seconds * 1000), window.close)
        QTimer.singleShot(int(smoke_seconds * 1000 + 150), app.quit)
    return app.exec()
