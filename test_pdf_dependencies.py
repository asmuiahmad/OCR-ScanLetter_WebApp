#!/usr/bin/env python3
"""
Standalone script to test PDF processing dependencies for OCR Cuti V2
Run this script to diagnose issues with PDF processing
"""

import os
import sys

print("=" * 60)
print("Testing PDF Processing Dependencies for OCR Cuti V2")
print("=" * 60)
print()

# Test 1: Check Python version
print("1. Python Version:")
print(f"   ✓ {sys.version}")
print()

# Test 2: Check pdf2image
print("2. Testing pdf2image...")
try:
    import pdf2image

    print(f"   ✓ pdf2image is installed")
    if hasattr(pdf2image, "__version__"):
        print(f"   ✓ Version: {pdf2image.__version__}")
    else:
        print(f"   ⚠ Version: unknown")
except ImportError as e:
    print(f"   ✗ pdf2image NOT installed")
    print(f"   ✗ Error: {e}")
    print(f"   → Install with: pip install pdf2image")
    pdf2image = None
print()

# Test 3: Check Poppler (required for pdf2image)
print("3. Testing Poppler...")
if pdf2image:
    try:
        import subprocess

        result = subprocess.run(
            ["pdftoppm", "-v"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 or "version" in result.stderr.lower():
            print(f"   ✓ Poppler is installed")
            version_line = result.stderr.split("\n")[0] if result.stderr else "unknown"
            print(f"   ✓ {version_line}")
        else:
            print(f"   ⚠ Poppler may not be properly configured")
    except FileNotFoundError:
        print(f"   ✗ Poppler NOT found")
        print(f"   → macOS: brew install poppler")
        print(f"   → Ubuntu/Debian: sudo apt-get install poppler-utils")
        print(
            f"   → Windows: Download from https://github.com/oschwartz10612/poppler-windows/releases/"
        )
    except Exception as e:
        print(f"   ⚠ Could not verify Poppler: {e}")
else:
    print(f"   ⊘ Skipped (pdf2image not available)")
print()

# Test 4: Check pytesseract
print("4. Testing pytesseract...")
try:
    import pytesseract

    print(f"   ✓ pytesseract is installed")
    if hasattr(pytesseract, "__version__"):
        print(f"   ✓ Version: {pytesseract.__version__}")

    # Try to get tesseract version
    try:
        version = pytesseract.get_tesseract_version()
        print(f"   ✓ Tesseract OCR binary: v{version}")
    except Exception as e:
        print(f"   ✗ Tesseract OCR binary NOT found or not configured")
        print(f"   ✗ Error: {e}")
        print(f"   → macOS: brew install tesseract")
        print(f"   → Ubuntu/Debian: sudo apt-get install tesseract-ocr")
        print(
            f"   → Windows: Download installer from https://github.com/UB-Mannheim/tesseract/wiki"
        )
except ImportError as e:
    print(f"   ✗ pytesseract NOT installed")
    print(f"   ✗ Error: {e}")
    print(f"   → Install with: pip install pytesseract")
print()

# Test 5: Check PIL/Pillow
print("5. Testing Pillow (PIL)...")
try:
    import PIL
    from PIL import Image

    print(f"   ✓ Pillow is installed")
    print(f"   ✓ Version: {PIL.__version__}")
except ImportError as e:
    print(f"   ✗ Pillow NOT installed")
    print(f"   ✗ Error: {e}")
    print(f"   → Install with: pip install Pillow")
print()

# Test 6: Test actual PDF conversion (if all dependencies are available)
print("6. Testing PDF Conversion...")
if pdf2image and "pytesseract" in sys.modules and "PIL" in sys.modules:
    try:
        # Try to create a simple test
        print(f"   → Attempting to test pdf2image.convert_from_path...")

        # Check if we have a test PDF
        test_pdf_paths = [
            "static/ocr/cuti/surat_cuti_ahmad_asmui_2026-01-13.pdf",
            "test.pdf",
            "sample.pdf",
        ]

        test_pdf = None
        for path in test_pdf_paths:
            if os.path.exists(path):
                test_pdf = path
                break

        if test_pdf:
            print(f"   → Found test PDF: {test_pdf}")
            images = pdf2image.convert_from_path(test_pdf, first_page=1, last_page=1)
            if images:
                print(f"   ✓ Successfully converted PDF to image!")
                print(f"   ✓ Image size: {images[0].size}")

                # Try OCR on the first page
                import pytesseract

                text = pytesseract.image_to_string(images[0], lang="ind")
                print(f"   ✓ Successfully extracted text ({len(text)} characters)")
                if text.strip():
                    print(f"   ✓ Sample text: {text[:100]}...")
                else:
                    print(f"   ⚠ Warning: No text extracted (image may be blank)")
            else:
                print(f"   ✗ PDF conversion returned no images")
        else:
            print(f"   ⊘ No test PDF found in common locations")
            print(f"   → Place a test PDF in project root to test conversion")

    except Exception as e:
        print(f"   ✗ PDF conversion test failed")
        print(f"   ✗ Error: {e}")
        import traceback

        print(f"   ✗ Traceback:")
        traceback.print_exc()
else:
    print(f"   ⊘ Skipped (missing dependencies)")
print()

# Test 7: Check upload folder
print("7. Testing upload folder...")
upload_folder = "static/ocr/cuti"
try:
    if os.path.exists(upload_folder):
        print(f"   ✓ Upload folder exists: {upload_folder}")
        if os.access(upload_folder, os.W_OK):
            print(f"   ✓ Upload folder is writable")

            # List files in folder
            files = os.listdir(upload_folder)
            print(f"   ✓ Files in folder: {len(files)}")
            if files:
                print(f"   → Sample files: {', '.join(files[:5])}")
        else:
            print(f"   ✗ Upload folder is NOT writable")
            print(f"   → Check folder permissions")
    else:
        print(f"   ⚠ Upload folder does NOT exist: {upload_folder}")
        print(f"   → Will be created automatically")
except Exception as e:
    print(f"   ✗ Error checking upload folder: {e}")
print()

# Summary
print("=" * 60)
print("Summary:")
print("=" * 60)

all_ok = True

if "pdf2image" not in sys.modules:
    print("✗ pdf2image is NOT installed")
    all_ok = False
else:
    try:
        subprocess.run(["pdftoppm", "-v"], capture_output=True, timeout=5)
        print("✓ PDF processing is ready (pdf2image + poppler)")
    except:
        print("⚠ pdf2image installed but poppler NOT found")
        all_ok = False

if "pytesseract" not in sys.modules:
    print("✗ pytesseract is NOT installed")
    all_ok = False
else:
    try:
        import pytesseract

        pytesseract.get_tesseract_version()
        print("✓ OCR is ready (pytesseract + tesseract)")
    except:
        print("⚠ pytesseract installed but tesseract binary NOT found")
        all_ok = False

if "PIL" not in sys.modules:
    print("✗ Pillow is NOT installed")
    all_ok = False
else:
    print("✓ Image processing is ready (Pillow)")

print()
if all_ok:
    print("🎉 All dependencies are installed and working!")
    print("   OCR Cuti V2 should work properly.")
else:
    print("⚠ Some dependencies are missing or not working.")
    print("   Please install the missing dependencies.")
    print()
    print("Quick install commands:")
    print("  pip install pdf2image pytesseract Pillow")
    print()
    print("System dependencies:")
    print("  macOS: brew install poppler tesseract")
    print(
        "  Ubuntu/Debian: sudo apt-get install poppler-utils tesseract-ocr tesseract-ocr-ind"
    )

print("=" * 60)
