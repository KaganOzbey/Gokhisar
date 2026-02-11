import sys


def main() -> int:
    try:
        import PySide6  # noqa: F401
        from PySide6.QtWidgets import QApplication
        import numpy  # noqa: F401
        import cv2  # noqa: F401

        app = QApplication([])
        app.quit()
        print("OK: PySide6/numpy/opencv-python import ve QApplication testi geçti")
        return 0

    except Exception as e:
        print(f"FAIL: import/Qt testi başarısız: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
