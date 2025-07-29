#!/usr/bin/env python3
"""
generate_filelist.py  –  Create filelist.json with every data file
in *this* directory.

Usage:
    $ python generate_filelist.py
"""

import json
from pathlib import Path

# --- configuration ----------------------------------------------------------
# If you only want certain extensions, change the tuple below, e.g. (".bin",)
INCLUDE_EXTENSIONS = (".bin", ".json", ".txt")  # keep .json if patterns use JSON
EXCLUDE_FILES = {
    "filelist.json",          # output file – don’t include it in the list
    Path(__file__).name,      # this script itself
}
# ---------------------------------------------------------------------------

def main() -> None:
    here = Path(__file__).resolve().parent
    files = sorted(
        f.name
        for f in here.iterdir()
        if f.is_file()
        and f.name not in EXCLUDE_FILES
        and (not INCLUDE_EXTENSIONS or f.suffix in INCLUDE_EXTENSIONS)
    )

    outfile = here / "filelist.json"
    outfile.write_text(json.dumps(files, indent=2), encoding="utf-8")
    print(f"Wrote {outfile} with {len(files)} filenames.")


if __name__ == "__main__":
    main()
