"""
OCR routes
OCR testing and processing functionality
"""

import os
import tempfile

import pytesseract
from flask import (
    Blueprint,
    current_app,
    flash,
    render_template,
    request,
    send_from_directory,
)
from flask_login import login_required
from werkzeug.utils import secure_filename

ocr_routes_bp = Blueprint("ocr_routes", __name__)


@ocr_routes_bp.route("/favicon.ico")
def favicon():
    """Serve favicon"""
    return send_from_directory(
        os.path.join(current_app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )
