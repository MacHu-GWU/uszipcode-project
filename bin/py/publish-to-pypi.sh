#!/bin/bash
# -*- coding: utf-8 -*-
#
# Publish this Package to https://pypi.org/

dir_here="$( cd "$(dirname "$0")" ; pwd -P )"
dir_bin="$(dirname "${dir_here}")"
dir_project_root=$(dirname "${dir_bin}")

source ${dir_bin}/py/python-env.sh

print_colored_line $color_cyan "[DOING] Publish ${package_name} to https://pypi.org ..."
rm_if_exists $path_build_dir
rm_if_exists $path_dist_dir
rm_if_exists $path_egg_dir
(
    cd ${dir_project_root};
    ${bin_python} setup.py sdist bdist_wheel --universal;
    ${bin_twine} upload dist/*;
)
rm_if_exists $path_build_dir
rm_if_exists $path_dist_dir
rm_if_exists $path_egg_dir
