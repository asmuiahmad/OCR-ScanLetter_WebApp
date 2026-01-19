"""
PDF Form Generator untuk Formulir Permintaan dan Pemberian Cuti
===============================================================
Generator PDF yang mengikuti format resmi Mahkamah Agung RI
"""

import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class CutiFormPDFGenerator:
    def __init__(self):
        self.pdf_folder = "static/pdf_forms"
        os.makedirs(self.pdf_folder, exist_ok=True)

    def create_cuti_form_pdf(self, cuti_data, output_filename=None):
        """Generate PDF formulir cuti sesuai format Mahkamah Agung"""

        if not output_filename:
            output_filename = f"formulir_cuti_{cuti_data.get('id_cuti', 'new')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        pdf_path = os.path.join(self.pdf_folder, output_filename)

        # Create PDF document
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            rightMargin=1 * cm,
            leftMargin=1 * cm,
            topMargin=1 * cm,
            bottomMargin=1 * cm,
        )

        story = []

        # Create styles
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Normal"],
            fontSize=11,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
            spaceAfter=6,
        )

        header_style = ParagraphStyle(
            "CustomHeader",
            parent=styles["Normal"],
            fontSize=10,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
            spaceAfter=3,
        )

        normal_style = ParagraphStyle(
            "CustomNormal",
            parent=styles["Normal"],
            fontSize=9,
            fontName="Helvetica",
            spaceAfter=3,
        )

        small_style = ParagraphStyle(
            "SmallText", parent=styles["Normal"], fontSize=8, fontName="Helvetica"
        )

        # Header Section
        story.append(
            Paragraph(
                "LAMPIRAN II : SURAT EDARAN SEKRETARIS MAHKAMAH AGUNG", title_style
            )
        )
        story.append(Paragraph("REPUBLIK INDONESIA", title_style))
        story.append(Paragraph("NOMOR 13 TAHUN 2019", title_style))
        story.append(Spacer(1, 12))

        # Date and Address
        date_location = f"Banjarbaru, {datetime.now().strftime('%d %B %Y')}"
        story.append(Paragraph(date_location, normal_style))
        story.append(Paragraph("Yth. Ketua Pengadilan Agama Banjarbaru", normal_style))
        story.append(Paragraph("Di -", normal_style))
        story.append(Paragraph("Banjarbaru", normal_style))
        story.append(Spacer(1, 12))

        # Form Title
        story.append(Paragraph("FORMULIR PERMINTAAN DAN PEMBERIAN CUTI", title_style))
        nomor_form = cuti_data.get(
            "nomor_form", f"/{datetime.now().strftime('%Y')}/KPA-W15-A12/KP5.3/X/2024"
        )
        story.append(Paragraph(f"Nomor : {nomor_form}", normal_style))
        story.append(Spacer(1, 12))

        # I. DATA PEGAWAI
        data_pegawai = [
            ["I. DATA PEGAWAI", "", "", ""],
            ["NAMA", cuti_data.get("nama", ""), "NIP.", cuti_data.get("nip", "")],
            [
                "JABATAN",
                cuti_data.get("jabatan", ""),
                "GOL/RUANG",
                cuti_data.get("gol_ruang", ""),
            ],
            [
                "UNIT KERJA",
                cuti_data.get("unit_kerja", ""),
                "MASA KERJA",
                cuti_data.get("masa_kerja", ""),
            ],
        ]

        table_pegawai = Table(
            data_pegawai, colWidths=[3 * cm, 5 * cm, 2.5 * cm, 4 * cm]
        )
        table_pegawai.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("SPAN", (0, 0), (3, 0)),  # Merge header cells
                ]
            )
        )

        story.append(table_pegawai)
        story.append(Spacer(1, 8))

        # II. JENIS CUTI YANG DIAMBIL
        jenis_cuti_options = [
            ("1. CUTI TAHUNAN", cuti_data.get("jenis_cuti") == "Cuti Tahunan"),
            ("2. CUTI BESAR", cuti_data.get("jenis_cuti") == "Cuti Besar"),
            ("3. CUTI SAKIT", cuti_data.get("jenis_cuti") == "Cuti Sakit"),
            ("4. CUTI MELAHIRKAN", cuti_data.get("jenis_cuti") == "Cuti Melahirkan"),
            (
                "5. CUTI KARENA ALASAN PENTING",
                cuti_data.get("jenis_cuti") == "Cuti Karena Alasan Penting",
            ),
            (
                "6. CUTI DI LUAR TANGGUNGAN NEGARA",
                cuti_data.get("jenis_cuti") == "Cuti Di Luar Tanggungan Negara",
            ),
        ]

        jenis_cuti_data = [["II. JENIS CUTI YANG DIAMBIL**"]]

        # Create checkbox-like display
        for i in range(0, len(jenis_cuti_options), 2):
            row = []
            # Left option
            option1 = jenis_cuti_options[i]
            checkbox1 = "☑" if option1[1] else "☐"
            row.append(f"{checkbox1} {option1[0]}")

            # Right option (if exists)
            if i + 1 < len(jenis_cuti_options):
                option2 = jenis_cuti_options[i + 1]
                checkbox2 = "☑" if option2[1] else "☐"
                row.append(f"{checkbox2} {option2[0]}")
            else:
                row.append("")

            jenis_cuti_data.append(row)

        table_jenis_cuti = Table(jenis_cuti_data, colWidths=[7.5 * cm, 7.5 * cm])
        table_jenis_cuti.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("SPAN", (0, 0), (1, 0)),  # Merge header
                ]
            )
        )

        story.append(table_jenis_cuti)
        story.append(Spacer(1, 8))

        # III. ALASAN CUTI
        alasan_cuti_data = [["III. ALASAN CUTI"], [cuti_data.get("alasan_cuti", "")]]

        table_alasan = Table(alasan_cuti_data, colWidths=[15 * cm])
        table_alasan.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ]
            )
        )

        story.append(table_alasan)
        story.append(Spacer(1, 8))

        # IV. LAMANYA CUTI
        tanggal_mulai = (
            cuti_data.get("tanggal_cuti", datetime.now()).strftime("%d %B %Y")
            if cuti_data.get("tanggal_cuti")
            else ""
        )
        tanggal_selesai = (
            cuti_data.get("sampai_cuti", datetime.now()).strftime("%d %B %Y")
            if cuti_data.get("sampai_cuti")
            else ""
        )

        lamanya_cuti_data = [
            ["IV. LAMANYA CUTI", "", "", ""],
            ["Selama", cuti_data.get("lama_cuti", ""), "hari", ""],
            ["", "Tanggal", tanggal_mulai, "Sampai", "Tanggal", tanggal_selesai],
        ]

        table_lamanya = Table(
            lamanya_cuti_data, colWidths=[2 * cm, 2 * cm, 4 * cm, 2 * cm, 5 * cm]
        )
        table_lamanya.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("SPAN", (0, 0), (4, 0)),  # Merge header
                ]
            )
        )

        story.append(table_lamanya)
        story.append(Spacer(1, 8))

        # V. CATATAN CUTI
        catatan_cuti_data = [
            ["V. CATATAN CUTI***"],
            ["1. CUTI TAHUNAN", "PARAF", "2. CUTI BESAR"],
            ["Tahun", "Sisa", "Keterangan", "PETUGAS CUTI", "3. CUTI SAKIT"],
            ["2023", "", "", "", "4. CUTI MELAHIRKAN"],
            ["2024", "", "", "", "5. CUTI KARENA ALASAN PENTING"],
            ["2025", "", "", "", "6. CUTI DILUAR TANGGUNGAN NEGARA"],
            ["", "", "", "", ""],
            ["Catatan tambahan baris kedua", "", "", "", ""],
        ]

        table_catatan = Table(
            catatan_cuti_data, colWidths=[2 * cm, 2 * cm, 3 * cm, 3 * cm, 5 * cm]
        )
        table_catatan.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("SPAN", (0, 0), (4, 0)),  # Merge header
                ]
            )
        )

        story.append(table_catatan)
        story.append(Spacer(1, 8))

        # VI. ALAMAT SELAMA MENJALANKAN CUTI
        alamat_data = [
            ["VI. ALAMAT SELAMA MENJALANKAN CUTI", "Telp.", cuti_data.get("telp", "")],
            [cuti_data.get("alamat", ""), "", ""],
            ["", "", ""],
            ["", cuti_data.get("nama", ""), ""],
            ["", f"NIP. {cuti_data.get('nip', '')}", ""],
        ]

        table_alamat = Table(alamat_data, colWidths=[8 * cm, 2 * cm, 5 * cm])
        table_alamat.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ]
            )
        )

        story.append(table_alamat)
        story.append(Spacer(1, 8))

        # VII. PERTIMBANGAN ATASAN LANGSUNG
        pertimbangan_data = [
            ["VII. PERTIMBANGAN ATASAN LANGSUNG**"],
            ["DISETUJUI", "PERUBAHAN****", "DITANGGUHKAN****", "TIDAK DISETUJUI****"],
            ["", "", "", ""],
            ["", "", "", "Panitera"],
            ["", "", "", ""],
            ["", "", "", "H. Murnianti, S.H."],
            ["", "", "", "NIP. 196201110 198601 2 001"],
        ]

        table_pertimbangan = Table(
            pertimbangan_data, colWidths=[3.75 * cm, 3.75 * cm, 3.75 * cm, 3.75 * cm]
        )
        table_pertimbangan.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("SPAN", (0, 0), (3, 0)),  # Merge header
                    ("ALIGN", (3, 3), (3, -1), "CENTER"),  # Center signature area
                ]
            )
        )

        story.append(table_pertimbangan)
        story.append(Spacer(1, 8))

        # VIII. KEPUTUSAN PEJABAT YANG BERWENANG MEMBERIKAN CUTI
        keputusan_data = [
            ["VIII. KEPUTUSAN PEJABAT YANG BERWENANG MEMBERIKAN CUTI **"],
            ["DISETUJUI", "PERUBAHAN****", "DITANGGUHKAN****", "TIDAK DISETUJUI****"],
            ["", "", "", ""],
            ["", "", "", ""],
            ["", "", "", ""],
            ["", "", "", "Rasyid Rizani, S.H.I., M.H.I."],
            ["", "", "", "NIP.19850628 200904 1 003"],
        ]

        table_keputusan = Table(
            keputusan_data, colWidths=[3.75 * cm, 3.75 * cm, 3.75 * cm, 3.75 * cm]
        )
        table_keputusan.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("SPAN", (0, 0), (3, 0)),  # Merge header
                    ("ALIGN", (3, 5), (3, -1), "CENTER"),  # Center signature area
                ]
            )
        )

        story.append(table_keputusan)
        story.append(Spacer(1, 12))

        # Footer notes
        footer_notes = [
            "Catatan:",
            "* Coret yang tidak perlu",
            "** Pilih salah satu dengan memberi tanda centang (√)",
            "*** Diisi oleh pejabat yang berwenang memberikan cuti",
            "**** Bila tidak disetujui atau ditangguhkan, sebutkan alasannya",
            "***** Diberikan kepada yang bersangkutan setelah diisi lengkap dan ditandatangani",
            "****** Catatan tambahan dapat ditulis di baris kedua jika diperlukan",
        ]

        for note in footer_notes:
            story.append(Paragraph(note, small_style))

        # Build PDF
        doc.build(story)

        return pdf_path

    def create_cuti_form_from_model(self, cuti_model):
        """Create PDF from Cuti model instance"""
        cuti_data = {
            "id_cuti": cuti_model.id_cuti,
            "nama": cuti_model.nama,
            "nip": cuti_model.nip,
            "jabatan": cuti_model.jabatan,
            "gol_ruang": cuti_model.gol_ruang,
            "unit_kerja": cuti_model.unit_kerja,
            "masa_kerja": cuti_model.masa_kerja,
            "jenis_cuti": cuti_model.jenis_cuti,
            "alasan_cuti": cuti_model.alasan_cuti,
            "lama_cuti": cuti_model.lama_cuti,
            "tanggal_cuti": cuti_model.tanggal_cuti,
            "sampai_cuti": cuti_model.sampai_cuti,
            "alamat": cuti_model.alamat,
            "telp": cuti_model.telp,
            "nomor_form": getattr(
                cuti_model,
                "no_suratmasuk",
                f"/{datetime.now().year}/KPA-W15-A12/KP5.3/X/{datetime.now().year}",
            ),
        }

        return self.create_cuti_form_pdf(cuti_data)
