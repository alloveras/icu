# Copyright (C) 2024 and later: Unicode, Inc. and others.
# License & terms of use: http://www.unicode.org/copyright.html

"""Wrapper script for generating ICU data in Bazel.

This script orchestrates the ICU data generation pipeline:
1. databuilder - generates .res files from source data
2. pkgdata - packages .res files into a .dat archive
3. genccode - converts .dat to assembly for static linking

The script handles directory setup and path manipulation to match
each tool's expectations.
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
    include_uni_core_data: bool,
    verbose: bool = False,
) -> None:
    """Run the databuilder to generate .res files."""
    # Import databuilder module directly to avoid subprocess issues with Bazel
    # Add the python directory to path so we can import icutools
    python_dir = os.path.join(os.path.dirname(__file__), "..", "python")
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
    if include_uni_core_data:
        argv.append("--include_uni_core_data")
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


def get_assembly_type() -> str | None:
    """Get the assembly type for the current platform.

    Returns the genccode --assembly flag value, or None if the platform
    uses direct object file generation (Windows with MSVC).
    """
    system = platform.system()
    if system == "Linux":
        return "gcc"
    elif system == "Darwin":
        return "gcc-darwin"
    elif system == "Windows":
        # Windows with MSVC generates .obj files directly, no assembly flag needed
        return None
    else:
        # Default to gcc for other Unix-like systems
        return "gcc"


def run_genccode(
    genccode_bin: str,
    dat_file: str,
    entry_name: str,
    out_dir: str,
    verbose: bool = False,
) -> str:
    """Run genccode to convert .dat to object code.

    Returns the name of the output file (without directory).
    """
    assembly_type = get_assembly_type()

    cmd = [genccode_bin]

    if assembly_type:
        # Unix: generate assembly file
        cmd.extend(["--assembly", assembly_type])
    # Windows: no --assembly flag means generate .obj directly

    cmd.extend([
        "--name", entry_name,
        "--entrypoint", entry_name,
        "--destdir", out_dir,
        dat_file,
    ])

    if verbose:
        cmd.insert(1, "-v")
        print(f"Running: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if verbose and result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        sys.exit(result.returncode)

    # Return the output filename based on platform
    dat_basename = os.path.splitext(os.path.basename(dat_file))[0]
    if assembly_type:
        return f"{dat_basename}_dat.S"
    else:
        return f"{dat_basename}_dat.obj"


def create_package_list(
    res_dir: str,
    lst_file: str,
    verbose: bool = False,
) -> None:
    """Create a package list file from the .res directory."""
    files: list[str] = []
    for root, _, filenames in os.walk(res_dir):
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
    parser = argparse.ArgumentParser(description="Generate ICU data for Bazel")
    parser.add_argument("--src_dir", required=True,
                        help="Source data directory containing BUILDRULES.py")
    parser.add_argument("--tool_dir", required=True,
                        help="Directory containing ICU tools (pkgdata, genccode, etc.)")
    parser.add_argument("--out_dir", required=True,
                        help="Output directory for .dat and .S files")
    parser.add_argument("--pkg_name", required=True,
                        help="Package name (e.g., icudt79l)")
    parser.add_argument("--entry_name", required=True,
                        help="Entry point name for assembly (e.g., icudt79)")
    parser.add_argument("--include_uni_core_data", action="store_true",
                        help="Include Unicode core data")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose output")
    args = parser.parse_args()

    verbose: bool = args.verbose

    # Resolve paths
    src_dir = os.path.normpath(args.src_dir)
    tool_dir = os.path.normpath(args.tool_dir)
    out_dir = os.path.normpath(args.out_dir)

    # Create temporary working directories
    with tempfile.TemporaryDirectory() as tmp_base:
        work_out_dir = os.path.join(tmp_base, "out", args.pkg_name)
        work_tmp_dir = os.path.join(tmp_base, "tmp")
        os.makedirs(work_out_dir)
        os.makedirs(work_tmp_dir)

        # Step 1: Run databuilder
        run_databuilder(src_dir, work_out_dir, work_tmp_dir, tool_dir,
                        args.include_uni_core_data, verbose)

        # Step 2: Create package list
        lst_file = os.path.join(work_tmp_dir, f"{args.pkg_name}.lst")
        create_package_list(work_out_dir, lst_file, verbose)

        # Step 3: Run pkgdata
        pkgdata_bin = os.path.join(tool_dir, "pkgdata")
        run_pkgdata(pkgdata_bin, work_out_dir, lst_file, args.pkg_name,
                    work_tmp_dir, verbose)

        # Step 4: Run genccode
        dat_file = os.path.join(work_tmp_dir, f"{args.pkg_name}.dat")
        genccode_bin = os.path.join(tool_dir, "genccode")
        os.makedirs(out_dir, exist_ok=True)
        run_genccode(genccode_bin, dat_file, args.entry_name, out_dir, verbose)

        # Step 5: Copy .dat file to output directory
        shutil.copy(dat_file, out_dir)
        if verbose:
            print(f"Copied .dat file to: {out_dir}")

    if verbose:
        print("Data generation complete.")


if __name__ == "__main__":
    main()
