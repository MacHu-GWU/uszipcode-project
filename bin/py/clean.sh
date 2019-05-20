#!/bin/bash
# -*- coding: utf-8 -*-
#
# Clean up all temp dir and files (except virtualenv)

dir_here="$( cd "$(dirname "$0")" ; pwd -P )"
dir_bin="$(dirname "${dir_here}")"
dir_project_root=$(dirname "${dir_bin}")

source ${dir_bin}/py/python-env.sh

print_colored_line $color_cyan "[DOING] remove all temp files ..."

tmp_to_remove_list=(
    ${path_coverage_annotate_dir}
    ${path_tox_dir}
    ${path_build_dir}
    ${path_dist_dir}
    ${path_egg_dir}
    ${path_pytest_cache_dir}
    ${path_sphinx_doc_build}
    ${path_lambda_deploy_pkg_file}
)

for tmp_path in "${tmp_to_remove_list[@]}"
do
    echo "remove ${tmp_path}"
    rm_if_exists ${tmp_path}
done
