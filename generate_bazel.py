import os
import glob

def read_sources(filepath):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return []
    with open(filepath, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

def extract_objects_from_makefile(filepath):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return []

    objects = []
    with open(filepath, 'r') as f:
        content = f.read()

    import re
    content = content.replace('\\\n', ' ')
    match = re.search(r'OBJECTS\s*=\s*(.*?)(?:\n\S|\Z)', content, re.DOTALL)
    if match:
        obj_block = match.group(1)
        for obj in obj_block.split():
            if obj.endswith('.o'):
                objects.append(obj.replace('.o', '.cpp'))

    return objects

def get_headers(directory):
    headers = []
    if os.path.exists(directory):
        for f in os.listdir(directory):
            if f.endswith('.h') or f.endswith('.inc') or f.endswith('.hpp'):
                headers.append(f)
    return headers

def write_build_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)

    if path.startswith("bazel/"):
        source_path = path[6:]
        if os.path.exists(os.path.dirname(source_path)):
            if os.path.exists(source_path) or os.path.islink(source_path):
                os.remove(source_path)
            target = os.path.relpath(path, os.path.dirname(source_path))
            os.symlink(target, source_path)
            print(f"Symlinked {source_path} -> {target}")

# Data Packages
def create_data_package(path):
    if not os.path.exists(path):
        return
    content = """package(default_visibility = ["//visibility:public"])
exports_files(glob(["**"]))
"""
    build_path = os.path.join("bazel", path, "BUILD.bazel")
    write_build_file(build_path, content)

create_data_package("icu4c/source/data")
create_data_package("icu4c/source/test/testdata")

# Common
common_srcs = read_sources("icu4c/source/common/sources.txt")
common_srcs_formatted = ',\n        '.join([f'"{s}"' for s in common_srcs])
common_hdrs = get_headers("icu4c/source/common/unicode")
common_hdrs_internal = get_headers("icu4c/source/common")
common_hdrs_formatted = ',\n        '.join([f'"unicode/{h}"' for h in common_hdrs] +
                                        [f'"{h}"' for h in common_hdrs_internal])

common_build = f"""load("@rules_cc//cc:defs.bzl", "cc_library")

package(default_visibility = ["//visibility:public"])

cc_library(
    name = "common_headers",
    hdrs = [
        {common_hdrs_formatted}
    ],
    includes = ["."],
    copts = [
        "-Iicu4c/source/common",
    ],
)

cc_library(
    name = "common",
    srcs = [
        {common_srcs_formatted}
    ],
    hdrs = [
        {common_hdrs_formatted}
    ],
    includes = ["."],
    copts = [
        "-DU_COMMON_IMPLEMENTATION",
    ],
    deps = [
        "//icu4c/source/stubdata:stubdata",
        ":common_headers",
    ],
)
"""
write_build_file("bazel/icu4c/source/common/BUILD.bazel", common_build)

# I18n
i18n_srcs = read_sources("icu4c/source/i18n/sources.txt")
i18n_srcs_formatted = ',\n        '.join([f'"{s}"' for s in i18n_srcs])
i18n_hdrs = get_headers("icu4c/source/i18n/unicode")
i18n_hdrs_internal = get_headers("icu4c/source/i18n")
i18n_hdrs_formatted = ',\n        '.join([f'"unicode/{h}"' for h in i18n_hdrs] +
                                      [f'"{h}"' for h in i18n_hdrs_internal])

i18n_build = f"""load("@rules_cc//cc:defs.bzl", "cc_library")

package(default_visibility = ["//visibility:public"])

cc_library(
    name = "i18n",
    srcs = [
        {i18n_srcs_formatted}
    ],
    hdrs = [
        {i18n_hdrs_formatted}
    ],
    includes = ["."],
    copts = [
        "-DU_I18N_IMPLEMENTATION",
    ],
    deps = [
        "//icu4c/source/common:common",
    ],
)
"""
write_build_file("bazel/icu4c/source/i18n/BUILD.bazel", i18n_build)

# IO
io_srcs = read_sources("icu4c/source/io/sources.txt")
io_srcs_formatted = ',\n        '.join([f'"{s}"' for s in io_srcs])
io_hdrs = get_headers("icu4c/source/io/unicode")
io_hdrs_internal = get_headers("icu4c/source/io")
io_hdrs_formatted = ',\n        '.join([f'"unicode/{h}"' for h in io_hdrs] +
                                    [f'"{h}"' for h in io_hdrs_internal])

