#!/usr/bin/env python
# -*- coding: utf-8 -*-

fpath = "..\\.venv\\Scripts\\Script Analyse\\analyse.py"
with open(fpath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Commenter la section 12 qui est problématique
new_lines = []
in_section_12 = False
for line in lines:
    if "# 12) NOUVEAU" in line:
        in_section_12 = True
        new_lines.append("# [SKIPPED DUE TO PANDAS BUG] " + line)
    elif in_section_12 and ("# 13) NOUVEAU" in line or "# HTML index" in line):
        in_section_12 = False
        new_lines.append(line)
    elif in_section_12:
        if line.strip():
            new_lines.append("#"  + line)
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

with open(fpath, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
    
print("[OK] Section 12 commentee")
