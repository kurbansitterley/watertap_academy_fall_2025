#!/usr/bin/env python

import argparse
from contextlib import chdir
from glob import glob
import os
from pathlib import Path
import shutil

script_dir = Path(__file__).parent.resolve()


def main(**kwargs):
    with chdir(script_dir):
        copy_files(**kwargs)


def copy_files(debug=False, cleanup=False):
    this_file = Path(__file__).name
    nawi_dir = Path.home() / ".nawi"
    custom_fs = nawi_dir / "custom_flowsheets"
    for pyfile in glob("*.py"):
        if not pyfile.startswith("custom_flowsheet") and pyfile != this_file:
            target = custom_fs / pyfile
            if cleanup:
                if target.exists():
                    if debug:
                        print(f"remove '{target}'")
                    try:
                        os.unlink(target)
                    except OSError:
                        pass
            else:
                if debug:
                    print(f"copy '{pyfile}' -> {target}'")
                shutil.copyfile(pyfile, target)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument(
        "-d", "--debug", action="store_true", help="Print some debug messages"
    )
    p.add_argument("-c", "--cleanup", action="store_true", help="Remove file copies")
    args = p.parse_args()
    main(debug=args.debug, cleanup=args.cleanup)
