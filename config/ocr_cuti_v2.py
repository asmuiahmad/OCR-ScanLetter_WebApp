import logging
import os
import random
import re
import string
import tempfile
from datetime import datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from config.extensions import db
from config.models import Cuti, SuratKeluar

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import untuk PDF processing
try:
    import pdf2image

    PDF_SUPPORT = True
    logger.info("pdf2image successfully imported")

    # Check if poppler is available
    try:
        test_images = pdf2image.convert_from_path.__doc__
        logger.info("pdf2image.convert_from_path is available")
    except Exception as e:
        logger.warning(f"pdf2image imported but may have issues: {e}")

except ImportError as e:
    PDF_SUPPORT = False
    logger.warning(
        f"pdf2image not installed. PDF processing will be disabled. Error: {e}"
    )
    logger.warning("Install with: pip install pdf2image")
    logger.warning(
        "Also install poppler: brew install poppler (macOS) or apt-get install poppler-utils (Linux)"
    )

ocr_cuti_v2_bp = Blueprint("ocr_cuti_v2", __name__, template_folder="../templates/home")

UPLOAD_FOLDER = "static/ocr/cuti"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def extract_text_from_pdf(pdf_file_or_path):
    """
    Extract text from PDF file using OCR
    Args:
        pdf_file_or_path: Either a file object or a file path string
    """
    if not PDF_SUPPORT:
        return None

    try:
        # Determine if input is a file path or file object
        if isinstance(pdf_file_or_path, str):
            # It's already a file path
            pdf_path = pdf_file_or_path
            temp_file_created = False
        else:
            # It's a file object, save it temporarily
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
                pdf_file_or_path.save(tmp_pdf)
                pdf_path = tmp_pdf.name
            temp_file_created = True

        # Konversi PDF ke gambar
        images = pdf2image.convert_from_path(pdf_path)

        # Ekstrak teks dari setiap halaman
        full_text = ""
        for i, image in enumerate(images):
            import pytesseract

            page_text = pytesseract.image_to_string(image, lang="ind")
            full_text += page_text
            if len(images) > 1:
                full_text += f"\n\n--- PAGE {i + 1} ---\n\n"

        # Hapus file sementara jika kita yang membuat
        if temp_file_created:
            os.unlink(pdf_path)

        return full_text
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return None


