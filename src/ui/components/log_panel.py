"""
Log Paneli Bileşeni

Sistem mesajlarını, hataları ve olayları gösteren konsol benzeri panel.
Debug ve operatör bilgilendirmesi için kullanılır.
"""

from datetime import datetime

from PySide6.QtWidgets import QFrame, QVBoxLayout, QTextEdit, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QTextCursor

from src.ui.styles import Styles


class LogPanel(QFrame):
    """
    Log/konsol paneli
    
    Özellikler:
    - Zaman damgalı log mesajları
    - Farklı log seviyeleri (INFO, WARNING, ERROR)
    - Otomatik scroll
    - Temizle butonu
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._max_lines = 500  # Maksimum log satırı
        self._setup_ui()
    
    def _setup_ui(self):
        """UI oluştur"""
        self.setStyleSheet(Styles.PANEL)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 8, 10, 8)
        
        # Başlık ve kontroller
        header_layout = QHBoxLayout()
        
        title = QLabel("SİSTEM LOG")
        title.setStyleSheet(Styles.SUBTITLE_LABEL)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        self.btn_clear = QPushButton("Temizle")
        self.btn_clear.setStyleSheet(Styles.BUTTON_NORMAL)
        self.btn_clear.setMinimumWidth(120)
        header_layout.addWidget(self.btn_clear)
        
        layout.addLayout(header_layout)
        
        # Log alanı
        self.log_text = QTextEdit()
        self.log_text.setStyleSheet(Styles.LOG_AREA)
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(80)
        layout.addWidget(self.log_text)
        
        # Signal bağlantıları
        self.btn_clear.clicked.connect(self.clear)
    
    def _get_timestamp(self) -> str:
        """Zaman damgası döndür"""
        return datetime.now().strftime("%H:%M:%S")
    
    def _append_log(self, message: str, color: str = "#00ff00"):
        """Log mesajı ekle"""
        timestamp = self._get_timestamp()
        html = f'<span style="color: #888;">[{timestamp}]</span> <span style="color: {color};">{message}</span><br>'
        
        # Cursor'u sona taşı
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
        
        # HTML ekle
        self.log_text.insertHtml(html)
        
        # Otomatik scroll
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # Satır limiti kontrolü
        self._trim_lines()
    
    def _trim_lines(self):
        """Fazla satırları sil"""
        text = self.log_text.toPlainText()
        lines = text.split('\n')
        
        if len(lines) > self._max_lines:
            # Son N satırı tut
            self.log_text.clear()
            # Not: Bu basit implementasyon, production'da optimize edilmeli
    
    @Slot(str)
    def log_info(self, message: str):
        """Bilgi mesajı logla"""
        self._append_log(f"[INFO] {message}", "#00ff00")
    
    @Slot(str)
    def log_warning(self, message: str):
        """Uyarı mesajı logla"""
        self._append_log(f"[UYARI] {message}", "#ffff00")
    
    @Slot(str)
    def log_error(self, message: str):
        """Hata mesajı logla"""
        self._append_log(f"[HATA] {message}", "#ff0000")
    
    @Slot(str)
    def log_status(self, message: str):
        """Durum mesajı logla (worker'lardan)"""
        self._append_log(message, "#00aaff")
    
    @Slot()
    def clear(self):
        """Log'u temizle"""
        self.log_text.clear()
        self.log_info("Log temizlendi")
