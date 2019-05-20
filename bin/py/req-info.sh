#!/bin/bash
# -*- coding: utf-8 -*-

dir_here="$( cd "$(dirname "$0")" ; pwd -P )"
dir_bin="$(dirname "${dir_here}")"
dir_project_root=$(dirname "${dir_bin}")

source ${dir_bin}/py/python-env.sh

print_colored_line ${color_yellow} "--- $(basename ${path_requirement_file}) ---"
cat ${path_requirement_file}
print_colored_line ${color_yellow} "--- $(basename ${path_dev_requirement_file}) ---"
cat ${path_dev_requirement_file}
print_colored_line ${color_yellow} "--- $(basename ${path_doc_requirement_file}) ---"
cat ${path_doc_requirement_file}
print_colored_line ${color_yellow} "--- $(basename ${path_test_requirement_file}) ---"
cat ${path_test_requirement_file}
