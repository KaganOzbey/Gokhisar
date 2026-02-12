"""
Durum Paneli Bileşeni

Bağlantı durumu, mod bilgisi ve sistem uyarılarını gösteren panel.
Modüler yapıda - ana pencereye widget olarak eklenir.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGroupBox
)
from PySide6.QtCore import Qt, Slot

from src.ui.styles import Styles


class StatusIndicator(QLabel):
    """
    Tek bir durum göstergesi (LED benzeri)
    
    Kullanım:
        indicator = StatusIndicator("Bağlantı")
        indicator.set_status(True)  # Yeşil
        indicator.set_status(False) # Kırmızı
    """
    
    def __init__(self, label_text: str, parent=None):
        super().__init__(parent)
        self._label_text = label_text
        self._is_ok = False
        self.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.setMinimumHeight(24)
        self._update_display()
    
    def _update_display(self):
        """Görünümü duruma göre güncelle"""
        if self._is_ok:
            icon = "●"
            status_text = "ONLINE"
        else:
            icon = "○"
            status_text = "OFFLINE"
        self.setText(f"{icon}  {self._label_text}: {status_text}")
        
        if self._is_ok:
            self.setStyleSheet(Styles.STATUS_LABEL_OK)
        else:
            self.setStyleSheet(Styles.STATUS_LABEL_WARNING)
    
    @Slot(bool)
    def set_status(self, is_ok: bool):
        """
        Durumu güncelle
        
        Bu bir Slot - Signal'dan çağrılabilir
        Örnek: worker.connection_status.connect(indicator.set_status)
        """
        self._is_ok = is_ok
        self._update_display()


class StatusPanel(QFrame):
    """
    Sistem durum paneli
    
    İçerik:
    - TCP bağlantı durumu
    - UDP video durumu  
    - Aktif mod gösterimi
    - Kritik bölge uyarısı
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """UI bileşenlerini oluştur"""
        self.setStyleSheet(Styles.PANEL)
        self.setMinimumWidth(280)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Başlık
        title = QLabel("SİSTEM DURUMU")
        title.setStyleSheet(Styles.TITLE_LABEL)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Bağlantı durumları
        connection_group = QGroupBox("Bağlantı")
        connection_group.setStyleSheet(Styles.GROUP_BOX)
        conn_layout = QVBoxLayout(connection_group)
        conn_layout.setContentsMargins(8, 6, 8, 8)
        conn_layout.setSpacing(4)
        
        self.tcp_indicator = StatusIndicator("TCP Kontrol")
        self.udp_indicator = StatusIndicator("UDP Video")
        
        conn_layout.addWidget(self.tcp_indicator)
        conn_layout.addWidget(self.udp_indicator)
        layout.addWidget(connection_group)
        
        # Mod durumu
        mode_group = QGroupBox("Çalışma Modu")
        mode_group.setStyleSheet(Styles.GROUP_BOX)
        mode_layout = QVBoxLayout(mode_group)
        mode_layout.setContentsMargins(8, 6, 8, 8)
        mode_layout.setSpacing(4)
        
        self.mode_label = QLabel("MANUEL")
        self.mode_label.setStyleSheet(Styles.STATUS_LABEL_OK)
        self.mode_label.setAlignment(Qt.AlignCenter)
        self.mode_label.setFixedHeight(30)
        mode_layout.addWidget(self.mode_label)
        layout.addWidget(mode_group)
        
        # Hedef durumu
        target_group = QGroupBox("Hedef Bilgisi")
        target_group.setStyleSheet(Styles.GROUP_BOX)
        target_layout = QVBoxLayout(target_group)
        target_layout.setContentsMargins(8, 6, 8, 8)
        target_layout.setSpacing(4)
        
        self.target_label = QLabel("HEDEF YOK")
        self.target_label.setStyleSheet(Styles.STATUS_LABEL_CAUTION)
        self.target_label.setAlignment(Qt.AlignCenter)
        self.target_label.setFixedHeight(30)
        target_layout.addWidget(self.target_label)
        
        self.target_type_label = QLabel("Tür: -")
        self.target_type_label.setStyleSheet(Styles.SUBTITLE_LABEL)
        target_layout.addWidget(self.target_type_label)
        layout.addWidget(target_group)
        
        # Menzil durumu
        range_group = QGroupBox("Menzil Durumu")
        range_group.setStyleSheet(Styles.GROUP_BOX)
        range_layout = QVBoxLayout(range_group)
        range_layout.setContentsMargins(8, 6, 8, 8)
        range_layout.setSpacing(6)
        
        # Mesafe göstergesi
        self.distance_label = QLabel("Mesafe: - km")
        self.distance_label.setStyleSheet("""
            QLabel {
                color: #00ff00;
                font-size: 18px;
                font-weight: bold;
                padding: 8px;
                background-color: #1a1a2e;
                border: 1px solid #333;
                border-radius: 4px;
            }
        """)
        self.distance_label.setAlignment(Qt.AlignCenter)
        range_layout.addWidget(self.distance_label)
        
        # Menzil bantları (5m, 10m, 15m)
        bands_layout = QHBoxLayout()
        bands_layout.setSpacing(4)
        
        self.range_5m = QLabel("5m")
        self.range_10m = QLabel("10m")
        self.range_15m = QLabel("15m")
        
        for label in [self.range_5m, self.range_10m, self.range_15m]:
            label.setAlignment(Qt.AlignCenter)
            label.setFixedHeight(28)
            label.setStyleSheet("""
                QLabel {
                    color: #888;
                    background-color: #2a2a3e;
                    border: 1px solid #444;
                    border-radius: 3px;
                    font-size: 11px;
                    padding: 2px 8px;
                }
            """)
            bands_layout.addWidget(label)
        
        range_layout.addLayout(bands_layout)
        
        # Menzil durumu etiketi
        self.range_status_label = QLabel("Bekleniyor...")
        self.range_status_label.setStyleSheet(Styles.SUBTITLE_LABEL)
        self.range_status_label.setAlignment(Qt.AlignCenter)
        range_layout.addWidget(self.range_status_label)
        
        layout.addWidget(range_group)
        
        # Kritik bölge uyarısı
        self.critical_warning = QLabel("⚠ KRİTİK BÖLGE")
        self.critical_warning.setStyleSheet(Styles.STATUS_LABEL_WARNING)
        self.critical_warning.setAlignment(Qt.AlignCenter)
        self.critical_warning.setVisible(False)  # Varsayılan: gizli
        layout.addWidget(self.critical_warning)
        
        layout.addStretch()
    
    @Slot(str)
    def set_mode(self, mode: str):
        """Aktif modu güncelle"""
        self.mode_label.setText(mode.upper())
    
    @Slot(bool)
    def set_tcp_status(self, connected: bool):
        """TCP bağlantı durumunu güncelle"""
        self.tcp_indicator.set_status(connected)
    
    @Slot(bool)
    def set_udp_status(self, connected: bool):
        """UDP bağlantı durumunu güncelle"""
        self.udp_indicator.set_status(connected)
    
    @Slot(str, str)
    def set_target_info(self, status: str, target_type: str = ""):
        """Hedef bilgisini güncelle"""
        self.target_label.setText(status)
        self.target_type_label.setText(f"Tür: {target_type}" if target_type else "Tür: -")
        
        # Düşman hedefinde kırmızı, dost hedefinde yeşil
        if "DÜŞMAN" in target_type.upper():
            self.target_label.setStyleSheet(Styles.STATUS_LABEL_WARNING)
        elif "DOST" in target_type.upper():
            self.target_label.setStyleSheet(Styles.STATUS_LABEL_OK)
        else:
            self.target_label.setStyleSheet(Styles.STATUS_LABEL_CAUTION)
    
    @Slot(bool)
    def set_critical_zone_warning(self, is_critical: bool):
        """Kritik bölge uyarısını göster/gizle"""
        self.critical_warning.setVisible(is_critical)
    
    @Slot(float)
    def set_target_distance(self, distance_m: float):
        """
        Hedef mesafesini güncelle
        
        Args:
            distance_m: Mesafe (metre cinsinden)
        """
        distance_m = distance_m  # Zaten metre cinsinden
        self.distance_label.setText(f"Mesafe: {distance_m:.1f} m")
        
        # Menzil bantlarını güncelle
        self._update_range_bands(distance_m)
        
        # Menzil durumunu güncelle
        if distance_m <= 5:
            self.range_status_label.setText("✅ YAKIN MENZİL - Angajman Öncelikli")
            self.range_status_label.setStyleSheet("color: #00ff00; font-weight: bold;")
            self.distance_label.setStyleSheet(self.distance_label.styleSheet().replace("#00ff00", "#ff0000"))
        elif distance_m <= 10:
            self.range_status_label.setText("⚠️ ORTA MENZİL - Takipte")
            self.range_status_label.setStyleSheet("color: #ffaa00; font-weight: bold;")
            self.distance_label.setStyleSheet(self.distance_label.styleSheet().replace("#ff0000", "#ffaa00").replace("#00ff00", "#ffaa00"))
        elif distance_m <= 15:
            self.range_status_label.setText("🟡 UZAK MENZİL - İzleniyor")
            self.range_status_label.setStyleSheet("color: #ffff00;")
            self.distance_label.setStyleSheet(self.distance_label.styleSheet().replace("#ffaa00", "#ffff00").replace("#ff0000", "#ffff00"))
        else:
            self.range_status_label.setText("⚪ MENZİL DIŞI")
            self.range_status_label.setStyleSheet("color: #888;")
            self.distance_label.setStyleSheet(self.distance_label.styleSheet().replace("#ffff00", "#888").replace("#ffaa00", "#888").replace("#ff0000", "#888"))
    
    def _update_range_bands(self, distance_m: float):
        """Menzil bantlarını görsel olarak güncelle"""
        # Aktif bantı vurgula
        active_style = """
            QLabel {
                color: #fff;
                background-color: #ff4444;
                border: 2px solid #ff0000;
                border-radius: 3px;
                font-size: 11px;
                font-weight: bold;
                padding: 2px 8px;
            }
        """
        inactive_style = """
            QLabel {
                color: #888;
                background-color: #2a2a3e;
                border: 1px solid #444;
                border-radius: 3px;
                font-size: 11px;
                padding: 2px 8px;
            }
        """
        
        # Tüm bantları sıfırla
        self.range_5m.setStyleSheet(inactive_style)
        self.range_10m.setStyleSheet(inactive_style)
        self.range_15m.setStyleSheet(inactive_style)
        
        # Aktif bantı vurgula
        if distance_m <= 5:
            self.range_5m.setStyleSheet(active_style)
        elif distance_m <= 10:
            self.range_10m.setStyleSheet(active_style.replace("#ff4444", "#ff8800").replace("#ff0000", "#ff6600"))
        elif distance_m <= 15:
            self.range_15m.setStyleSheet(active_style.replace("#ff4444", "#ffcc00").replace("#ff0000", "#ffaa00"))
    
    @Slot()
    def clear_target_distance(self):
        """Hedef mesafesini temizle"""
        self.distance_label.setText("Mesafe: - m")
        self.distance_label.setStyleSheet("""
            QLabel {
                color: #00ff00;
                font-size: 18px;
                font-weight: bold;
                padding: 8px;
                background-color: #1a1a2e;
                border: 1px solid #333;
                border-radius: 4px;
            }
        """)
        self.range_status_label.setText("Bekleniyor...")
        self.range_status_label.setStyleSheet(Styles.SUBTITLE_LABEL)
        
        # Bantları sıfırla
        inactive_style = """
            QLabel {
                color: #888;
                background-color: #2a2a3e;
                border: 1px solid #444;
                border-radius: 3px;
                font-size: 11px;
                padding: 2px 8px;
            }
        """
        self.range_5m.setStyleSheet(inactive_style)
        self.range_10m.setStyleSheet(inactive_style)
        self.range_15m.setStyleSheet(inactive_style)
