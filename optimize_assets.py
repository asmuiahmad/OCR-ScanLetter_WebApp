#!/usr/bin/env python3
"""
Asset Optimization Script
Minifies and compresses CSS/JS files for better performance
"""

import os
import re
import gzip
import json
from pathlib import Path

def minify_css(css_content):
    """Minify CSS content"""
    # Remove comments
    css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
    
    # Remove unnecessary whitespace
    css_content = re.sub(r'\s+', ' ', css_content)
    css_content = re.sub(r';\s*}', '}', css_content)
    css_content = re.sub(r'{\s*', '{', css_content)
    css_content = re.sub(r'}\s*', '}', css_content)
    css_content = re.sub(r':\s*', ':', css_content)
    css_content = re.sub(r';\s*', ';', css_content)
    css_content = re.sub(r',\s*', ',', css_content)
    
    return css_content.strip()

def minify_js(js_content):
    """Basic JS minification"""
    # Remove single-line comments
    js_content = re.sub(r'//.*$', '', js_content, flags=re.MULTILINE)
    
    # Remove multi-line comments
    js_content = re.sub(r'/\*.*?\*/', '', js_content, flags=re.DOTALL)
    
    # Remove unnecessary whitespace
    js_content = re.sub(r'\s+', ' ', js_content)
    js_content = re.sub(r';\s*', ';', js_content)
    js_content = re.sub(r'{\s*', '{', js_content)
    js_content = re.sub(r'}\s*', '}', js_content)
    
    return js_content.strip()

def create_gzip_version(file_path):
    """Create gzipped version of file"""
    with open(file_path, 'rb') as f_in:
        with gzip.open(f"{file_path}.gz", 'wb') as f_out:
            f_out.writelines(f_in)

def optimize_assets():
    """Optimize all CSS and JS assets"""
    static_dir = Path('static/assets')
    
    # CSS files to optimize
    css_files = [
        'css/modal.css',
        'css/ocr-pages.css',
        'css/ocr-modal-fix.css',
        'css/dashboard.css'
    ]
    
    # JS files to optimize
    js_files = [
        'js/ocr-modal-optimized.js',
        'js/force-300px-height.js'
    ]
    
    print("🚀 Starting asset optimization...")
    
    # Optimize CSS files
    for css_file in css_files:
        file_path = static_dir / css_file
        if file_path.exists():
            print(f"📄 Processing {css_file}...")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Minify
            minified = minify_css(content)
            
            # Save minified version
            min_path = file_path.with_suffix('.min.css')
            with open(min_path, 'w', encoding='utf-8') as f:
                f.write(minified)
            
            # Create gzipped version
            create_gzip_version(min_path)
            
            original_size = len(content)
            minified_size = len(minified)
            savings = ((original_size - minified_size) / original_size) * 100
            
            print(f"   ✅ {original_size} → {minified_size} bytes ({savings:.1f}% smaller)")
    
    # Optimize JS files
    for js_file in js_files:
        file_path = static_dir / js_file
        if file_path.exists():
            print(f"📄 Processing {js_file}...")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Minify
            minified = minify_js(content)
            
            # Save minified version
            min_path = file_path.with_suffix('.min.js')
            with open(min_path, 'w', encoding='utf-8') as f:
                f.write(minified)
            
            # Create gzipped version
            create_gzip_version(min_path)
            
            original_size = len(content)
            minified_size = len(minified)
            savings = ((original_size - minified_size) / original_size) * 100
            
            print(f"   ✅ {original_size} → {minified_size} bytes ({savings:.1f}% smaller)")
    
    # Create asset manifest
    manifest = {
        "css": {
            "modal": "css/modal.min.css",
            "ocr-pages": "css/ocr-pages.min.css", 
            "ocr-modal-fix": "css/ocr-modal-fix.min.css",
            "dashboard": "css/dashboard.min.css"
        },
        "js": {
            "ocr-modal": "js/ocr-modal-optimized.min.js",
            "force-height": "js/force-300px-height.min.js"
        },
        "version": "1.0.0",
        "timestamp": int(time.time())
    }
    
    with open(static_dir / 'manifest.json', 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print("\n🎉 Asset optimization complete!")
    print("📋 Created asset manifest at static/assets/manifest.json")
    print("💡 Don't forget to update your templates to use .min.css and .min.js files")

if __name__ == "__main__":
    import time
    optimize_assets()