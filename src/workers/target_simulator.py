"""
Hedef Simülasyonu Worker

Test amaçlı rastgele hedefler üretir ve log paneline görev odaklı mesajlar gönderir.
Gerçek sistemde bu veriler radar/sensörlerden gelecektir.

Kullanım:
    simulator = TargetSimulator()
    simulator.target_detected.connect(log_panel.log_target_detected)
    simulator.start_worker()
"""

import random
from typing import List, Dict
from PySide6.QtCore import Signal, QTimer

from src.workers.base_worker import BaseWorker


class Target:
    """Simüle edilmiş hedef"""
    
    def __init__(self, target_id: str, is_hostile: bool = True):
        self.id = target_id
        self.is_hostile = is_hostile
        self.bearing = random.randint(0, 359)
        self.distance = random.randint(500, 8000)  # metre
        self.altitude = random.randint(100, 5000)  # metre
        self.speed = random.randint(50, 500)  # km/h
        self.threat_type = random.choice(["UAV", "Cruise Missile", "Aircraft", "Drone", "Helicopter"])
        self.friendly_type = random.choice(["F-16", "Bayraktar TB2", "ATAK", "Kaan", "Hürkuş"])
        self.in_range = self.distance <= 4000  # 4km menzil
        self.tracked = True


class TargetSimulator(BaseWorker):
    """
    Hedef simülasyonu worker'ı
    
    Signals:
    - target_detected(str, int): Hedef tespit edildi (id, bearing)
    - target_lost(str): Hedef kaybedildi
    - in_range(str, float): Menzil içine girdi
    - out_of_range(str, float): Menzil dışına çıktı
    - friendly_detected(str, str): Dost unsur (id, type)
    - hostile_detected(str, str): Düşman unsur (id, type)
    - engagement_started(str): Angajman başladı
    - engagement_result(str, bool): Angajman sonucu
    - track_update(int, str): Track sayısı güncellendi
    """
    
    # Görev odaklı signal'lar
    target_detected = Signal(str, int)      # target_id, bearing
    target_lost = Signal(str)               # target_id
    in_range = Signal(str, float)           # target_id, distance
    out_of_range = Signal(str, float)       # target_id, distance
    friendly_detected = Signal(str, str)    # target_id, unit_type
    hostile_detected = Signal(str, str)     # target_id, threat_type
    engagement_started = Signal(str)        # target_id
    engagement_result = Signal(str, bool)   # target_id, success
    track_update = Signal(int, str)         # count, status
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._targets: Dict[str, Target] = {}
        self._target_counter = 0
        self._timer = None
        self._event_interval = 3000  # 3 saniyede bir event (ms)
    
    def run(self):
        """Simülasyon döngüsü"""
        self.emit_status("Hedef simülasyonu başlatıldı")
        
        # İlk hedefleri oluştur
        self._generate_initial_targets()
        
        while self.is_running:
            # Rastgele event üret
            self._generate_random_event()
            
            # Track güncellemesi
            hostile_count = sum(1 for t in self._targets.values() if t.is_hostile)
            friendly_count = len(self._targets) - hostile_count
            self.track_update.emit(
                len(self._targets), 
                f"Düşman: {hostile_count} | Dost: {friendly_count}"
            )
            
            # Bekleme
            self.msleep(self._event_interval)
    
    def _generate_initial_targets(self):
        """Başlangıç hedeflerini oluştur"""
        # 2-3 başlangıç hedefi
        for _ in range(random.randint(2, 3)):
            self._create_new_target()
    
    def _create_new_target(self, is_hostile: bool = None) -> Target:
        """Yeni hedef oluştur"""
        self._target_counter += 1
        
        if is_hostile is None:
            is_hostile = random.random() > 0.3  # %70 düşman
        
        prefix = "T" if is_hostile else "F"
        target_id = f"{prefix}-{self._target_counter:03d}"
        
        target = Target(target_id, is_hostile)
        self._targets[target_id] = target
        
        # Tespit mesajı
        self.target_detected.emit(target_id, target.bearing)
        
        # Dost/düşman tanımlama
        if is_hostile:
            self.hostile_detected.emit(target_id, target.threat_type)
        else:
            self.friendly_detected.emit(target_id, target.friendly_type)
        
        # Menzil durumu
        if target.in_range:
            self.in_range.emit(target_id, float(target.distance))
        else:
            self.out_of_range.emit(target_id, float(target.distance))
        
        return target
    
    def _generate_random_event(self):
        """Rastgele olay üret"""
        event_type = random.choice([
            "new_target",
            "target_lost", 
            "range_change",
            "engagement",
            "nothing"
        ])
        
        if event_type == "new_target":
            self._create_new_target()
            
        elif event_type == "target_lost" and self._targets:
            # Rastgele bir hedefi kaybet
            target_id = random.choice(list(self._targets.keys()))
            del self._targets[target_id]
            self.target_lost.emit(target_id)
            
        elif event_type == "range_change" and self._targets:
            # Rastgele bir hedefin menzil durumunu değiştir
            target_id = random.choice(list(self._targets.keys()))
            target = self._targets[target_id]
            
            # Mesafeyi değiştir
            target.distance += random.randint(-1000, 1000)
            target.distance = max(500, min(8000, target.distance))
            target.in_range = target.distance <= 4000
            
            if target.in_range:
                self.in_range.emit(target_id, float(target.distance))
            else:
                self.out_of_range.emit(target_id, float(target.distance))
                
        elif event_type == "engagement" and self._targets:
            # Düşman hedeflerden birine angajman
            hostile_targets = [t for t in self._targets.values() if t.is_hostile and t.in_range]
            
            if hostile_targets:
                target = random.choice(hostile_targets)
                self.engagement_started.emit(target.id)
                
                # 1 saniye sonra sonuç
                self.msleep(1000)
                
                success = random.random() > 0.3  # %70 başarı
                self.engagement_result.emit(target.id, success)
                
                if success:
                    # Hedefi kaldır
                    del self._targets[target.id]
    
    def set_event_interval(self, interval_ms: int):
        """Event aralığını ayarla"""
        self._event_interval = max(1000, interval_ms)
    
    def get_active_targets(self) -> Dict[str, Target]:
        """Aktif hedefleri döndür"""
        return self._targets.copy()
