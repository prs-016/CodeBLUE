import os
import glob

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    if '| None' not in content:
        return

    # Add import typing Optional
    if 'from typing import Optional' not in content:
        content = content.replace('from pydantic import', 'from typing import Optional\nfrom pydantic import')

    # Replace specific patterns
    content = content.replace('str | None', 'Optional[str]')
    content = content.replace('float | None', 'Optional[float]')

    with open(filepath, 'w') as f:
        f.write(content)

if __name__ == '__main__':
    for py_file in glob.glob('/Users/divyanshkanodia/Desktop/CodeBLUE/threshold/backend/**/*.py', recursive=True):
        fix_file(py_file)
    print("Files fixed.")
