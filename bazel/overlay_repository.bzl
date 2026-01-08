MAX_TRAVERSAL_STEPS = 1000

def _icu_overlay_impl(repository_ctx):
    # bazel/MODULE.bazel is the anchor.
    # We want the parent of the directory containing MODULE.bazel.
    bazel_dir = repository_ctx.path(Label("@//:MODULE.bazel")).dirname
    src_root = bazel_dir.get_child("..")

    overlay_root = bazel_dir

    # We want to traverse `icu4c` directory in `src_root`.

    stack = ["icu4c"]

    for _ in range(MAX_TRAVERSAL_STEPS):
        if not stack:
            break
        rel_dir = stack.pop()

        # Check if this dir exists in overlay (bazel/)
        overlay_dir = overlay_root.get_child(rel_dir)
        has_overlay = overlay_dir.exists and overlay_dir.is_dir

        # Check source dir
        src_dir = src_root.get_child(rel_dir)

        # List source entries
        src_names = []
        if src_dir.exists and src_dir.is_dir:
            src_entries = src_dir.readdir()
            src_names = [e.basename for e in src_entries]

        # List overlay entries
        overlay_names = []
        if has_overlay:
            overlay_entries = overlay_dir.readdir()
            overlay_names = [e.basename for e in overlay_entries]

        all_names = sorted(list(set(src_names + overlay_names)))

        for name in all_names:
            full_rel_path = rel_dir + "/" + name

            is_in_overlay = name in overlay_names
            is_in_src = name in src_names

            # Use overlay version if present, unless we need to merge directories.
            # We merge directories if they exist in BOTH.

            # Check directory status
            is_dir_overlay = False
            if is_in_overlay:
                is_dir_overlay = overlay_root.get_child(full_rel_path).is_dir

            is_dir_src = False
            if is_in_src:
                is_dir_src = src_root.get_child(full_rel_path).is_dir

            if is_in_overlay and is_in_src and is_dir_overlay and is_dir_src:
                # Both are directories, recurse
                stack.append(full_rel_path)
            elif is_in_overlay:
                # Use overlay version (dir or file)
                # repository_ctx.symlink target is RELATIVE to the repo root (which is empty initially).
                repository_ctx.symlink(overlay_root.get_child(full_rel_path), full_rel_path)
            elif is_in_src:
                # Use source version (dir or file)
                repository_ctx.symlink(src_root.get_child(full_rel_path), full_rel_path)

    # Apply patches
    patches = [
        "patches/intltest.patch",
        "patches/cintltst.patch",
    ]
    for patch in patches:
        patch_path = overlay_root.get_child(patch)
        if patch_path.exists:
            repository_ctx.patch(patch_path, strip=1)

icu_overlay = repository_rule(
    implementation = _icu_overlay_impl,
)
