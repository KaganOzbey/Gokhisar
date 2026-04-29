"""
Ana Pencere (MainWindow) - GÖKHİSAR Yer Kontrol İstasyonu

Tüm UI bileşenlerini bir araya getiren ana pencere.
Worker thread'ler burada başlatılır ve signal/slot bağlantıları yapılır.

Mimari:
- Sol: Video görüntüleme
- Sağ üst: Durum paneli
- Sağ alt: Kontrol paneli
- Alt: Log paneli

Neden bu yapı?
- Operatör tek ekrandan tüm sistemi görebilir
- Kritik kontroller sağ tarafta (sağ el kullanımı için optimize)
- Log paneli detaylı bilgi için alt kısımda
"""

import sys
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMessageBox, QStatusBar, QSizePolicy
)
from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtGui import QGuiApplication  # Boyutlandırma görevi için eklendi

from src.utils.config import UIConfig, NetworkConfig, SystemConfig
from src.ui.styles import Styles
from src.ui.components.video_display import VideoDisplay
from src.ui.components.status_panel import StatusPanel
from src.ui.components.control_panel import ControlPanel
from src.ui.components.log_panel import LogPanel
from src.workers.network_worker import UDPVideoWorker, TCPCommandWorker
from src.workers.gstreamer_video_worker import GStreamerVideoWorker
from src.workers.detection_worker import DetectionWorker
from src.workers.target_simulator import TargetSimulator


