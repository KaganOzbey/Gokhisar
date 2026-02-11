"""
Video Görüntüleme Bileşeni

UDP üzerinden gelen video frame'lerini gösterir.
OpenCV ile frame işleme ve QLabel üzerine çizim yapılır.

Neden QLabel?
- QVideoWidget'tan daha esnek
- OpenCV ile doğrudan entegrasyon
- Hedef işaretleme, overlay çizimi kolay
"""

from PySide6.QtWidgets import QLabel, QFrame, QVBoxLayout, QHBoxLayout, QSizePolicy, QWidget
from PySide6.QtCore import Qt, Slot, QSize
from PySide6.QtGui import QImage, QPixmap, QPainter, QPen, QColor

from src.ui.styles import Styles


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
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Hedef bilgileri
        self._target_box = None      # (x, y, w, h) tuple
        self._crosshair_pos = None   # (x, y) tuple
        self._show_crosshair = True

        self._last_pixmap = None
        
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
        Raw bytes'dan frame güncelle (UDP'den gelen veri)
        
        Bu slot, UDPVideoWorker.frame_received signal'ına bağlanır.
        
        Not: Gerçek implementasyonda frame decode işlemi gerekecek.
        Furkan'ın simülasyonu ile test edilecek.
        """
        try:
            import numpy as np
            import cv2
            
            # Bytes'ı numpy array'e çevir
            np_arr = np.frombuffer(frame_data, dtype=np.uint8)
            
            # JPEG decode (GStreamer genelde JPEG gönderir)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            if frame is not None:
                self.update_frame(frame)
                
        except Exception as e:
            print(f"Frame decode hatası: {e}")
    
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
            
            # NumPy array -> QImage
            q_img = QImage(
                rgb_frame.data, 
                w, h, 
                bytes_per_line, 
                QImage.Format_RGB888
            )
            
            # Crosshair ve hedef kutusu çiz
            if self._show_crosshair or self._target_box:
                q_img = self._draw_overlays(q_img)
            
            self._last_pixmap = QPixmap.fromImage(q_img)
            self._render_pixmap()
            
            # Çözünürlük güncelle
            self.resolution_label.setText(f"Çözünürlük: {w}x{h}")
            
        except Exception as e:
            print(f"Frame gösterme hatası: {e}")

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
        """Crosshair ve hedef kutusu çiz"""
        img = q_img.copy()
        painter = QPainter(img)
        
        # Crosshair çiz (merkez)
        if self._show_crosshair:
            pen = QPen(QColor(0, 255, 0), 2)
            painter.setPen(pen)
            
            center_x = img.width() // 2
            center_y = img.height() // 2
            size = 30
            
            # Yatay çizgi
            painter.drawLine(center_x - size, center_y, center_x + size, center_y)
            # Dikey çizgi
            painter.drawLine(center_x, center_y - size, center_x, center_y + size)
            # Merkez daire
            painter.drawEllipse(center_x - 5, center_y - 5, 10, 10)
        
        # Hedef kutusu çiz
        if self._target_box:
            x, y, w, h = self._target_box
            pen = QPen(QColor(255, 0, 0), 3)
            painter.setPen(pen)
            painter.drawRect(x, y, w, h)
            
            # "HEDEF" yazısı
            painter.drawText(x, y - 5, "HEDEF")
        
        painter.end()
        return img
    
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
    
    def show_placeholder(self, message: str = "VIDEO BEKLENİYOR..."):
        """Placeholder mesajı göster"""
        self._last_pixmap = None
        self.video_label.clear()
        self.video_label.setText(message)
