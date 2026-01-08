#include "tools/cpp/runfiles/runfiles.h"
#include <string>
#include <memory>
#include <cstdio>

static std::string gIcuDataPath;

extern "C" const char* get_icudt_path(const char* argv0) {
    using bazel::tools::cpp::runfiles::Runfiles;
    std::string error;
    Runfiles* runfiles = Runfiles::Create(argv0, &error);
    if (runfiles == nullptr) {
        fprintf(stderr, "Runfiles::Create error: %s\n", error.c_str());
        return nullptr;
    }
    // Try with 'icu' repo name
    gIcuDataPath = runfiles->Rlocation("icu/icu4c/source/data/out/build/icudt79l");
    if (gIcuDataPath.empty()) {
         gIcuDataPath = runfiles->Rlocation("icu4c/source/data/out/build/icudt79l");
    }
    delete runfiles;
    return gIcuDataPath.c_str();
}
