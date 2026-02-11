#!/usr/bin/env python3
"""
KAMERA SİMÜLASYONU - UDP JPEG Frame Gönderici
==========================================
Kağan'ın arayüzünü test etmek için UDP üzerinden JPEG encoded sahte kamera frame'leri gönderir.

Özellikler:
- Basit hareketli hedef simülasyonu
- Detaylı loglama
- Hata yönetimi

Kullanım:
    python sender.py                    # Normal mod
    python sender.py --scenario fast    # Hızlı hareket senaryosu
    python sender.py --config myconf.ini # Özel config
"""

import socket
import time
import argparse
import logging
from datetime import datetime
from pathlib import Path

import numpy as np
import cv2

# ============================================================================
# KONFIGURASYON
# ============================================================================

class Config:
    """Simülasyon ayarları"""
    
    # Ağ Ayarları
    UDP_IP = "127.0.0.1"      # Hedef IP (Kağan'ın Linux PC'si)
    UDP_PORT = 5000           # Hedef Port (NetworkConfig.UDP_VIDEO_PORT ile uyumlu)
    SEND_RATE = 2.0           # Saniyede kaç paket (Hz)

    # Görüntü ayarları
    WIDTH = 320
    HEIGHT = 240
    JPEG_QUALITY = 60

    # Simülasyon Modu
    SCENARIO = "tracking"       # tracking, sweep, stationary

# ============================================================================
# LOGLAMA AYARLARI
# ============================================================================

