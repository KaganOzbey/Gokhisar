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
        
        # Hedef sınıfı ve ikon (yatay layout)
        class_layout = QHBoxLayout()
        class_layout.setSpacing(6)
        
        self.target_icon = QLabel("●")  # Varsayılan ikon
        self.target_icon.setStyleSheet("color: #4f83ff; font-size: 18px;")
        self.target_icon.setFixedWidth(24)
        class_layout.addWidget(self.target_icon)
        
        self.target_type_label = QLabel("Tür: -")
        self.target_type_label.setStyleSheet(Styles.TARGET_CLASS_LABEL)
        class_layout.addWidget(self.target_type_label, stretch=1)
        
        target_layout.addLayout(class_layout)
        
        # IFF (Dost/Düşman) Badge
        self.iff_badge = QLabel("BİLİNMİYOR")
        self.iff_badge.setStyleSheet(Styles.STATUS_LABEL_CAUTION)
        self.iff_badge.setAlignment(Qt.AlignCenter)
        self.iff_badge.setFixedHeight(32)
        target_layout.addWidget(self.iff_badge)
        
        layout.addWidget(target_group)
        
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
        
        # Hedef tipine göre ikon seçimi
        icon_map = {
            "Balistik Füze": "↑",
            "İHA": "✈",
            "Helikopter": "🚁",
            "Savaş Uçağı": "✈",
            "Mini/Micro İHA": "⚡",
        }
        
        icon = icon_map.get(target_type, "●")
        self.target_icon.setText(icon)
        
        # Düşman hedefinde kırmızı, dost hedefinde yeşil
        if "DÜŞMAN" in target_type.upper():
            self.target_label.setStyleSheet(Styles.STATUS_LABEL_WARNING)
        elif "DOST" in target_type.upper():
            self.target_label.setStyleSheet(Styles.STATUS_LABEL_OK)
        else:
            self.target_label.setStyleSheet(Styles.STATUS_LABEL_CAUTION)
    
    @Slot(str, bool)
    def set_target_classification(self, target_class: str, is_friendly: bool):
        """
        Hedef sınıflandırma ve IFF bilgisini güncelle
        
        Args:
            target_class: "Balistik Füze", "İHA", "Helikopter", vb.
            is_friendly: True=DOST, False=DÜŞMAN
        """
        # Hedef durumu güncelle
        self.target_label.setText("HEDEF TESPİT")
        
        # Sınıf bilgisi
        self.target_type_label.setText(f"Tür: {target_class}")
        
        # İkon seçimi
        icon_map = {
            "Balistik Füze": "↑",
            "İHA": "✈",
            "Helikopter": "🚁",
            "Savaş Uçağı": "✈",
            "Mini/Micro İHA": "⚡",
        }
        icon = icon_map.get(target_class, "●")
        self.target_icon.setText(icon)
        
        # IFF Badge güncelleme
        if is_friendly:
            self.iff_badge.setText("✓ DOST")
            self.iff_badge.setStyleSheet(Styles.IFF_BADGE_FRIENDLY)
            self.target_label.setStyleSheet(Styles.STATUS_LABEL_OK)
        else:
            self.iff_badge.setText("✕ DÜŞMAN")
            self.iff_badge.setStyleSheet(Styles.IFF_BADGE_HOSTILE)
            self.target_label.setStyleSheet(Styles.STATUS_LABEL_WARNING)
    
    @Slot()
    def clear_target_info(self):
        """Hedef bilgilerini temizle"""
        self.target_label.setText("HEDEF YOK")
        self.target_label.setStyleSheet(Styles.STATUS_LABEL_CAUTION)
        self.target_type_label.setText("Tür: -")
        self.target_icon.setText("●")
        self.iff_badge.setText("BİLİNMİYOR")
        self.iff_badge.setStyleSheet(Styles.STATUS_LABEL_CAUTION)
    
    @Slot(bool)
    def set_critical_zone_warning(self, is_critical: bool):
        """Kritik bölge uyarısını göster/gizle"""
        self.critical_warning.setVisible(is_critical)
