from flask import Blueprint, render_template, request
from models import SuratMasuk, SuratKeluar
from sqlalchemy import or_

report_bp = Blueprint('report', __name__)

@report_bp.route('/laporan-statistik')
@app.route('/laporan_statistik')
@login_required
def laporan_statistik():

    semua_surat_keluar = SuratKeluar.query.all()
    semua_surat_masuk = SuratMasuk.query.all()

    gagal_ekstraksi = [s for s in semua_surat_keluar if s.ocr_accuracy_suratKeluar is not None and s.ocr_accuracy_suratKeluar < 100]
    total_surat = len(semua_surat_keluar)
    berhasil_count = len([s for s in semua_surat_keluar if s.ocr_accuracy_suratKeluar == 100])

    persentase_berhasil = round((berhasil_count / total_surat) * 100, 2) if total_surat else 0

    akurasi_keluar = [s.ocr_accuracy_suratKeluar for s in semua_surat_keluar if s.ocr_accuracy_suratKeluar is not None]
    akurasi_masuk = [s.ocr_accuracy_suratMasuk for s in semua_surat_masuk if s.ocr_accuracy_suratMasuk is not None]

    rata2_akurasi_keluar = round(sum(akurasi_keluar) / len(akurasi_keluar), 2) if akurasi_keluar else 0
    rata2_akurasi_masuk = round(sum(akurasi_masuk) / len(akurasi_masuk), 2) if akurasi_masuk else 0

    return render_template(
        'laporan_statistik.html',
        persentase_berhasil=persentase_berhasil,
        gagal_ekstraksi=gagal_ekstraksi,
        keyword=request.args.get('keyword', ''),
        surat_keyword=[],
        rata2_akurasi_masuk=rata2_akurasi_masuk,
        rata2_akurasi_keluar=rata2_akurasi_keluar
    )