#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GÖKHİSAR - Yer Kontrol İstasyonu"""
import sys, os, argparse

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.utils.config import SystemConfig


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test-ui',    action='store_true')
    parser.add_argument('--fullscreen', action='store_true')
    parser.add_argument('--no-splash',  action='store_true')
    return parser.parse_args()


def main():
    args = parse_arguments()
    print("=" * 50)
    print("GÖKHİSAR - Yer Kontrol İstasyonu")
    print("=" * 50)

    app = QApplication(sys.argv)
    window = MainWindow()

    # --no-splash veya --test-ui ise direkt ana arayüze geç
    if args.no_splash or args.test_ui:
        window._stack.setCurrentIndex(1)

    if args.fullscreen:
        window.showFullScreen()
    else:
        window.showMaximized()

    info = SystemConfig.get_platform_info()
    print(f"Platform: {info['platform']} | Python: {info['python_version'].split()[0]}")
    print("Hazır! | BAŞLAT butonuna bas veya --no-splash ile atla")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
