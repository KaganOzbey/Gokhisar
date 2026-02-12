#!/usr/bin/env python3
"""
ATEŞ KOMUTU SUNUCUSU - TCP Server
====================================
Kağan'ın arayüzünden gelen "Ateş Et" komutlarını alır ve işler.

Özellikler:
- Binary protokol (struct)
- Komut geçmişi tutma
- ACK/NACK yanıtları
- Detaylı loglama
- Çoklu client desteği
- Komut validasyonu

Protokol:
    CLIENT -> SERVER:
        [1 byte cmd_id][4 byte azimuth][4 byte elevation][4 byte distance]
        Toplam: 13 byte
    
    SERVER -> CLIENT:
        [1 byte status_code]
        0 = Success
        1 = Invalid command
        2 = Processing error

Kullanım:
    python tcp_fire_server.py
    python tcp_fire_server.py --port 6000
"""

import socket
import struct
import time
import argparse
import logging
from datetime import datetime
from pathlib import Path
from threading import Thread, Lock, Semaphore

# ============================================================================
# KONFIGURASYON
# ============================================================================

class Config:
    """Server ayarları"""
    TCP_IP = "0.0.0.0"        # Tüm interface'lerden dinle
    TCP_PORT = 6000           # Port numarası
    MAX_CLIENTS = 5           # Maksimum eşzamanlı client
    TIMEOUT = 30.0            # Client timeout (saniye)
    
    # Komut ID'leri (UI formatıyla uyumlu)
    CMD_SERVO = 1             # Servo komutu
    CMD_FIRE = 2              # Ateş et komutu
    CMD_MODE = 3              # Mod değişikliği
    
    # Yanıt kodları
    # 1-byte status kodları (0-255)
    STATUS_SUCCESS = 0        # Başarılı
    STATUS_INVALID_CMD = 1    # Geçersiz komut
    STATUS_ERROR = 2          # İşlem hatası

    # UI Paket formatı: <BhhBH (8 byte)
    # cmd_id(1) + x(2) + y(2) + flags(1) + checksum(2)
    PACKET_SIZE = 8

# ============================================================================
# LOGLAMA
# ============================================================================

def setup_logging():
    """Log dosyası ve konsol çıktısı"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"fire_server_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

# ============================================================================
# KOMUT GEÇMİŞİ
# ============================================================================

class CommandHistory:
    """Gelen komutları kaydet"""
    
    def __init__(self, max_size=1000):
        self.commands = []
        self.max_size = max_size
        self.lock = Lock()
        
    def add(self, client_addr, cmd_id, x, y, flags, success):
        """Komut ekle"""
        with self.lock:
            command = {
                'timestamp': datetime.now(),
                'client': f"{client_addr[0]}:{client_addr[1]}",
                'cmd_id': cmd_id,
                'x': x,
                'y': y,
                'flags': flags,
                'success': success
            }
            
            self.commands.append(command)
            
            # Sınırı aşarsa eski komutları sil
            if len(self.commands) > self.max_size:
                self.commands = self.commands[-self.max_size:]
    
    def get_stats(self):
        """İstatistik al"""
        with self.lock:
            total = len(self.commands)
            success = sum(1 for c in self.commands if c['success'])
            failed = total - success
            
            return {
                'total': total,
                'success': success,
                'failed': failed
            }
    
    def save_to_file(self):
        """Komut geçmişini dosyaya kaydet"""
        with self.lock:
            if not self.commands:
                return
            
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = log_dir / f"command_history_{timestamp}.txt"
            
            with open(filename, 'w') as f:
                f.write("KOMUT GEÇMİŞİ\n")
                f.write("=" * 80 + "\n\n")
                
                for cmd in self.commands:
                    status = "✓" if cmd['success'] else "✗"
                    f.write(
                        f"{status} {cmd['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} | "
                        f"{cmd['client']} | "
                        f"CMD:{cmd['cmd_id']} | "
                        f"X:{cmd['x']}° Y:{cmd['y']}° Flags:{cmd['flags']}\n"
                    )
            
            return filename

# ============================================================================
# KOMUT İŞLEYİCİ
# ============================================================================

class CommandProcessor:
    """Komutları doğrula ve işle"""
    
    def __init__(self, logger):
        self.logger = logger
    
    def validate_servo_command(self, x: int, y: int):
        """Servo komutu parametrelerini doğrula"""
        errors = []
        
        # X kontrolü (-180 ile 180)
        if not (-180 <= x <= 180):
            errors.append(f"Geçersiz X: {x}° (-180 ile 180 olmalı)")
        
        # Y kontrolü (-90 ile 90)
        if not (-90 <= y <= 90):
            errors.append(f"Geçersiz Y: {y}° (-90 ile 90 olmalı)")
        
        return len(errors) == 0, errors
    
    def process_servo_command(self, x: int, y: int):
        """Servo komutunu işle"""
        valid, errors = self.validate_servo_command(x, y)
        
        if not valid:
            for error in errors:
                self.logger.warning(error)
            return False
        
        self.logger.info(
            f"[SERVO] SERVO KOMUTU İŞLENDİ | "
            f"X: {x}° | Y: {y}°"
        )
        return True
    
    def process_fire_command(self, flags: int):
        """Ateş komutunu işle"""
        self.logger.info(
            f"[FIRE] 🔥 ATEŞ KOMUTU İŞLENDİ | "
            f"Flags: {flags}"
        )
        return True
    
    def process_mode_command(self, mode_id: int):
        """Mod değişikliği komutunu işle"""
        mode_names = {0: "MANUEL", 1: "YARI_OTONOM", 2: "TAM_OTONOM"}
        mode_name = mode_names.get(mode_id, f"UNKNOWN({mode_id})")
        self.logger.info(
            f"[MODE] MOD DEĞİŞTİRİLDİ | "
            f"Mod: {mode_name}"
        )
        return True

# ============================================================================
# TCP SERVER
# ============================================================================

def recv_exact(sock: socket.socket, size: int) -> bytes:
    """TCP framing: socket'ten tam `size` byte okuyana kadar bekle."""
    buf = bytearray()
    while len(buf) < size:
        chunk = sock.recv(size - len(buf))
        if not chunk:
            break
        buf.extend(chunk)
    return bytes(buf)

