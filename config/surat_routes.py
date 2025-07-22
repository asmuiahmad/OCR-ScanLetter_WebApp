"""
Surat routes
Handles surat masuk and surat keluar management
"""

import io
import tempfile
import subprocess
from datetime import datetime
from collections import defaultdict
from calendar import monthrange

import pytesseract
from flask import (
    Blueprint, render_template, request, send_file, redirect, url_for,
    flash, jsonify, current_app, send_from_directory
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import desc, asc, extract, func, or_
from docx import Document
from mailmerge import MailMerge

from config.extensions import db
from config.models import SuratKeluar, SuratMasuk
from config.forms import SuratKeluarForm, SuratMasukForm
from config.route_utils import role_required
from config.ocr_utils import hitung_field_not_found

surat_bp = Blueprint('surat', __name__)

# Seluruh endpoint surat keluar dan surat masuk sudah dipindahkan ke surat_keluar_routes.py dan surat_masuk_routes.py
# File ini bisa dikosongkan atau hanya berisi blueprint kosong jika ingin tetap register surat_bp