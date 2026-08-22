"""
Verify that `alr clean` does not rehash shared dependencies from the
environment it exports before generating the build configuration.
"""

import os

from drivers import builds
from drivers.alr import alr_with, init_local_crate, run_alr
from drivers.asserts import assert_file_exists


init_local_crate()
alr_with("envdep")

# Make gprclean require an environment variable exported by the dependency.
with open("xxx.gpr", "r+") as project:
    contents = project.read()
    project.seek(0)
    project.write(contents.replace(
        "project Xxx is",
        'project Xxx is\n\n   Envdep_Share := external ("ENVDEP_SHARE");'))
    project.truncate()

# Deploy the shared dependency without running its pre-build action.
run_alr("build", "--stop-after=generation")

build_dir = builds.find_dir("envdep")
assert_file_exists(os.path.join(build_dir, "alire", "flags", "complete_copy"))
assert_file_exists(os.path.join(build_dir, "pre_build_ran"), wanted=False)
hash_input = builds.hash_input("envdep")
assert "environment:ENVDEP_INCLUDE=envdep_1.0.0_filesystem/include" in hash_input
assert "environment:ENVDEP_SHARE=envdep_1.0.0_filesystem/share" in hash_input
assert build_dir not in hash_input

# A fresh `alr clean` process must retain the same normalized build hash. In
# particular, its own exported ENVDEP_* values must not become hash inputs.
run_alr("clean")

assert builds.find_dir("envdep") == build_dir
assert_file_exists(os.path.join(build_dir, "pre_build_ran"), wanted=False)

print("SUCCESS")
