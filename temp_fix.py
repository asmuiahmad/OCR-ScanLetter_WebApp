with open('config/routes.py', 'r') as f:
    lines = f.readlines()

# Find the line numbers for the functions we need to fix
approve_start = -1
reject_start = -1

for i, line in enumerate(lines):
    if 'def approve_surat_keluar' in line:
        approve_start = i
    if 'def reject_surat_keluar' in line:
        reject_start = i

# Fix approve_surat_keluar function
if approve_start != -1:
    # Replace the problematic lines
    lines[approve_start+1:approve_start+7] = [
        '    try:\n',
        '        surat = SuratKeluar.query.get_or_404(surat_id)\n',
        '        surat.status_suratKeluar = \'approved\'\n',
        '        \n',
        '        db.session.commit()\n',
        '        return jsonify({"success": True, "message": "Surat keluar berhasil disetujui"})\n'
    ]

# Fix reject_surat_keluar function
if reject_start != -1:
    # Replace the problematic lines
    lines[reject_start+1:reject_start+7] = [
        '    try:\n',
        '        surat = SuratKeluar.query.get_or_404(surat_id)\n',
        '        surat.status_suratKeluar = \'rejected\'\n',
        '        \n',
        '        db.session.commit()\n',
        '        return jsonify({"success": True, "message": "Surat keluar berhasil ditolak"})\n'
    ]

with open('config/routes.py', 'w') as f:
    f.writelines(lines)

print(f"Fixed functions at lines {approve_start} and {reject_start}")
