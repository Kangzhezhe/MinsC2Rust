# Test Project

This minimal C project exercises handling of duplicate source filenames located in different directories.

## Layout

- `include/` holds shared headers that are referenced by each module.
- `src/module_a/shared.c` and `src/module_b/shared.c` share the same filename but provide distinct implementations.
- `src/main.c` links the two modules and verifies their outputs at runtime.

A simple `CMakeLists.txt` is provided so the project can be configured and built with CMake.
