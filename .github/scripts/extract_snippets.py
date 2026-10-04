#!/usr/bin/env python3
"""Extract fenced bash, sh, zsh, and python blocks from tracked Markdown.

Apart from monocle/scripts/verify_report.py, the commands an agent copies
and runs live in fenced code blocks in SKILL.md, references/, and README.md. This
writes each block to its own file so the security-scan workflow can syntax-
check and lint it, and records where it came from in manifest.tsv:

    <kind>\t<markdown file>\t<fence line>\t<indent>\t<snippet path>

Snippet line N (line 1 is the added shebang) maps to Markdown line
<fence line> + N - 1, column + <indent>. CommonMark backtick and tilde
fences are supported, including fences longer than three characters.

Usage: extract_snippets.py <output directory>
"""

import re
import subprocess
import sys
from pathlib import Path

FENCE_OPEN = re.compile(r"^(\s*)(`{3,}|~{3,})\s*(?:([A-Za-z0-9_+-]+)\b.*)?$")
KINDS = {"bash": "bash", "sh": "sh", "zsh": "zsh", "python": "python", "py": "python"}
SHEBANGS = {
    "bash": "#!/bin/bash\n",
    "sh": "#!/bin/sh\n",
    "zsh": "#!/bin/zsh\n",
    "python": "#!/usr/bin/env python3\n",
}
EXTENSIONS = {"bash": "bash", "sh": "sh", "zsh": "zsh", "python": "py"}


def is_closing_fence(line, fence):
    marker = re.escape(fence[0])
    return re.match(rf"^\s*{marker}{{{len(fence)},}}\s*$", line) is not None


def main():
    out_dir = Path(sys.argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = []

    for md_name in subprocess.check_output(["git", "ls-files", "*.md"], text=True).splitlines():
        lines = Path(md_name).read_text(encoding="utf-8").splitlines()
        i = 0
        while i < len(lines):
            match = FENCE_OPEN.match(lines[i])
            if not match:
                i += 1
                continue

            indent = len(match.group(1))
            fence = match.group(2)
            kind = KINDS.get((match.group(3) or "").lower())
            fence_line = i + 1
            j = i + 1
            while j < len(lines) and not is_closing_fence(lines[j], fence):
                j += 1

            if kind:
                body = "".join(
                    (line[indent:] if not line[:indent].strip() else line) + "\n"
                    for line in lines[i + 1 : j]
                )
                stem = re.sub(r"[^A-Za-z0-9]+", "_", md_name)
                snippet = out_dir / f"{stem}_L{fence_line}.{EXTENSIONS[kind]}"
                snippet.write_text(SHEBANGS[kind] + body, encoding="utf-8")
                manifest.append(f"{kind}\t{md_name}\t{fence_line}\t{indent}\t{snippet}")

            i = j + 1

    (out_dir / "manifest.tsv").write_text("".join(f"{row}\n" for row in manifest), encoding="utf-8")
    print(f"Extracted {len(manifest)} snippet(s) to {out_dir}")


if __name__ == "__main__":
    main()