class MainWindow(QMainWindow):
    """
    GÖKHİSAR Ana Pencere
    
    Sorumluluklar:
    1. UI bileşenlerini oluştur ve yerleştir
    2. Worker thread'leri başlat/durdur
    3. Signal/Slot bağlantılarını yönet
    4. Kullanıcı etkileşimlerini işle
    """
    
    def __init__(self):
        super().__init__()
        
        # Worker referansları
        # Not: _udp_worker artık GStreamer tabanlı (RTP/JPEG depay yapıyor).
        # Aynı sinyal sözleşmesini koruduğumuz için tip Union halinde tutulabilir.
        self._udp_worker: Optional[GStreamerVideoWorker] = None
        self._tcp_worker: Optional[TCPCommandWorker] = None
        self._detection_worker: Optional[DetectionWorker] = None
        self._target_simulator: Optional[TargetSimulator] = None
        
        # Sistem durumu
        self._current_mode = "MANUEL"
        
        # UI oluştur
        self._setup_window()
        self._setup_ui()
        self._setup_status_bar()
        self._setup_connections()
        
        # Başlangıç log'u
        self._log_system_info()
    
    def _setup_window(self):
        """Pencere ayarlarını yapılandır"""
        self.setWindowTitle(UIConfig.WINDOW_TITLE)
        
        # --- BOYUTLANDIRMA GÖREVE ENTEGRASYONU ---
        # Ekranın kullanılabilir yüksekliğini alıp dikeyde kilitliyoruz
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        full_height = screen_geometry.height()
        
        # Genişliği (target_w) 1150px olarak ayarlıyoruz
        target_w = 1150
        
        # Pencereyi ekranın tam boyuna (üstten alta) ayarla
        self.resize(target_w, full_height)
        
        # Minimum Değerler: Daha fazla küçülüp butonların ezilmesini engeller
        self.setMinimumWidth(target_w)      
        self.setMinimumHeight(full_height)  # Dikeyde ekran boyundan küçük olamaz (Kilitli)
        
        # Ekranın ortasına konumlandır
        self.move(screen_geometry.x() + (screen_geometry.width() - target_w) // 2, screen_geometry.y())
        # ------------------------------------------

        self.setStyleSheet(Styles.MAIN_WINDOW)
        
        # Tam ekran için F11 kısayolu
        # self.showMaximized()  # Opsiyonel: başlangıçta tam ekran
    
    def _setup_ui(self):
        """
        UI bileşenlerini oluştur ve yerleştir
        
        Layout yapısı:
        ┌─────────────────────────────────────────────┐
        │  ┌─────────────────┐ ┌───────────────────┐  │
        │  │                 │ │   Status Panel    │  │
        │  │                 │ ├───────────────────┤  │
        │  │  Video Display  │ │                   │  │
        │  │                 │ │  Control Panel    │  │
        │  │                 │ │                   │  │
        │  └─────────────────┘ └───────────────────┘  │
        │  ┌─────────────────────────────────────────┐│
        │  │            Log Panel                    ││
        │  └─────────────────────────────────────────┘│
        └─────────────────────────────────────────────┘
        """
        # Ana widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Ana dikey layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(4)
        main_layout.setContentsMargins(4, 4, 4, 4)
        
        # Üst Bölüm: Video (Sol) + Sağ Panel (Status + Control)
        upper_layout = QHBoxLayout()
        upper_layout.setSpacing(4)
        
        # 1. Video Görüntüleme (Sol - En çok alanı kaplar)
        self.video_display = VideoDisplay()
        self.video_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        upper_layout.addWidget(self.video_display, stretch=1)
        
        # 2. Sağ Panel Konteyneri (Dikey: Status + Control)
        right_panel_widget = QWidget()
        right_panel_widget.setFixedWidth(280)
        right_panel_layout = QVBoxLayout(right_panel_widget)
        right_panel_layout.setContentsMargins(0, 0, 0, 0)
        right_panel_layout.setSpacing(4)
        
        # Sistem Durumu
        self.status_panel = StatusPanel()
        self.status_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        right_panel_layout.addWidget(self.status_panel)
        
        # Kontrol Paneli
        self.control_panel = ControlPanel()
        self.control_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        right_panel_layout.addWidget(self.control_panel)

        # --- Boyutlandırma Görevi: Elemanları yukarı yaslamak için stretch ekle ---
        right_panel_layout.addStretch()
        
        upper_layout.addWidget(right_panel_widget, stretch=0)
        
        main_layout.addLayout(upper_layout, stretch=1)
        
        # Alt Bölüm: Log Paneli (Tam genişlik)
        self.log_panel = LogPanel()
        self.log_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.log_panel.setFixedHeight(160)
        main_layout.addWidget(self.log_panel, stretch=0)
    
    def _setup_status_bar(self):
        """Durum çubuğunu ayarla"""
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(Styles.STATUS_BAR)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("⚡ Sistem hazır - Bağlantı bekleniyor...")
    
    def _setup_connections(self):
        """
        Signal/Slot bağlantılarını kur
        """
        # Kontrol paneli signal'ları
        self.control_panel.mode_changed.connect(self._on_mode_changed)
        self.control_panel.fire_command.connect(self._on_fire_command)
        self.control_panel.servo_command.connect(self._on_servo_command) # SERVO KONTROLÜ BURADA

        # Video bileşeninin decode/işleme hatalarını log paneline yönlendir.
        # Önceden 'print' ile terminale yazılıyordu; arayüzden görülmüyordu.
        self.video_display.error_occurred.connect(self.log_panel.log_error)
    
    def _log_system_info(self):
        """Sistem bilgilerini logla"""
        info = SystemConfig.get_platform_info()
        self.log_panel.log_info(f"Platform: {info['platform']}")
        self.log_panel.log_info(f"Python: {info['python_version'].split()[0]}")
        self.log_panel.log_info(f"Seri Port: {info['serial_port']}")
        self.log_panel.log_info("GÖKHİSAR Yer Kontrol İstasyonu başlatıldı")
    
    # ==================== WORKER YÖNETİMİ ====================
    
    def start_udp_worker(self, port: int = None):
        """
        Video akışı worker'ını başlat.

        İçeride RTP/JPEG depay işini GStreamer'a yaptıran bir subprocess
        worker (GStreamerVideoWorker) kullanılır; UI tarafından bakıldığında
        eski UDPVideoWorker ile aynı sinyallere sahip olduğu için bu detay
        şeffaftır (Liskov Substitution).

        Aynı zamanda DetectionWorker'ı da başlatır ve frame_received sinyalini
        hem VideoDisplay'e hem de DetectionWorker'a "fan-out" eder. Böylece
        ekrana ham görüntü gösterilirken paralel olarak YOLO inference çalışır.
        """
        if self._udp_worker and self._udp_worker.isRunning():
            self.log_panel.log_warning("Video Worker zaten çalışıyor")
            return

        port = port or NetworkConfig.UDP_VIDEO_PORT

        # 1) Detection worker'ı önce başlat ki ilk frame geldiğinde hazır olsun.
        self._start_detection_worker()

        # 2) GStreamer video worker'ı kur
        self._udp_worker = GStreamerVideoWorker(port=port)
        self._udp_worker.frame_received.connect(self.video_display.update_frame_from_bytes)
        # Frame'i detection'a da yolla — ama submit_frame doğrudan slot olduğundan
        # Qt.DirectConnection ile çağırırsak GStreamer thread'inde yürür ve
        # mutex ile zaten korunuyor. Sinyal üzerinden de çalışır;
        # default Qt connection AutoConnection: aynı thread'deyse direct,
        # değilse queued. Submit_frame thread-safe olduğu için her iki yol da OK.
        if self._detection_worker is not None:
            self._udp_worker.frame_received.connect(self._detection_worker.submit_frame)

        self._udp_worker.connection_status.connect(self.status_panel.set_udp_status)
        self._udp_worker.status_changed.connect(self.log_panel.log_status)
        self._udp_worker.error_occurred.connect(self.log_panel.log_error)
        self._udp_worker.start_worker()
        self.log_panel.log_info(f"GStreamer Video Worker başlatıldı (UDP {port})")

    def _start_detection_worker(self):
        """
        YOLO detection worker'ını idempotent olarak başlat.

        Idempotent = "birden fazla çağrılırsa zarar vermez". F5 ile bağlantı
        yenilenirken yeniden çağrılır; modeli her seferinde yeniden yüklemek
        israf olur, bu yüzden çalışan worker varsa korur.
        """
        if self._detection_worker and self._detection_worker.isRunning():
            return
        self._detection_worker = DetectionWorker()
        self._detection_worker.detections_ready.connect(self.video_display.set_detections)
        self._detection_worker.status_changed.connect(self.log_panel.log_status)
        self._detection_worker.error_occurred.connect(self.log_panel.log_error)
        self._detection_worker.model_loaded.connect(self._on_model_loaded)
        self._detection_worker.start_worker()
        self.log_panel.log_info("YOLO Detection Worker başlatıldı")

    def stop_detection_worker(self):
        if self._detection_worker:
            self._detection_worker.stop_worker()
            self._detection_worker = None
            self.log_panel.log_info("Detection Worker durduruldu")

    @Slot(bool, str)
    def _on_model_loaded(self, ok: bool, info: str):
        if ok:
            self.log_panel.log_info(f"Model: {info}")
            self.status_bar.showMessage(f"Model: {info}")
        else:
            self.log_panel.log_error(f"Model: {info}")
            self.status_bar.showMessage("Model yüklenemedi")
    
    def stop_udp_worker(self):
        if self._udp_worker:
            self._udp_worker.stop_worker()
            self._udp_worker = None
            self.log_panel.log_info("Video Worker durduruldu")
    
    def start_tcp_worker(self, host: str = None, port: int = None):
        if self._tcp_worker and self._tcp_worker.isRunning():
            self.log_panel.log_warning("TCP Worker zaten çalışıyor")
            return
        
        host = host or NetworkConfig.RPI_HOST
        port = port or NetworkConfig.TCP_COMMAND_PORT
        self._tcp_worker = TCPCommandWorker(host=host, port=port)
        self._tcp_worker.connection_status.connect(self.status_panel.set_tcp_status)
        self._tcp_worker.status_changed.connect(self.log_panel.log_status)
        self._tcp_worker.error_occurred.connect(self.log_panel.log_error)
        self._tcp_worker.response_received.connect(self._on_tcp_response)
        self._tcp_worker.command_sent.connect(lambda msg: self.log_panel.log_info(msg))
        self._tcp_worker.start_worker()
        self.log_panel.log_info(f"TCP Worker başlatıldı ({host}:{port})")
    
    def stop_tcp_worker(self):
        if self._tcp_worker:
            self._tcp_worker.stop_worker()
            self._tcp_worker = None
            self.log_panel.log_info("TCP Worker durduruldu")
    
    def start_target_simulator(self):
        """Hedef simülasyonunu başlat"""
        if self._target_simulator and self._target_simulator.isRunning():
            self.log_panel.log_warning("Hedef simülasyonu zaten çalışıyor")
            return
        
        self._target_simulator = TargetSimulator()
        
        # Görev odaklı signal bağlantıları
        self._target_simulator.target_detected.connect(self.log_panel.log_target_detected)
        self._target_simulator.target_lost.connect(self.log_panel.log_target_lost)
        self._target_simulator.in_range.connect(self.log_panel.log_in_range)
        self._target_simulator.out_of_range.connect(self.log_panel.log_out_of_range)
        self._target_simulator.friendly_detected.connect(self.log_panel.log_friendly)
        self._target_simulator.hostile_detected.connect(self.log_panel.log_hostile)
        self._target_simulator.engagement_started.connect(self.log_panel.log_engagement_start)
        self._target_simulator.engagement_result.connect(self.log_panel.log_engagement_result)
        self._target_simulator.track_update.connect(self.log_panel.log_track_update)
        self._target_simulator.status_changed.connect(self.log_panel.log_status)
        
        # Menzil göstergesi bağlantısı
        self._target_simulator.distance_updated.connect(self.status_panel.set_target_distance)
        
        self._target_simulator.start_worker()
        self.log_panel.log_info("🎯 Hedef simülasyonu başlatıldı")
        self.status_bar.showMessage("Hedef simülasyonu aktif")
    
    def stop_target_simulator(self):
        """Hedef simülasyonunu durdur"""
        if self._target_simulator:
            self._target_simulator.stop_worker()
            self._target_simulator = None
            self.log_panel.log_info("Hedef simülasyonu durduruldu")
            self.status_panel.clear_target_distance()
    
    def toggle_target_simulator(self):
        """Hedef simülasyonunu aç/kapat"""
        if self._target_simulator and self._target_simulator.isRunning():
            self.stop_target_simulator()
        else:
            self.start_target_simulator()
    
    # ==================== SLOT'LAR ====================
    
    @Slot(str)
    def _on_mode_changed(self, mode: str):
        self._current_mode = mode
        self.status_panel.set_mode(mode)
        self.log_panel.log_info(f"Mod değiştirildi: {mode}")
        self.status_bar.showMessage(f"Aktif Mod: {mode}")
        if self._tcp_worker and self._tcp_worker.isRunning():
            self._tcp_worker.send_command_json("MODE", {"mode": mode})
    
    @Slot()
    def _on_fire_command(self):
        self.log_panel.log_warning("🔥 ATEŞ KOMUTU VERİLDİ!")
        if self._tcp_worker and self._tcp_worker.isRunning():
            self._tcp_worker.send_command_binary(command_id=2, x=0, y=0, flags=1)
        else:
            self.log_panel.log_error("TCP bağlantısı yok - Ateş komutu gönderilemedi!")
    
    @Slot(int, int)
    def _on_servo_command(self, x: int, y: int):
        if self._tcp_worker and self._tcp_worker.isRunning():
            self._tcp_worker.send_command_binary(command_id=1, x=x, y=y, flags=0)
    
    @Slot(dict)
    def _on_tcp_response(self, response: dict):
        """
        TCP yanıtlarını işle
        
        Beklenen yanıt formatı:
        {
            "status": "ok",
            "target_class": "İHA",           # Opsiyonel
            "is_friendly": false,             # Opsiyonel
            "target_box": [x, y, w, h]       # Opsiyonel
        }
        """
        self.log_panel.log_info(f"TCP Yanıt: {response}")
        
        if "status" in response:
            self.status_bar.showMessage(f"Raspberry Pi: {response['status']}")
        
        # Hedef Sınıflandırma ve IFF Verisi Parse
        if "target_class" in response and "is_friendly" in response:
            target_class = response["target_class"]
            is_friendly = response["is_friendly"]
            
            # VideoDisplay'e hedef bilgilerini gönder
            self.video_display.set_target_info(target_class, is_friendly)
            
            # StatusPanel'e güncelleme gönder
            self.status_panel.set_target_classification(target_class, is_friendly)
            
            # ControlPanel'e IFF durumunu gönder (DOST ise ateş kilidi)
            self.control_panel.set_friendly_target(is_friendly)
            
            # Log mesajı
            iff_status = "DOST" if is_friendly else "DÜŞMAN"
            self.log_panel.log_warning(f"🎯 Hedef Tespit: {target_class} ({iff_status})")
            
            # DOST hedef uyarısı
            if is_friendly:
                self.log_panel.log_warning("⚠️ DOST HEDEF - ATEŞ KİLİDİ AKTİF")
        
        # Hedef kutusu güncelleme (opsiyonel)
        if "target_box" in response:
            box = response["target_box"]
            if len(box) == 4:
                self.video_display.set_target_box(*box)
        
        # Hedef kaybedildi
        if response.get("target_lost", False):
            self._clear_target_data()
    
    def _clear_target_data(self):
        """Hedef verilerini temizle"""
        self.video_display.clear_target_box()
        self.status_panel.clear_target_info()
        self.control_panel.clear_target_lock()
        self.log_panel.log_info("Hedef kaybedildi")

    # ==================== PENCERE OLAYLARI ====================
    
    def closeEvent(self, event):
        # Worker kapanış sırası: önce frame üretici (UDP), sonra tüketici
        # (Detection). Aksi sırada detection halen frame işlerken UDP
        # kapanırsa sorun olmaz ama tersine kapatmak en güvenlisi.
        self.stop_udp_worker()
        self.stop_detection_worker()
        self.stop_tcp_worker()
        self.stop_target_simulator()
        event.accept()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F11:
            if self.isFullScreen(): self.showNormal()
            else: self.showFullScreen()
        elif event.key() == Qt.Key_Escape:
            if self.isFullScreen(): self.showNormal()
        elif event.key() == Qt.Key_F5:
            self._restart_connections()
        elif event.key() == Qt.Key_F6:
            self.toggle_target_simulator()
        else:
            super().keyPressEvent(event)
    
    def _restart_connections(self):
        self.stop_udp_worker()
        self.stop_tcp_worker()
        QTimer.singleShot(500, self.start_udp_worker)
        QTimer.singleShot(1000, self.start_tcp_worker)