io_build = f"""load("@rules_cc//cc:defs.bzl", "cc_library")

package(default_visibility = ["//visibility:public"])

cc_library(
    name = "io",
    srcs = [
        {io_srcs_formatted}
    ],
    hdrs = [
        {io_hdrs_formatted}
    ],
    includes = ["."],
    copts = [
        "-DU_IO_IMPLEMENTATION",
    ],
    deps = [
        "//icu4c/source/common:common",
        "//icu4c/source/i18n:i18n",
    ],
)
"""
write_build_file("bazel/icu4c/source/io/BUILD.bazel", io_build)

# Stubdata
stubdata_srcs = read_sources("icu4c/source/stubdata/sources.txt")
stubdata_srcs_formatted = ',\n        '.join([f'"{s}"' for s in stubdata_srcs])
stubdata_hdrs = get_headers("icu4c/source/stubdata")
stubdata_hdrs_formatted = ',\n        '.join([f'"{h}"' for h in stubdata_hdrs])

stubdata_build = f"""load("@rules_cc//cc:defs.bzl", "cc_library")

package(default_visibility = ["//visibility:public"])

cc_library(
    name = "stubdata",
    srcs = [
        {stubdata_srcs_formatted}
    ],
    hdrs = [
        {stubdata_hdrs_formatted}
    ],
    includes = ["."],
    deps = [
        "//icu4c/source/common:common_headers",
    ],
    linkstatic = 1,
)
"""
write_build_file("bazel/icu4c/source/stubdata/BUILD.bazel", stubdata_build)

# Toolutil
toolutil_srcs = read_sources("icu4c/source/tools/toolutil/sources.txt")
toolutil_srcs_formatted = ',\n        '.join([f'"{s}"' for s in toolutil_srcs])
toolutil_hdrs = get_headers("icu4c/source/tools/toolutil")
toolutil_hdrs_formatted = ',\n        '.join([f'"{h}"' for h in toolutil_hdrs])

toolutil_build = f"""load("@rules_cc//cc:defs.bzl", "cc_library")

package(default_visibility = ["//visibility:public"])

cc_library(
    name = "toolutil",
    srcs = [
        {toolutil_srcs_formatted}
    ],
    hdrs = [
        {toolutil_hdrs_formatted}
    ],
    includes = ["."],
    copts = [
        "-DU_TOOLUTIL_IMPLEMENTATION",
    ],
    deps = [
        "//icu4c/source/common:common",
        "//icu4c/source/i18n:i18n",
    ],
)
"""
write_build_file("bazel/icu4c/source/tools/toolutil/BUILD.bazel", toolutil_build)

# Ctestfw
ctestfw_srcs = read_sources("icu4c/source/tools/ctestfw/sources.txt")
ctestfw_srcs_formatted = ',\n        '.join([f'"{s}"' for s in ctestfw_srcs])
ctestfw_hdrs = get_headers("icu4c/source/tools/ctestfw")
ctestfw_hdrs_unicode = get_headers("icu4c/source/tools/ctestfw/unicode")
ctestfw_hdrs_formatted = ',\n        '.join([f'"{h}"' for h in ctestfw_hdrs] +
                                           [f'"unicode/{h}"' for h in ctestfw_hdrs_unicode])

ctestfw_build = f"""load("@rules_cc//cc:defs.bzl", "cc_library")

package(default_visibility = ["//visibility:public"])

cc_library(
    name = "ctestfw",
    srcs = [
        {ctestfw_srcs_formatted}
    ],
    hdrs = [
        {ctestfw_hdrs_formatted}
    ],
    includes = ["."],
    deps = [
        "//icu4c/source/common:common",
        "//icu4c/source/i18n:i18n",
        "//icu4c/source/tools/toolutil:toolutil",
    ],
)
"""
write_build_file("bazel/icu4c/source/tools/ctestfw/BUILD.bazel", ctestfw_build)

# Data
data_files = []
def add_data_files(path):
    if os.path.exists(path):
        for root, dirs, files in os.walk(path):
            for f in files:
                full_path = os.path.join(root, f)
                pkg = ""
                rel_path = ""
                if full_path.startswith("icu4c/source/test/testdata"):
                    pkg = "icu4c/source/test/testdata"
                    rel_path = os.path.relpath(full_path, pkg)
                elif full_path.startswith("icu4c/source/data"):
                    pkg = "icu4c/source/data"
                    rel_path = os.path.relpath(full_path, pkg)
                else:
                    continue
                data_files.append(f'"//{pkg}:{rel_path}"')