def setup_logging():
    """Log dosyası ve konsol çıktısı ayarla"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"sender_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

# ============================================================================
# SENARYO MODLARI
# ============================================================================

class FrameGenerator:
    """Sahte kamera frame'i üretir (BGR numpy array)"""

    def __init__(self, config: Config):
        self.config = config
        self.t = 0

    def next_frame(self) -> np.ndarray:
        w, h = int(self.config.WIDTH), int(self.config.HEIGHT)
        img = np.zeros((h, w, 3), dtype=np.uint8)

        # Arka plan gradient
        for y in range(h):
            c = int(20 + (y / max(h - 1, 1)) * 40)
            img[y, :, :] = (c, c // 2, c // 3)

        scenario = (self.config.SCENARIO or "tracking").lower()
        self.t += 1

        if scenario == "stationary":
            cx = w // 2
            cy = h // 2
        elif scenario == "sweep":
            cx = int((self.t * 4) % w)
            cy = h // 2
        else:  # tracking
            cx = int(w / 2 + (w * 0.35) * np.sin(self.t * 0.08))
            cy = int(h / 2 + (h * 0.25) * np.cos(self.t * 0.06))

        # Hedef (kırmızı daire) + crosshair
        cv2.circle(img, (cx, cy), 14, (0, 0, 255), -1)
        cv2.circle(img, (cx, cy), 22, (0, 0, 180), 2)
        cv2.line(img, (cx - 30, cy), (cx + 30, cy), (0, 255, 0), 1)
        cv2.line(img, (cx, cy - 30), (cx, cy + 30), (0, 255, 0), 1)

        # HUD metni
        cv2.putText(img, f"SIM CAM | {scenario.upper()} | t={self.t}", (10, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1, cv2.LINE_AA)

        return img

# ============================================================================
# UDP SENDER
# ============================================================================

class UDPSender:
    """UDP üzerinden binary veri gönder"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.sock = None
        self.packet_count = 0
        self.error_count = 0
        
    def connect(self):
        """UDP socket oluştur"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.logger.info(f"UDP Socket oluşturuldu: {self.config.UDP_IP}:{self.config.UDP_PORT}")
            return True
        except Exception as e:
            self.logger.error(f"Socket oluşturulamadı: {e}")
            return False
    
    def send_packet(self, jpeg_bytes: bytes):
        """JPEG frame paketi gönder"""
        try:
            # UDP ile gönder
            self.sock.sendto(jpeg_bytes, (self.config.UDP_IP, self.config.UDP_PORT))
            
            self.packet_count += 1
            return True
            
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Gönderim hatası: {e}")
            return False
    
    def close(self):
        """Socket'i kapat"""
        if self.sock:
            self.sock.close()
            self.logger.info(f"Socket kapatıldı. Toplam gönderilen: {self.packet_count}, Hata: {self.error_count}")

# ============================================================================
# ANA PROGRAM
# ============================================================================

def parse_arguments():
    """Komut satırı argümanlarını parse et"""
    parser = argparse.ArgumentParser(
        description='Kamera Simülasyonu - UDP JPEG Frame Gönderici',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument('--scenario', type=str, default='tracking',
                       choices=['tracking', 'sweep', 'stationary'],
                       help='Simülasyon senaryosu (default: random)')
    
    parser.add_argument('--ip', type=str, default='127.0.0.1',
                       help='Hedef IP adresi (default: 127.0.0.1)')
    
    parser.add_argument('--port', type=int, default=5000,
                       help='Hedef port (default: 5000)')
    
    parser.add_argument('--rate', type=float, default=2.0,
                       help='Gönderim hızı Hz (default: 2.0)')

    parser.add_argument('--width', type=int, default=320,
                       help='Frame genişliği (default: 320)')

    parser.add_argument('--height', type=int, default=240,
                       help='Frame yüksekliği (default: 240)')

    parser.add_argument('--jpeg-quality', type=int, default=60,
                       help='JPEG kalite (0-100) (default: 60)')
    
    return parser.parse_args()

def main():
    """Ana program"""
    
    # Argümanları al
    args = parse_arguments()
    
    # Loglama ayarla
    logger = setup_logging()
    
    # Konfigürasyon
    config = Config()
    config.UDP_IP = args.ip
    config.UDP_PORT = args.port
    config.SEND_RATE = args.rate
    config.SCENARIO = args.scenario
    config.WIDTH = args.width
    config.HEIGHT = args.height
    config.JPEG_QUALITY = max(10, min(100, int(args.jpeg_quality)))
    
    # Başlangıç mesajları
    logger.info("=" * 70)
    logger.info("KAMERA SİMÜLASYONU BAŞLATILDI")
    logger.info("=" * 70)
    logger.info(f"Hedef        : {config.UDP_IP}:{config.UDP_PORT}")
    logger.info(f"Gönderim Hızı: {config.SEND_RATE} Hz ({1.0/config.SEND_RATE:.2f} saniye/paket)")
    logger.info(f"Senaryo      : {config.SCENARIO.upper()}")
    logger.info(f"Frame        : {config.WIDTH}x{config.HEIGHT} JPEG quality={config.JPEG_QUALITY}")
    logger.info(f"Paket Formatı: JPEG bytes (Tek UDP datagram)")
    logger.info("Ctrl+C ile durdurun")
    logger.info("=" * 70)
    
    # Bileşenleri oluştur
    sender = UDPSender(config, logger)
    frame_gen = FrameGenerator(config)
    
    # Bağlan
    if not sender.connect():
        logger.error("Program sonlandırılıyor.")
        return
    
    # Ana döngü
    try:
        delay = 1.0 / config.SEND_RATE
        
        while True:
            frame = frame_gen.next_frame()
            ok, buf = cv2.imencode(
                '.jpg',
                frame,
                [int(cv2.IMWRITE_JPEG_QUALITY), int(config.JPEG_QUALITY)]
            )

            if not ok:
                logger.error("JPEG encode başarısız")
                time.sleep(delay)
                continue

            payload = buf.tobytes()
            if len(payload) > 65000:
                logger.warning(f"UYARI: JPEG payload çok büyük ({len(payload)} byte). width/height/quality düşür.")

            success = sender.send_packet(payload)
            
            if success:
                logger.info(f"[#{sender.packet_count:04d}] frame_bytes={len(payload)}")
            
            time.sleep(delay)
            
    except KeyboardInterrupt:
        logger.info("\n")
        logger.info("=" * 70)
        logger.info("KULLANICI TARAFINDAN DURDURULDU")
        logger.info("=" * 70)
        
    finally:
        sender.close()
        logger.info("Program sonlandı.")

if __name__ == "__main__":
    main()