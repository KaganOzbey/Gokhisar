"""
Modern Arayüz Stil Tanımlamaları - Glassmorphism & Gradient Tema

Tasarım Felsefesi:
- Glassmorphism: Yarı saydam paneller, blur efekti hissi
- Gradient: Yumuşak renk geçişleri
- Neon Glow: Parlayan kenarlar ve vurgular
- Modern Spacing: Geniş padding ve yuvarlak köşeler
"""

from src.utils.config import UIConfig


class Colors:
    """Modern renk paleti - Koyu tema + Neon vurgular"""
    
    # Ana arka plan - Derin uzay mavisi
    BG_PRIMARY = "#0b1020"
    BG_SECONDARY = "#111a2e"
    BG_TERTIARY = "#1a233a"
    
    # Glassmorphism panel arka planları
    GLASS_BG = "rgba(26, 35, 58, 0.72)"
    GLASS_BORDER = "rgba(255, 255, 255, 0.06)"
    
    # Neon vurgular
    NEON_CYAN = "#4f83ff"
    NEON_GREEN = "#34d399"
    NEON_BLUE = "#4f83ff"
    NEON_PURPLE = "#7c5cff"
    NEON_PINK = "#db2777"
    NEON_RED = "#ff4d4d"
    NEON_ORANGE = "#fb923c"
    NEON_YELLOW = "#fbbf24"
    
    # Gradient başlangıç/bitiş
    GRADIENT_START = "#121a2e"
    GRADIENT_END = "#070b14"
    
    # Metin renkleri
    TEXT_PRIMARY = "#e6eaf2"
    TEXT_SECONDARY = "#9aa4b2"
    TEXT_MUTED = "#6b7280"
    
    # Durum renkleri
    SUCCESS = "#10b981"
    WARNING = "#f59e0b"
    DANGER = "#ef4444"
    INFO = "#3b82f6"


