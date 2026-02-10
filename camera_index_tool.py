#!/usr/bin/env python3
"""
Extract embedded gzipped HTML from camera_index.h to .html files, or
re-embed edited .html back into C array format for camera_index.h.

Usage:
  python camera_index_tool.py extract [camera_index.h]
    -> Writes index_ov2640.html, index_ov3660.html, index_ov5640.html

  python camera_index_tool.py embed <name> <file.html> [camera_index.h]
    -> name: ov2640 | ov3660 | ov5640
    -> Prints C array + #define to stdout (or use --inplace to patch .h)
"""

import re
import gzip
import sys
import os

HEADER_DEFAULT = os.path.join(os.path.dirname(__file__), "camera_index.h")

def parse_c_array(lines, start_idx):
    """From line index after 'const unsigned char X[] = {', collect bytes until '};'. Returns (bytes, end_line_idx)."""
    bytes_list = []
    i = start_idx
    while i < len(lines):
        line = lines[i]
        if line.strip() == "};":
            return bytes(bytes_list), i
        for m in re.finditer(r"0x[0-9A-Fa-f]{2}", line):
            bytes_list.append(int(m.group(), 16))
        i += 1
    raise ValueError("No closing '};' found")

def find_arrays(path):
    """Yield (array_name, comment_line, define_line, data_start, bytes_data) for each array."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    i = 0
    while i < len(lines):
        m = re.match(r"//File: (index_(\w+)\.html\.gz), Size: (\d+)", lines[i])
        if m:
            comment_line = i
            file_ref, name = m.group(1), m.group(2)  # e.g. index_ov2640.html.gz, ov2640
        else:
            i += 1
            continue
        i += 1
        if i >= len(lines):
            break
        define_m = re.match(r"#define (index_\w+_html_gz_len) (\d+)", lines[i])
        if not define_m:
            i += 1
            continue
        define_line = i
        i += 1
        if i >= len(lines):
            break
        arr_m = re.match(r"const unsigned char (index_\w+_html_gz)\[\] = \{", lines[i])
        if not arr_m:
            i += 1
            continue
        data_start = i + 1
        data, end_idx = parse_c_array(lines, data_start)
        yield (name, comment_line, define_line, data_start, end_idx, data, lines)
        i = end_idx + 1

def extract(header_path=HEADER_DEFAULT, out_dir=None):
    out_dir = out_dir or os.path.dirname(header_path)
    for name, comment_line, define_line, data_start, end_idx, data, lines in find_arrays(header_path):
        try:
            html = gzip.decompress(data).decode("utf-8")
        except Exception as e:
            print(f"Warning: {name} decompress failed: {e}", file=sys.stderr)
            continue
        out_path = os.path.join(out_dir, f"index_{name}.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Wrote {out_path} ({len(html)} bytes HTML)")

def bytes_to_c_array(data, indent="  ", per_line=12):
    """Format bytes as C array lines."""
    parts = []
    for i in range(0, len(data), per_line):
        chunk = data[i : i + per_line]
        line = indent + ", ".join(f"0x{b:02X}" for b in chunk)
        if i + per_line < len(data):
            line += ","
        parts.append(line)
    return "\n".join(parts)

def embed(name, html_path, header_path=HEADER_DEFAULT, inplace=False):
    if name not in ("ov2640", "ov3660", "ov5640"):
        print(f"Invalid name: {name}. Use ov2640, ov3660, or ov5640.", file=sys.stderr)
        sys.exit(1)
    with open(html_path, "rb") as f:
        html = f.read()
    gz = gzip.compress(html, compresslevel=9)
    var_name = f"index_{name}_html_gz"
    len_name = f"{var_name}_len"
    comment = f"//File: index_{name}.html.gz, Size: {len(gz)}"
    define = f"#define {len_name} {len(gz)}"
    decl = f"const unsigned char {var_name}[] = {{"
    body = bytes_to_c_array(gz)
    block = f"{comment}\n{define}\n{decl}\n{body}\n}};\n"
    if inplace:
        with open(header_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        # Find this array's block (comment line through "};")
        start_line = None
        end_line = None
        for info in find_arrays(header_path):
            if info[0] == name:
                start_line = info[1]
                end_line = info[4]  # line index of "};"
                break
        if start_line is None:
            print(f"Array for {name} not found in {header_path}", file=sys.stderr)
            sys.exit(1)
        new_lines = lines[:start_line] + [block] + lines[end_line + 1 :]
        with open(header_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"Updated {header_path} with {name} ({len(gz)} gz bytes)")
    else:
        print(block)

def main():
    argv = sys.argv[1:]
    if not argv or argv[0] not in ("extract", "embed"):
        print(__doc__)
        sys.exit(0)
    cmd = argv[0]
    if cmd == "extract":
        header = argv[1] if len(argv) > 1 else HEADER_DEFAULT
        extract(header)
    else:
        # embed <name> <file.html> [camera_index.h] [--inplace]
        if len(argv) < 3:
            print("embed requires: <name> <file.html> [camera_index.h] [--inplace]", file=sys.stderr)
            sys.exit(1)
        name, html_path = argv[1], argv[2]
        header = HEADER_DEFAULT
        inplace = False
        for a in argv[3:]:
            if a == "--inplace":
                inplace = True
            elif not a.startswith("-"):
                header = a
        embed(name, html_path, header, inplace=inplace)

if __name__ == "__main__":
    main()
