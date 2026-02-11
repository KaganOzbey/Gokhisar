"""
Ağ İletişim Worker'ları - TCP/UDP Client işlemleri

Bu worker'lar UI thread'ini bloklamadan ağ işlemlerini yürütür.
Raspberry Pi ile haberleşme bu worker'lar üzerinden yapılır.

Mimari:
- UDPVideoWorker: Kameradan gelen video frame'lerini alır
- TCPCommandWorker: Kontrol komutlarını (Servo, Ateş) gönderir
"""

import socket
import struct
import json
from typing import Optional

from PySide6.QtCore import Signal

from src.workers.base_worker import BaseWorker
from src.utils.config import NetworkConfig


class UDPVideoWorker(BaseWorker):
    """
    UDP üzerinden video frame'lerini alan worker
    
    Signal'lar:
    - frame_received: Yeni frame geldiğinde tetiklenir (bytes)
    - connection_status: Bağlantı durumu değiştiğinde
    
    Neden UDP?
    - Video akışında hız önemli, kayıp paketler tolere edilebilir
    - TCP'nin handshake overhead'i yok
    - GStreamer ile uyumlu
    """
    
    # Video frame signal'ı - UI'da QLabel'e çizim için kullanılacak
    frame_received = Signal(bytes)
    connection_status = Signal(bool)  # True=bağlı, False=bağlı değil
    
    def __init__(self, host: str = "", port: int = None, parent=None):
        super().__init__(parent)
        
        self._host = host or "0.0.0.0"  # Tüm interface'lerden dinle
        self._port = port or NetworkConfig.UDP_VIDEO_PORT
        self._socket: Optional[socket.socket] = None
    
    def run(self):
        """UDP socket'ten sürekli veri oku"""
        try:
            # UDP socket oluştur
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.bind((self._host, self._port))
            self._socket.settimeout(NetworkConfig.UDP_TIMEOUT)
            
            self.emit_status(f"UDP dinleniyor: {self._host}:{self._port}")
            self.connection_status.emit(True)
            
            while self.is_running:
                try:
                    # Frame verisi al
                    data, addr = self._socket.recvfrom(NetworkConfig.UDP_BUFFER_SIZE)
                    if data:
                        self.frame_received.emit(data)
                        
                except socket.timeout:
                    # Timeout normal, döngüye devam
                    continue
                except Exception as e:
                    self.emit_error(f"Veri alma hatası: {e}")
                    
        except Exception as e:
            self.emit_error(f"Socket hatası: {e}")
            self.connection_status.emit(False)
        finally:
            self._cleanup()
    
    def _cleanup(self):
        """Socket'i temizle"""
        if self._socket:
            try:
                self._socket.close()
            except:
                pass
            self._socket = None
        self.connection_status.emit(False)
        self.emit_status("UDP bağlantısı kapatıldı")


class TCPCommandWorker(BaseWorker):
    """
    TCP üzerinden komut gönderen worker
    
    Signal'lar:
    - response_received: Raspberry Pi'den yanıt geldiğinde
    - connection_status: Bağlantı durumu
    
    Neden TCP?
    - Komutların (özellikle ATEŞ) kesinlikle ulaşması gerekiyor
    - Güvenilir, sıralı iletim
    - Handshake ile bağlantı doğrulama
    """
    
    response_received = Signal(dict)  # JSON response
    command_sent = Signal(str)        # Gönderilen komut onayı
    connection_status = Signal(bool)
    
    def __init__(self, host: str = None, port: int = None, parent=None):
        super().__init__(parent)
        
        self._host = host or NetworkConfig.RPI_HOST
        self._port = port or NetworkConfig.TCP_COMMAND_PORT
        self._socket: Optional[socket.socket] = None
        
        # Komut kuyruğu (thread-safe olmak için Signal kullanacağız)
        self._pending_command: Optional[bytes] = None
    
    def connect_to_server(self) -> bool:
        """Raspberry Pi'ye TCP bağlantısı kur"""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(NetworkConfig.TCP_TIMEOUT)
            self._socket.connect((self._host, self._port))
            
            self.emit_status(f"TCP bağlantısı kuruldu: {self._host}:{self._port}")
            self.connection_status.emit(True)
            return True
            
        except Exception as e:
            self.emit_error(f"TCP bağlantı hatası: {e}")
            self.connection_status.emit(False)
            return False
    
    def send_command_json(self, command_type: str, data: dict) -> bool:
        """
        JSON formatında komut gönder
        
        Args:
            command_type: "SERVO", "FIRE", "MODE" vs.
            data: Komut parametreleri
            
        Örnek:
            send_command_json("SERVO", {"x": 45, "y": 30})
        """
        if not self._socket:
            self.emit_error("Socket bağlı değil")
            return False
        
        try:
            payload = {
                "type": command_type,
                "data": data
            }
            json_data = json.dumps(payload).encode('utf-8')
            
            self._socket.sendall(json_data)
            self.command_sent.emit(f"Gönderildi: {command_type}")
            return True
            
        except Exception as e:
            self.emit_error(f"Komut gönderme hatası: {e}")
            return False
    
    def send_command_binary(self, command_id: int, x: int, y: int, flags: int = 0) -> bool:
        """
        Binary (struct) formatında komut gönder
        
        Neden binary?
        - Daha küçük paket boyutu
        - Daha hızlı parse
        - Gömülü sistemlerde yaygın
        
        Paket formatı (8 byte):
        - command_id: 1 byte (uint8)
        - x: 2 byte (int16)
        - y: 2 byte (int16)  
        - flags: 1 byte (uint8)
        - checksum: 2 byte (uint16)
        
        Args:
            command_id: Komut tipi (1=SERVO, 2=FIRE, 3=MODE)
            x: X değeri (-180 ile 180)
            y: Y değeri (-90 ile 90)
            flags: Ek bayraklar
        """
        if not self._socket:
            self.emit_error("Socket bağlı değil")
            return False
        
        try:
            # Struct ile binary paketleme
            # Format: B=uint8, h=int16, H=uint16
            packet = struct.pack('<BhhB', command_id, x, y, flags)
            
            # Basit checksum hesapla (tüm byte'ların toplamı mod 65536)
            checksum = sum(packet) % 65536
            packet += struct.pack('<H', checksum)
            
            self._socket.sendall(packet)
            self.command_sent.emit(f"Binary komut gönderildi: ID={command_id}")
            return True
            
        except Exception as e:
            self.emit_error(f"Binary komut hatası: {e}")
            return False
    
    def run(self):
        """Bağlantıyı kur ve yanıtları dinle"""
        if not self.connect_to_server():
            return
        
        try:
            while self.is_running:
                try:
                    # Yanıt bekle
                    self._socket.settimeout(1.0)
                    data = self._socket.recv(NetworkConfig.TCP_BUFFER_SIZE)
                    
                    if data:
                        try:
                            response = json.loads(data.decode('utf-8'))
                            self.response_received.emit(response)
                        except json.JSONDecodeError:
                            # Binary response olabilir
                            self.emit_status(f"Binary yanıt: {len(data)} byte")
                            
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.is_running:
                        self.emit_error(f"Yanıt okuma hatası: {e}")
                    break
                    
        finally:
            self._cleanup()
    
    def _cleanup(self):
        """Socket'i temizle"""
        if self._socket:
            try:
                self._socket.close()
            except:
                pass
            self._socket = None
        self.connection_status.emit(False)
        self.emit_status("TCP bağlantısı kapatıldı")
