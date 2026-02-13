"""
Kontrol Paneli Bileşeni

Manuel kontrol (servo), mod seçimi ve ateş kontrolü için panel.
Güvenlik: ATEŞ butonu varsayılan olarak kilitli.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGroupBox, QPushButton, QSlider, QButtonGroup, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot

from src.ui.styles import Styles


class ServoControlWidget(QFrame):
    """
    Servo motor kontrol widget'ı
    
    X ve Y ekseni için slider'lar ve değer göstergeleri.
    
    Signals:
    - servo_changed(x, y): Servo değerleri değiştiğinde emit edilir
    """
    
    servo_changed = Signal(int, int)  # x, y değerleri
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """UI oluştur"""
        self.setStyleSheet("background: transparent; border: none;")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # X ekseni (Azimuth)
        x_layout = QHBoxLayout()
        x_label = QLabel("Azimuth")
        x_label.setStyleSheet(Styles.SUBTITLE_LABEL)
        x_label.setMinimumWidth(60)
        
        self.x_slider = QSlider(Qt.Horizontal)
        self.x_slider.setRange(-180, 180)
        self.x_slider.setValue(0)
        self.x_slider.setStyleSheet(Styles.SLIDER)
        
        self.x_value = QLabel("0°")
        self.x_value.setStyleSheet(Styles.SUBTITLE_LABEL)
        self.x_value.setMinimumWidth(50)
        
        x_layout.addWidget(x_label)
        x_layout.addWidget(self.x_slider)
        x_layout.addWidget(self.x_value)
        layout.addLayout(x_layout)
        
        # Y ekseni (Elevation)
        y_layout = QHBoxLayout()
        y_label = QLabel("Elevation")
        y_label.setStyleSheet(Styles.SUBTITLE_LABEL)
        y_label.setMinimumWidth(60)
        
        self.y_slider = QSlider(Qt.Horizontal)
        self.y_slider.setRange(-90, 90)
        self.y_slider.setValue(0)
        self.y_slider.setStyleSheet(Styles.SLIDER)
        
        self.y_value = QLabel("0°")
        self.y_value.setStyleSheet(Styles.SUBTITLE_LABEL)
        self.y_value.setMinimumWidth(50)
        
        y_layout.addWidget(y_label)
        y_layout.addWidget(self.y_slider)
        y_layout.addWidget(self.y_value)
        layout.addLayout(y_layout)
        
        # Signal bağlantıları
        self.x_slider.valueChanged.connect(self._on_x_changed)
        self.y_slider.valueChanged.connect(self._on_y_changed)
    
    def _on_x_changed(self, value: int):
        """X slider değiştiğinde"""
        self.x_value.setText(f"{value}°")
        self._emit_servo_changed()
    
    def _on_y_changed(self, value: int):
        """Y slider değiştiğinde"""
        self.y_value.setText(f"{value}°")
        self._emit_servo_changed()
    
    def _emit_servo_changed(self):
        """Servo değerlerini emit et"""
        self.servo_changed.emit(self.x_slider.value(), self.y_slider.value())
    
    def _reset_position(self):
        """Servo pozisyonunu sıfırla"""
        self.x_slider.setValue(0)
        self.y_slider.setValue(0)
    
    def reset_position(self):
        """Public reset method"""
        self._reset_position()
    
    def get_position(self) -> tuple:
        """Mevcut servo pozisyonunu döndür"""
        return (self.x_slider.value(), self.y_slider.value())
    
    @Slot(int, int)
    def set_position(self, x: int, y: int):
        """Servo pozisyonunu ayarla (dışarıdan)"""
        self.x_slider.blockSignals(True)
        self.y_slider.blockSignals(True)
        
        self.x_slider.setValue(x)
        self.y_slider.setValue(y)
        self.x_value.setText(f"{x}°")
        self.y_value.setText(f"{y}°")
        
        self.x_slider.blockSignals(False)
        self.y_slider.blockSignals(False)


class ControlPanel(QFrame):
    """
    Ana kontrol paneli
    
    İçerik:
    - Mod seçimi (Manuel, Yarı Otonom, Tam Otonom)
    - Servo kontrol
    - Ateş kontrolü (güvenlik kilidi ile)
    
    Signals:
    - mode_changed(str): Mod değiştiğinde
    - fire_command(): Ateş komutu verildiğinde
    - servo_command(x, y): Servo komutu gönderildiğinde
    """
    
    mode_changed = Signal(str)
    fire_command = Signal()
    servo_command = Signal(int, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._fire_unlocked = False  # Güvenlik kilidi
        self._emergency_active = False
        self._is_friendly_target = None  # IFF durumu (DOST hedeflerde ateş kilidi)
        self._setup_ui()
    
    def _setup_ui(self):
        """UI oluştur"""
        self.setStyleSheet(Styles.PANEL)
        self.setMinimumWidth(280)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Başlık
        title = QLabel("KONTROL PANELİ")
        title.setStyleSheet(Styles.TITLE_LABEL)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Mod seçimi
        mode_group = QGroupBox("Çalışma Modu")
        mode_group.setStyleSheet(Styles.GROUP_BOX)
        mode_layout = QHBoxLayout(mode_group)
        mode_layout.setSpacing(4)
        mode_layout.setContentsMargins(6, 4, 6, 6)
        
        self.mode_group = QButtonGroup(self)
        
        self.btn_manual = QPushButton("MANUEL")
        self.btn_manual.setCheckable(True)
        self.btn_manual.setChecked(True)
        self.btn_manual.setStyleSheet(Styles.BUTTON_MODE)
        self.btn_manual.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_manual.setFixedHeight(30)
        
        self.btn_semi = QPushButton("YARI OTO")
        self.btn_semi.setCheckable(True)
        self.btn_semi.setStyleSheet(Styles.BUTTON_MODE)
        self.btn_semi.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_semi.setFixedHeight(30)
        
        self.btn_auto = QPushButton("TAM OTO")
        self.btn_auto.setCheckable(True)
        self.btn_auto.setStyleSheet(Styles.BUTTON_MODE)
        self.btn_auto.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_auto.setFixedHeight(30)
        
        self.mode_group.addButton(self.btn_manual, 0)
        self.mode_group.addButton(self.btn_semi, 1)
        self.mode_group.addButton(self.btn_auto, 2)
        
        mode_layout.addWidget(self.btn_manual)
        mode_layout.addWidget(self.btn_semi)
        mode_layout.addWidget(self.btn_auto)
        layout.addWidget(mode_group)
        
        # Servo kontrol
        servo_group = QGroupBox("Servo Kontrol")
        servo_group.setStyleSheet(Styles.GROUP_BOX)
        servo_layout = QVBoxLayout(servo_group)
        servo_layout.setContentsMargins(6, 4, 6, 6)
        servo_layout.setSpacing(4)
        
        self.servo_control = ServoControlWidget()
        servo_layout.addWidget(self.servo_control)
        
        # Sıfırla butonu
        self.btn_reset = QPushButton("SIFIRLA")
        self.btn_reset.setStyleSheet(Styles.BUTTON_NORMAL)
        self.btn_reset.setFixedHeight(30)
        servo_layout.addWidget(self.btn_reset)
        
        layout.addWidget(servo_group)
        
        # Ateş kontrolü
        fire_group = QGroupBox("Ateş Kontrolü")
        fire_group.setStyleSheet(Styles.GROUP_BOX)
        fire_layout = QVBoxLayout(fire_group)
        fire_layout.setContentsMargins(6, 4, 6, 6)
        fire_layout.setSpacing(4)

        # Güvenlik kilidi
        self.btn_unlock = QPushButton("KİLİDİ AÇ")
        self.btn_unlock.setStyleSheet(Styles.BUTTON_NORMAL)
        self.btn_unlock.setCheckable(True)
        self.btn_unlock.setFixedHeight(32)
        fire_layout.addWidget(self.btn_unlock)
        
        # Ateş butonu
        self.btn_fire = QPushButton("ATEŞ")
        self.btn_fire.setStyleSheet(Styles.BUTTON_DANGER)
        self.btn_fire.setEnabled(False)  # Varsayılan: devre dışı
        self.btn_fire.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.btn_fire.setMinimumHeight(40)
        fire_layout.addWidget(self.btn_fire)
        
        layout.addWidget(fire_group, stretch=1)
        
        # Signal bağlantıları
        self.mode_group.buttonClicked.connect(self._on_mode_changed)
        self.servo_control.servo_changed.connect(self._on_servo_changed)
        self.btn_reset.clicked.connect(self._on_reset_clicked)
        self.btn_unlock.toggled.connect(self._on_unlock_toggled)
        self.btn_fire.clicked.connect(self._on_fire_clicked)

    def _on_mode_changed(self, button):
        mode_id = self.mode_group.id(button)
        mode_map = {
            0: "MANUEL",
            1: "YARI_OTONOM",
            2: "TAM_OTONOM",
        }
        mode = mode_map.get(mode_id, "MANUEL")
        
        # Servo kontrolü sadece manuel modda aktif
        self.servo_control.setEnabled(mode == "MANUEL")
        
        self.mode_changed.emit(mode)
    
    def _on_servo_changed(self, x: int, y: int):
        """Servo değerleri değiştiğinde"""
        self.servo_command.emit(x, y)
    
    def _on_reset_clicked(self):
        """Servo pozisyonunu sıfırla"""
        self.servo_control.reset_position()
    
    def _on_unlock_toggled(self, checked: bool):
        """Güvenlik kilidi değiştiğinde"""
        self._fire_unlocked = checked
        self.btn_fire.setEnabled(checked)
        
        if checked:
            self.btn_unlock.setText("KİLİT AÇIK")
            self.btn_unlock.setStyleSheet(Styles.BUTTON_SUCCESS)
        else:
            self.btn_unlock.setText("KİLİDİ AÇ")
            self.btn_unlock.setStyleSheet(Styles.BUTTON_NORMAL)
    
    def _on_fire_clicked(self):
        """
        Ateş butonuna basıldığında
        
        GÜVENLİK: 
        - Sadece kilit açıksa çalışır
        - DOST hedeflere ateş edilmez
        """
        if self._emergency_active:
            return
        
        # DOST hedef kontrolü (3. Aşama Şartnamesi)
        if self._is_friendly_target is True:
            # DOST hedef - Ateş engellendi
            return
        
        if self._fire_unlocked:
            self.fire_command.emit()
            
            # Ateşten sonra kilidi otomatik kapat (güvenlik)
            self.btn_unlock.setChecked(False)
    
    @Slot(str)
    def set_mode(self, mode: str):
        """Modu dışarıdan ayarla"""
        mode_map = {
            "MANUEL": self.btn_manual,
            "YARI_OTONOM": self.btn_semi,
            "TAM_OTONOM": self.btn_auto
        }
        btn = mode_map.get(mode.upper())
        if btn:
            btn.setChecked(True)
    
    @Slot(bool)
    def set_friendly_target(self, is_friendly: bool):
        """
        Hedef IFF durumunu güncelle ve ateş kontrolü yap
        
        Args:
            is_friendly: True=DOST (Ateş kilidi), False=DÜŞMAN (Ateş serbest)
        """
        self._is_friendly_target = is_friendly
        
        if is_friendly:
            # DOST hedef - Ateş butonunu kapat ve görsel uyarı
            self.btn_fire.setEnabled(False)
            self.btn_fire.setText("🛡️ DOST HEDEF")
            self.btn_unlock.setEnabled(False)
            self.btn_unlock.setChecked(False)
        else:
            # DÜŞMAN hedef - Normal ateş kontrolü
            self.btn_fire.setText("ATEŞ")
            self.btn_unlock.setEnabled(not self._emergency_active)
            # Ateş butonu sadece kilit açıksa aktif
            if self._fire_unlocked and not self._emergency_active:
                self.btn_fire.setEnabled(True)
    
    @Slot()
    def clear_target_lock(self):
        """Hedef kilidini temizle"""
        self._is_friendly_target = None
        self.btn_fire.setText("ATEŞ")
        if not self._emergency_active:
            self.btn_unlock.setEnabled(True)
