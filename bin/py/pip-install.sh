#!/bin/bash
# -*- coding: utf-8 -*-

dir_here="$( cd "$(dirname "$0")" ; pwd -P )"
dir_bin="$(dirname "${dir_here}")"
dir_project_root=$(dirname "${dir_bin}")

source ${dir_bin}/py/python-env.sh

print_colored_line $color_cyan "[DOING] pip install ${package_name} ..."
${bin_pip} install ${dir_project_root}
