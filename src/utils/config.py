"""
Cross-platform konfigürasyon ve yardımcı fonksiyonlar
Linux/Windows uyumluluğu için os.path kullanılıyor
"""

import os
import sys
import platform
from pathlib import Path


class SystemConfig:
    """
    Sistem konfigürasyonu - Cross-platform uyumluluk
    
    Neden bu yapı?
    - Windows ve Linux'ta dosya yolları farklı (\ vs /)
    - Seri port isimleri farklı (COM3 vs /dev/ttyUSB0)
    - os.path ve pathlib kullanarak platform bağımsız çalışıyoruz
    """
    
    # Platform tespiti
    IS_WINDOWS = platform.system() == "Windows"
    IS_LINUX = platform.system() == "Linux"
    IS_MAC = platform.system() == "Darwin"
    
    # Proje kök dizini (bu dosyanın 3 üst dizini)
    PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
    
    # Alt dizinler - pathlib ile platform bağımsız
    SRC_DIR = PROJECT_ROOT / "src"
    UI_DIR = SRC_DIR / "ui"
    WORKERS_DIR = SRC_DIR / "workers"
    NETWORK_DIR = SRC_DIR / "network"
    UTILS_DIR = SRC_DIR / "utils"
    
    # Ağ ayarları
    UDP_VIDEO_PORT = 5000          # Kameradan gelen video akışı
    TCP_CONTROL_PORT = 5001        # Kontrol komutları (Ateş, Servo vs.)
    RASPBERRY_PI_IP = "192.168.1.100"  # Raspberry Pi IP adresi
    
    # Seri port ayarları (opsiyonel - doğrudan USB bağlantı için)
    @classmethod
    def get_serial_port(cls) -> str:
        """
        Platform'a göre varsayılan seri port döndürür
        
        Neden?
        - Windows: COM3, COM4 gibi isimler kullanır
        - Linux: /dev/ttyUSB0, /dev/ttyACM0 gibi isimler kullanır
        """
        if cls.IS_WINDOWS:
            return "COM3"
        elif cls.IS_LINUX:
            return "/dev/ttyUSB0"
        elif cls.IS_MAC:
            return "/dev/tty.usbserial"
        return "/dev/ttyUSB0"
    
    @classmethod
    def get_platform_info(cls) -> dict:
        """Sistem bilgilerini döndürür - debug için kullanışlı"""
        return {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "python_version": sys.version,
            "project_root": str(cls.PROJECT_ROOT),
            "serial_port": cls.get_serial_port()
        }


class NetworkConfig:
    """
    Ağ iletişim konfigürasyonu
    TCP/UDP ayarları burada merkezi olarak yönetiliyor
    """
    
    # Raspberry Pi bağlantı ayarları
    RPI_HOST = os.environ.get("GOKHISAR_RPI_HOST", "192.168.1.100")
    
    # Port numaraları
    UDP_VIDEO_PORT = int(os.environ.get("GOKHISAR_UDP_VIDEO_PORT", "5000"))      # GStreamer video akışı
    TCP_COMMAND_PORT = int(os.environ.get("GOKHISAR_TCP_COMMAND_PORT", "5001"))    # Kontrol komutları
    
    # Timeout ayarları (saniye)
    TCP_TIMEOUT = 5.0
    UDP_TIMEOUT = 1.0
    
    # Buffer boyutları
    TCP_BUFFER_SIZE = 1024
    UDP_BUFFER_SIZE = 65535    # Video frame'leri için büyük buffer


class UIConfig:
    """
    Arayüz konfigürasyonu
    Renkler, boyutlar ve stil ayarları
    """
    
    # Pencere boyutları
    WINDOW_WIDTH = 1280
    WINDOW_HEIGHT = 800
    WINDOW_TITLE = "GÖKHİSAR - Yer Kontrol İstasyonu"
    
    # Renkler (Askeri tema)
    COLOR_BG_DARK = "#1a1a2e"
    COLOR_BG_PANEL = "#16213e"
    COLOR_ACCENT_GREEN = "#00ff00"
    COLOR_ACCENT_RED = "#ff0000"
    COLOR_WARNING_YELLOW = "#ffff00"
    COLOR_TEXT_PRIMARY = "#ffffff"
    COLOR_TEXT_SECONDARY = "#aaaaaa"
    
    # Font boyutları
    FONT_SIZE_LARGE = 24
    FONT_SIZE_MEDIUM = 16
    FONT_SIZE_SMALL = 12


# Singleton erişim için
system_config = SystemConfig()
network_config = NetworkConfig()
ui_config = UIConfig()
