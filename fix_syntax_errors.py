#!/usr/bin/env python3
"""
Fix syntax errors in cuti_routes.py
"""

# Read the file
with open('config/cuti_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the unterminated string literal
content = content.replace("replace('\\', '_')", "replace('\\\\', '_')")

# Write back
with open('config/cuti_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed syntax errors in cuti_routes.py")