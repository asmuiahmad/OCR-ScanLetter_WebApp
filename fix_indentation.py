with open('config/routes.py', 'r') as f:
    lines = f.readlines()

# Find the problematic section
start_line = 0
for i, line in enumerate(lines):
    if '    try:' in line and i > 700 and i < 750:
        start_line = i
        break

if start_line > 0:
    # Fix indentation for context dictionary
    lines[start_line + 2] = '        context = {\n'
    
    # Write the fixed file
    with open('config/routes.py', 'w') as f:
        f.writelines(lines)
        print(f"Fixed indentation at line {start_line + 2}")
else:
    print("Could not find the problematic section")
