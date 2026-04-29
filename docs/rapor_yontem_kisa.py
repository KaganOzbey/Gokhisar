#!/usr/bin/env python3
"""
GÖKHİSAR Rapor - 4. YÖNTEM bölümü (1 Sayfa - Özet)
Sequence Diagram ile modül haberleşmesi
"""

from docx import Document
from docx.shared import Pt, Cm, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def set_cell_shading(cell, color):
    shading = OxmlElement('w:shd')
    shading.set(qn('w:fill'), color)
    cell._tc.get_or_add_tcPr().append(shading)

def create_report():
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
    p.add_run(" tabanlı çok katmanlı mimariye sahiptir. Asenkron işlemler için ")
    p.add_run("QThread").bold = True
    p.add_run(" tabanlı Worker sınıfları, thread-safe iletişim için ")
    p.add_run("Signal/Slot").bold = True
    p.add_run(" mekanizması kullanılmaktadır.")
    
    # ==================== SEQUENCE DIAGRAM ====================
    doc.add_heading("4.2 Modül Haberleşme Diyagramı (Sequence Diagram)", level=2)
    
    # Sequence Diagram - Tablo formatında
    seq_table = doc.add_table(rows=9, cols=5)
    seq_table.style = 'Table Grid'
    
    # Modül başlıkları
    modules = ["KAMERA\n(RPI)", "UDPWorker\n(Thread)", "MainWindow\n(UI)", "TCPWorker\n(Thread)", "RPI\nSERVO"]
    for i, mod in enumerate(modules):
        cell = seq_table.rows[0].cells[i]
        cell.text = mod
        set_cell_shading(cell, "4472C4")  # Mavi
        for para in cell.paragraphs:
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in para.runs:
                run.bold = True
                run.font.size = Pt(9)
                run.font.color.rgb = None  # Beyaz için
    
    # Sequence adımları
    seq_steps = [
        ["─UDP Frame─►", "", "", "", ""],
        ["", "(Port 5000)", "", "", ""],
        ["", "─Signal─►", "frame_received", "", ""],
        ["", "", "Görüntü İşle", "", ""],
        ["", "", "─Komut─►", "send_command", ""],
        ["", "", "", "─TCP Pkt─►", "(Port 5001)"],
        ["", "", "", "◄─ACK─", ""],
        ["", "", "◄─response─", "", ""],
    ]
    
    for row_idx, row_data in enumerate(seq_steps, 1):
        for col_idx, cell_data in enumerate(row_data):
            cell = seq_table.rows[row_idx].cells[col_idx]
            cell.text = cell_data
            for para in cell.paragraphs:
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in para.runs:
                    run.font.size = Pt(8)
                    if "►" in cell_data or "◄" in cell_data:
                        run.bold = True
    
    doc.add_paragraph()
    
    # ==================== AŞAMALAR TABLOSU ====================
    doc.add_heading("4.3 Yarışma Aşamaları", level=2)
    
    table = doc.add_table(rows=1, cols=4)
    table.style = 'Table Grid'
    
    # Header
    headers = ["Aşama", "İşlem", "Protokol", "Modüller"]
    for i, h in enumerate(headers):
        table.rows[0].cells[i].text = h
        set_cell_shading(table.rows[0].cells[i], "DDDDDD")
        table.rows[0].cells[i].paragraphs[0].runs[0].bold = True
        table.rows[0].cells[i].paragraphs[0].runs[0].font.size = Pt(10)
    
    # Data
    data = [
        ["1. Tespit", "Video alımı, hedef algılama", "UDP", "Kamera → UDPWorker → VideoDisplay"],
        ["2. Takip", "Servo kontrolü, menzil hesabı", "TCP", "ControlPanel → TCPWorker → Servo"],
        ["3. Angajman", "Ateş komutu, güvenlik kontrolü", "TCP", "ControlPanel → TCPWorker → RPI"],
    ]
    
    for row_data in data:
        row = table.add_row()
        for i, cell_data in enumerate(row_data):
            row.cells[i].text = cell_data
            row.cells[i].paragraphs[0].runs[0].font.size = Pt(9)
    
    doc.add_paragraph()
    
    # ==================== PROTOKOL DETAYI ====================
    doc.add_heading("4.4 Haberleşme Protokolü", level=2)
    
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
    doc.add_heading("4.5 Çalışma Modları (State Machine)", level=2)
    
    # State Machine - Tablo formatında
    state_table = doc.add_table(rows=3, cols=3)
    state_table.style = 'Table Grid'
    
    states = [
        ["MANUEL", "YARI OTONOM", "TAM OTONOM"],
        ["Servo: Operatör\nAteş: Operatör", "Servo: Otomatik\nAteş: Operatör", "Servo: Otomatik\nAteş: Otomatik"],
        ["◄── Mod Değiştir ──►", "◄── Mod Değiştir ──►", ""]
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
    
    doc.add_paragraph()
    
    # Emergency Stop notu
    p = doc.add_paragraph()
    p.add_run("⚠ ACİL DURDUR: ").bold = True
    p.add_run("Tüm modlarda tüm komutları anlık engeller, servo ve ateş sistemi devre dışı kalır.")
    
    # Kaydet
    output_path = "/home/kagan/Gokhisar/docs/4_YONTEM_Raporu_1Sayfa.docx"
    doc.save(output_path)
    print(f"✅ 1 Sayfalık rapor oluşturuldu: {output_path}")
    return output_path

if __name__ == "__main__":
    create_report()
