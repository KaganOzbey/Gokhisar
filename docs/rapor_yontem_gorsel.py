#!/usr/bin/env python3
"""
GÖKHİSAR Rapor - 4. YÖNTEM bölümü (1 Sayfa)
Sequence Diagram görsel olarak çizildi
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from docx import Document
from docx.shared import Pt, Cm, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os

def set_cell_shading(cell, color):
    shading = OxmlElement('w:shd')
    shading.set(qn('w:fill'), color)
    cell._tc.get_or_add_tcPr().append(shading)

def draw_sequence_diagram():
    """Sequence diagram çiz ve kaydet"""
    fig, ax = plt.subplots(1, 1, figsize=(10, 5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')
    
    # Modül pozisyonları
    modules = [
        (1, "KAMERA\n(RPI)"),
        (3, "UDPWorker"),
        (5, "MainWindow"),
        (7, "TCPWorker"),
        (9, "RPI SERVO")
    ]
    
    # Modül kutuları çiz
    box_width = 1.4
    box_height = 0.6
    for x, name in modules:
        # Kutu
        rect = FancyBboxPatch(
            (x - box_width/2, 5.2), box_width, box_height,
            boxstyle="round,pad=0.05",
            facecolor='#4472C4',
            edgecolor='black',
            linewidth=1.5
        )
        ax.add_patch(rect)
        # Yazı
        ax.text(x, 5.5, name, ha='center', va='center', 
                fontsize=8, fontweight='bold', color='white')
        # Dikey çizgi (lifeline)
        ax.plot([x, x], [0.5, 5.2], 'k--', linewidth=1, alpha=0.7)
    
    # Mesajlar (oklar)
    messages = [
        (1, 3, 4.6, "1: UDP Frame (Port 5000)", "right"),
        (3, 5, 3.8, "2: frame_received Signal", "right"),
        (5, 7, 3.0, "3: send_command (Binary 8B)", "right"),
        (7, 9, 2.2, "4: TCP Packet (Port 5001)", "right"),
        (9, 7, 1.4, "5: ACK", "left"),
    ]
    
    for x1, x2, y, label, direction in messages:
        # Ok çiz
        if direction == "right":
            ax.annotate('', xy=(x2-0.1, y), xytext=(x1+0.1, y),
                       arrowprops=dict(arrowstyle='->', color='#333333', lw=1.5))
        else:
            ax.annotate('', xy=(x1+0.1, y), xytext=(x2-0.1, y),
                       arrowprops=dict(arrowstyle='->', color='#333333', lw=1.5))
        
        # Etiket
        mid_x = (x1 + x2) / 2
        ax.text(mid_x, y + 0.25, label, ha='center', va='bottom', fontsize=7)
    
    plt.tight_layout()
    
    # Kaydet
    img_path = "/home/kagan/Gokhisar/docs/sequence_diagram.png"
    plt.savefig(img_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"✅ Sequence diagram oluşturuldu: {img_path}")
    return img_path

def create_report():
    # Önce sequence diagram'ı çiz
    seq_img_path = draw_sequence_diagram()
    
    doc = Document()
    
    # Sayfa kenar boşluklarını küçült
    sections = doc.sections
    for section in sections:
        section.top_margin = Cm(1.5)
        section.bottom_margin = Cm(1.5)
        section.left_margin = Cm(2)
        section.right_margin = Cm(2)
    
    # Stil
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(11)
    style.paragraph_format.space_after = Pt(6)
    
    # ==================== BAŞLIK ====================
    title = doc.add_heading("4. YÖNTEM", level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # ==================== SİSTEM MİMARİSİ ====================
    doc.add_heading("4.1 Sistem Mimarisi", level=2)
    
    p = doc.add_paragraph()
    p.add_run("GÖKHİSAR Yer Kontrol İstasyonu, ").bold = False
    p.add_run("PySide6 (Qt6)").bold = True
    p.add_run(" tabanlı çok katmanlı (multi-tier) bir masaüstü uygulaması olarak geliştirilmiştir. ")
    p.add_run("Sistem mimarisi dört ana katmandan oluşmaktadır:")
    
    # Katman açıklamaları
    layers = [
        ("UI Layer:", "MainWindow, StatusPanel, ControlPanel, VideoDisplay ve LogPanel bileşenlerinden oluşur. Kullanıcı etkileşimlerini yönetir."),
        ("Worker Layer:", "UDPVideoWorker ve TCPCommandWorker sınıfları QThread tabanlı arka plan iş parçacıkları olarak çalışır. Ana thread'i bloklamadan ağ operasyonlarını gerçekleştirir."),
        ("Communication Layer:", "UDP protokolü ile düşük gecikmeli video akışı, TCP protokolü ile güvenilir komut iletimi sağlanır."),
        ("Hardware Layer:", "Raspberry Pi üzerine entegre edilmiş kamera ve servo motorlar fiziksel kontrolü gerçekleştirir."),
    ]
    
    for title, desc in layers:
        p = doc.add_paragraph()
        p.add_run(title).bold = True
        p.add_run(" " + desc)
        p.paragraph_format.left_indent = Cm(0.5)
        p.paragraph_format.space_after = Pt(2)
    
    # Thread yapısı
    p = doc.add_paragraph()
    p.add_run("Thread Yapısı: ").bold = True
    p.add_run("Sistemde asenkron işlem için QThread tabanlı Worker sınıfları kullanılmaktadır. ")
    p.add_run("Ana Thread (UI Thread) kullanıcı etkileşimlerini, UDP Worker Thread video alımını, ")
    p.add_run("TCP Worker Thread ise komut iletimini yönetir. Thread'ler arası güvenli iletişim ")
    p.add_run("Signal/Slot").bold = True
    p.add_run(" mekanizması ile sağlanır.")
    
    # ==================== SEQUENCE DIAGRAM ====================
    doc.add_heading("4.2 Modül Haberleşme Diyagramı", level=2)
    
    # Görsel ekle
    doc.add_picture(seq_img_path, width=Inches(6))
    last_paragraph = doc.paragraphs[-1]
    last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # ==================== PROTOKOL DETAYI ====================
    doc.add_heading("4.3 Haberleşme Protokolü", level=2)
    
    # İki sütunlu mini tablo
    table2 = doc.add_table(rows=3, cols=4)
    table2.style = 'Table Grid'
    
    protocol_data = [
        ["UDP (Video)", "Port: 5000", "TCP (Komut)", "Port: 5001"],
        ["Format: JPEG", "Buffer: 64KB", "Format: Binary 8B", "Checksum: CRC16"],
        ["Gecikme: Düşük", "Güvenilirlik: -", "Gecikme: Orta", "Güvenilirlik: ✓"],
    ]
    
    for i, row_data in enumerate(protocol_data):
        for j, cell_data in enumerate(row_data):
            table2.rows[i].cells[j].text = cell_data
            table2.rows[i].cells[j].paragraphs[0].runs[0].font.size = Pt(9)
            if i == 0:
                set_cell_shading(table2.rows[i].cells[j], "EEEEEE")
                table2.rows[i].cells[j].paragraphs[0].runs[0].bold = True
    
    doc.add_paragraph()
    
    # ==================== ÇALIŞMA MODLARI ====================
    doc.add_heading("4.4 Çalışma Modları", level=2)
    
    # State Machine - Tablo formatında
    state_table = doc.add_table(rows=2, cols=3)
    state_table.style = 'Table Grid'
    
    states = [
        ["MANUEL", "YARI OTONOM", "TAM OTONOM"],
        ["Servo: Operatör\nAteş: Operatör", "Servo: Otomatik\nAteş: Operatör", "Servo: Otomatik\nAteş: Otomatik"],
    ]
    
    colors = ["70AD47", "ED7D31", "C00000"]  # Yeşil, Turuncu, Kırmızı
    
    for row_idx, row_data in enumerate(states):
        for col_idx, cell_data in enumerate(row_data):
            cell = state_table.rows[row_idx].cells[col_idx]
            cell.text = cell_data
            for para in cell.paragraphs:
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in para.runs:
                    run.font.size = Pt(9)
                    if row_idx == 0:
                        run.bold = True
                        set_cell_shading(cell, colors[col_idx])
    
    # Kaydet
    output_path = "/home/kagan/Gokhisar/docs/4_YONTEM_Raporu_1Sayfa.docx"
    doc.save(output_path)
    print(f"✅ 1 Sayfalık rapor oluşturuldu: {output_path}")
    return output_path

if __name__ == "__main__":
    create_report()
