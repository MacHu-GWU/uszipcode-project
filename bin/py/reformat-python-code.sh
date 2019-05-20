#!/bin/bash
# -*- coding: utf-8 -*-
#
# Apply pep8 (https://www.python.org/dev/peps/pep-0008/)
# to source code and tests
# using https://pypi.org/project/autopep8

dir_here="$( cd "$(dirname "$0")" ; pwd -P )"
dir_bin="$(dirname "${dir_here}")"
dir_project_root=$(dirname "${dir_bin}")

source ${dir_bin}/py/python-env.sh

print_colored_line $color_cyan "[DOING] reformat python code style, execute ${path_auto_pep8_script} ..."
${bin_python} ${path_auto_pep8_script}
