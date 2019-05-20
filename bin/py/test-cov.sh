#!/bin/bash
# -*- coding: utf-8 -*-

dir_here="$( cd "$(dirname "$0")" ; pwd -P )"
dir_bin="$(dirname "${dir_here}")"
dir_project_root=$(dirname "${dir_bin}")

source ${dir_bin}/py/python-env.sh

print_colored_line $color_cyan "[DOING] Run code coverage tests in ${path_test_dir} ..."
cd ${dir_project_root}
rm -r ${path_coverage_annotate_dir}
${bin_pytest} ${path_test_dir} -s --cov=${package_name} --cov-report term-missing --cov-report annotate:${path_coverage_annotate_dir}
