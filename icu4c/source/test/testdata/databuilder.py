"""Bazel-friendly wrapper around 'databuilder' to generate test data."""

import argparse
import atexit
import os
import shutil

import source.python.icutools.databuilder.__main__ as db

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--src_dir", required=True, help="The source directory containing the data files."
    )

    parser.add_argument(
        "--out_dir",
        required=True,
        help="The output directory where the generated data files will be placed.",
    )

    parser.add_argument(
        "--tmp_dir",
        required=True,
        help="The temporary directory where intermediate files will be placed.",
    )

    parser.add_argument(
        "--icu_data",
        required=True,
        help="The path to the ICU data file (e.g., icudt76l.dat) that will be used by databuilder.",
    )

    args, rest = parser.parse_known_args()

    src_dir = os.path.dirname(args.src_dir)
    out_dir = args.out_dir
    tmp_dir = args.tmp_dir

    # This is to match databuilder's expectation that the ICU data file is located
    # in the build root directory.
    os.makedirs(os.path.join(out_dir, "build"), exist_ok=True)
    shutil.copy(args.icu_data, os.path.join(out_dir, "build", os.path.basename(args.icu_data)))
    atexit.register(lambda: shutil.rmtree(os.path.join(out_dir, "build"), ignore_errors=True))

    args = [f"--src_dir={src_dir}", f"--out_dir={out_dir}", f"--tmp_dir={tmp_dir}"] + rest
    db.main(args)
    # The generated files list is produced under the temporary directory which we are not
    # capturing as an output directory because it's mostly intermediate files. However, we
    # need the 'testdata.lst' for the pkgdata invocation. Thus, we move it over.
    shutil.move(os.path.join(tmp_dir, "testdata.lst"), os.path.join(out_dir, "testdata.lst"))
