#!/usr/bin/env python3
"""
TEST CLIENT - TCP Fire Command Test
=====================================
Fire server'ı test etmek için basit TCP client.

Kullanım:
    python test_client.py                    # 3 test komutu gönder
    python test_client.py --count 10         # 10 test komutu
    python test_client.py --interactive      # Manuel mod
"""

import socket
import struct
import time
import argparse
import random

class FireCommandClient:
    """TCP Fire Command Client"""
    
    def __init__(self, host="127.0.0.1", port=6000):
        self.host = host
        self.port = port
    
    def send_fire_command(self, azimuth, elevation, distance):
        """Tek bir ateş komutu gönder"""
        try:
            # Socket oluştur
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(5.0)
            client.connect((self.host, self.port))
            
            # Binary paket hazırla
            packet = struct.pack('=Bfff', 1, azimuth, elevation, distance)
            
            print(f"[>] Gönderiliyor: Az:{azimuth:.2f}° El:{elevation:.2f}° Dist:{distance:.1f}m")
            
            # Gönder
            client.sendall(packet)
            
            # ACK bekle
            ack = client.recv(1)
            if len(ack) == 1:
                status = struct.unpack('=B', ack)[0]

                if status == 0:
                    print(f"[✓] BAŞARILI (ACK: {status})")
                    result = True
                elif status == 1:
                    print(f"[✗] GEÇERSİZ KOMUT (NACK: {status})")
                    result = False
                else:
                    print(f"[✗] HATA (NACK: {status})")
                    result = False
            else:
                print(f"[✗] Yanıt alınamadı")
                result = False
            
            client.close()
            return result
            
        except socket.timeout:
            print(f"[✗] TIMEOUT - Server yanıt vermiyor")
            return False
        except ConnectionRefusedError:
            print(f"[✗] BAĞLANTI REDDEDİLDİ - Server çalışıyor mu?")
            return False
        except Exception as e:
            print(f"[✗] HATA: {e}")
            return False

def run_automated_tests(client, count=3):
    """Otomatik test senaryoları"""
    print("\n" + "=" * 70)
    print(f"OTOMATİK TEST - {count} Komut Gönderilecek")
    print("=" * 70 + "\n")
    
    success_count = 0
    
    for i in range(count):
        print(f"\n--- Test {i+1}/{count} ---")
        
        # Rastgele ama geçerli değerler üret
        azimuth = random.uniform(0, 360)
        elevation = random.uniform(-15, 85)
        distance = random.uniform(100, 5000)
        
        if client.send_fire_command(azimuth, elevation, distance):
            success_count += 1
        
        if i < count - 1:
            time.sleep(1)
    
    # Sonuç
    print("\n" + "=" * 70)
    print("TEST SONUÇLARI")
    print("=" * 70)
    print(f"Toplam Test   : {count}")
    print(f"Başarılı      : {success_count}")
    print(f"Başarısız     : {count - success_count}")
    print(f"Başarı Oranı  : {(success_count/count)*100:.1f}%")
    print("=" * 70 + "\n")

def run_interactive_mode(client):
    """Manuel test modu"""
    print("\n" + "=" * 70)
    print("İNTERAKTİF MOD")
    print("=" * 70)
    print("Ateş komutu parametrelerini girin (Çıkmak için 'q')")
    print("\n")
    
    while True:
        try:
            # Azimuth
            az_input = input("Azimuth (0-360°) [veya 'q']: ").strip()
            if az_input.lower() == 'q':
                break
            azimuth = float(az_input)
            
            # Elevation
            el_input = input("Elevation (-15-85°): ").strip()
            elevation = float(el_input)
            
            # Distance
            dist_input = input("Distance (100-5000m): ").strip()
            distance = float(dist_input)
            
            print()
            client.send_fire_command(azimuth, elevation, distance)
            print()
            
        except ValueError:
            print("[!] Geçersiz değer, sayı girin!\n")
        except KeyboardInterrupt:
            print("\n")
            break
    
    print("İnteraktif mod kapatıldı.\n")

def run_stress_test(client, count=100):
    """Yük testi - hızlı ardışık komutlar"""
    print("\n" + "=" * 70)
    print(f"YÜK TESTİ - {count} Hızlı Ardışık Komut")
    print("=" * 70 + "\n")
    
    success_count = 0
    start_time = time.time()
    
    for i in range(count):
        azimuth = random.uniform(0, 360)
        elevation = random.uniform(-15, 85)
        distance = random.uniform(100, 5000)
        
        if client.send_fire_command(azimuth, elevation, distance):
            success_count += 1
        
        # Bekleme yok, tam hız!
    
    elapsed = time.time() - start_time
    
    # Sonuç
    print("\n" + "=" * 70)
    print("YÜK TESTİ SONUÇLARI")
    print("=" * 70)
    print(f"Toplam Komut  : {count}")
    print(f"Başarılı      : {success_count}")
    print(f"Başarısız     : {count - success_count}")
    print(f"Süre          : {elapsed:.2f} saniye")
    print(f"Hız           : {count/elapsed:.2f} komut/saniye")
    print(f"Başarı Oranı  : {(success_count/count)*100:.1f}%")
    print("=" * 70 + "\n")

def main():
    parser = argparse.ArgumentParser(
        description='Fire Command Test Client',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  python test_client.py                         # 3 otomatik test
  python test_client.py --count 10              # 10 otomatik test
  python test_client.py --interactive           # Manuel mod
  python test_client.py --stress --count 100    # Yük testi
  python test_client.py --host 192.168.1.100    # Uzak server
        """
    )
    
    parser.add_argument('--host', type=str, default='127.0.0.1',
                       help='Server IP (default: 127.0.0.1)')
    
    parser.add_argument('--port', type=int, default=6000,
                       help='Server port (default: 6000)')
    
    parser.add_argument('--count', type=int, default=3,
                       help='Test sayısı (default: 3)')
    
    parser.add_argument('--interactive', action='store_true',
                       help='İnteraktif mod')
    
    parser.add_argument('--stress', action='store_true',
                       help='Yük testi modu')
    
    args = parser.parse_args()
    
    # Client oluştur
    client = FireCommandClient(args.host, args.port)
    
    print("\n" + "=" * 70)
    print("FIRE COMMAND TEST CLIENT")
    print("=" * 70)
    print(f"Hedef: {args.host}:{args.port}")
    print("=" * 70)
    
    # Mod seç
    if args.interactive:
        run_interactive_mode(client)
    elif args.stress:
        run_stress_test(client, args.count)
    else:
        run_automated_tests(client, args.count)
    
    print("Test tamamlandı.\n")

if __name__ == "__main__":
    main()