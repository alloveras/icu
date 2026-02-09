# Copyright (C) 2024 and later: Unicode, Inc. and others.
# License & terms of use: http://www.unicode.org/copyright.html

"""Wrapper script for generating ICU test data in Bazel.

This script orchestrates the ICU test data generation pipeline:
1. databuilder - generates .res files from source test data
2. pkgdata - packages .res files into a .dat archive
3. genccode - converts .dat to assembly for static linking

Additionally handles:
- Copying the main ICU data file for genrb collation compilation
- Copying standalone test files (zoneinfo64.res, nam.typ)
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import tempfile


def run_databuilder(
    src_dir: str,
    out_dir: str,
    tmp_dir: str,
    tool_dir: str,
    verbose: bool = False,
) -> None:
    """Run the databuilder to generate .res files."""
    # Import databuilder module directly to avoid subprocess issues with Bazel
    # Add the python directory to path so we can import icutools
    python_dir = os.path.join(os.path.dirname(__file__), "..", "..", "python")
    if os.path.isdir(python_dir):
        sys.path.insert(0, os.path.abspath(python_dir))

    from icutools.databuilder import __main__ as databuilder_main

    argv = [
        "--mode", "windows-exec" if platform.system() == "Windows" else "unix-exec",
        "--src_dir", src_dir,
        "--out_dir", out_dir,
        "--tmp_dir", tmp_dir,
        "--tool_dir", tool_dir,
        "--seqmode", "parallel",
    ]
    if verbose:
        argv.append("--verbose")

    if verbose:
        print(f"Running databuilder with args: {' '.join(argv)}")
    databuilder_main.main(argv)


def run_pkgdata(
    pkgdata_bin: str,
    res_dir: str,
    lst_file: str,
    pkg_name: str,
    out_dir: str,
    verbose: bool = False,
) -> None:
    """Run pkgdata to package .res files into .dat."""
    cmd = [
        pkgdata_bin,
        "-m", "common",
        "-p", pkg_name,
        "-c",
        "-s", res_dir,
        "-d", out_dir,
        lst_file,
    ]
    if verbose:
        cmd.insert(1, "-v")

    if verbose:
        print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if verbose and result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        sys.exit(result.returncode)


def run_genccode(
    genccode_bin: str,
    dat_file: str,
    entry_name: str,
    out_dir: str,
    verbose: bool = False,
) -> None:
    """Run genccode to convert .dat to assembly."""
    cmd = [
        genccode_bin,
        "--assembly", "gcc",
        "--name", entry_name,
        "--entrypoint", entry_name,
        "--destdir", out_dir,
        dat_file,
    ]
    if verbose:
        cmd.insert(1, "-v")

    if verbose:
        print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if verbose and result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        sys.exit(result.returncode)


def create_package_list(
    res_dir: str,
    lst_file: str,
    exclude_dirs: list[str] | None = None,
    verbose: bool = False,
) -> None:
    """Create a package list file from the .res directory."""
    exclude_dirs = exclude_dirs or []
    files: list[str] = []
    for root, _, filenames in os.walk(res_dir):
        # Skip excluded directories
        rel_root = os.path.relpath(root, res_dir)
        if any(rel_root.startswith(d) for d in exclude_dirs):
            continue

        for f in filenames:
            rel_path = os.path.relpath(os.path.join(root, f), res_dir)
            files.append(rel_path)

    files.sort()
    with open(lst_file, "w") as f:
        for file in files:
            f.write(file + "\n")

    if verbose:
        print(f"Created package list with {len(files)} files: {lst_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate ICU test data for Bazel")
    parser.add_argument("--src_dir", required=True,
                        help="Source data directory containing BUILDRULES.py")
    parser.add_argument("--tool_dir", required=True,
                        help="Directory containing ICU tools (pkgdata, genccode, etc.)")
    parser.add_argument("--out_dir", required=True,
                        help="Output directory for generated files")
    parser.add_argument("--pkg_name", required=True,
                        help="Package name (e.g., testdata)")
    parser.add_argument("--entry_name", required=True,
                        help="Entry point name for assembly (e.g., testdata)")
    parser.add_argument("--icu_data_file", required=True,
                        help="Path to main ICU data file for genrb collation compilation")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose output")
    args = parser.parse_args()

    verbose: bool = args.verbose

    # Resolve paths
    src_dir = os.path.normpath(args.src_dir)
    tool_dir = os.path.normpath(args.tool_dir)
    out_dir = os.path.normpath(args.out_dir)
    icu_data_file = os.path.normpath(args.icu_data_file)

    # Create temporary working directories
    with tempfile.TemporaryDirectory() as tmp_base:
        work_out_dir = os.path.join(tmp_base, "out", args.pkg_name)
        work_tmp_dir = os.path.join(tmp_base, "tmp")
        os.makedirs(work_out_dir)
        os.makedirs(work_tmp_dir)

        # Set up build directory with main ICU data for genrb to use
        # genrb needs this to compile collation tailoring rules
        build_dir = os.path.join(work_out_dir, "build")
        os.makedirs(build_dir)
        shutil.copy(icu_data_file, build_dir)
        if verbose:
            print(f"Copied ICU data file to build dir: {icu_data_file} -> {build_dir}")

        # Step 1: Run databuilder
        run_databuilder(src_dir, work_out_dir, work_tmp_dir, tool_dir, verbose)

        # Step 2: Create package list (exclude build directory)
        lst_file = os.path.join(work_tmp_dir, f"{args.pkg_name}.lst")
        create_package_list(work_out_dir, lst_file, exclude_dirs=["build"],
                            verbose=verbose)

        # Step 3: Run pkgdata
        pkgdata_bin = os.path.join(tool_dir, "pkgdata")
        run_pkgdata(pkgdata_bin, work_out_dir, lst_file, args.pkg_name,
                    work_tmp_dir, verbose)

        # Step 4: Run genccode
        dat_file = os.path.join(work_tmp_dir, f"{args.pkg_name}.dat")
        genccode_bin = os.path.join(tool_dir, "genccode")
        os.makedirs(out_dir, exist_ok=True)
        run_genccode(genccode_bin, dat_file, args.entry_name, out_dir, verbose)

        # Step 5: Copy .dat file to output (under out/testdata.dat structure)
        dat_out_dir = os.path.join(out_dir, "out")
        os.makedirs(dat_out_dir, exist_ok=True)
        shutil.copy(dat_file, os.path.join(dat_out_dir, f"{args.pkg_name}.dat"))
        if verbose:
            print(f"Copied .dat file to: {dat_out_dir}")

        # Step 6: Copy standalone test files that tests expect outside .dat package
        # These are TmpFile outputs from the databuilder
        standalone_files = [
            ("zoneinfo64.res", f"out/{args.pkg_name}/zoneinfo64.res"),
            ("nam.typ", f"out/{args.pkg_name}/nam.typ"),
        ]
        for src_name, dst_rel_path in standalone_files:
            src_path = os.path.join(work_tmp_dir, src_name)
            if os.path.exists(src_path):
                dst_path = os.path.join(out_dir, dst_rel_path)
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                shutil.copy(src_path, dst_path)
                if verbose:
                    print(f"Copied standalone file: {src_path} -> {dst_path}")
            else:
                print(f"Warning: Standalone file not found: {src_path}", file=sys.stderr)

    if verbose:
        print("Test data generation complete.")


if __name__ == "__main__":
    main()