add_data_files("icu4c/source/data/out/build/icudt79l")
add_data_files("icu4c/source/test/testdata/out")

if os.path.exists("icu4c/source/test/testdata"):
    for root, dirs, files in os.walk("icu4c/source/test/testdata"):
        if "/out" in root.replace(os.sep, "/"):
            continue
        for f in files:
            full_path = os.path.join(root, f)
            pkg = "icu4c/source/test/testdata"
            rel_path = os.path.relpath(full_path, pkg)
            data_files.append(f'"//{pkg}:{rel_path}"')

if os.path.exists("icu4c/source/data"):
    for root, dirs, files in os.walk("icu4c/source/data"):
        if "/out" in root.replace(os.sep, "/"):
            continue
        for f in files:
            full_path = os.path.join(root, f)
            pkg = "icu4c/source/data"
            rel_path = os.path.relpath(full_path, pkg)
            data_files.append(f'"//{pkg}:{rel_path}"')

data_files = sorted(list(set(data_files)))
data_files_formatted = ',\n        '.join(data_files)

# Cintltst
cintltst_objs = extract_objects_from_makefile("icu4c/source/test/cintltst/Makefile.in")
cintltst_srcs = []
for obj in cintltst_objs:
    if os.path.exists(f"icu4c/source/test/cintltst/{obj.replace('.cpp', '.c')}"):
        cintltst_srcs.append(obj.replace('.cpp', '.c'))
    else:
        cintltst_srcs.append(obj)

cintltst_srcs_formatted = ',\n        '.join([f'"{s}"' for s in cintltst_srcs])
cintltst_hdrs = get_headers("icu4c/source/test/cintltst")
cintltst_hdrs_formatted = ',\n        '.join([f'"{h}"' for h in cintltst_hdrs])

cintltst_build = f"""load("@rules_cc//cc:defs.bzl", "cc_library", "cc_test")

package(default_visibility = ["//visibility:public"])

cc_library(
    name = "cintltst_headers",
    hdrs = [
        {cintltst_hdrs_formatted}
    ],
    includes = ["."],
)

cc_test(
    name = "cintltst",
    srcs = [
        {cintltst_srcs_formatted},
        "runfiles_helper.cpp",
        {cintltst_hdrs_formatted}
    ],
    includes = ["."],
    copts = [
        "-DU_TOPSRCDIR=\\\\\\"icu4c/source/\\\\\\"",
    ],
    deps = [
        "//icu4c/source/common:common",
        "//icu4c/source/i18n:i18n",
        "//icu4c/source/tools/toolutil:toolutil",
        "//icu4c/source/tools/ctestfw:ctestfw",
        "@bazel_tools//tools/cpp/runfiles",
    ],
    data = [
        {data_files_formatted}
    ],
    env = {{
        "ICU_DATA": "icu4c/source/data/out/build/icudt79l"
    }},
    args = ["-w"]
)
"""
write_build_file("bazel/icu4c/source/test/cintltst/BUILD.bazel", cintltst_build)

# Intltest
intltest_objs = extract_objects_from_makefile("icu4c/source/test/intltest/Makefile.in")
intltest_srcs = [obj for obj in intltest_objs]
intltest_srcs_formatted = ',\n        '.join([f'"{s}"' for s in intltest_srcs])
intltest_hdrs = get_headers("icu4c/source/test/intltest")
intltest_hdrs_formatted = ',\n        '.join([f'"{h}"' for h in intltest_hdrs])

intltest_build = f"""load("@rules_cc//cc:defs.bzl", "cc_test")

package(default_visibility = ["//visibility:public"])

cc_test(
    name = "intltest",
    srcs = [
        {intltest_srcs_formatted},
        {intltest_hdrs_formatted}
    ],
    includes = [".", ".."],
    copts = [
        "-DU_TOPSRCDIR=\\\\\\"icu4c/source/\\\\\\"",
    ],
    deps = [
        "//icu4c/source/common:common",
        "//icu4c/source/i18n:i18n",
        "//icu4c/source/io:io",
        "//icu4c/source/tools/toolutil:toolutil",
        "//icu4c/source/tools/ctestfw:ctestfw",
        "//icu4c/source/test/cintltst:cintltst_headers",
        "@bazel_tools//tools/cpp/runfiles",
    ],
    data = [
        {data_files_formatted}
    ],
    env = {{
        "ICU_DATA": "icu4c/source/data/out/build/icudt79l"
    }},
    args = ["-w"]
)
"""
write_build_file("bazel/icu4c/source/test/intltest/BUILD.bazel", intltest_build)