def verify_checksum(packet: bytes) -> bool:
    """UI'nin gönderdiği checksum'ı doğrula"""
    if len(packet) != 8:
        return False
    # İlk 6 byte'ın toplamı mod 65536 = son 2 byte (little-endian uint16)
    data_part = packet[:6]
    received_checksum = struct.unpack('<H', packet[6:8])[0]
    calculated_checksum = sum(data_part) % 65536
    return received_checksum == calculated_checksum

class FireCommandServer:
    """TCP Fire Command Server"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.server_socket = None
        self.running = False
        self.history = CommandHistory()
        self.processor = CommandProcessor(logger)
        self.client_count = 0
        self._client_slots = Semaphore(self.config.MAX_CLIENTS)
        
    def start(self):
        """Server'ı başlat"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.config.TCP_IP, self.config.TCP_PORT))
            self.server_socket.listen(self.config.MAX_CLIENTS)
            
            self.running = True
            
            self.logger.info("=" * 70)
            self.logger.info("TCP FIRE COMMAND SERVER BAŞLATILDI")
            self.logger.info("=" * 70)
            self.logger.info(f"Adres         : {self.config.TCP_IP}:{self.config.TCP_PORT}")
            self.logger.info(f"Max Client    : {self.config.MAX_CLIENTS}")
            self.logger.info(f"Timeout       : {self.config.TIMEOUT} saniye")
            self.logger.info(f"Protokol      : Binary (UI uyumlu)")
            self.logger.info(f"Paket Boyutu  : 8 byte (<BhhBH)")
            self.logger.info("Ctrl+C ile durdurun")
            self.logger.info("=" * 70)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Server başlatılamadı: {e}")
            return False
    
    def handle_client(self, client_socket, client_addr):
        """Client bağlantısını handle et"""
        self.client_count += 1
        client_id = self.client_count
        
        self.logger.info(f"[CLIENT #{client_id}] Bağlandı: {client_addr[0]}:{client_addr[1]}")
        
        try:
            client_socket.settimeout(self.config.TIMEOUT)
            
            while self.running:
                # UI formatı: 8 byte (<BhhBH)
                data = recv_exact(client_socket, self.config.PACKET_SIZE)
                if len(data) != self.config.PACKET_SIZE:
                    break

                try:
                    # Checksum doğrula
                    if not verify_checksum(data):
                        self.logger.warning(f"[CLIENT #{client_id}] Checksum hatası!")
                        response = struct.pack('=B', self.config.STATUS_ERROR)
                        client_socket.send(response)
                        continue
                    
                    # UI formatı: cmd_id(1) + x(2) + y(2) + flags(1) + checksum(2)
                    cmd_id, x, y, flags = struct.unpack('<BhhB', data[:6])
                        
                    self.logger.info(
                        f"[CLIENT #{client_id}] "
                        f"CMD:{cmd_id} | X:{x}° Y:{y}° Flags:{flags}"
                    )
                    
                    # Komutu işle
                    success = False
                    if cmd_id == self.config.CMD_SERVO:
                        success = self.processor.process_servo_command(x, y)
                        self.history.add(client_addr, cmd_id, x, y, 0, success)
                    elif cmd_id == self.config.CMD_FIRE:
                        success = self.processor.process_fire_command(flags)
                        self.history.add(client_addr, cmd_id, x, y, 0, success)
                    elif cmd_id == self.config.CMD_MODE:
                        success = self.processor.process_mode_command(x)
                        self.history.add(client_addr, cmd_id, x, y, 0, success)
                    else:
                        self.logger.warning(f"[CLIENT #{client_id}] Bilinmeyen komut: {cmd_id}")
                        response = struct.pack('=B', self.config.STATUS_INVALID_CMD)
                        client_socket.send(response)
                        continue
                    
                    # ACK/NACK gönder
                    if success:
                        response = struct.pack('=B', self.config.STATUS_SUCCESS)
                    else:
                        response = struct.pack('=B', self.config.STATUS_ERROR)
                    client_socket.send(response)
                        
                except struct.error as e:
                    self.logger.error(f"[CLIENT #{client_id}] Parse hatası: {e}")
                    response = struct.pack('=B', self.config.STATUS_ERROR)
                    client_socket.send(response)
                    
        except socket.timeout:
            self.logger.warning(f"[CLIENT #{client_id}] Timeout ({self.config.TIMEOUT}s)")
        except Exception as e:
            self.logger.error(f"[CLIENT #{client_id}] Hata: {e}")
        finally:
            client_socket.close()
            self.logger.info(f"[CLIENT #{client_id}] Bağlantı kapatıldı: {client_addr[0]}:{client_addr[1]}")
            self._client_slots.release()
    
    def run(self):
        """Ana server döngüsü"""
        try:
            while self.running:
                self._client_slots.acquire()
                client_socket, client_addr = self.server_socket.accept()
                
                # Her client için yeni thread
                client_thread = Thread(
                    target=self.handle_client,
                    args=(client_socket, client_addr),
                    daemon=True
                )
                client_thread.start()
                
        except KeyboardInterrupt:
            self.logger.info("\n")
            self.logger.info("=" * 70)
            self.logger.info("KULLANICI TARAFINDAN DURDURULDU")
            
        finally:
            self.stop()
    
    def stop(self):
        """Server'ı durdur"""
        self.running = False
        
        if self.server_socket:
            self.server_socket.close()
        
        # İstatistikleri göster
        stats = self.history.get_stats()
        self.logger.info("=" * 70)
        self.logger.info("SERVER İSTATİSTİKLERİ")
        self.logger.info("=" * 70)
        self.logger.info(f"Toplam Komut  : {stats['total']}")
        self.logger.info(f"Başarılı      : {stats['success']}")
        self.logger.info(f"Başarısız     : {stats['failed']}")
        self.logger.info(f"Toplam Client : {self.client_count}")
        
        # Geçmişi kaydet
        if stats['total'] > 0:
            filename = self.history.save_to_file()
            self.logger.info(f"Komut geçmişi kaydedildi: {filename}")
        
        self.logger.info("=" * 70)
        self.logger.info("Server kapatıldı.")

# ============================================================================
# ANA PROGRAM
# ============================================================================

def parse_arguments():
    """Komut satırı argümanları"""
    parser = argparse.ArgumentParser(
        description='Fire Command Server - TCP Ateş Komutu Sunucusu'
    )
    
    parser.add_argument('--port', type=int, default=6000,
                       help='Server port (default: 6000)')
    
    parser.add_argument('--max-clients', type=int, default=5,
                       help='Maksimum eşzamanlı client (default: 5)')
    
    parser.add_argument('--timeout', type=float, default=30.0,
                       help='Client timeout saniye (default: 30)')
    
    return parser.parse_args()

def main():
    """Ana program"""
    args = parse_arguments()
    
    logger = setup_logging()
    
    config = Config()
    config.TCP_PORT = args.port
    config.MAX_CLIENTS = args.max_clients
    config.TIMEOUT = args.timeout
    
    server = FireCommandServer(config, logger)
    
    if server.start():
        server.run()

if __name__ == "__main__":
    main()