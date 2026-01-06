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
            # Include .h, .inc, .hpp files
            if f.endswith('.h') or f.endswith('.inc') or f.endswith('.hpp'):
                headers.append(f)
    return headers

def write_build_file(path, content):
    with open(path, 'w') as f:
        f.write(content)

# Common
common_srcs = read_sources("icu4c/source/common/sources.txt")
common_srcs_formatted = ',\n        '.join([f'"//:icu4c/source/common/{s}"' for s in common_srcs])
common_hdrs = get_headers("icu4c/source/common/unicode")
common_hdrs_internal = get_headers("icu4c/source/common")
common_hdrs_formatted = ',\n        '.join([f'"//:icu4c/source/common/unicode/{h}"' for h in common_hdrs] +
                                        [f'"//:icu4c/source/common/{h}"' for h in common_hdrs_internal])

common_build = f"""load("@rules_cc//cc:defs.bzl", "cc_library")

package(default_visibility = ["//visibility:public"])

cc_library(
    name = "common_headers",
    hdrs = [
        {common_hdrs_formatted}
    ],
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
    copts = [
        "-DU_COMMON_IMPLEMENTATION",
        "-Iicu4c/source/common",
        "-Iicu4c/source/i18n",
    ],
    deps = [
        "//bazel/icu4c/source/stubdata:stubdata",
        ":common_headers",
    ],
)
"""
write_build_file("bazel/icu4c/source/common/BUILD.bazel", common_build)

# I18n
i18n_srcs = read_sources("icu4c/source/i18n/sources.txt")
i18n_srcs_formatted = ',\n        '.join([f'"//:icu4c/source/i18n/{s}"' for s in i18n_srcs])
i18n_hdrs = get_headers("icu4c/source/i18n/unicode")
i18n_hdrs_internal = get_headers("icu4c/source/i18n")
i18n_hdrs_formatted = ',\n        '.join([f'"//:icu4c/source/i18n/unicode/{h}"' for h in i18n_hdrs] +
                                      [f'"//:icu4c/source/i18n/{h}"' for h in i18n_hdrs_internal])

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
    copts = [
        "-DU_I18N_IMPLEMENTATION",
        "-Iicu4c/source/common",
        "-Iicu4c/source/i18n",
    ],
    deps = [
        "//bazel/icu4c/source/common:common",
    ],
)
"""
write_build_file("bazel/icu4c/source/i18n/BUILD.bazel", i18n_build)

# IO
io_srcs = read_sources("icu4c/source/io/sources.txt")
io_srcs_formatted = ',\n        '.join([f'"//:icu4c/source/io/{s}"' for s in io_srcs])
io_hdrs = get_headers("icu4c/source/io/unicode")
io_hdrs_internal = get_headers("icu4c/source/io")
io_hdrs_formatted = ',\n        '.join([f'"//:icu4c/source/io/unicode/{h}"' for h in io_hdrs] +
                                    [f'"//:icu4c/source/io/{h}"' for h in io_hdrs_internal])

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
    copts = [
        "-DU_IO_IMPLEMENTATION",
        "-Iicu4c/source/common",
        "-Iicu4c/source/i18n",
        "-Iicu4c/source/io",
    ],
    deps = [
        "//bazel/icu4c/source/common:common",
        "//bazel/icu4c/source/i18n:i18n",
    ],
)
"""
write_build_file("bazel/icu4c/source/io/BUILD.bazel", io_build)

# Stubdata
stubdata_srcs = read_sources("icu4c/source/stubdata/sources.txt")
stubdata_srcs_formatted = ',\n        '.join([f'"//:icu4c/source/stubdata/{s}"' for s in stubdata_srcs])
stubdata_hdrs = get_headers("icu4c/source/stubdata")
stubdata_hdrs_formatted = ',\n        '.join([f'"//:icu4c/source/stubdata/{h}"' for h in stubdata_hdrs])

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
    copts = [
        "-Iicu4c/source/common",
    ],
    deps = [
        "//bazel/icu4c/source/common:common_headers",
    ],
    linkstatic = 1,
)
"""
write_build_file("bazel/icu4c/source/stubdata/BUILD.bazel", stubdata_build)

# Toolutil
toolutil_srcs = read_sources("icu4c/source/tools/toolutil/sources.txt")
toolutil_srcs_formatted = ',\n        '.join([f'"//:icu4c/source/tools/toolutil/{s}"' for s in toolutil_srcs])
toolutil_hdrs = get_headers("icu4c/source/tools/toolutil")
toolutil_hdrs_formatted = ',\n        '.join([f'"//:icu4c/source/tools/toolutil/{h}"' for h in toolutil_hdrs])

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
    copts = [
        "-DU_TOOLUTIL_IMPLEMENTATION",
        "-Iicu4c/source/common",
        "-Iicu4c/source/i18n",
        "-Iicu4c/source/tools/toolutil",
    ],
    deps = [
        "//bazel/icu4c/source/common:common",
        "//bazel/icu4c/source/i18n:i18n",
    ],
)
"""
write_build_file("bazel/icu4c/source/tools/toolutil/BUILD.bazel", toolutil_build)