def extract_cuti_fields(text):
    """
    Ekstrak field dari formulir cuti dengan strategi line-by-line parsing
    untuk menangani layout 2 kolom yang dibaca OCR secara vertikal
    """
    print("\n" + "=" * 70)
    print("OCR CUTI V2 - EXTRACTION")
    print("=" * 70)

    # Save raw OCR text to file for debugging
    try:
        debug_path = os.path.join(UPLOAD_FOLDER, "debug_ocr_v2_output.txt")
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write("RAW OCR OUTPUT (V2)\n")
            f.write("=" * 70 + "\n")
            f.write(text)
            f.write("\n" + "=" * 70 + "\n")
        print(f"✓ Raw OCR text saved to: {debug_path}")
    except Exception as e:
        print(f"✗ Error saving debug file: {e}")

    # Split text into lines
    lines = text.split("\n")
    lines = [line.strip() for line in lines]  # Clean whitespace

    # Initialize result dictionary
    result = {
        "nomor_surat": "Tidak terbaca",
        "nama": "Tidak terbaca",
        "nip": "Tidak terbaca",
        "jabatan": "Tidak terbaca",
        "gol_ruang": "Tidak terbaca",
        "unit_kerja": "Tidak terbaca",
        "masa_kerja": "Tidak terbaca",
        "alamat": "Tidak terbaca",
        "telp": "Tidak terbaca",
        "jenis_cuti": "Tidak terbaca",
        "alasan_cuti": "Tidak terbaca",
        "lama_cuti": "Tidak terbaca",
        "tanggal_mulai_cuti": "Tidak terbaca",
        "tanggal_selesai_cuti": "Tidak terbaca",
        "no_suratmasuk": "Tidak terbaca",
    }

    # Helper function to find index of line containing pattern
    def find_line_index(pattern, start=0):
        for i in range(start, len(lines)):
            if re.search(pattern, lines[i], re.IGNORECASE):
                return i
        return -1

    # Helper function to get next non-empty line
    def get_next_value(start_idx, skip_patterns=None):
        if skip_patterns is None:
            skip_patterns = []

        for i in range(start_idx + 1, min(start_idx + 20, len(lines))):
            line = lines[i]
            if not line:  # Skip empty lines
                continue

            # Skip lines matching skip patterns
            skip = False
            for pattern in skip_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    skip = True
                    break

            if not skip:
                return line, i

        return None, -1

    # === SECTION 1: DATA PEGAWAI ===
    print("\n--- Section 1: Data Pegawai ---")

    # Nama Lengkap
    nama_idx = find_line_index(r"Nama\s+Lengkap")
    if nama_idx >= 0:
        # Check same line first
        parts = re.split(r"Nama\s+Lengkap\s*", lines[nama_idx], flags=re.IGNORECASE)
        if len(parts) > 1 and parts[1].strip():
            result["nama"] = parts[1].strip()
            print(f"✓ Nama: {result['nama']}")
        else:
            # Get from next line
            nama, _ = get_next_value(nama_idx, [r"Nomor\s+Induk", r"\(NIP\)"])
            if nama:
                result["nama"] = nama
                print(f"✓ Nama: {result['nama']}")

    # Jabatan, Gol/Ruang, Unit Kerja, Masa Kerja - simple extraction
    for field_name, pattern in [
        ("jabatan", r"Jabatan"),
        ("gol_ruang", r"Golongan/Ruang"),
        ("unit_kerja", r"Unit\s+Kerja"),
        ("masa_kerja", r"Masa\s+Kerja"),
    ]:
        idx = find_line_index(pattern)
        if idx >= 0:
            parts = re.split(pattern + r"\s*", lines[idx], flags=re.IGNORECASE)
            if len(parts) > 1 and parts[1].strip():
                result[field_name] = parts[1].strip()
                print(f"✓ {field_name.title()}: {result[field_name]}")

    # === SECTION 2: DETAIL PERMOHONAN CUTI ===
    # Find section III (which appears before section II in OCR output due to 2-column layout)
    print("\n--- Section 2: Detail Permohonan Cuti ---")

    detail_idx = find_line_index(r"III?\.\s*DETAIL\s+PERMOHONAN\s+CUTI")
    if detail_idx < 0:
        detail_idx = find_line_index(r"Alasan\s+Cuti")

    if detail_idx >= 0:
        # After "III. DETAIL PERMOHONAN CUTI" section, parse sequentially
        # The order in OCR for 2-column layout is:
        # 1. Alasan Cuti label
        # 2. Lama Cuti label
        # 3. Tanggal Mulai Cuti label
        # 4. Tanggal Selesai Cuti label
        # 5. Nomor Surat Masuk label
        # 6. Empty or section header (II. JENIS CUTI)
        # 7. Checkbox or empty
        # 8. Alamat value (from Alamat Lengkap in column 2)
        # 9. Telepon value (from Nomor Telepon in column 2)
        # 10. NIP value (long number from column 2)
        # 11. Alasan Cuti value
        # 12. Lama Cuti value (e.g., "8 hari")
        # 13. Tanggal Mulai value
        # 14. Tanggal Selesai value
        # 15. Nomor Surat Masuk value

        # Find where values start (after labels and section headers)
        values_start = detail_idx + 1

        # Skip all label lines and section headers
        skip_patterns = [
            r"Alasan\s+Cuti",
            r"Lama\s+Cuti",
            r"Tanggal\s+Mulai",
            r"Tanggal\s+Selesai",
            r"Nomor\s+Surat\s+Masuk",
            r"II\.\s*JENIS\s+CUTI",
            r"^[MUD\(\)]+$",  # Checkbox symbols
        ]

        while values_start < len(lines) and (
            not lines[values_start]
            or any(
                re.search(p, lines[values_start], re.IGNORECASE) for p in skip_patterns
            )
        ):
            values_start += 1

        # Extract values in order
        value_lines = []
        for i in range(values_start, min(values_start + 15, len(lines))):
            if lines[i]:
                value_lines.append(lines[i])

        print(f"Debug - Values found: {value_lines[:8]}")

        # Map values to fields based on expected order
        if len(value_lines) >= 7:
            # value_lines[0] = Alamat (e.g., "Komp. Sa'adah...")
            # value_lines[1] = Telepon (e.g., "1421241412")
            # value_lines[2] = Alasan Cuti (e.g., "21412321312231") - could be same as NIP
            # value_lines[3] = Lama Cuti (e.g., "8 hari")
            # value_lines[4] = Tanggal Mulai (e.g., "14 Januari 2026")
            # value_lines[5] = Tanggal Selesai (e.g., "21 Januari 2026")
            # value_lines[6] = Nomor Surat Masuk (e.g., "124")

            # Alamat - has "Komp." or "Gg." or "Jl." or "No."
            if re.search(
                r"(Komp\.|Gg\.|Jl\.|No\.|RT|RW)", value_lines[0], re.IGNORECASE
            ):
                result["alamat"] = value_lines[0]
                print(f"✓ Alamat: {result['alamat']}")

            # Telepon - 10+ digits
            if re.match(r"^\d{10,}$", value_lines[1]):
                result["telp"] = value_lines[1]
                print(f"✓ Telepon: {result['telp']}")

            # Alasan Cuti - value_lines[2] (bisa berupa text atau angka)
            if value_lines[2]:
                result["alasan_cuti"] = value_lines[2]
                print(f"✓ Alasan Cuti: {result['alasan_cuti']}")

                # If Alasan Cuti is a long number (14-18 digits), also use it as NIP
                if re.match(r"^\d{14,18}$", value_lines[2]):
                    result["nip"] = value_lines[2]
                    print(f"✓ NIP (from Alasan Cuti): {result['nip']}")

            # Lama Cuti - contains "hari" or just a number (value_lines[3])
            if len(value_lines) > 3 and re.search(
                r"\d+\s*hari", value_lines[3], re.IGNORECASE
            ):
                nums = re.findall(r"\d+", value_lines[3])
                if nums:
                    result["lama_cuti"] = nums[0]
                    print(f"✓ Lama Cuti: {result['lama_cuti']} hari")

            # Tanggal Mulai - date format (value_lines[4])
            if len(value_lines) > 4 and re.search(
                r"\d{1,2}\s+[A-Za-z]+\s+\d{4}", value_lines[4]
            ):
                result["tanggal_mulai_cuti"] = value_lines[4]
                print(f"✓ Tanggal Mulai: {result['tanggal_mulai_cuti']}")

            # Tanggal Selesai - date format (value_lines[5])
            if len(value_lines) > 5 and re.search(
                r"\d{1,2}\s+[A-Za-z]+\s+\d{4}", value_lines[5]
            ):
                result["tanggal_selesai_cuti"] = value_lines[5]
                print(f"✓ Tanggal Selesai: {result['tanggal_selesai_cuti']}")

            # Nomor Surat Masuk - remaining value (value_lines[6])
            if len(value_lines) > 6:
                nomor = value_lines[6]
                # Clean from "Mengetahui" or other following sections
                nomor = re.sub(
                    r"\s*(Mengetahui|Atasan|Di\s*-).*", "", nomor, flags=re.IGNORECASE
                ).strip()
                if nomor:
                    result["no_suratmasuk"] = nomor
                    print(f"✓ Nomor Surat Masuk: {result['no_suratmasuk']}")

    # === SECTION 3: JENIS CUTI ===
    print("\n--- Section 3: Jenis Cuti ---")

    # Detect checked checkbox (marked with V, X, M, etc.)
    jenis_cuti_map = {
        "cuti tahunan": "Cuti Tahunan",
        "cuti besar": "Cuti Besar",
        "cuti sakit": "Cuti Sakit",
        "cuti melahirkan": "Cuti Melahirkan",
        "cuti alasan penting": "Cuti Alasan Penting",
        "cuti luar negara": "Cuti Luar Negara",
    }

    # Strategy: Find all jenis cuti mentions
    # The one WITHOUT U) O) prefix is the selected one
    selected_cuti = None
    for i, line in enumerate(lines):
        # Skip empty lines
        if not line.strip():
            continue

        # Check each jenis cuti
        for key, value in jenis_cuti_map.items():
            if key in line.lower():
                # Check if line starts with U) or O) (means NOT selected)
                line_stripped = line.strip()
                if (
                    line_stripped.startswith("U)")
                    or line_stripped.startswith("O)")
                    or line_stripped.startswith("CJ)")
                ):
                    print(f"  Found (NOT selected): {value} - {line_stripped}")
                else:
                    # This is the selected one!
                    print(f"  Found (SELECTED): {value} - {line_stripped}")
                    selected_cuti = value
                    break

        if selected_cuti:
            break

    if selected_cuti:
        result["jenis_cuti"] = selected_cuti
        print(f"✓ Jenis Cuti: {result['jenis_cuti']}")

    # === ADDITIONAL DATA ===
    result["jenis_surat"] = "Cuti"
    result["pengirim"] = result["nama"] if result["nama"] != "Tidak terbaca" else "N/A"
    result["penerima"] = "Ketua Pengadilan Agama"
    result["isi"] = (
        f"Surat Permintaan Cuti oleh {result['nama']} (NIP: {result['nip']}) - {result['jenis_cuti']}"
    )

    # Print summary
    print("\n" + "=" * 70)
    print("HASIL EKSTRAKSI")
    print("=" * 70)
    for key, value in result.items():
        if key not in ["jenis_surat", "pengirim", "penerima", "isi"]:
            status = "✓" if value != "Tidak terbaca" else "✗"
            print(f"{status} {key:25s}: {value}")
    print("=" * 70 + "\n")

    # Save extraction result
    try:
        result_path = os.path.join(UPLOAD_FOLDER, "debug_extraction_v2_result.txt")
        with open(result_path, "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write("HASIL EKSTRAKSI OCR CUTI (V2)\n")
            f.write("=" * 70 + "\n")
            for key, value in result.items():
                status = "✓" if value != "Tidak terbaca" else "✗"
                f.write(f"{status} {key:25s}: {value}\n")
            f.write("=" * 70 + "\n")
        print(f"✓ Extraction result saved to: {result_path}")
    except Exception as e:
        print(f"✗ Error saving extraction result: {e}")

    return result


@ocr_cuti_v2_bp.route("/", methods=["GET", "POST"])
@login_required
def ocr_cuti_v2():
    if request.method == "GET":
        return render_template("cuti/ocr_cuti_v2.html")

    # Handle POST request for OCR processing
    if "image" not in request.files:
        flash("Tidak ada file yang diunggah.", "error")
        return render_template("cuti/ocr_cuti_v2.html")

    files = request.files.getlist("image")
    if not files or files[0].filename == "":
        flash("Tidak ada file yang dipilih.", "error")
        return render_template("cuti/ocr_cuti_v2.html")

    extracted_data_list = []

    for file in files:
        if file.filename == "":
            continue

        # Check file type
        allowed_extensions = {"png", "jpg", "jpeg", "webp", "pdf"}
        if (
            not file.filename
            or "." not in file.filename
            or file.filename.rsplit(".", 1)[1].lower() not in allowed_extensions
        ):
            flash(
                f"Format file {file.filename} tidak didukung. Gunakan PNG, JPG, JPEG, WEBP, atau PDF.",
                "error",
            )
            continue

        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            random_str = "".join(
                random.choices(string.ascii_lowercase + string.digits, k=6)
            )
            original_filename = secure_filename(file.filename)
            file_ext = original_filename.rsplit(".", 1)[1].lower()
            unique_filename = f"cuti_{timestamp}_{random_str}.{file_ext}"

            # Save file to upload folder
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

            # Reset file pointer and save
            file.seek(0)
            file.save(file_path)

            # Store relative path for database and URL
            relative_path = f"ocr/cuti/{unique_filename}"

            extracted_text = ""

            if file_ext == "pdf":
                # Proses file PDF
                if not PDF_SUPPORT:
                    flash(
                        f"Dukungan PDF tidak tersedia. Install pdf2image: pip install pdf2image",
                        "error",
                    )
                    continue

                # Read file from saved path for OCR
                logger.info(f"Processing PDF file: {file_path}")
                logger.info(f"File size: {os.path.getsize(file_path)} bytes")

                if not os.path.exists(file_path):
                    flash(f"File tidak ditemukan: {file.filename}", "error")
                    logger.error(f"File not found: {file_path}")
                    continue

                extracted_text = extract_text_from_pdf(file_path)

                if not extracted_text:
                    flash(
                        f"Gagal memproses PDF: {file.filename}. Pastikan pdf2image dan poppler terinstall dengan benar.",
                        "error",
                    )
                    logger.error(f"Failed to extract text from PDF: {file.filename}")
                    logger.error(f"PDF_SUPPORT status: {PDF_SUPPORT}")
                    continue

                logger.info(
                    f"Successfully extracted {len(extracted_text)} characters from PDF"
                )
            else:
                # Proses file gambar
                import pytesseract
                from PIL import Image

                logger.info(f"Processing image file: {file_path}")
                try:
                    image = Image.open(file_path)
                    extracted_text = pytesseract.image_to_string(image, lang="ind")
                    logger.info(
                        f"Successfully extracted {len(extracted_text)} characters from image"
                    )
                except Exception as img_error:
                    flash(
                        f"Gagal memproses gambar: {file.filename}. Error: {str(img_error)}",
                        "error",
                    )
                    logger.error(
                        f"Failed to process image {file.filename}: {str(img_error)}"
                    )
                    continue

            if not extracted_text.strip():
                flash(
                    f"Tidak ada teks yang dapat diekstrak dari {file.filename}.",
                    "error",
                )
                continue

            # Extract specific fields for cuti form
            logger.info(f"Extracting cuti fields from {original_filename}")
            extracted_data = extract_cuti_fields(extracted_text)
            extracted_data["filename"] = original_filename
            extracted_data["file_path"] = relative_path
            extracted_data["file_type"] = file_ext
            extracted_data_list.append(extracted_data)

            logger.info(f"Successfully processed {original_filename}")

        except Exception as e:
            flash(f"Error saat memproses {file.filename}: {str(e)}", "error")
            logger.error(f"Exception processing {file.filename}: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())
            continue

    if extracted_data_list:
        flash(f"{len(extracted_data_list)} dokumen berhasil diproses.", "success")

    return render_template(
        "cuti/ocr_cuti_v2.html", extracted_data_list=extracted_data_list
    )


@ocr_cuti_v2_bp.route("/list", methods=["GET"])
@login_required
def list_cuti_v2():
    """Menampilkan daftar data cuti yang tersimpan di database"""
    try:
        cuti_list = Cuti.query.order_by(Cuti.created_at.desc()).all()
        return render_template("cuti/list_cuti.html", cuti_list=cuti_list)
    except Exception as e:
        flash(f"Error saat mengambil data cuti: {str(e)}", "error")
        return render_template("cuti/list_cuti.html", cuti_list=[])


@ocr_cuti_v2_bp.route("/check_dependencies", methods=["GET"])
@login_required
def check_dependencies():
    """Check OCR dependencies status"""
    dependencies_status = {}

    # Check pdf2image
    try:
        import pdf2image

        dependencies_status["pdf2image"] = {
            "installed": True,
            "version": getattr(pdf2image, "__version__", "unknown"),
        }

        # Try to check poppler
        try:
            import subprocess

            from pdf2image.exceptions import PDFInfoNotInstalledError

            result = subprocess.run(["pdftoppm", "-v"], capture_output=True, text=True)
            dependencies_status["poppler"] = {
                "installed": True,
                "info": result.stderr.split("\n")[0] if result.stderr else "Available",
            }
        except Exception as e:
            dependencies_status["poppler"] = {
                "installed": False,
                "error": str(e),
                "note": "Install with: brew install poppler (macOS) or apt-get install poppler-utils (Linux/Windows WSL)",
            }
    except ImportError as e:
        dependencies_status["pdf2image"] = {
            "installed": False,
            "error": str(e),
            "note": "Install with: pip install pdf2image",
        }

    # Check pytesseract
    try:
        import pytesseract

        dependencies_status["pytesseract"] = {
            "installed": True,
            "version": getattr(pytesseract, "__version__", "unknown"),
        }

        # Check tesseract binary
        try:
            version = pytesseract.get_tesseract_version()
            dependencies_status["tesseract"] = {
                "installed": True,
                "version": str(version),
            }
        except Exception as e:
            dependencies_status["tesseract"] = {
                "installed": False,
                "error": str(e),
                "note": "Install tesseract-ocr binary for your OS",
            }
    except ImportError as e:
        dependencies_status["pytesseract"] = {
            "installed": False,
            "error": str(e),
            "note": "Install with: pip install pytesseract",
        }

    # Check PIL/Pillow
    try:
        import PIL
        from PIL import Image

        dependencies_status["Pillow"] = {"installed": True, "version": PIL.__version__}
    except ImportError as e:
        dependencies_status["Pillow"] = {
            "installed": False,
            "error": str(e),
            "note": "Install with: pip install Pillow",
        }

    # Check upload folder
    dependencies_status["upload_folder"] = {
        "path": UPLOAD_FOLDER,
        "exists": os.path.exists(UPLOAD_FOLDER),
        "writable": os.access(UPLOAD_FOLDER, os.W_OK)
        if os.path.exists(UPLOAD_FOLDER)
        else False,
    }

    return jsonify(
        {
            "success": True,
            "dependencies": dependencies_status,
            "PDF_SUPPORT": PDF_SUPPORT,
        }
    )


@ocr_cuti_v2_bp.route("/save_extracted_data", methods=["POST"])
@login_required
def save_extracted_data_v2():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        saved_count = 0

        for item in data:
            try:
                if item.get("jenis_surat") == "Cuti":
                    save_cuti_data(item)
                    saved_count += 1
            except Exception as e:
                print(f"Error saving item: {str(e)}")
                return jsonify(
                    {"success": False, "error": f"Error saving item: {str(e)}"}
                ), 500

        return jsonify(
            {
                "success": True,
                "message": f"Data saved successfully. {saved_count} items saved.",
            }
        ), 200

    except Exception as e:
        print(f"Server error: {str(e)}")
        return jsonify({"success": False, "error": f"Server error: {str(e)}"}), 500


def save_cuti_data(item):
    """Save cuti data to database"""
    try:
        # Parse tanggal
        tgl_mulai = tgl_selesai = None

        # Parse Tanggal Mulai Cuti
        if (
            item.get("tanggal_mulai_cuti")
            and item["tanggal_mulai_cuti"] != "Tidak terbaca"
        ):
            try:
                # Try parsing "14 Januari 2026" format
                tgl_str = item["tanggal_mulai_cuti"]
                # Convert Indonesian month names to numbers
                months = {
                    "januari": 1,
                    "februari": 2,
                    "maret": 3,
                    "april": 4,
                    "mei": 5,
                    "juni": 6,
                    "juli": 7,
                    "agustus": 8,
                    "september": 9,
                    "oktober": 10,
                    "november": 11,
                    "desember": 12,
                }
                parts = tgl_str.split()
                if len(parts) == 3:
                    day = int(parts[0])
                    month = months.get(parts[1].lower(), 1)
                    year = int(parts[2])
                    tgl_mulai = datetime(year, month, day).date()
            except Exception as e:
                print(f"Error parsing tanggal_mulai_cuti: {str(e)}")
                tgl_mulai = datetime.utcnow().date()

        # Parse Tanggal Selesai Cuti
        if (
            item.get("tanggal_selesai_cuti")
            and item["tanggal_selesai_cuti"] != "Tidak terbaca"
        ):
            try:
                tgl_str = item["tanggal_selesai_cuti"]
                months = {
                    "januari": 1,
                    "februari": 2,
                    "maret": 3,
                    "april": 4,
                    "mei": 5,
                    "juni": 6,
                    "juli": 7,
                    "agustus": 8,
                    "september": 9,
                    "oktober": 10,
                    "november": 11,
                    "desember": 12,
                }
                parts = tgl_str.split()
                if len(parts) == 3:
                    day = int(parts[0])
                    month = months.get(parts[1].lower(), 1)
                    year = int(parts[2])
                    tgl_selesai = datetime(year, month, day).date()
            except Exception as e:
                print(f"Error parsing tanggal_selesai_cuti: {str(e)}")
                tgl_selesai = tgl_mulai if tgl_mulai else datetime.utcnow().date()

        # Create Cuti object
        cuti = Cuti(
            nama=item.get("nama", "Tidak terbaca"),
            nip=item.get("nip", "Tidak terbaca"),
            jabatan=item.get("jabatan", "Tidak terbaca"),
            gol_ruang=item.get("gol_ruang", "Tidak terbaca"),
            unit_kerja=item.get("unit_kerja", "Tidak terbaca"),
            masa_kerja=item.get("masa_kerja", "Tidak terbaca"),
            alamat=item.get("alamat", "Tidak terbaca"),
            no_suratmasuk=item.get("no_suratmasuk", "Tidak terbaca"),
            tgl_ajuan_cuti=datetime.utcnow().date(),
            tanggal_cuti=tgl_mulai if tgl_mulai else datetime.utcnow().date(),
            sampai_cuti=tgl_selesai if tgl_selesai else datetime.utcnow().date(),
            telp=item.get("telp", "Tidak terbaca"),
            jenis_cuti=item.get("jenis_cuti", "Tidak terbaca"),
            alasan_cuti=item.get("alasan_cuti", "Tidak terbaca"),
            lama_cuti=item.get("lama_cuti", "Tidak terbaca"),
            status_cuti="pending",
            pdf_path=item.get("file_path", None),
        )

        db.session.add(cuti)
        db.session.commit()
        print(f"✓ Cuti data saved successfully for {cuti.nama}")

    except Exception as e:
        print(f"✗ Error in save_cuti_data: {str(e)}")
        db.session.rollback()
        raise e
