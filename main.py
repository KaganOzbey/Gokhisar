#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GÖKHİSAR Hava Savunma Sistemi - Yer Kontrol İstasyonu
Ana giriş noktası (Entry Point)

Kullanım:
    python main.py              # Normal başlatma
    python main.py --debug      # Debug modunda başlat
    python main.py --test-ui    # Sadece UI testi (ağ bağlantısı yok)

Gereksinimler:
    - Python 3.9+
    - PySide6
    - OpenCV (opencv-python)
    - NumPy
"""

import sys
import os
import argparse

# Proje kök dizinini Python path'e ekle
# Bu sayede 'src' modülü her yerden import edilebilir
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from src.ui.main_window import MainWindow
from src.utils.config import SystemConfig


def parse_arguments():
    """Komut satırı argümanlarını parse et"""
    parser = argparse.ArgumentParser(
        description="GÖKHİSAR Hava Savunma Sistemi - Yer Kontrol İstasyonu"
    )
    parser.add_argument(
        '--debug', 
        action='store_true',
        help='Debug modunda başlat (ekstra log)'
    )
    parser.add_argument(
        '--test-ui',
        action='store_true', 
        help='Sadece UI testi - ağ bağlantısı kurulmaz'
    )
    parser.add_argument(
        '--fullscreen',
        action='store_true',
        help='Tam ekran modunda başlat'
    )
    return parser.parse_args()


def main():
    """Ana giriş fonksiyonu"""
    args = parse_arguments()
    
    # Sistem bilgisi
    print("=" * 50)
    print("GÖKHİSAR - Yer Kontrol İstasyonu")
    print("=" * 50)
    
    info = SystemConfig.get_platform_info()
    print(f"Platform: {info['platform']}")
    print(f"Python: {info['python_version'].split()[0]}")
    print(f"Proje Dizini: {info['project_root']}")
    print("=" * 50)
    
    # Qt uygulaması oluştur
    app = QApplication(sys.argv)
    
    # High DPI desteği PySide6'da varsayılan olarak aktif
    
    # Ana pencereyi oluştur
    window = MainWindow()
    
    # Tam ekran modu
    if args.fullscreen:
        window.showFullScreen()
    else:
        window.show()
    
    # Ağ bağlantılarını başlat (test modu değilse)
    if not args.test_ui:
        print("Ağ bağlantıları başlatılıyor...")
        # UDP ve TCP worker'ları başlat
        # Not: Gerçek bağlantı için Raspberry Pi'nin açık olması gerekir
        # window.start_udp_worker()
        # window.start_tcp_worker()
        print("Not: Ağ bağlantıları manuel olarak başlatılmalı (F5 veya UI üzerinden)")
    else:
        print("TEST MODU: Ağ bağlantıları devre dışı")
    
    print("🚀 Sistem başlatıldı!")
    print("Kısayollar: F11=Tam Ekran, F5=Bağlantıları Yenile, ESC=Çık")
    
    # Event loop başlat
    sys.exit(app.exec())


if __name__ == "__main__":
    main()