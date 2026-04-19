import os
import glob

def fix_imports(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    content = "".join(lines)
    if 'Optional[' not in content or 'from typing import Optional' in content:
        return

    # Add the import just after future annotations or at the top
    for i, line in enumerate(lines):
        if not line.startswith('from __future__'):
            lines.insert(i, "from typing import Optional\n")
            break

    with open(filepath, 'w') as f:
        f.writelines(lines)

if __name__ == '__main__':
    for py_file in glob.glob('/Users/divyanshkanodia/Desktop/CodeBLUE/threshold/backend/**/*.py', recursive=True):
        fix_imports(py_file)
    print("Imports fixed.")