# Ctestfw
ctestfw_srcs = read_sources("icu4c/source/tools/ctestfw/sources.txt")
ctestfw_srcs_formatted = ',\n        '.join([f'"//:icu4c/source/tools/ctestfw/{s}"' for s in ctestfw_srcs])
ctestfw_hdrs = get_headers("icu4c/source/tools/ctestfw")
ctestfw_hdrs_unicode = get_headers("icu4c/source/tools/ctestfw/unicode")
ctestfw_hdrs_formatted = ',\n        '.join([f'"//:icu4c/source/tools/ctestfw/{h}"' for h in ctestfw_hdrs] +
                                           [f'"//:icu4c/source/tools/ctestfw/unicode/{h}"' for h in ctestfw_hdrs_unicode])

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
    copts = [
        "-Iicu4c/source/common",
        "-Iicu4c/source/i18n",
        "-Iicu4c/source/tools/toolutil",
        "-Iicu4c/source/tools/ctestfw",
    ],
    deps = [
        "//bazel/icu4c/source/common:common",
        "//bazel/icu4c/source/i18n:i18n",
        "//bazel/icu4c/source/tools/toolutil:toolutil",
    ],
)
"""
write_build_file("bazel/icu4c/source/tools/ctestfw/BUILD.bazel", ctestfw_build)

# Cintltst
cintltst_objs = extract_objects_from_makefile("icu4c/source/test/cintltst/Makefile.in")
cintltst_srcs = []
for obj in cintltst_objs:
    if os.path.exists(f"icu4c/source/test/cintltst/{obj.replace('.cpp', '.c')}"):
        cintltst_srcs.append(obj.replace('.cpp', '.c'))
    else:
        cintltst_srcs.append(obj)

cintltst_srcs_formatted = ',\n        '.join([f'"//:icu4c/source/test/cintltst/{s}"' for s in cintltst_srcs])
cintltst_hdrs = get_headers("icu4c/source/test/cintltst")
cintltst_hdrs_formatted = ',\n        '.join([f'"//:icu4c/source/test/cintltst/{h}"' for h in cintltst_hdrs])

# Get data files (built data + test data + source/data)
data_files = []
# Built data
data_path = "icu4c/source/data/out/build/icudt79l"
if os.path.exists(data_path):
    for root, dirs, files in os.walk(data_path):
        for f in files:
            full_path = os.path.join(root, f)
            data_files.append(f'"//:{full_path}"')

# Test data (built)
test_data_out_path = "icu4c/source/test/testdata/out"
if os.path.exists(test_data_out_path):
    for root, dirs, files in os.walk(test_data_out_path):
        for f in files:
            full_path = os.path.join(root, f)
            data_files.append(f'"//:{full_path}"')

# Test data (raw)
test_data_path = "icu4c/source/test/testdata"
if os.path.exists(test_data_path):
    for root, dirs, files in os.walk(test_data_path):
        if "icu4c/source/test/testdata/out" in root:
            continue
        for f in files:
            full_path = os.path.join(root, f)
            data_files.append(f'"//:{full_path}"')

# Source data (needed for some tests reading raw files)
source_data_path = "icu4c/source/data"
if os.path.exists(source_data_path):
    for root, dirs, files in os.walk(source_data_path):
        if "icu4c/source/data/out" in root:
            continue
        for f in files:
            full_path = os.path.join(root, f)
            data_files.append(f'"//:{full_path}"')

data_files_formatted = ',\n        '.join(data_files)

cintltst_build = f"""load("@rules_cc//cc:defs.bzl", "cc_library", "cc_test")

package(default_visibility = ["//visibility:public"])

cc_library(
    name = "cintltst_headers",
    hdrs = [
        {cintltst_hdrs_formatted}
    ],
    copts = [
        "-Iicu4c/source/test/cintltst",
    ],
)

cc_test(
    name = "cintltst",
    srcs = [
        {cintltst_srcs_formatted},
        "//:icu4c/source/test/cintltst/runfiles_helper.cpp",
        {cintltst_hdrs_formatted}
    ],
    copts = [
        "-Iicu4c/source/common",
        "-Iicu4c/source/i18n",
        "-Iicu4c/source/tools/toolutil",
        "-Iicu4c/source/tools/ctestfw",
        "-Iicu4c/source/test/cintltst",
        "-DU_TOPSRCDIR=\\\\\\"icu4c/source/\\\\\\"",
    ],
    deps = [
        "//bazel/icu4c/source/common:common",
        "//bazel/icu4c/source/i18n:i18n",
        "//bazel/icu4c/source/tools/toolutil:toolutil",
        "//bazel/icu4c/source/tools/ctestfw:ctestfw",
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
intltest_srcs_formatted = ',\n        '.join([f'"//:icu4c/source/test/intltest/{s}"' for s in intltest_srcs])
intltest_hdrs = get_headers("icu4c/source/test/intltest")
intltest_hdrs_formatted = ',\n        '.join([f'"//:icu4c/source/test/intltest/{h}"' for h in intltest_hdrs])

intltest_build = f"""load("@rules_cc//cc:defs.bzl", "cc_test")

package(default_visibility = ["//visibility:public"])

cc_test(
    name = "intltest",
    srcs = [
        {intltest_srcs_formatted},
        {intltest_hdrs_formatted}
    ],
    copts = [
        "-Iicu4c/source/common",
        "-Iicu4c/source/i18n",
        "-Iicu4c/source/io",
        "-Iicu4c/source/tools/toolutil",
        "-Iicu4c/source/tools/ctestfw",
        "-Iicu4c/source/test/intltest",
        "-Iicu4c/source/test",
        "-DUNISTR_FROM_CHAR_EXPLICIT=",
        "-DUNISTR_FROM_STRING_EXPLICIT=",
        "-DU_TOPSRCDIR=\\\\\\"icu4c/source/\\\\\\"",
    ],
    deps = [
        "//bazel/icu4c/source/common:common",
        "//bazel/icu4c/source/i18n:i18n",
        "//bazel/icu4c/source/io:io",
        "//bazel/icu4c/source/tools/toolutil:toolutil",
        "//bazel/icu4c/source/tools/ctestfw:ctestfw",
        "//bazel/icu4c/source/test/cintltst:cintltst_headers",
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
