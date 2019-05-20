#!/bin/bash
# -*- coding: utf-8 -*-
#
# Run Jupyter notebook

dir_here="$( cd "$(dirname "$0")" ; pwd -P )"
dir_bin="$(dirname "${dir_here}")"
dir_project_root=$(dirname "${dir_bin}")

source ${dir_bin}/py/python-env.sh

print_colored_line $color_cyan "[DOING] Run Jupyter Notebook locally ..."
${bin_pip} install jupyter
${bin_jupyter} notebook
