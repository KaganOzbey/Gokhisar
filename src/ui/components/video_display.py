"""
Video Görüntüleme Bileşeni

UDP üzerinden gelen video frame'lerini gösterir.
OpenCV ile frame işleme ve QLabel üzerine çizim yapılır.

Neden QLabel?
- QVideoWidget'tan daha esnek
- OpenCV ile doğrudan entegrasyon
- Hedef işaretleme, overlay çizimi kolay
"""

from typing import Optional

from PySide6.QtWidgets import QLabel, QFrame, QVBoxLayout, QHBoxLayout, QSizePolicy, QWidget
from PySide6.QtCore import Qt, Slot, QSize, Signal
from PySide6.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QBrush, QFont

from src.ui.styles import Styles
from src.utils.config import ModelConfig


class VideoDisplay(QFrame):
    """
    Video görüntüleme widget'ı
    
    Özellikler:
    - UDP'den gelen frame'leri gösterme
    - Hedef işaretçisi (crosshair) çizimi
    - Hedef kutusu (bounding box) çizimi
    - FPS göstergesi
    
    Kullanım:
        video = VideoDisplay()
        udp_worker.frame_received.connect(video.update_frame)
    """

    # Decode/işleme sırasında oluşan hataları üst katmana yayınlar.
    # MainWindow bunu LogPanel'e bağlar — kullanıcı print yerine
    # arayüzde hata mesajını görür ("error transparency" prensibi).
    error_occurred = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Hedef bilgileri
        self._target_box = None      # (x, y, w, h) tuple
        self._crosshair_pos = None   # (x, y) tuple
        self._show_crosshair = True

        self._last_pixmap = None

        # YOLO detection'ları (DetectionWorker tarafından setlenir)
        # Tipini import etmek döngüsel import riskine sokar; "Any" gibi tutuyoruz.
        self._detections = None         # DetectionFrame | None
        self._show_detections: bool = True
        self._last_frame_size: Optional[tuple[int, int]] = None  # (w, h)

        # Hata raporlamayı rate-limit eden tampon. Aynı mesajı 30 fps'de
        # her frame için tekrar tekrar bağırırsak log paneli işe yaramaz hâle
        # gelir. Bu yüzden son hatayı hatırlayıp aynısı tekrarlanırsa
        # sessizce yutuyoruz; farklı bir hata gelirse yeniden raporlarız.
        self._last_error_msg: Optional[str] = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI oluştur"""
        self.setStyleSheet(Styles.PANEL)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)
        
        # Video gösterme alanı
        self.video_label = QLabel()
        self.video_label.setStyleSheet(Styles.VIDEO_DISPLAY)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_label.setMinimumSize(520, 360)
        self.video_label.setText("VIDEO BEKLENİYOR...")
        self.video_label.setScaledContents(False)
        layout.addWidget(self.video_label, stretch=1)
        
        # Alt bilgi paneli
        info_bar = QWidget()
        info_bar.setFixedHeight(36)
        info_layout = QHBoxLayout(info_bar)
        info_layout.setContentsMargins(6, 0, 6, 0)
        
        self.fps_label = QLabel("FPS: --")
        self.fps_label.setStyleSheet(Styles.SUBTITLE_LABEL)
        
        self.resolution_label = QLabel("Çözünürlük: --")
        self.resolution_label.setStyleSheet(Styles.SUBTITLE_LABEL)
        
        info_layout.addWidget(self.fps_label)
        info_layout.addStretch()
        info_layout.addWidget(self.resolution_label)
        layout.addWidget(info_bar, stretch=0)
    
    @Slot(bytes)
    def update_frame_from_bytes(self, frame_data: bytes):
        """
        Raw bytes'dan frame güncelle (UDP'den gelen veri).

        Bu slot, GStreamerVideoWorker.frame_received signal'ına bağlanır.
        Gelen bytes tam bir JPEG karesidir (depay edilmiş). Burada cv2.imdecode
        ile RGB matrise çeviririz.
        """
        try:
            import numpy as np
            import cv2

            np_arr = np.frombuffer(frame_data, dtype=np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if frame is None:
                self._report_error("JPEG decode başarısız (bozuk paket olabilir)")
                return

            self.update_frame(frame)

        except Exception as e:
            # Tipik hata: NumPy/OpenCV ABI uyumsuzluğu —
            # "AttributeError: _ARRAY_API not found"
            self._report_error(f"Frame decode hatası: {type(e).__name__}: {e}")

    def _report_error(self, message: str) -> None:
        """
        Hata mesajını sinyal yoluyla bir kez yayınla.
        Aynı hatanın 30 fps'de tekrarlanmasını engellemek için son
        mesajla karşılaştırırız (rate-limit).
        """
        if message == self._last_error_msg:
            return
        self._last_error_msg = message
        self.video_label.setText(f"VIDEO HATASI\n{message}")
        self.video_label.setPixmap(QPixmap())  # Önceki frame'i temizle
        self.error_occurred.emit(message)
    
    def update_frame(self, frame):
        """
        OpenCV frame'i (numpy array) göster

        Args:
            frame: BGR formatında numpy array (OpenCV standardı)
        """
        try:
            import cv2

            # BGR -> RGB dönüşümü (Qt RGB bekler)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            self._last_frame_size = (w, h)

            # NumPy array -> QImage
            # Not: rgb_frame numpy buffer'ına bağlıyız; QImage.copy() ile
            # detach etmezsek next call'da bellek değişir → görsel bozulur.
            q_img = QImage(
                rgb_frame.data,
                w, h,
                bytes_per_line,
                QImage.Format_RGB888
            ).copy()

            # Crosshair, hedef kutusu, ve YOLO detection'ları çiz
            if self._show_crosshair or self._target_box or (self._show_detections and self._detections):
                q_img = self._draw_overlays(q_img)

            self._last_pixmap = QPixmap.fromImage(q_img)
            self._render_pixmap()

            # Çözünürlük güncelle
            self.resolution_label.setText(f"Çözünürlük: {w}x{h}")

            # Bir frame başarıyla gösterildiğinde önceki hata "iyileşmiş"
            # demektir. Yeni bir hata oluşursa tekrar raporlanabilsin diye
            # tamponu sıfırlıyoruz.
            self._last_error_msg = None

        except Exception as e:
            self._report_error(f"Frame gösterme hatası: {type(e).__name__}: {e}")

    def _render_pixmap(self):
        if not self._last_pixmap:
            return
        target_size = self.video_label.size()
        if target_size.width() <= 0 or target_size.height() <= 0:
            return

        scaled = self._last_pixmap.scaled(
            target_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.video_label.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._render_pixmap()
    
    def _draw_overlays(self, q_img: QImage) -> QImage:
        """Crosshair, hedef kutusu ve YOLO detection bbox'larını çiz."""
        img = q_img.copy()
        painter = QPainter(img)

        # Crosshair çiz (merkez)
        if self._show_crosshair:
            pen = QPen(QColor(0, 255, 0), 2)
            painter.setPen(pen)

            center_x = img.width() // 2
            center_y = img.height() // 2
            size = 30

            painter.drawLine(center_x - size, center_y, center_x + size, center_y)
            painter.drawLine(center_x, center_y - size, center_x, center_y + size)
            painter.drawEllipse(center_x - 5, center_y - 5, 10, 10)

        # Hedef kutusu çiz (manuel set_target_box ile gelen)
        if self._target_box:
            x, y, w, h = self._target_box
            pen = QPen(QColor(255, 0, 0), 3)
            painter.setPen(pen)
            painter.drawRect(x, y, w, h)
            painter.drawText(x, y - 5, "HEDEF")

        # YOLO detection bounding box'ları
        if self._show_detections and self._detections:
            self._draw_detections(painter, img.width(), img.height())

        painter.end()
        return img

    def _draw_detections(self, painter: QPainter, img_w: int, img_h: int):
        """
        DetectionFrame içindeki bbox'ları çiz.

        Detection bbox'ları orijinal frame piksellerinde (decode boyutu)
        verildiği için, şu an gösterdiğimiz frame ile detection'ın frame
        boyutu farklıysa scale-back uygulamamız gerekir. Yayıncı çözünürlük
        değiştirmedikçe ikisi aynı olur.
        """
        det_frame = self._detections
        if not det_frame or not det_frame.detections:
            return

        # Eğer detection farklı çözünürlükte yapıldıysa orantılı scale et.
        sx = img_w / det_frame.frame_width if det_frame.frame_width else 1.0
        sy = img_h / det_frame.frame_height if det_frame.frame_height else 1.0

        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        painter.setFont(font)
        fm = painter.fontMetrics()

        for det in det_frame.detections:
            x1, y1, x2, y2 = det.bbox_xyxy
            x1 *= sx; x2 *= sx
            y1 *= sy; y2 *= sy

            color_rgb = ModelConfig.CLASS_COLORS.get(
                det.cls_name, ModelConfig.DEFAULT_COLOR
            )
            color = QColor(*color_rgb)

            # Bounding box
            pen = QPen(color, 2)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(int(x1), int(y1), int(x2 - x1), int(y2 - y1))

            # Etiket: "iha 0.87"
            label = f"{det.cls_name} {det.confidence:.2f}"
            text_w = fm.horizontalAdvance(label) + 8
            text_h = fm.height() + 4

            # Etiket arka planı (okunurluk için yarı saydam)
            bg_color = QColor(color)
            bg_color.setAlpha(180)
            painter.setBrush(QBrush(bg_color))
            painter.setPen(Qt.NoPen)

            label_y = int(y1) - text_h
            if label_y < 0:           # Tepeye yakınsa içeri al
                label_y = int(y1) + 2
            painter.drawRect(int(x1), label_y, text_w, text_h)

            # Etiket metni
            painter.setPen(QPen(QColor(0, 0, 0)))
            painter.drawText(int(x1) + 4, label_y + fm.ascent() + 2, label)
    
    @Slot(int, int, int, int)
    def set_target_box(self, x: int, y: int, w: int, h: int):
        """Hedef kutusunu ayarla"""
        self._target_box = (x, y, w, h)
    
    @Slot()
    def clear_target_box(self):
        """Hedef kutusunu temizle"""
        self._target_box = None
    
    @Slot(bool)
    def set_crosshair_visible(self, visible: bool):
        """Crosshair görünürlüğünü ayarla"""
        self._show_crosshair = visible
    
    @Slot(int)
    def update_fps(self, fps: int):
        """FPS değerini güncelle"""
        self.fps_label.setText(f"FPS: {fps}")

    @Slot(object)
    def set_detections(self, detection_frame):
        """
        DetectionWorker.detections_ready sinyaline bağlanır.

        Burada gelen ``detection_frame`` parametresi DetectionFrame tipinde
        bir nesnedir; biz tipi import etmemek için ``object`` olarak
        anotluyoruz (döngüsel import'tan kaçınmak için).

        Detection'lar bir sonraki frame çiziminde overlay olarak görünür.
        """
        self._detections = detection_frame
        # Eğer elimizdeki son pixmap üzerine yeniden çizmek istersek frame
        # yeniden render edilmeli. En basit yöntem: son frame'i tekrar
        # paint döngüsüne sokmak. Hız için yeni frame gelene kadar
        # beklemeyi seçiyoruz; bir sonraki frame'de çizilir.
        # (30 fps'de bu en fazla 33 ms gecikme demektir.)

        # Inference süresi varsa fps_label'a yaz (UX için faydalı)
        try:
            inf_ms = float(getattr(detection_frame, "inference_ms", 0.0))
            n = len(getattr(detection_frame, "detections", []) or [])
            self.fps_label.setText(
                f"Inference: {inf_ms:.0f} ms | Tespit: {n}"
            )
        except Exception:
            pass

    @Slot(bool)
    def set_detections_visible(self, visible: bool):
        """Detection bbox'larını göster/gizle (kısayolla bağlanabilir)."""
        self._show_detections = visible
    
    def show_placeholder(self, message: str = "VIDEO BEKLENİYOR..."):
        """Placeholder mesajı göster"""
        self._last_pixmap = None
        self.video_label.clear()
        self.video_label.setText(message)
