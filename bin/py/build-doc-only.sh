#!/bin/bash
# -*- coding: utf-8 -*-

dir_here="$( cd "$(dirname "$0")" ; pwd -P )"
dir_bin="$(dirname "${dir_here}")"
dir_project_root=$(dirname "${dir_bin}")

source ${dir_bin}/py/python-env.sh

print_colored_line $color_cyan "[DOING] Build doc at ${path_sphinx_index_html} ..."

rm_if_exists "${path_sphinx_doc_source}/${package_name}"
(
    source ${bin_activate};
    cd ${path_sphinx_doc};
    make html;
)