class Styles:
    """
    Modern Qt StyleSheet tanımlamaları
    Glassmorphism + Neon tema
    """
    
    # Ana pencere - Gradient arka plan
    MAIN_WINDOW = f"""
        QMainWindow {{
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 {Colors.BG_PRIMARY},
                stop:0.6 {Colors.BG_SECONDARY},
                stop:1 {Colors.GRADIENT_END}
            );
        }}
        QWidget {{
            font-family: 'Segoe UI', 'SF Pro Display', 'Ubuntu', sans-serif;
        }}
    """
    
    # Modern Panel - Glassmorphism efekti
    PANEL = f"""
        QFrame {{
            background-color: rgba(22, 30, 48, 0.92);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 18px;
        }}
    """
    
    # Video görüntüleme - Neon çerçeve
    VIDEO_DISPLAY = f"""
        QLabel {{
            background-color: #000000;
            border: 1px solid rgba(79, 131, 255, 0.45);
            border-radius: 14px;
            padding: 6px;
        }}
    """
    
    # Durum etiketi - Başarı (Yeşil glow)
    STATUS_LABEL_OK = f"""
        QLabel {{
            background-color: rgba(52, 211, 153, 0.08);
            color: {Colors.TEXT_PRIMARY};
            font-size: 13px;
            font-weight: 500;
            padding: 10px 14px;
            border: 1px solid rgba(52, 211, 153, 0.18);
            border-radius: 10px;
            letter-spacing: 0.5px;
        }}
    """
    
    # Durum etiketi - Tehlike (Kırmızı glow)
    STATUS_LABEL_WARNING = f"""
        QLabel {{
            background-color: rgba(255, 77, 77, 0.08);
            color: {Colors.TEXT_PRIMARY};
            font-size: 13px;
            font-weight: 500;
            padding: 10px 14px;
            border: 1px solid rgba(255, 77, 77, 0.18);
            border-radius: 10px;
            letter-spacing: 0.5px;
        }}
    """
    
    # Durum etiketi - Dikkat (Sarı/Turuncu glow)
    STATUS_LABEL_CAUTION = f"""
        QLabel {{
            background-color: rgba(251, 146, 60, 0.08);
            color: {Colors.TEXT_PRIMARY};
            font-size: 13px;
            font-weight: 500;
            padding: 10px 14px;
            border: 1px solid rgba(251, 146, 60, 0.18);
            border-radius: 10px;
            letter-spacing: 0.5px;
        }}
    """
    
    # Başlık - Gradient text efekti için büyük ve bold
    TITLE_LABEL = f"""
        QLabel {{
            color: {Colors.TEXT_PRIMARY};
            font-size: 22px;
            font-weight: 700;
            letter-spacing: 1px;
        }}
    """
    
    # Alt başlık
    SUBTITLE_LABEL = f"""
        QLabel {{
            color: {Colors.TEXT_SECONDARY};
            font-size: 13px;
            font-weight: 500;
        }}
    """
    
    # Modern Buton - Glassmorphism + hover efekti
    BUTTON_NORMAL = f"""
        QPushButton {{
            background-color: rgba(255, 255, 255, 0.04);
            color: {Colors.TEXT_PRIMARY};
            font-size: 13px;
            font-weight: 600;
            padding: 8px 16px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 10px;
            letter-spacing: 0.3px;
        }}
        QPushButton:hover {{
            background-color: rgba(79, 131, 255, 0.12);
            border-color: rgba(79, 131, 255, 0.35);
        }}
        QPushButton:pressed {{
            background-color: rgba(79, 131, 255, 0.18);
        }}
        QPushButton:disabled {{
            background-color: rgba(100, 116, 139, 0.1);
            color: {Colors.TEXT_MUTED};
            border-color: rgba(100, 116, 139, 0.2);
        }}
    """
    
    # Tehlike Butonu - ATEŞ için (Kırmızı neon glow)
    BUTTON_DANGER = f"""
        QPushButton {{
            background-color: rgba(239, 68, 68, 0.15);
            color: {Colors.NEON_RED};
            font-size: 14px;
            font-weight: 700;
            padding: 8px 16px;
            border: 2px solid rgba(239, 68, 68, 0.5);
            border-radius: 12px;
            letter-spacing: 1.5px;
        }}
        QPushButton:hover {{
            background-color: rgba(239, 68, 68, 0.3);
            border-color: {Colors.NEON_RED};
        }}
        QPushButton:pressed {{
            background-color: rgba(239, 68, 68, 0.45);
        }}
        QPushButton:disabled {{
            background-color: rgba(239, 68, 68, 0.05);
            color: rgba(239, 68, 68, 0.3);
            border-color: rgba(239, 68, 68, 0.15);
        }}
    """
    
    # Başarı Butonu - Yeşil neon
    BUTTON_SUCCESS = f"""
        QPushButton {{
            background-color: rgba(16, 185, 129, 0.15);
            color: {Colors.NEON_GREEN};
            font-size: 13px;
            font-weight: 600;
            padding: 8px 16px;
            border: 1px solid rgba(16, 185, 129, 0.4);
            border-radius: 10px;
        }}
        QPushButton:hover {{
            background-color: rgba(16, 185, 129, 0.3);
            border-color: {Colors.NEON_GREEN};
        }}
        QPushButton:pressed {{
            background-color: rgba(16, 185, 129, 0.4);
        }}
    """
    
    # Mod Seçim Butonu - Toggle tarzı
    BUTTON_MODE = f"""
        QPushButton {{
            background-color: rgba(255, 255, 255, 0.07);
            color: {Colors.TEXT_PRIMARY};
            font-size: 10px;
            font-weight: 600;
            padding: 6px 2px;
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 6px;
            min-height: 28px;
        }}
        QPushButton:checked {{
            background-color: rgba(79, 131, 255, 0.18);
            border-color: rgba(79, 131, 255, 0.45);
            color: {Colors.NEON_BLUE};
        }}
        QPushButton:hover {{
            background-color: rgba(79, 131, 255, 0.10);
            border-color: rgba(79, 131, 255, 0.30);
        }}
    """
    
    # Modern Slider - Neon cyan
    SLIDER = f"""
        QSlider::groove:horizontal {{
            border: none;
            height: 6px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 3px;
        }}
        QSlider::sub-page:horizontal {{
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {Colors.NEON_CYAN},
                stop:1 {Colors.NEON_BLUE}
            );
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: {Colors.NEON_CYAN};
            border: 2px solid {Colors.BG_PRIMARY};
            width: 14px;
            height: 14px;
            margin: -5px 0;
            border-radius: 8px;
        }}
        QSlider::handle:horizontal:hover {{
            background: {Colors.TEXT_PRIMARY};
            border-color: {Colors.NEON_CYAN};
        }}
    """
    
    # GroupBox - Modern başlık
    GROUP_BOX = f"""
        QGroupBox {{
            color: {Colors.TEXT_PRIMARY};
            font-size: 13px;
            font-weight: 600;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 10px;
            margin-top: 10px;
            padding: 12px 6px 8px 6px;
            background-color: rgba(255, 255, 255, 0.03);
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
            color: {Colors.NEON_BLUE};
        }}
    """
    
    # Log/Konsol Alanı - Terminal tarzı
    LOG_AREA = f"""
        QTextEdit {{
            background-color: rgba(0, 0, 0, 0.6);
            color: {Colors.TEXT_SECONDARY};
            font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
            font-size: 12px;
            border: 1px solid rgba(79, 131, 255, 0.18);
            border-radius: 10px;
            padding: 12px;
            selection-background-color: rgba(79, 131, 255, 0.25);
        }}
    """
    
    # Splitter - İnce ve modern
    SPLITTER = f"""
        QSplitter {{
            background: transparent;
        }}
        QSplitter::handle {{
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 2px;
        }}
        QSplitter::handle:horizontal {{
            width: 4px;
            margin: 0 4px;
        }}
        QSplitter::handle:vertical {{
            height: 4px;
            margin: 4px 0;
        }}
        QSplitter::handle:hover {{
            background-color: rgba(79, 131, 255, 0.35);
        }}
    """
    
    # ScrollBar - İnce ve modern
    SCROLLBAR = f"""
        QScrollBar:vertical {{
            background: transparent;
            width: 8px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: rgba(255, 255, 255, 0.2);
            min-height: 30px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: rgba(255, 255, 255, 0.3);
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: transparent;
        }}
    """
    
    # StatusBar - Alt bilgi çubuğu
    STATUS_BAR = f"""
        QStatusBar {{
            background-color: rgba(17, 24, 39, 0.9);
            color: {Colors.TEXT_SECONDARY};
            font-size: 12px;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            padding: 6px 12px;
        }}
    """
